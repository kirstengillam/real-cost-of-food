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
    # (energy_kcal, protein_g, fat_g, carbs_g, fiber_g, iron_mg, zinc_mg, b12_mcg, folate_mcg)
    MOCK_NUTRITION = {
        "egg whole raw":                          (143, 12.6,  9.5,  0.7,  0.0, 1.75, 1.29, 1.11,  47),
        "ground beef 80% lean raw":               (254, 17.2, 20.0,  0.0,  0.0, 2.60, 5.36, 2.50,   8),
        "milk whole 3.25% milkfat":               ( 61,  3.2,  3.3,  4.8,  0.0, 0.03, 0.38, 0.45,   5),
        "bananas raw":                            ( 89,  1.1,  0.3, 22.8,  2.6, 0.26, 0.15, 0.00,  20),
        "tomatoes red ripe raw":                  ( 18,  0.9,  0.2,  3.9,  1.2, 0.27, 0.17, 0.00,  15),
        "pork bacon cooked":                      (541, 37.0, 42.0,  1.4,  0.0, 1.44, 3.59, 0.68,   1),
        "chicken broilers or fryers whole raw":    (215, 18.6, 15.1,  0.0,  0.0, 1.07, 1.95, 0.31,   8),
        "bread white commercially prepared":      (266,  9.0,  3.3, 49.4,  2.4, 3.60, 0.77, 0.00,  93),
        "bread whole wheat commercially prepared":(247,  9.4,  3.3, 48.0,  7.4, 2.85, 1.42, 0.00,  41),
        "cheese cheddar":                         (404, 23.0, 33.0,  1.3,  0.0, 0.68, 3.11, 0.83,  18),
        "beans pinto mature seeds raw":           (347, 21.4,  1.2, 62.6, 15.5, 5.07, 2.28, 0.00, 525),
        "lentils mature seeds raw":               (353, 25.8,  1.1, 60.1, 30.5, 6.51, 3.63, 0.00, 479),
        "frankfurters beef":                      (290, 11.3, 26.3,  2.1,  0.0, 1.85, 2.62, 0.95,   4),
        "tuna light canned in water":             (116, 25.5,  1.0,  0.0,  0.0, 1.55, 0.77, 2.52,   4),
        "peanut butter smooth style without salt":(588, 25.1, 50.4, 20.0,  6.0, 1.74, 2.97, 0.00, 87),
        "butter salted":                          (717,  0.9, 81.1,  0.1,  0.0, 0.02, 0.05, 0.17,   3),
        "apples raw with skin":                   ( 52,  0.3,  0.2, 13.8,  2.4, 0.12, 0.04, 0.00,   3),
        "oranges raw navels":                     ( 47,  0.9,  0.1, 11.8,  2.4, 0.10, 0.07, 0.00,  30),
        "potatoes flesh and skin raw":            ( 77,  2.0,  0.1, 17.5,  2.2, 0.81, 0.30, 0.00,  15),
        "lettuce iceberg raw":                    ( 14,  0.9,  0.1,  2.0,  0.9, 0.41, 0.15, 0.00,  29),
        "carrots raw":                            ( 41,  0.9,  0.2,  9.6,  2.8, 0.30, 0.24, 0.00,  19),
        "broccoli raw":                           ( 34,  2.8,  0.4,  6.6,  2.6, 0.73, 0.41, 0.00,  63),
        "rice white long grain unenriched raw":   (365,  7.1,  0.7, 80.0,  1.3, 0.80, 1.09, 0.00,   8),
        "wheat flour white all purpose unenriched":(364, 10.3,  1.0, 76.3,  2.7, 1.17, 0.70, 0.00,  26),
        "spaghetti dry unenriched":               (371, 13.0,  1.5, 74.7,  3.2, 1.30, 1.41, 0.00,   7),
        "sugars granulated":                      (387,  0.0,  0.0, 100.0, 0.0, 0.01, 0.01, 0.00,   0),
        "coffee brewed from grounds":             (  1,  0.1,  0.0,  0.0,  0.0, 0.01, 0.02, 0.00,   2),
        "carbonated beverage cola":               ( 37,  0.0,  0.0,  9.6,  0.0, 0.18, 0.02, 0.00,   0),
        "orange juice frozen concentrate unsweetened": (150, 2.3, 0.1, 36.3, 0.4, 0.44, 0.27, 0.00, 34),
    }
    if query not in MOCK_NUTRITION:
        return None
    kcal, protein, fat, carbs, fiber, iron, zinc, b12, folate = MOCK_NUTRITION[query]
    return FdcFood(
        fdc_id=999999,
        description=f"TEST: {query}",
        data_type=data_type,
        nutrients_per_100g={
            "energy_kcal": kcal, "protein_g": protein, "fat_g": fat,
            "carbs_g": carbs, "fiber_g": fiber,
            "iron_mg": iron, "zinc_mg": zinc, "vitamin_b12_mcg": b12, "folate_mcg": folate,
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

    # dry-beans has price_verified=True and a mock BLS price -> real price and metrics
    dry_beans = foods_by_slug["dry-beans"]
    assert dry_beans["price"]["price_source"] == "bls_avg_price", dry_beans["price"]
    assert dry_beans["value_metrics"]["protein_g_per_dollar"] is not None

    # soft-drinks-2l exercises the "per 2 liters" unit path (price_verified=False -> estimate, no value metrics)
    soft_drinks = foods_by_slug["soft-drinks-2l"]
    assert soft_drinks["price"]["price_source"] == "estimate"
    assert soft_drinks["value_metrics"]["protein_g_per_dollar"] is None

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
