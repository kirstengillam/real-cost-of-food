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
    # (energy_kcal, protein_g, fat_g, carbs_g, fiber_g, iron_mg, zinc_mg, b12_mcg, folate_mcg,
    #  calcium_mg, potassium_mg, magnesium_mg, vitamin_a_mcg, vitamin_c_mg, vitamin_d_mcg,
    #  vitamin_e_mg, vitamin_k_mcg)
    MOCK_NUTRITION = {
        "egg whole raw":                          (143, 12.6,  9.5,  0.7,  0.0, 1.75, 1.29, 1.11,  47,  56, 138, 10,  160, 0.0, 2.0, 1.05, 0.3),
        "ground beef 80% lean raw":               (254, 17.2, 20.0,  0.0,  0.0, 2.60, 5.36, 2.50,   8,  18, 270, 18,    0, 0.0, 0.1, 0.20, 1.6),
        "milk whole 3.25% milkfat":               ( 61,  3.2,  3.3,  4.8,  0.0, 0.03, 0.38, 0.45,   5, 113, 143, 10,   46, 0.0, 1.3, 0.07, 0.2),
        "bananas raw":                            ( 89,  1.1,  0.3, 22.8,  2.6, 0.26, 0.15, 0.00,  20,   5, 358, 27,    3, 8.7, 0.0, 0.10, 0.5),
        "tomatoes red ripe raw":                  ( 18,  0.9,  0.2,  3.9,  1.2, 0.27, 0.17, 0.00,  15,  10, 237, 11,   42, 13.7, 0.0, 0.54, 7.9),
        "pork bacon cooked":                      (541, 37.0, 42.0,  1.4,  0.0, 1.44, 3.59, 0.68,   1,  15, 565, 24,    0, 0.0, 0.4, 0.36, 0.0),
        "chicken broilers or fryers whole raw":    (215, 18.6, 15.1,  0.0,  0.0, 1.07, 1.95, 0.31,   8,  11, 173, 20,   38, 0.0, 0.1, 0.25, 0.3),
        "bread white commercially prepared":      (266,  9.0,  3.3, 49.4,  2.4, 3.60, 0.77, 0.00,  93, 151, 100, 24,    0, 0.0, 0.0, 0.20, 4.8),
        "bread whole wheat commercially prepared":(247,  9.4,  3.3, 48.0,  7.4, 2.85, 1.42, 0.00,  41, 172, 254, 82,    0, 0.0, 0.0, 0.31, 6.5),
        "cheese cheddar":                         (404, 23.0, 33.0,  1.3,  0.0, 0.68, 3.11, 0.83,  18, 721, 76,  28,  265, 0.0, 0.6, 0.71, 2.4),
        "beans pinto mature seeds raw":           (347, 21.4,  1.2, 62.6, 15.5, 5.07, 2.28, 0.00, 525, 113, 1393, 176,   0, 6.3, 0.0, 0.19, 5.6),
        "lentils mature seeds raw":               (353, 25.8,  1.1, 60.1, 30.5, 6.51, 3.63, 0.00, 479,  35, 955, 122,   2, 4.5, 0.0, 0.11, 5.0),
        "frankfurters beef":                      (290, 11.3, 26.3,  2.1,  0.0, 1.85, 2.62, 0.95,   4,  10, 168, 11,    0, 0.0, 0.1, 0.36, 0.0),
        "tuna light canned in water":              (116, 25.5,  1.0,  0.0,  0.0, 1.55, 0.77, 2.52,   4,  12, 237, 27,    0, 0.0, 1.7, 0.36, 0.1),
        "peanut butter smooth style without salt":(588, 25.1, 50.4, 20.0,  6.0, 1.74, 2.97, 0.00, 87,  49, 649, 168,   0, 0.0, 0.0, 9.10, 0.0),
        "butter salted":                          (717,  0.9, 81.1,  0.1,  0.0, 0.02, 0.05, 0.17,   3,  24, 24,  2,   684, 0.0, 1.5, 2.32, 7.0),
        "apples raw with skin":                   ( 52,  0.3,  0.2, 13.8,  2.4, 0.12, 0.04, 0.00,   3,   6, 107,  5,    3, 4.6, 0.0, 0.18, 2.2),
        "oranges raw navels":                     ( 47,  0.9,  0.1, 11.8,  2.4, 0.10, 0.07, 0.00,  30,  40, 181, 10,   11, 59.1, 0.0, 0.18, 0.0),
        "potatoes flesh and skin raw":            ( 77,  2.0,  0.1, 17.5,  2.2, 0.81, 0.30, 0.00,  15,  12, 425, 23,    2, 19.7, 0.0, 0.01, 1.9),
        "lettuce iceberg raw":                    ( 14,  0.9,  0.1,  2.0,  0.9, 0.41, 0.15, 0.00,  29,  18, 141, 7,    25, 2.8, 0.0, 0.18, 24.1),
        "carrots raw":                            ( 41,  0.9,  0.2,  9.6,  2.8, 0.30, 0.24, 0.00,  19,  33, 320, 12,  835, 5.9, 0.0, 0.66, 13.2),
        "broccoli raw":                           ( 34,  2.8,  0.4,  6.6,  2.6, 0.73, 0.41, 0.00,  63,  47, 316, 21,   31, 89.2, 0.0, 0.78, 101.6),
        "rice white long grain unenriched raw":   (365,  7.1,  0.7, 80.0,  1.3, 0.80, 1.09, 0.00,   8,  28, 115, 25,    0, 0.0, 0.0, 0.11, 0.1),
        "wheat flour white all purpose unenriched":(364, 10.3,  1.0, 76.3,  2.7, 1.17, 0.70, 0.00,  26,  15, 107, 22,    0, 0.0, 0.0, 0.06, 0.3),
        "spaghetti dry unenriched":               (371, 13.0,  1.5, 74.7,  3.2, 1.30, 1.41, 0.00,   7,  21, 223, 53,    0, 0.0, 0.0, 0.30, 0.1),
        "sugars granulated":                      (387,  0.0,  0.0, 100.0, 0.0, 0.01, 0.01, 0.00,   0,   1,  2,  0,     0, 0.0, 0.0, 0.00, 0.0),
        "coffee brewed from grounds":              (  1,  0.1,  0.0,  0.0,  0.0, 0.01, 0.02, 0.00,   2,   2, 49,  3,     0, 0.0, 0.0, 0.01, 0.0),
        "carbonated beverage cola":                ( 37,  0.0,  0.0,  9.6,  0.0, 0.18, 0.02, 0.00,   0,   4,  0,  1,     0, 0.0, 0.0, 0.00, 0.0),
        "orange juice frozen concentrate unsweetened": (150, 2.3, 0.1, 36.3, 0.4, 0.44, 0.27, 0.00, 34,  22, 202, 20,   10, 38.9, 0.0, 0.13, 0.0),
    }
    if query not in MOCK_NUTRITION:
        return None
    (kcal, protein, fat, carbs, fiber, iron, zinc, b12, folate,
     calcium, potassium, magnesium, vitamin_a, vitamin_c, vitamin_d, vitamin_e, vitamin_k) = MOCK_NUTRITION[query]
    return FdcFood(
        fdc_id=999999,
        description=f"TEST: {query}",
        data_type=data_type,
        nutrients_per_100g={
            "energy_kcal": kcal, "protein_g": protein, "fat_g": fat,
            "carbs_g": carbs, "fiber_g": fiber,
            "iron_mg": iron, "zinc_mg": zinc, "vitamin_b12_mcg": b12, "folate_mcg": folate,
            "calcium_mg": calcium, "potassium_mg": potassium, "magnesium_mg": magnesium,
            "vitamin_a_mcg": vitamin_a, "vitamin_c_mg": vitamin_c, "vitamin_d_mcg": vitamin_d,
            "vitamin_e_mg": vitamin_e, "vitamin_k_mcg": vitamin_k,
        },
    )


def fake_lookup_food_by_id(fdc_id):
    """Pinned-fdc_id foods resolve through the same mock table via their seed fdc_query."""
    food = next(f for f in FOODS if f.fdc_id == fdc_id)
    return fake_lookup_food(food.fdc_query, food.fdc_data_type)


def run():
    test_db_path = DEFAULT_DB_PATH.parent / "test_real_cost_of_food.db"
    test_db_path.unlink(missing_ok=True)

    with patch("run_etl.fetch_series", fake_fetch_series), \
         patch("run_etl.lookup_food", fake_lookup_food), \
         patch("run_etl.lookup_food_by_id", fake_lookup_food_by_id), \
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

    # coffee has a real BLS price but a mismatched nutrition basis (dry grounds vs brewed) -> no per-dollar metrics
    coffee = foods_by_slug["coffee"]
    assert coffee["price"]["price_source"] == "bls_avg_price"
    assert coffee["value_metrics"]["suppressed_reason"], coffee["value_metrics"]
    assert all(v is None for k, v in coffee["value_metrics"].items() if k.endswith("_per_dollar")), coffee["value_metrics"]
    assert eggs["value_metrics"]["suppressed_reason"] is None

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
