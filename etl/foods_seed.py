"""
foods_seed.py

The curated food list, grounded in the BLS Average Price (AP) and CPI series
that have confirmed counterparts in both official BLS item lists:
  ap.item: https://download.bls.gov/pub/time.series/ap/ap.item
  cu.item: https://download.bls.gov/pub/time.series/cu/cu.item

Series ID construction:
  avg_price_series_id = "APU0000" + ap_item_code
  cpi_series_id       = "CUUR0000" + cu_item_code

WHY TWO DIFFERENT BLS SERIES PER ITEM:
BLS explicitly warns that Average Price series should be used to show the
price LEVEL in a given month, not to measure price CHANGE over time — the
CPI index series is the correct tool for that. So:
  avg_price_series_id  -> display "$X.XX as of <month>"
  cpi_series_id        -> compute "+X% YoY" inflation stats
Never compute % change from the avg_price series. Never display the CPI
index value as a dollar amount.

VERIFICATION STATUS:
  price_verified=True  — avg_price_series_id confirmed live (returns data).
  price_verified=False — series ID sourced from official ap.item file but
                         not yet confirmed to return live data via the API.
                         Flip to True after spot-checking on FRED or BLS.
  cpi_series_id fields — all need live confirmation before displaying
                         inflation %. The cu_item_code sources are noted inline.

CATEGORIES: protein, dairy, produce, grain, pantry, beverage
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FoodSeed:
    slug: str
    display_name: str
    category: str
    avg_price_series_id: Optional[str]  # APU0000 + ap_item_code
    avg_price_unit: str                 # denomination from BLS item name
    cpi_series_id: Optional[str]        # CUUR0000 + cu_item_code
    fdc_query: str                      # search string for USDA FoodData Central
    fdc_data_type: str                  # "SR Legacy" | "Foundation" | "Survey (FNDDS)"
    serving_unit: str                   # display label; nutrition is always fetched per 100g
    price_verified: bool                # True only after confirmed live via API/FRED
    notes: str = ""


FOODS: list[FoodSeed] = [

    # ── Proteins ──────────────────────────────────────────────────────────────

    FoodSeed(
        slug="eggs",
        display_name="Eggs (Grade A, Large)",
        category="protein",
        avg_price_series_id="APU0000708111",  # ap: 708111 — Eggs, grade A, large, per doz.
        avg_price_unit="per dozen",
        cpi_series_id="CUUR0000SEFH",         # cu: SEFH — Eggs
        fdc_query="egg whole raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g (~2 large eggs)",
        price_verified=True,
        notes="avg_price confirmed via FRED. cpi_series needs live confirmation.",
    ),
    FoodSeed(
        slug="ground-beef",
        display_name="Ground Beef (100% Beef)",
        category="protein",
        avg_price_series_id="APU0000703112",  # ap: 703112 — Ground beef, 100% beef, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFC01",       # cu: SEFC01 — Uncooked ground beef
        fdc_query="ground beef 80% lean raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="chicken-breast",
        display_name="Chicken Breast (Boneless)",
        category="protein",
        avg_price_series_id="APU0000FF1101",  # ap: FF1101 — Chicken breast, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS06021",      # cu: SS06021 — Fresh and frozen chicken parts (closest available)
        fdc_query="chicken breast boneless skinless raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item. CPI series covers all chicken parts, not boneless-only — inflation % will be approximate.",
    ),
    FoodSeed(
        slug="bacon",
        display_name="Bacon (Sliced)",
        category="protein",
        avg_price_series_id="APU0000704111",  # ap: 704111 — Bacon, sliced, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS04011",      # cu: SS04011 — Bacon and related products
        fdc_query="pork bacon cooked",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="frankfurters",
        display_name="Frankfurters (All Meat)",
        category="protein",
        avg_price_series_id="APU0000705111",  # ap: 705111 — Frankfurters, all meat or all beef, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS05011",      # cu: SS05011 — Frankfurters
        fdc_query="frankfurters beef",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="tuna",
        display_name="Tuna (Light, Chunk, Canned)",
        category="protein",
        avg_price_series_id="APU0000707111",  # ap: 707111 — Tuna, light, chunk, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS07011",      # cu: SS07011 — Shelf stable fish and seafood
        fdc_query="tuna light canned in water",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="peanut-butter",
        display_name="Peanut Butter (Creamy)",
        category="protein",
        avg_price_series_id="APU0000716141",  # ap: 716141 — Peanut butter, creamy, all sizes, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS16014",      # cu: SS16014 — Peanut butter
        fdc_query="peanut butter smooth style without salt",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="dry-beans",
        display_name="Dry Beans (Any Type)",
        category="protein",
        avg_price_series_id="APU0000714233",  # ap: 714233 — Beans, dried, any type, all sizes, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS14022",      # cu: SS14022 — Dried beans, peas, and lentils
        fdc_query="beans pinto mature seeds raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",
        price_verified=False,
        notes="BLS series covers 'any type' dried beans — price reflects category average, not pinto specifically.",
    ),
    FoodSeed(
        slug="lentils",
        display_name="Lentils (Dry)",
        category="protein",
        avg_price_series_id=None,
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS14022",      # cu: SS14022 — Dried beans, peas, and lentils (shared with dry-beans)
        fdc_query="lentils mature seeds raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",
        price_verified=False,
        notes="No dedicated BLS AP series for lentils. Price must come from manual sampling; disclose as estimate on page.",
    ),

    # ── Dairy ─────────────────────────────────────────────────────────────────

    FoodSeed(
        slug="whole-milk",
        display_name="Milk (Whole, Fortified)",
        category="dairy",
        avg_price_series_id="APU0000709112",  # ap: 709112 — Milk, fresh, whole, fortified, per gal.
        avg_price_unit="per gallon",
        cpi_series_id="CUUR0000SS09011",      # cu: SS09011 — Fresh whole milk
        fdc_query="milk whole 3.25% milkfat",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="butter",
        display_name="Butter (Salted, Grade AA)",
        category="dairy",
        avg_price_series_id="APU0000710111",  # ap: 710111 — Butter, salted, grade AA, stick, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS10011",      # cu: SS10011 — Butter
        fdc_query="butter salted",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="cheddar-cheese",
        display_name="Cheddar Cheese (Natural)",
        category="dairy",
        avg_price_series_id="APU0000710212",  # ap: 710212 — Cheddar cheese, natural, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFJ02",       # cu: SEFJ02 — Cheese and related products
        fdc_query="cheese cheddar",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID confirmed from official ap.item. Confirm live data before flipping price_verified.",
    ),

    # ── Produce ───────────────────────────────────────────────────────────────

    FoodSeed(
        slug="bananas",
        display_name="Bananas",
        category="produce",
        avg_price_series_id="APU0000711211",  # ap: 711211 — Bananas, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFK02",       # cu: SEFK02 — Bananas
        fdc_query="bananas raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="apples",
        display_name="Apples (Red Delicious)",
        category="produce",
        avg_price_series_id="APU0000711111",  # ap: 711111 — Apples, Red Delicious, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFK01",       # cu: SEFK01 — Apples
        fdc_query="apples raw with skin",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="oranges",
        display_name="Oranges (Navel)",
        category="produce",
        avg_price_series_id="APU0000711311",  # ap: 711311 — Oranges, Navel, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS11031",      # cu: SS11031 — Oranges, including tangerines
        fdc_query="oranges raw navels",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="tomatoes",
        display_name="Tomatoes (Field Grown)",
        category="produce",
        avg_price_series_id="APU0000712311",  # ap: 712311 — Tomatoes, field grown, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFL03",       # cu: SEFL03 — Tomatoes
        fdc_query="tomatoes red ripe raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="potatoes",
        display_name="Potatoes (White)",
        category="produce",
        avg_price_series_id="APU0000712112",  # ap: 712112 — Potatoes, white, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFL01",       # cu: SEFL01 — Potatoes
        fdc_query="potatoes flesh and skin raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="lettuce",
        display_name="Lettuce (Iceberg)",
        category="produce",
        avg_price_series_id="APU0000712211",  # ap: 712211 — Lettuce, iceberg, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFL02",       # cu: SEFL02 — Lettuce
        fdc_query="lettuce iceberg raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="carrots",
        display_name="Carrots",
        category="produce",
        avg_price_series_id="APU0000712403",  # ap: 712403 — Carrots, short trimmed and topped, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFL04",       # cu: SEFL04 — Other fresh vegetables (no carrot-specific series)
        fdc_query="carrots raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="CPI series SEFL04 covers all 'other fresh vegetables' — inflation % reflects the category, not carrots specifically.",
    ),
    FoodSeed(
        slug="broccoli",
        display_name="Broccoli",
        category="produce",
        avg_price_series_id="APU0000712412",  # ap: 712412 — Broccoli, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFL04",       # cu: SEFL04 — Other fresh vegetables (shared with carrots)
        fdc_query="broccoli raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="CPI series SEFL04 covers all 'other fresh vegetables' — inflation % reflects the category, not broccoli specifically.",
    ),

    # ── Grains ────────────────────────────────────────────────────────────────

    FoodSeed(
        slug="bread-white",
        display_name="Bread (White, Pan)",
        category="grain",
        avg_price_series_id="APU0000702111",  # ap: 702111 — Bread, white, pan, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS02011",      # cu: SS02011 — White bread
        fdc_query="bread white commercially prepared",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID confirmed from official ap.item. Confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="bread-whole-wheat",
        display_name="Bread (Whole Wheat, Pan)",
        category="grain",
        avg_price_series_id="APU0000702212",  # ap: 702212 — Bread, whole wheat, pan, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS02021",      # cu: SS02021 — Bread other than white
        fdc_query="bread whole wheat commercially prepared",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="rice",
        display_name="Rice (White, Long Grain, Uncooked)",
        category="grain",
        avg_price_series_id="APU0000701312",  # ap: 701312 — Rice, white, long grain, uncooked, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS01031",      # cu: SS01031 — Rice
        fdc_query="rice white long grain unenriched raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="flour",
        display_name="Flour (White, All Purpose)",
        category="grain",
        avg_price_series_id="APU0000701111",  # ap: 701111 — Flour, white, all purpose, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFA01",       # cu: SEFA01 — Flour and prepared flour mixes
        fdc_query="wheat flour white all purpose unenriched",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="pasta",
        display_name="Pasta (Spaghetti / Macaroni)",
        category="grain",
        avg_price_series_id="APU0000701322",  # ap: 701322 — Spaghetti and macaroni, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFA03",       # cu: SEFA03 — Rice, pasta, cornmeal
        fdc_query="spaghetti dry unenriched",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",
        price_verified=False,
        notes="ID from official ap.item; confirm live. CPI series covers rice+pasta+cornmeal — inflation % reflects the category.",
    ),

    # ── Pantry ────────────────────────────────────────────────────────────────

    FoodSeed(
        slug="sugar",
        display_name="Sugar (White, Granulated)",
        category="pantry",
        avg_price_series_id="APU0000715212",  # ap: 715212 — Sugar, white, 33-80 oz. pkg, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFR01",       # cu: SEFR01 — Sugar and sugar substitutes
        fdc_query="sugars granulated",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),

    # ── Beverages ─────────────────────────────────────────────────────────────

    FoodSeed(
        slug="coffee",
        display_name="Coffee (Ground Roast)",
        category="beverage",
        avg_price_series_id="APU0000717311",  # ap: 717311 — Coffee, 100%, ground roast, all sizes, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS17031",      # cu: SS17031 — Roasted coffee
        fdc_query="coffee brewed from grounds",
        fdc_data_type="SR Legacy",
        serving_unit="100ml brewed",
        price_verified=False,
        notes="ID from official ap.item; confirm live. Nutrition query reflects brewed coffee, not dry grounds.",
    ),
    FoodSeed(
        slug="cola",
        display_name="Cola (Non-Diet, 2 Liter)",
        category="beverage",
        avg_price_series_id="APU0000717114",  # ap: 717114 — Cola, nondiet, per 2 liters
        avg_price_unit="per 2 liters",
        cpi_series_id="CUUR0000SEFN01",       # cu: SEFN01 — Carbonated drinks
        fdc_query="carbonated beverage cola",
        fdc_data_type="SR Legacy",
        serving_unit="100ml",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="oj-frozen",
        display_name="Orange Juice (Frozen Concentrate)",
        category="beverage",
        avg_price_series_id="APU0000713111",  # ap: 713111 — Orange juice, frozen concentrate, 12 oz. can, per 16 oz.
        avg_price_unit="per 16 oz",
        cpi_series_id="CUUR0000SEFN02",       # cu: SEFN02 — Frozen noncarbonated juices and drinks
        fdc_query="orange juice frozen concentrate unsweetened",
        fdc_data_type="SR Legacy",
        serving_unit="100ml reconstituted",
        price_verified=False,
        notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
]


def get_food(slug: str) -> Optional[FoodSeed]:
    for f in FOODS:
        if f.slug == slug:
            return f
    return None


def verified_foods() -> list[FoodSeed]:
    """Foods with a confirmed-live BLS average-price series — safe to ship."""
    return [f for f in FOODS if f.price_verified]


def needs_verification() -> list[FoodSeed]:
    """Foods whose AP series still need a live data check before going live."""
    return [f for f in FOODS if not f.price_verified]
