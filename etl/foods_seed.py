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
    fdc_id: Optional[int] = None        # pin a specific FDC record, bypassing fdc_query search.
                                         # FDC's search relevance ranking is not trustworthy for
                                         # picking the right food (e.g. "chicken leg raw" ranked
                                         # "Frog legs, raw" above the actual chicken cuts) -- set
                                         # this after manually verifying the fdc_id via
                                         # https://fdc.nal.usda.gov/food-search once fdc_query
                                         # has been confirmed to mismatch.
    per_dollar_suppressed_reason: Optional[str] = None
                                         # Set when the BLS price basis and the FDC nutrition basis
                                         # can't be compared (e.g. price per lb of dry grounds vs
                                         # nutrition for brewed coffee). run_etl.py then leaves every
                                         # per-dollar metric null and the site shows this text instead.


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
        slug="chicken-whole",
        display_name="Chicken (Fresh, Whole)",
        category="protein",
        avg_price_series_id="APU0000706111",  # ap: 706111 — Chicken, fresh, whole, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS06011",      # cu: SS06011 — Fresh whole chicken
        fdc_query="chicken broilers or fryers whole raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        fdc_id=171447,  # "Chicken, broilers or fryers, meat and skin, raw" -- fdc_query was
                         # matching 171057 "Chicken, broilers or fryers, giblets, raw" instead.

        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
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
        fdc_id=168277,  # "Pork, cured, bacon, unprepared" -- fdc_query was matching 168324
                         # "Pork, bacon, rendered fat, cooked" (drippings, not bacon; also cooked
                         # rather than raw, inconsistent with every other raw-basis nutrition row).
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
        fdc_id=175199,  # "Beans, pinto, mature seeds, raw" -- fdc_query was matching 170086 "Beans, pinto,
                        # mature seeds, sprouted, raw" (62 kcal / 5g protein per 100g, ~4x too low for dry beans).
        serving_unit="100g dry",

        price_verified=True,
        # notes="BLS series covers 'any type' dried beans — price reflects category average, not pinto specifically.",
    ),
    FoodSeed(
        slug="ground-beef-all",
        display_name="Ground Beef (All Uncooked)",
        category="protein",
        avg_price_series_id="APU0000FC1101",  # ap: FC1101 — All uncooked ground beef, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="ground beef 80% lean raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="BLS aggregate covering all uncooked ground beef types; newer series code (FC prefix).",
    ),
    FoodSeed(
        slug="beef-roasts-all",
        display_name="Beef Roasts (All Uncooked)",
        category="protein",
        avg_price_series_id="APU0000FC2101",  # ap: FC2101 — All Uncooked Beef Roasts, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef chuck roast raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="BLS aggregate covering all uncooked beef roasts.",
    ),
    FoodSeed(
        slug="beef-steaks-all",
        display_name="Beef Steaks (All Uncooked)",
        category="protein",
        avg_price_series_id="APU0000FC3101",  # ap: FC3101 — All Uncooked Beef Steaks, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef steak raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="BLS aggregate covering all uncooked beef steaks.",
    ),
    FoodSeed(
        slug="beef-other",
        display_name="Other Beef (Uncooked, Excl. Veal)",
        category="protein",
        avg_price_series_id="APU0000FC4101",  # ap: FC4101 — All Uncooked Other Beef (Excluding Veal), per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="BLS aggregate for uncooked beef cuts not in roast/steak/ground categories.",
    ),
    FoodSeed(
        slug="ground-chuck",
        display_name="Ground Chuck (100% Beef)",
        category="protein",
        avg_price_series_id="APU0000703111",  # ap: 703111 — Ground chuck, 100% beef, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="ground beef 80% lean raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="ground-beef-lean",
        display_name="Ground Beef (Lean and Extra Lean)",
        category="protein",
        avg_price_series_id="APU0000703113",  # ap: 703113 — Ground beef, lean and extra lean, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="ground beef 95% lean raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="beef-stew",
        display_name="Beef for Stew (Boneless)",
        category="protein",
        avg_price_series_id="APU0000703432",  # ap: 703432 — Beef for stew, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef chuck for stew raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="chuck-roast-choice",
        display_name="Chuck Roast (USDA Choice, Boneless)",
        category="protein",
        avg_price_series_id="APU0000703213",  # ap: 703213 — Chuck roast, USDA Choice, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef chuck arm pot roast raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="round-roast",
        display_name="Round Roast (USDA Choice, Boneless)",
        category="protein",
        avg_price_series_id="APU0000703311",  # ap: 703311 — Round roast, USDA Choice, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef round bottom round roast raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="steak-round",
        display_name="Round Steak (Ungraded)",
        category="protein",
        avg_price_series_id="APU0000703512",  # ap: 703512 — Steak, round, graded and ungraded, excl. USDA Prime and Choice, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef round bottom round steak raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="steak-round-choice",
        display_name="Round Steak (USDA Choice, Boneless)",
        category="protein",
        avg_price_series_id="APU0000703511",  # ap: 703511 — Steak, round, USDA Choice, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef round bottom round steak raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="steak-sirloin",
        display_name="Sirloin Steak (USDA Choice, Boneless)",
        category="protein",
        avg_price_series_id="APU0000703613",  # ap: 703613 — Steak, sirloin, USDA Choice, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="beef sirloin top sirloin raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        fdc_id=168728,  # "Beef, top sirloin, steak, separable lean and fat, trimmed to 1/8"
                         # fat, choice, raw" -- fdc_query was matching 167673 "DENNY'S, top
                         # sirloin steak" (a branded, cooked restaurant menu item).
    ),
    FoodSeed(
        slug="pork-chops-all",
        display_name="Pork Chops (All)",
        category="protein",
        avg_price_series_id="APU0000FD3101",  # ap: FD3101 — All Pork Chops, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="pork chop raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="BLS aggregate covering all pork chop cuts; newer series code (FD prefix).",
        fdc_id=168238,  # "Pork, fresh, loin, center loin (chops), bone-in, separable lean and
                         # fat, raw" -- fdc_query was matching 168287 "Pork, cured, salt pork,
                         # raw" (not a chop at all).
    ),
    FoodSeed(
        slug="pork-other",
        display_name="Other Pork (Excl. Canned Ham and Luncheon)",
        category="protein",
        avg_price_series_id="APU0000FD4101",  # ap: FD4101 — All Other Pork (Excluding Canned Ham and Luncheon Slices), per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="pork raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="BLS aggregate for pork cuts not in chops/ham/bacon categories.",
        fdc_id=167888,  # "Pork, fresh, composite of trimmed retail cuts (leg, loin, shoulder,
                         # and spareribs), separable lean and fat, raw" -- fdc_query was matching
                         # 168287 "Pork, cured, salt pork, raw".
    ),
    FoodSeed(
        slug="pork-chops-center-cut",
        display_name="Pork Chops (Center Cut, Bone-In)",
        category="protein",
        avg_price_series_id="APU0000704211",  # ap: 704211 — Chops, center cut, bone-in, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="pork fresh loin center rib chops raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="pork-chops-boneless",
        display_name="Pork Chops (Boneless)",
        category="protein",
        avg_price_series_id="APU0000704212",  # ap: 704212 — Chops, boneless, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="pork fresh loin center rib chops boneless raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="ham-boneless",
        display_name="Ham (Boneless, Excl. Canned)",
        category="protein",
        avg_price_series_id="APU0000704312",  # ap: 704312 — Ham, boneless, excluding canned, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="pork fresh ham whole raw",
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
        cpi_series_id=None,
        fdc_query="chicken breast boneless skinless raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Newer series code (FF prefix).",
    ),
    FoodSeed(
        slug="chicken-legs",
        display_name="Chicken Legs (Bone-In)",
        category="protein",
        avg_price_series_id="APU0000706212",  # ap: 706212 — Chicken legs, bone-in, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="chicken leg raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        fdc_id=172378,  # "Chicken, broilers or fryers, leg, meat and skin, raw" -- fdc_query
                         # was matching 168148 "Frog legs, raw" instead.
    ),
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
        slug="cheddar-cheese",
        display_name="Cheddar Cheese (Natural)",
        category="dairy",
        avg_price_series_id="APU0000710212",  # ap: 710212 — Cheddar cheese, natural, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SEFJ02",       # cu: SEFJ02 — Cheese and related products
        fdc_query="cheese cheddar",
        fdc_data_type="SR Legacy",
        serving_unit="100g",

        price_verified=True,
        # notes="ID confirmed from official ap.item. Confirm live data before flipping price_verified.",
        fdc_id=173414,  # "Cheese, cheddar" -- fdc_query was matching 169901 "Cheese, american
                         # cheddar, imitation" (not real cheese).
    ),

    FoodSeed(
        slug="american-cheese",
        display_name="American Processed Cheese",
        category="dairy",
        avg_price_series_id="APU0000710211",  # ap: 710211 — American processed cheese, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="cheese american processed",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="butter-stick",
        display_name="Butter (Stick)",
        category="dairy",
        avg_price_series_id="APU0000FS1101",  # ap: FS1101 — Butter, stick, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="butter salted",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Newer BLS aggregate series (FS prefix). Distinct from APU0000710111 (grade AA salted).",
    ),
    FoodSeed(
        slug="lowfat-milk",
        display_name="Milk (Low-Fat / Skim)",
        category="dairy",
        avg_price_series_id="APU0000FJ1101",  # ap: FJ1101 — Milk, fresh, low-fat, reduced fat, skim, per gal.
        avg_price_unit="per gallon",
        cpi_series_id=None,
        fdc_query="milk lowfat 1% milkfat",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Newer BLS aggregate series (FJ prefix) covering low-fat, reduced-fat, and skim milk.",
        fdc_id=170872,  # "Milk, lowfat, fluid, 1% milkfat, with added vitamin A and vitamin D"
                         # -- fdc_query was matching 173417 "Cheese, cottage, lowfat, 1%
                         # milkfat" (not milk at all).
    ),
    FoodSeed(
        slug="ice-cream",
        display_name="Ice Cream (Regular, Prepackaged)",
        category="dairy",
        avg_price_series_id="APU0000710411",  # ap: 710411 — Ice cream, prepackaged, bulk, regular, per 1/2 gal.
        avg_price_unit="per half gallon",
        cpi_series_id=None,
        fdc_query="ice cream vanilla",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="yogurt",
        display_name="Yogurt",
        category="dairy",
        avg_price_series_id="APU0000FJ4101",  # ap: FJ4101 — Yogurt, per 8 oz.
        avg_price_unit="per 8 oz",
        cpi_series_id=None,
        fdc_query="yogurt plain whole milk",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Newer BLS series (FJ prefix). Priced per 8 oz container; nutrition measured per 100g.",
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
        slug="oranges",
        display_name="Oranges (Navel)",
        category="produce",
        avg_price_series_id="APU0000711311",  # ap: 711311 — Oranges, Navel, per lb.
        avg_price_unit="per lb",
        cpi_series_id="CUUR0000SS11031",      # cu: SS11031 — Oranges, including tangerines
        fdc_query="oranges raw navels",
        fdc_data_type="SR Legacy",
        serving_unit="100g",

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
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

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
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

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="lettuce-romaine",
        display_name="Lettuce (Romaine)",
        category="produce",
        avg_price_series_id="APU0000FL2101",  # ap: FL2101 — Lettuce, romaine, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="lettuce cos or romaine raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Newer BLS series (FL prefix).",
    ),
    FoodSeed(
        slug="grapefruit",
        display_name="Grapefruit",
        category="produce",
        avg_price_series_id="APU0000711411",  # ap: 711411 — Grapefruit, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="grapefruit raw pink and red",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="lemons",
        display_name="Lemons",
        category="produce",
        avg_price_series_id="APU0000711412",  # ap: 711412 — Lemons, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="lemons raw without peel",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="strawberries",
        display_name="Strawberries",
        category="produce",
        avg_price_series_id="APU0000711415",  # ap: 711415 — Strawberries, dry pint, per 12 oz. (340.2 gm).
        avg_price_unit="per 12 oz",
        cpi_series_id=None,
        fdc_query="strawberries raw",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Priced per 12 oz dry pint; nutrition measured per 100g.",
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

        price_verified=True,
        # notes="ID confirmed from official ap.item. Confirm live data before flipping price_verified.",
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

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
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

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
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

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="pasta",
        display_name="Pasta (Spaghetti / Macaroni)",
        category="grain",
        avg_price_series_id="APU0000701322",  # ap: 701322 — Spaghetti and macaroni, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None, #"CUUR0000SEFA03",       # cu: SEFA03 — Rice, pasta, cornmeal
        fdc_query="spaghetti dry unenriched",
        fdc_data_type="SR Legacy",
        serving_unit="100g dry",

        price_verified=True,
        # notes="ID from official ap.item; confirm live. CPI series covers rice+pasta+cornmeal — inflation % reflects the category.",
    ),

    FoodSeed(
        slug="cookies-chocolate-chip",
        display_name="Cookies (Chocolate Chip)",
        category="grain",
        avg_price_series_id="APU0000702421",  # ap: 702421 — Cookies, chocolate chip, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="cookies chocolate chip commercially prepared",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),

    # ── Pantry ────────────────────────────────────────────────────────────────

    FoodSeed(
        slug="corn-canned",
        display_name="Corn (Canned, Any Style)",
        category="pantry",
        avg_price_series_id="APU0000714221",  # ap: 714221 — Corn, canned, any style, all sizes, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="corn sweet yellow canned",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
    ),
    FoodSeed(
        slug="potato-chips",
        display_name="Potato Chips",
        category="pantry",
        avg_price_series_id="APU0000718311",  # ap: 718311 — Potato chips, per 16 oz. (16 dry oz = 1 lb)
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="potato chips plain salted",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Priced per 16 oz bag; nutrition measured per 100g.",
    ),
    FoodSeed(
        slug="sugar-all-sizes",
        display_name="Sugar (White, All Sizes)",
        category="pantry",
        avg_price_series_id="APU0000715211",  # ap: 715211 — Sugar, white, all sizes, per lb.
        avg_price_unit="per lb",
        cpi_series_id=None,
        fdc_query="sugars granulated",
        fdc_data_type="SR Legacy",
        serving_unit="100g",
        price_verified=True,
        notes="Broader aggregate than APU0000715212 (33-80 oz pkg only).",
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

        price_verified=True,
        per_dollar_suppressed_reason=(
            "The price is for dry ground coffee, but USDA only publishes nutrition for brewed coffee "
            "(and instant powder), so the two can't be compared per dollar."
        ),
        # notes="ID from official ap.item; confirm live. Nutrition query reflects brewed coffee, not dry grounds.",
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

        price_verified=True,
        # notes="ID from official ap.item; confirm live data before flipping price_verified.",
    ),
    FoodSeed(
        slug="soft-drinks-2l",
        display_name="Soft Drinks (2 Liter)",
        category="beverage",
        avg_price_series_id="APU0000FN1101",  # ap: FN1101 — All soft drinks, per 2 liters.
        avg_price_unit="per 2 liters",
        cpi_series_id=None,
        fdc_query="carbonated beverage cola",
        fdc_data_type="SR Legacy",
        serving_unit="100ml",
        price_verified=True,
        notes="BLS aggregate covering all soft drink brands/types; newer series code (FN prefix). Series begins M04 2018.",
    ),
    FoodSeed(
        slug="soft-drinks-cans",
        display_name="Soft Drinks (12-Pack Cans)",
        category="beverage",
        avg_price_series_id="APU0000FN1102",  # ap: FN1102 — All soft drinks, 12 pk, 12 oz. cans, per 12 oz.
        avg_price_unit="per 12 oz",
        cpi_series_id=None,
        fdc_query="carbonated beverage cola",
        fdc_data_type="SR Legacy",
        serving_unit="100ml",
        price_verified=True,
        notes="BLS aggregate; newer series (FN prefix). Series begins M04 2018.",
    ),
    FoodSeed(
        slug="beer",
        display_name="Beer (Malt Beverages, All Types)",
        category="beverage",
        avg_price_series_id="APU0000720111",  # ap: 720111 — Malt beverages, all types, all sizes, any origin, per 16 oz.
        avg_price_unit="per 16 oz",
        cpi_series_id=None,
        fdc_query="beer regular",
        fdc_data_type="SR Legacy",
        serving_unit="100ml",
        price_verified=True,
    ),
    FoodSeed(
        slug="wine",
        display_name="Wine (Red and White Table)",
        category="beverage",
        avg_price_series_id="APU0000720311",  # ap: 720311 — Wine, red and white table, all sizes, any origin, per 1 liter.
        avg_price_unit="per liter",
        cpi_series_id=None,
        fdc_query="wine table red",
        fdc_data_type="SR Legacy",
        serving_unit="100ml",
        price_verified=True,
    ),
    FoodSeed(
        slug="vodka",
        display_name="Vodka",
        category="beverage",
        avg_price_series_id="APU0000720222",  # ap: 720222 — Vodka, all types, all sizes, any origin, per 1 liter.
        avg_price_unit="per liter",
        cpi_series_id=None,
        fdc_query="alcoholic beverage distilled 80 proof",
        fdc_data_type="SR Legacy",
        serving_unit="100ml",
        price_verified=True,
        notes="Series ended M10 2025.",
        fdc_id=174818,  # "Alcoholic beverage, distilled, vodka, 80 proof" -- fdc_query was
                         # matching 174817 "Alcoholic beverage, distilled, rum, 80 proof".
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
