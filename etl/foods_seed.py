"""
foods_seed.py

The curated MVP food list. This is the moat: a hand-picked set of foods
chosen to make good comparison content (protein sources especially), each
mapped to:
  - a BLS "Average Price" series ID -> for the actual $ figure shown on the page
  - a BLS CPI series ID              -> for the inflation % (YoY / MoM change)
  - a USDA FoodData Central search query -> for nutrition (protein/cal per 100g)
  - a manually-curated sustainability tier (water use, storage life, etc.)

WHY TWO DIFFERENT BLS SERIES PER ITEM:
BLS explicitly warns that Average Price series should be used to show the
price LEVEL in a given month, not to measure price CHANGE over time -- the
CPI index series is the correct tool for that. So:
  - avg_price_series_id  -> display "$X.XX as of <month>"
  - cpi_series_id        -> compute "+12% YoY" style inflation stats
Never compute a % change directly from the avg_price series and never
display the CPI index value as if it were a dollar amount.

VERIFICATION STATUS:
  - "verified" series IDs below were confirmed live against FRED/BLS pages.
  - "unverified" placeholders are marked explicitly and must be confirmed
    against https://data.bls.gov/cgi-bin/surveymost?ap (Average Price) and
    https://data.bls.gov/cgi-bin/surveymost?cu (CPI) before going live.
    DO NOT ship unverified series IDs to production -- a wrong series ID
    fails silently (it just returns a different food's data).

SUSTAINABILITY / NUTRITION FIELDS:
These are not computed from an API. Source them by hand from published
research (e.g. Mekonnen & Hoekstra water footprint studies, USDA storage
guides) and keep a citation per item in sustainability_sources.csv (to be
created alongside the data). Tiered (low/medium/high) is honest; a fake
precise number is not.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FoodSeed:
    slug: str                          # url-safe id, e.g. "eggs"
    display_name: str                  # "Eggs (Grade A, Large)"
    category: str                      # "protein", "grain", "dairy", "produce", "other"
    avg_price_series_id: Optional[str] # BLS Average Price series -> $ amount
    avg_price_unit: str                # what the avg_price series is denominated in, e.g. "per dozen", "per lb"
    cpi_series_id: Optional[str]       # BLS CPI series -> inflation % (NSA, U.S. city average)
    fdc_query: str                     # search term for USDA FoodData Central
    fdc_data_type: str                 # "SR Legacy", "Foundation", "Branded", "Survey (FNDDS)"
    serving_unit: str                  # nutrition serving basis, e.g. "100g"
    price_verified: bool               # True only if avg_price_series_id was confirmed live
    notes: str = ""


FOODS: list[FoodSeed] = [
    FoodSeed(
        slug="eggs",
        display_name="Eggs (Grade A, Large)",
        category="protein",
        avg_price_series_id="APU0000708111",
        avg_price_unit="per dozen",
        cpi_series_id="CUUR0000SEFL01",  # CPI: Eggs, NSA -- verify before launch
        fdc_query="egg whole raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g (~2 large eggs)",
        price_verified=True,
        notes="avg_price_series_id confirmed via FRED. cpi_series_id needs separate confirmation.",
    ),
    FoodSeed(
        slug="whole-milk",
        display_name="Milk (Whole, Fortified)",
        category="dairy",
        avg_price_series_id="APU0000709112",
        avg_price_unit="per gallon",
        cpi_series_id=None,
        fdc_query="milk whole 3.25% milkfat",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="cpi_series_id not yet verified -- confirm before computing inflation %.",
    ),
    FoodSeed(
        slug="ground-beef",
        display_name="Ground Beef (100% Beef)",
        category="protein",
        avg_price_series_id="APU0000703112",
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="ground beef 80% lean raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="chicken-breast",
        display_name="Chicken Breast (Boneless)",
        category="protein",
        avg_price_series_id="APU0000706111",  # "Chicken Breast, Boneless" -- name confirmed, ID needs re-check
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="chicken breast boneless skinless raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="Series NAME confirmed to exist on FRED; exact numeric ID must be re-verified before launch.",
    ),
    FoodSeed(
        slug="bacon",
        display_name="Bacon (Sliced)",
        category="protein",
        avg_price_series_id="APU0000704111",
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="pork bacon cooked",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="bananas",
        display_name="Bananas",
        category="produce",
        avg_price_series_id="APU0000711211",
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="bananas raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="tomatoes",
        display_name="Tomatoes (Field Grown)",
        category="produce",
        avg_price_series_id="APU0000712311",
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="tomatoes red ripe raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="bread-white",
        display_name="Bread (White, Pan)",
        category="grain",
        avg_price_series_id="APU0000702111",  # name confirmed ("Bread, White, Pan"); re-verify numeric ID
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="bread white commercially prepared",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="Series name confirmed on FRED; numeric ID needs direct re-check before launch.",
    ),
    FoodSeed(
        slug="cheddar-cheese",
        display_name="Cheddar Cheese (Natural)",
        category="dairy",
        avg_price_series_id=None,
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="cheese cheddar",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="Series confirmed to exist (name seen on FRED) but numeric ID not captured -- look up before launch.",
    ),
    FoodSeed(
        slug="dry-beans",
        display_name="Dry Beans (Pinto)",
        category="protein",
        avg_price_series_id=None,
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beans pinto mature seeds raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",
        price_verified=False,
        notes="No BLS average-price series found for dry beans. Use USDA ERS or manual grocery sampling; label page as 'estimated price'.",
    ),
    FoodSeed(
        slug="lentils",
        display_name="Lentils (Dry)",
        category="protein",
        avg_price_series_id=None,
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="lentils mature seeds raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",
        price_verified=False,
        notes="No BLS series. Price must come from manual sampling/estimate; disclose on page.",
    ),
    FoodSeed(
        slug="tofu",
        display_name="Tofu (Firm)",
        category="protein",
        avg_price_series_id=None,
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="tofu firm raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="No BLS series. Estimate-only for v1.",
    ),
]


def get_food(slug: str) -> Optional[FoodSeed]:
    for f in FOODS:
        if f.slug == slug:
            return f
    return None


def verified_foods() -> list[FoodSeed]:
    """Foods with a confirmed-live BLS average-price series -- safe to ship now."""
    return [f for f in FOODS if f.price_verified]


def needs_verification() -> list[FoodSeed]:
    """Foods whose series IDs still need to be checked against BLS before launch."""
    return [f for f in FOODS if not f.price_verified]
