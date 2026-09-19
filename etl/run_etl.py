"""
run_etl.py

Main ETL entry point. Run monthly (locally now, via Lambda/EventBridge later).

Pipeline:
  1. For each food in foods_seed.FOODS:
     a. If avg_price_series_id is set and price_verified=True, fetch BLS
        Average Price data -> $ figure for the latest month.
     b. If cpi_series_id is set, fetch BLS CPI data -> YoY % change.
     c. Fetch/refresh nutrition from USDA FDC (this barely changes month to
        month, but re-fetching monthly is cheap and keeps it self-healing).
  2. Upsert everything into SQLite.
  3. Export a flat JSON file for the static site build to consume.

Usage:
    export BLS_API_KEY=...      # optional but recommended
    export FDC_API_KEY=...      # optional but recommended (else DEMO_KEY)
    python run_etl.py

Design notes:
  - Foods with price_verified=False are SKIPPED for price data and logged
    loudly, rather than silently fetching a possibly-wrong series. Fix the
    series ID in foods_seed.py, confirm it on FRED/BLS, then flip the flag.
  - Foods with no avg_price_series_id at all get price_source='estimate'
    and a NULL avg_price_usd -- the site template must handle this and show
    an honest "price estimated, not from BLS" disclosure rather than
    inventing a number.
  - This script is intentionally idempotent: re-running it for the same
    month overwrites that month's snapshot rather than duplicating rows.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

from foods_seed import FOODS, FoodSeed
from bls_client import fetch_series, latest_value, year_over_year_pct_change, BlsClientError
from fdc_client import lookup_food, lookup_food_by_id, FdcClientError, NUTRIENT_IDS
from db import connect, init_db, DEFAULT_DB_PATH
from unit_convert import nutrient_per_dollar, UnsupportedUnitError

DATA_DIR = Path(__file__).parent.parent / "data"
EXPORT_PATH = DATA_DIR / "foods_export.json"

YEAR_LOOKBACK = 2

# Column order for the `nutrition` table's per-100g nutrient fields, taken
# directly from fdc_client.NUTRIENT_IDS so this list can't drift from what
# FDC extraction actually returns.
NUTRIENT_COLUMNS = list(NUTRIENT_IDS.keys())

# Macro + "nutrient of excess" fields that don't get a "per dollar" value
# metric (it makes no sense to want more sodium or saturated fat per dollar)
# -- everything else in NUTRIENT_COLUMNS is a true micronutrient and gets one.
_MACRO_KEYS = {
    "energy_kcal", "protein_g", "fat_g", "saturated_fat_g", "trans_fat_g",
    "monounsaturated_fat_g", "polyunsaturated_fat_g",
    "omega3_ala_g", "omega3_epa_g", "omega3_dha_g",
    "carbs_g", "fiber_g", "sugars_g", "cholesterol_mg", "sodium_mg",
}
MICRONUTRIENT_KEYS = [k for k in NUTRIENT_COLUMNS if k not in _MACRO_KEYS]

def upsert_food_row(conn, food: FoodSeed) -> None:
    conn.execute(
        """
        INSERT INTO foods (slug, display_name, category, serving_unit, avg_price_unit, price_verified, notes,
                           per_dollar_suppressed_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET
            display_name=excluded.display_name,
            category=excluded.category,
            serving_unit=excluded.serving_unit,
            avg_price_unit=excluded.avg_price_unit,
            price_verified=excluded.price_verified,
            notes=excluded.notes,
            per_dollar_suppressed_reason=excluded.per_dollar_suppressed_reason
        """,
        (food.slug, food.display_name, food.category, food.serving_unit,
         food.avg_price_unit, int(food.price_verified), food.notes, food.per_dollar_suppressed_reason),
    )


def fetch_and_store_price(conn, food: FoodSeed, now: datetime) -> None:
    if not food.avg_price_series_id or not food.price_verified:
        print(f"[run_etl] SKIP price fetch for {food.slug!r}: no verified avg_price_series_id.")
        conn.execute(
            """
            INSERT INTO price_snapshots (food_slug, year, month, avg_price_usd, price_source, yoy_pct_change, fetched_at)
            VALUES (?, ?, ?, NULL, 'estimate', NULL, ?)
            ON CONFLICT(food_slug, year, month) DO UPDATE SET
                price_source='estimate', fetched_at=excluded.fetched_at
            """,
            (food.slug, now.year, now.month, now.isoformat()),
        )
        return

    series_ids = [food.avg_price_series_id]
    if food.cpi_series_id:
        series_ids.append(food.cpi_series_id)

    try:
        results = fetch_series(series_ids, start_year=now.year - YEAR_LOOKBACK, end_year=now.year)
    except BlsClientError as e:
        print(f"[run_etl] ERROR fetching BLS data for {food.slug!r}: {e}")
        return

    avg_price_obs = results.get(food.avg_price_series_id, [])
    latest = latest_value(avg_price_obs)
    if not latest:
        print(f"[run_etl] WARNING: no avg price observations for {food.slug!r} (series {food.avg_price_series_id}).")
        return

    yoy_pct = None
    if food.cpi_series_id:
        cpi_obs = results.get(food.cpi_series_id, [])
        yoy_pct = year_over_year_pct_change(cpi_obs)

    conn.execute(
        """
        INSERT INTO price_snapshots (food_slug, year, month, avg_price_usd, price_source, yoy_pct_change, fetched_at)
        VALUES (?, ?, ?, ?, 'bls_avg_price', ?, ?)
        ON CONFLICT(food_slug, year, month) DO UPDATE SET
            avg_price_usd=excluded.avg_price_usd,
            price_source=excluded.price_source,
            yoy_pct_change=excluded.yoy_pct_change,
            fetched_at=excluded.fetched_at
        """,
        (food.slug, int(latest.year), int(latest.period.lstrip("M")), latest.value, yoy_pct, now.isoformat()),
    )
    print(f"[run_etl] OK price for {food.slug!r}: ${latest.value} ({latest.year}-{latest.period}), YoY={yoy_pct}")


def fetch_and_store_nutrition(conn, food: FoodSeed, now: datetime) -> None:
    try:
        if food.fdc_id is not None:
            result = lookup_food_by_id(food.fdc_id)
        else:
            result = lookup_food(food.fdc_query, food.fdc_data_type)
    except FdcClientError as e:
        print(f"[run_etl] ERROR fetching FDC data for {food.slug!r}: {e}")
        return

    if not result:
        print(f"[run_etl] WARNING: no FDC match for {food.slug!r} (query={food.fdc_query!r}).")
        return

    n = result.nutrients_per_100g
    columns_sql = ", ".join(NUTRIENT_COLUMNS)
    placeholders_sql = ", ".join("?" for _ in NUTRIENT_COLUMNS)
    update_sql = ", ".join(f"{c}=excluded.{c}" for c in NUTRIENT_COLUMNS)
    conn.execute(
        f"""
        INSERT INTO nutrition (food_slug, fdc_id, fdc_description, fdc_data_type,
                                {columns_sql}, fetched_at)
        VALUES (?, ?, ?, ?, {placeholders_sql}, ?)
        ON CONFLICT(food_slug) DO UPDATE SET
            fdc_id=excluded.fdc_id, fdc_description=excluded.fdc_description, fdc_data_type=excluded.fdc_data_type,
            {update_sql},
            fetched_at=excluded.fetched_at
        """,
        (food.slug, result.fdc_id, result.description, result.data_type,
         *[n.get(c) for c in NUTRIENT_COLUMNS],
         now.isoformat()),
    )
    print(f"[run_etl] OK nutrition for {food.slug!r}: matched FDC#{result.fdc_id} ({result.description!r})")


def export_json(conn) -> None:
    """Flatten foods + latest price + nutrition + sustainability into one JSON file the site reads at build time."""
    foods = conn.execute("SELECT * FROM foods").fetchall()
    out = []
    for f in foods:
        price_row = conn.execute(
            """
            SELECT * FROM price_snapshots
            WHERE food_slug = ?
            ORDER BY CASE WHEN price_source = 'bls_avg_price' THEN 0 ELSE 1 END,
                     year DESC, month DESC
            LIMIT 1
            """,
            (f["slug"],),
        ).fetchone()
        nutrition_row = conn.execute("SELECT * FROM nutrition WHERE food_slug = ?", (f["slug"],)).fetchone()
        sustainability_row = conn.execute(
            """
            SELECT s.*,
                   ws.short_key as water_source_key, ws.authors as water_authors,
                   ws.title as water_title, ws.year as water_year, ws.url as water_url,
                   ss.short_key as storage_source_key, ss.authors as storage_authors,
                   ss.title as storage_title, ss.year as storage_year, ss.url as storage_url
            FROM sustainability s
            LEFT JOIN sustainability_sources ws ON s.water_source_id = ws.id
            LEFT JOIN sustainability_sources ss ON s.storage_source_id = ss.id
            WHERE s.food_slug = ?
            """,
            (f["slug"],),
        ).fetchone()

        protein_per_dollar = None
        cal_per_dollar = None
        fiber_per_dollar = None
        micronutrient_per_dollar = {}
        if (
            price_row and price_row["avg_price_usd"] and price_row["price_source"] == "bls_avg_price"
            and nutrition_row and nutrition_row["protein_g"] is not None
            and not f["per_dollar_suppressed_reason"]
        ):
            try:
                protein_per_dollar = nutrient_per_dollar(
                    nutrition_row["protein_g"], price_row["avg_price_usd"], f["avg_price_unit"]
                )
                if nutrition_row["energy_kcal"] is not None:
                    cal_per_dollar = nutrient_per_dollar(
                        nutrition_row["energy_kcal"], price_row["avg_price_usd"], f["avg_price_unit"]
                    )
                if nutrition_row["fiber_g"] is not None:
                    fiber_per_dollar = nutrient_per_dollar(
                        nutrition_row["fiber_g"], price_row["avg_price_usd"], f["avg_price_unit"]
                    )
                for key in MICRONUTRIENT_KEYS:
                    if nutrition_row[key] is not None:
                        micronutrient_per_dollar[key] = nutrient_per_dollar(
                            nutrition_row[key], price_row["avg_price_usd"], f["avg_price_unit"]
                        )
            except UnsupportedUnitError as e:
                print(f"[run_etl] WARNING: {f['slug']!r}: {e}")

        out.append({
            "slug": f["slug"],
            "display_name": f["display_name"],
            "category": f["category"],
            "serving_unit": f["serving_unit"],
            "price": {
                "avg_price_usd": price_row["avg_price_usd"] if price_row else None,
                "avg_price_unit": f["avg_price_unit"],
                "price_source": price_row["price_source"] if price_row else "estimate",
                "yoy_pct_change": price_row["yoy_pct_change"] if price_row else None,
                "as_of": f"{price_row['year']}-{price_row['month']:02d}" if price_row else None,
            },
            "nutrition_per_100g": {
                "energy_kcal": nutrition_row["energy_kcal"],
                "protein_g": nutrition_row["protein_g"],
                "fat_g": nutrition_row["fat_g"],
                "saturated_fat_g": nutrition_row["saturated_fat_g"],
                "trans_fat_g": nutrition_row["trans_fat_g"],
                "monounsaturated_fat_g": nutrition_row["monounsaturated_fat_g"],
                "polyunsaturated_fat_g": nutrition_row["polyunsaturated_fat_g"],
                "omega3_ala_g": nutrition_row["omega3_ala_g"],
                "omega3_epa_g": nutrition_row["omega3_epa_g"],
                "omega3_dha_g": nutrition_row["omega3_dha_g"],
                "carbs_g": nutrition_row["carbs_g"],
                "fiber_g": nutrition_row["fiber_g"],
                "sugars_g": nutrition_row["sugars_g"],
                "cholesterol_mg": nutrition_row["cholesterol_mg"],
                "sodium_mg": nutrition_row["sodium_mg"],
                **{key: nutrition_row[key] for key in MICRONUTRIENT_KEYS},
                "source_fdc_id": nutrition_row["fdc_id"],
            } if nutrition_row else None,
            "value_metrics": {
                "protein_g_per_dollar": protein_per_dollar,
                "calories_per_dollar": cal_per_dollar,
                "fiber_g_per_dollar": fiber_per_dollar,
                **{f"{key}_per_dollar": micronutrient_per_dollar.get(key) for key in MICRONUTRIENT_KEYS},
                "note": "Computed only when price_source='bls_avg_price'. Null for estimated prices to avoid implying false precision.",
                "suppressed_reason": f["per_dollar_suppressed_reason"],
            },
            "sustainability": {
                "water_use_tier": sustainability_row["water_use_tier"],
                "storage_life_tier": sustainability_row["storage_life_tier"],
                "typical_local_production": sustainability_row["typical_local_production"],
                "notes": sustainability_row["notes"],
                "water_source": {
                    "key": sustainability_row["water_source_key"],
                    "authors": sustainability_row["water_authors"],
                    "title": sustainability_row["water_title"],
                    "year": sustainability_row["water_year"],
                    "url": sustainability_row["water_url"],
                } if sustainability_row["water_source_key"] else None,
                "storage_source": {
                    "key": sustainability_row["storage_source_key"],
                    "authors": sustainability_row["storage_authors"],
                    "title": sustainability_row["storage_title"],
                    "year": sustainability_row["storage_year"],
                    "url": sustainability_row["storage_url"],
                } if sustainability_row["storage_source_key"] else None,
            } if sustainability_row else None,
        })

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPORT_PATH, "w") as fp:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(), "foods": out}, fp, indent=2)
    print(f"[run_etl] Exported {len(out)} foods to {EXPORT_PATH}")


def main():
    init_db()
    now = datetime.now(timezone.utc)

    with connect(DEFAULT_DB_PATH) as conn:
        for food in FOODS:
            upsert_food_row(conn, food)

        for food in FOODS:
            fetch_and_store_price(conn, food, now)

        for food in FOODS:
            fetch_and_store_nutrition(conn, food, now)

        export_json(conn)

    print("[run_etl] Done.")


if __name__ == "__main__":
    sys.exit(main() or 0)
