"""
test_etl_offline.py

Exercises the full ETL pipeline (DB writes, unit conversion, JSON export)
using mocked BLS/FDC responses, since this sandbox has no network access.
This proves the orchestration logic is correct independent of live API
availability. Run the real thing (run_etl.py) once you have network access
and real API keys.

Run: python3 test_etl_offline.py
"""

from datetime import datetime, timezone
from unittest.mock import patch

from db import connect, init_db, DEFAULT_DB_PATH
from foods_seed import FOODS
from bls_client import BlsObservation
from fdc_client import FdcFood
from seed_sustainability import seed as seed_sustainability_data
import run_etl


def fake_fetch_series(series_ids, start_year, end_year, **kwargs):
    """
    Pretend BLS responses for all foods that have a price_verified=True AP series,
    plus a handful of the new unverified ones to exercise the pipeline paths.
    Series with no entry here return nothing, which tests the 'missing data' path.
    """
    MOCK_PRICES = {
        # Verified
        "APU0000708111": 2.58,   # eggs, per dozen
        "APU0000703112": 5.12,   # ground beef, per lb
        "APU0000709112": 4.02,   # whole milk, per gallon
        "APU0000711211": 0.65,   # bananas, per lb
        "APU0000712311": 1.89,   # tomatoes, per lb
        "APU0000704111": 7.21,   # bacon, per lb
        # Unverified but included to exercise unit conversion paths
        "APU0000710111": 5.85,   # butter, per lb
        "APU0000701312": 1.32,   # rice, per lb
        "APU0000701111": 0.72,   # flour, per lb
        "APU0000701322": 1.45,   # pasta, per lb
        "APU0000715212": 0.89,   # sugar, per lb
        "APU0000716141": 3.15,   # peanut butter, per lb
        "APU0000717311": 7.50,   # coffee, per lb
        "APU0000717114": 2.19,   # cola, per 2 liters
        "APU0000713111": 2.89,   # OJ frozen, per 16 oz
        "APU0000714233": 1.85,   # dry beans, per lb
        "APU0000711111": 1.65,   # apples, per lb
        "APU0000711311": 1.29,   # oranges, per lb
        "APU0000712112": 0.89,   # potatoes, per lb
        "APU0000710212": 6.45,   # cheddar cheese, per lb
        "APU0000702111": 3.45,   # bread white, per lb
        "APU0000702212": 3.89,   # bread whole wheat, per lb
        "APU0000712211": 1.49,   # lettuce, per lb
        "APU0000712403": 1.09,   # carrots, per lb
        "APU0000712412": 1.99,   # broccoli, per lb
        "APU0000705111": 4.25,   # frankfurters, per lb
        "APU0000707111": 3.89,   # tuna, per lb
        "APU0000706111": 1.89,   # chicken whole, per lb
    }
    out = {}
    for sid in series_ids:
        if sid in MOCK_PRICES:
            out[sid] = [BlsObservation(sid, "2026", "M01", "January", MOCK_PRICES[sid], [])]
        # CPI series and unknown series intentionally return nothing
    return out


def fake_lookup_food(query, data_type):
    """Pretend FDC responses keyed by fdc_query string."""
    # (energy_kcal, protein_g, fat_g, carbs_g, fiber_g)
    MOCK_NUTRITION = {
        "egg whole raw":                          (143, 12.6,  9.5,  0.7,  0.0),
        "ground beef 80% lean raw":               (254, 17.2, 20.0,  0.0,  0.0),
        "milk whole 3.25% milkfat":               ( 61,  3.2,  3.3,  4.8,  0.0),
        "bananas raw":                            ( 89,  1.1,  0.3, 22.8,  2.6),
        "tomatoes red ripe raw":                  ( 18,  0.9,  0.2,  3.9,  1.2),
        "pork bacon cooked":                      (541, 37.0, 42.0,  1.4,  0.0),
        "chicken broilers or fryers whole raw":    (215, 18.6, 15.1,  0.0,  0.0),
        "bread white commercially prepared":      (266,  9.0,  3.3, 49.4,  2.4),
        "bread whole wheat commercially prepared":(247,  9.4,  3.3, 48.0,  7.4),
        "cheese cheddar":                         (404, 23.0, 33.0,  1.3,  0.0),
        "beans pinto mature seeds raw":           (347, 21.4,  1.2, 62.6, 15.5),
        "lentils mature seeds raw":               (353, 25.8,  1.1, 60.1, 30.5),
        "frankfurters beef":                      (290, 11.3, 26.3,  2.1,  0.0),
        "tuna light canned in water":             (116, 25.5,  1.0,  0.0,  0.0),
        "peanut butter smooth style without salt":(588, 25.1, 50.4, 20.0,  6.0),
        "butter salted":                          (717,  0.9, 81.1,  0.1,  0.0),
        "apples raw with skin":                   ( 52,  0.3,  0.2, 13.8,  2.4),
        "oranges raw navels":                     ( 47,  0.9,  0.1, 11.8,  2.4),
        "potatoes flesh and skin raw":            ( 77,  2.0,  0.1, 17.5,  2.2),
        "lettuce iceberg raw":                    ( 14,  0.9,  0.1,  2.0,  0.9),
        "carrots raw":                            ( 41,  0.9,  0.2,  9.6,  2.8),
        "broccoli raw":                           ( 34,  2.8,  0.4,  6.6,  2.6),
        "rice white long grain unenriched raw":   (365,  7.1,  0.7, 80.0,  1.3),
        "wheat flour white all purpose unenriched":(364, 10.3,  1.0, 76.3,  2.7),
        "spaghetti dry unenriched":               (371, 13.0,  1.5, 74.7,  3.2),
        "sugars granulated":                      (387,  0.0,  0.0, 100.0, 0.0),
        "coffee brewed from grounds":             (  1,  0.1,  0.0,  0.0,  0.0),
        "carbonated beverage cola":               ( 37,  0.0,  0.0,  9.6,  0.0),
        "orange juice frozen concentrate unsweetened": (150, 2.3, 0.1, 36.3, 0.4),
    }
    if query not in MOCK_NUTRITION:
        return None
    kcal, protein, fat, carbs, fiber = MOCK_NUTRITION[query]
    return FdcFood(
        fdc_id=999999,
        description=f"TEST: {query}",
        data_type=data_type,
        nutrients_per_100g={
            "energy_kcal": kcal, "protein_g": protein, "fat_g": fat,
            "carbs_g": carbs, "fiber_g": fiber,
        },
    )


def run():
    test_db_path = DEFAULT_DB_PATH.parent / "test_real_cost_of_food.db"
    test_db_path.unlink(missing_ok=True)

    with patch("run_etl.fetch_series", fake_fetch_series), \
         patch("run_etl.lookup_food", fake_lookup_food), \
         patch("run_etl.DEFAULT_DB_PATH", test_db_path), \
         patch("seed_sustainability.DEFAULT_DB_PATH", test_db_path), \
         patch("run_etl.EXPORT_PATH", DEFAULT_DB_PATH.parent / "test_foods_export.json"):
        init_db(test_db_path)
        now = datetime.now(timezone.utc)
        with connect(test_db_path) as conn:
            for food in FOODS:
                run_etl.upsert_food_row(conn, food)
            for food in FOODS:
                run_etl.fetch_and_store_price(conn, food, now)
            for food in FOODS:
                run_etl.fetch_and_store_nutrition(conn, food, now)
        seed_sustainability_data()
        with connect(test_db_path) as conn:
            run_etl.export_json(conn)

    import json
    export_path = DEFAULT_DB_PATH.parent / "test_foods_export.json"
    with open(export_path) as fp:
        data = json.load(fp)

    foods_by_slug = {f["slug"]: f for f in data["foods"]}

    print(f"\n=== Exported {len(data['foods'])} foods ===")
    for food in data["foods"]:
        vm = food["value_metrics"]
        price = food["price"]
        print(
            f"{food['slug']:30s} price=${str(price['avg_price_usd']):7s} "
            f"({price['price_source']:14s}) protein/$={vm['protein_g_per_dollar']}"
        )

    # ── Assertions ────────────────────────────────────────────────────────────

    eggs = foods_by_slug["eggs"]
    assert eggs["price"]["avg_price_usd"] == 2.58
    assert eggs["value_metrics"]["protein_g_per_dollar"] == 29.3, eggs["value_metrics"]
    assert eggs["price"]["price_source"] == "bls_avg_price"

    # dry-beans now has a BLS series (714233), so price_source should be bls_avg_price
    # but price_verified=False means it gets skipped -> estimate
    dry_beans = foods_by_slug["dry-beans"]
    assert dry_beans["price"]["price_source"] == "estimate", \
        "dry-beans has price_verified=False so should still be skipped -> estimate"
    assert dry_beans["value_metrics"]["protein_g_per_dollar"] is None

    # lentils has no AP series at all -> estimate, no protein/$
    lentils = foods_by_slug["lentils"]
    assert lentils["price"]["price_source"] == "estimate"
    assert lentils["value_metrics"]["protein_g_per_dollar"] is None

    # cola exercises the "per 2 liters" unit path (price_verified=False -> estimate, no value metrics)
    cola = foods_by_slug["cola"]
    assert cola["price"]["price_source"] == "estimate"

    # sustainability should be present for all foods
    missing_sustainability = [f["slug"] for f in data["foods"] if f["sustainability"] is None]
    assert not missing_sustainability, f"Missing sustainability for: {missing_sustainability}"

    print("\nAll assertions passed. Pipeline logic is correct.")

    real_export_path = DEFAULT_DB_PATH.parent / "foods_export.json"
    with open(real_export_path, "w") as fp:
        json.dump(data, fp, indent=2)
    print(f"Also wrote preview data to {real_export_path} (for `astro dev`/`astro build` to consume).")

    test_db_path.unlink(missing_ok=True)
    export_path.unlink(missing_ok=True)


if __name__ == "__main__":
    run()
