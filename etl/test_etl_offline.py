"""
test_etl_offline.py

Exercises the full ETL pipeline (DB writes, unit conversion, JSON export)
using mocked BLS/FDC responses, since this sandbox has no network access.
This proves the orchestration logic is correct independent of live API
availability. Run the real thing (run_etl.py) once you have network access
and real API keys.

Run: python test_etl_offline.py
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
    """Pretend BLS response: eggs at $2.58/dozen, +12% YoY CPI."""
    out = {}
    for sid in series_ids:
        if sid == "APU0000708111":  # eggs avg price
            out[sid] = [
                BlsObservation(sid, "2025", "M12", "December", 2.45, []),
                BlsObservation(sid, "2026", "M01", "January", 2.58, []),
            ]
        elif sid == "APU0000703112":  # ground beef avg price
            out[sid] = [BlsObservation(sid, "2026", "M01", "January", 5.12, [])]
        elif sid == "APU0000709112":  # milk avg price
            out[sid] = [BlsObservation(sid, "2026", "M01", "January", 4.02, [])]
        elif sid == "APU0000711211":  # bananas
            out[sid] = [BlsObservation(sid, "2026", "M01", "January", 0.65, [])]
        elif sid == "APU0000712311":  # tomatoes
            out[sid] = [BlsObservation(sid, "2026", "M01", "January", 1.89, [])]
        elif sid == "APU0000704111":  # bacon
            out[sid] = [BlsObservation(sid, "2026", "M01", "January", 7.21, [])]
        # CPI series and unverified series intentionally return nothing -> tests the "missing" path
    return out


def fake_lookup_food(query, data_type):
    """Pretend FDC response keyed by query string -- covers our verified foods."""
    fake_nutrition = {
        "egg whole raw": (143, 12.6, 9.5, 0.7, 0.0),
        "ground beef 80% lean raw": (254, 17.2, 20.0, 0.0, 0.0),
        "milk whole 3.25% milkfat": (61, 3.2, 3.3, 4.8, 0.0),
        "bananas raw": (89, 1.1, 0.3, 22.8, 2.6),
        "tomatoes red ripe raw": (18, 0.9, 0.2, 3.9, 1.2),
        "pork bacon cooked": (541, 37.0, 42.0, 1.4, 0.0),
        "beans pinto mature seeds raw": (347, 21.4, 1.2, 62.6, 15.5),
        "lentils mature seeds raw": (353, 25.8, 1.1, 60.1, 30.5),
        "tofu firm raw": (144, 15.8, 8.7, 2.8, 1.2),
        "chicken breast boneless skinless raw": (120, 22.5, 2.6, 0.0, 0.0),
        "bread white commercially prepared": (266, 9.0, 3.3, 49.4, 2.4),
        "cheese cheddar": (404, 23.0, 33.0, 1.3, 0.0),
    }
    if query not in fake_nutrition:
        return None
    kcal, protein, fat, carbs, fiber = fake_nutrition[query]
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
    # Use a throwaway test DB so we don't clobber any real data.
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
        seed_sustainability_data()  # uses its own connect() call against the patched DEFAULT_DB_PATH
        with connect(test_db_path) as conn:
            run_etl.export_json(conn)

    # Validate output
    import json
    export_path = DEFAULT_DB_PATH.parent / "test_foods_export.json"
    with open(export_path) as fp:
        data = json.load(fp)

    print(f"\n=== Exported {len(data['foods'])} foods ===")
    for food in data["foods"]:
        vm = food["value_metrics"]
        price = food["price"]
        print(
            f"{food['slug']:20s} price=${price['avg_price_usd']} ({price['price_source']:14s}) "
            f"protein/$={vm['protein_g_per_dollar']}"
        )

    eggs = next(f for f in data["foods"] if f["slug"] == "eggs")
    assert eggs["price"]["avg_price_usd"] == 2.58, "Eggs price mismatch"
    assert eggs["value_metrics"]["protein_g_per_dollar"] == 29.3, f"Eggs protein/$ mismatch: {eggs['value_metrics']}"
    assert eggs["price"]["price_source"] == "bls_avg_price"

    dry_beans = next(f for f in data["foods"] if f["slug"] == "dry-beans")
    assert dry_beans["price"]["price_source"] == "estimate", "Dry beans should be marked estimate (no BLS series)"
    assert dry_beans["value_metrics"]["protein_g_per_dollar"] is None, "Should not compute protein/$ for estimated prices"

    print("\nAll assertions passed. Pipeline logic is correct.")

    # Also write a copy to the real export path so the Astro site has
    # something to build against during local dev/preview, until the
    # real run_etl.py is run against live APIs.
    real_export_path = DEFAULT_DB_PATH.parent / "foods_export.json"
    with open(real_export_path, "w") as fp:
        json.dump(data, fp, indent=2)
    print(f"Also wrote preview data to {real_export_path} (for `astro dev`/`astro build` to consume).")

    # cleanup
    test_db_path.unlink(missing_ok=True)
    export_path.unlink(missing_ok=True)


if __name__ == "__main__":
    run()
