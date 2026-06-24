"""
fdc_client.py

Thin client for the USDA FoodData Central API.

Docs: https://fdc.nal.usda.gov/api-guide
Get a free key at: https://fdc.nal.usda.gov/api-key-signup.html
(DEMO_KEY works for testing but is heavily rate-limited -- don't use it
for the scheduled production job.)

Data is public domain (CC0 1.0) -- no licensing concern, but cite
"U.S. Department of Agriculture, Agricultural Research Service. FoodData
Central." on the site per their request.

We pull specific nutrients (Protein, Energy, Fat, Carbohydrate, Fiber) per
100g for each food, since that's what powers the protein-per-dollar /
calories-per-dollar comparisons -- the core differentiator of the site.
"""

import os
import time
import requests
from dataclasses import dataclass, field

FDC_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
REQUEST_TIMEOUT_SECONDS = 30

# Nutrient IDs are stable across FDC's database. These are the ones we care
# about for "X per dollar" comparisons. Full list: https://fdc.nal.usda.gov/
NUTRIENT_IDS = {
    "energy_kcal": 1008,
    "protein_g": 1003,
    "fat_g": 1004,
    "carbs_g": 1005,
    "fiber_g": 1079,
    "sugars_g": 2000,
    "sodium_mg": 1093,
}


@dataclass
class FdcFood:
    fdc_id: int
    description: str
    data_type: str
    nutrients_per_100g: dict[str, float] = field(default_factory=dict)


class FdcClientError(Exception):
    pass


def _api_key() -> str:
    key = os.environ.get("FDC_API_KEY")
    if not key:
        print("[fdc_client] WARNING: FDC_API_KEY not set, falling back to DEMO_KEY (low rate limit).")
        return "DEMO_KEY"
    return key


def search_food(
    query: str,
    data_type: str | None = None,
    page_size: int = 5,
    retries: int = 3,
    backoff_seconds: float = 2.0,
) -> list[dict]:
    """
    Search FDC for foods matching `query`. Returns raw result dicts
    (caller picks the best match -- see pick_best_match below).
    """
    params = {"api_key": _api_key(), "query": query, "pageSize": page_size}
    if data_type:
        params["dataType"] = [data_type]

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(f"{FDC_BASE_URL}/foods/search", params=params, timeout=REQUEST_TIMEOUT_SECONDS)
            if resp.status_code == 429:
                raise FdcClientError("Rate limited (429). Get a real API key if using DEMO_KEY.")
            resp.raise_for_status()
            return resp.json().get("foods", [])
        except (requests.RequestException, FdcClientError) as e:
            last_error = e
            time.sleep(backoff_seconds * attempt)

    raise FdcClientError(f"FDC search failed after {retries} attempts for query={query!r}: {last_error}")


def get_food_details(fdc_id: int, retries: int = 3, backoff_seconds: float = 2.0) -> dict:
    params = {"api_key": _api_key()}
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(f"{FDC_BASE_URL}/food/{fdc_id}", params=params, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_error = e
            time.sleep(backoff_seconds * attempt)
    raise FdcClientError(f"FDC food/{fdc_id} failed after {retries} attempts: {last_error}")


def pick_best_match(results: list[dict], preferred_data_type: str) -> dict | None:
    """
    Prefer an exact data_type match; otherwise take the first result.
    SR Legacy / Foundation entries are generally cleaner for generic
    "raw ingredient" lookups than Branded entries (which are specific products).
    """
    if not results:
        return None
    for r in results:
        if r.get("dataType") == preferred_data_type:
            return r
    return results[0]


def extract_nutrients_per_100g(food_detail: dict) -> dict[str, float]:
    """
    Pull the nutrients we care about from a /food/{fdcId} response.
    FDC's per-food nutrient list is already per 100g for SR Legacy/Foundation
    types (the dataset's native basis) -- branded foods may differ, see notes
    in run_etl.py about serving-size normalization for branded items.
    """
    wanted = {v: k for k, v in NUTRIENT_IDS.items()}  # nutrient_id -> our_key
    out: dict[str, float] = {}
    for n in food_detail.get("foodNutrients", []):
        nutrient_id = n.get("nutrient", {}).get("id") or n.get("nutrientId")
        amount = n.get("amount")
        if nutrient_id in wanted and amount is not None:
            out[wanted[nutrient_id]] = amount
    return out


def lookup_food(query: str, preferred_data_type: str) -> FdcFood | None:
    """High-level convenience: search -> pick best match -> fetch full detail -> extract nutrients."""
    results = search_food(query, data_type=preferred_data_type)
    best = pick_best_match(results, preferred_data_type)
    if not best:
        return None
    detail = get_food_details(best["fdcId"])
    nutrients = extract_nutrients_per_100g(detail)
    return FdcFood(
        fdc_id=best["fdcId"],
        description=best.get("description", ""),
        data_type=best.get("dataType", ""),
        nutrients_per_100g=nutrients,
    )


if __name__ == "__main__":
    # Quick manual smoke test: python fdc_client.py
    result = lookup_food("egg whole raw", "SR Legacy")
    print(result)
