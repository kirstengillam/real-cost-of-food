"""
seed_sustainability.py

Hand-curated sustainability metadata. Each tier (water use, storage life)
references a row in sustainability_sources so citations are structured and
non-repetitive. The assertion on source fields ensures nobody ships an
uncited tier.

Run once after run_etl.py has populated the foods table.
"""

from db import connect, init_db, DEFAULT_DB_PATH
from foods_seed import FOODS


# ── Sources ───────────────────────────────────────────────────────────────────
# Add new sources here before referencing them in SUSTAINABILITY_SEED below.

SOURCES = [
    dict(
        short_key="mekonnen2010",
        authors="Mekonnen, M.M. & Hoekstra, A.Y.",
        title="The green, blue and grey water footprint of crops and derived crop products",
        year=2010,
        publisher="Value of Water Research Report Series No. 47, UNESCO-IHE",
        url="https://waterfootprint.org/resources/Report47-WaterFootprintCrops-Vol1.pdf",
    ),
    dict(
        short_key="mekonnen2012",
        authors="Mekonnen, M.M. & Hoekstra, A.Y.",
        title="A global assessment of the water footprint of farm animals and animal products",
        year=2012,
        publisher="Ecosystems 15(3), 401–415",
        url="https://doi.org/10.1007/s10021-011-9517-8",
    ),
    dict(
        short_key="usda_storage2023",
        authors="USDA Food Safety and Inspection Service",
        title="FoodKeeper App — Food Product Storage Recommendations",
        year=2023,
        publisher="USDA FSIS",
        url="https://www.foodsafety.gov/keep-food-safe/foodkeeper-app",
    ),
]


# ── Sustainability seed data ───────────────────────────────────────────────────
# Fields:
#   slug, water_use_tier, water_source_key,
#   storage_life_tier, storage_source_key,
#   typical_local_production, notes

SUSTAINABILITY_SEED = [
    # ── Eggs ──────────────────────────────────────────────────────────────────
    (
        "eggs",
        "medium", "mekonnen2012",
        "medium", "usda_storage2023",
        "Common in most US regions; backyard production widespread",
        None,
    ),
    # ── Dairy ─────────────────────────────────────────────────────────────────
    (
        "whole-milk",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in dairy-producing states (CA, WI, NY, ID)",
        None,
    ),
    (
        "lowfat-milk",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in dairy-producing states (CA, WI, NY, ID)",
        None,
    ),
    (
        "cheddar-cheese",
        "high", "mekonnen2012",
        "long", "usda_storage2023",
        "Common in dairy states; aged cheese has long shelf life relative to fresh dairy",
        None,
    ),
    (
        "american-cheese",
        "high", "mekonnen2012",
        "long", "usda_storage2023",
        "Common in dairy states; processed slices have longer shelf life than natural cheese",
        None,
    ),
    (
        "butter-stick",
        "high", "mekonnen2012",
        "medium", "usda_storage2023",
        "Common in dairy states; concentrated dairy fat product",
        "High water footprint inherits from dairy; refrigerated shelf life ~1–3 months",
    ),
    (
        "ice-cream",
        "high", "mekonnen2012",
        "medium", "usda_storage2023",
        "Manufactured nationwide; requires continuous frozen storage",
        "Dairy and sugar base both carry significant water footprints; quality declines after 2–4 months",
    ),
    (
        "yogurt",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in dairy-producing states; widely manufactured nationwide",
        None,
    ),
    # ── Beef ──────────────────────────────────────────────────────────────────
    (
        "ground-beef",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK)",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "ground-beef-all",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Cattle-producing states (TX, NE, KS, OK); broad BLS price series across all fat levels",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "ground-chuck",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK); cut from the chuck section",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "ground-beef-lean",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Cattle-producing states (TX, NE, KS, OK); lower fat content than regular ground beef",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "beef-roasts-all",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Cattle-producing states (TX, NE, KS, OK); broad series covering all roast cuts",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "chuck-roast-choice",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK); USDA Choice grade chuck",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "round-roast",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK); leaner roast from the round",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "beef-steaks-all",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Cattle-producing states (TX, NE, KS, OK); broad series covering all steak cuts",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "steak-round",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK); lean cut from the round",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "steak-round-choice",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK); USDA Choice grade round steak",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "steak-sirloin",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in cattle-producing states (TX, NE, KS, OK); premium cut from the loin",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "beef-stew",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Cattle-producing states (TX, NE, KS, OK); typically chuck or round trimmed for stewing",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "beef-other",
        "high", "mekonnen2012",
        "short", "usda_storage2023",
        "Cattle-producing states (TX, NE, KS, OK); miscellaneous beef cuts",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    # ── Pork ──────────────────────────────────────────────────────────────────
    (
        "bacon",
        "medium", "mekonnen2012",
        "medium", "usda_storage2023",
        "Common in pork-producing states (IA, NC, MN)",
        None,
    ),
    (
        "pork-chops-all",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in pork-producing states (IA, NC, MN); broad BLS series across all chop cuts",
        None,
    ),
    (
        "pork-chops-center-cut",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in pork-producing states (IA, NC, MN); leaner center loin cut",
        None,
    ),
    (
        "pork-chops-boneless",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Common in pork-producing states (IA, NC, MN)",
        None,
    ),
    (
        "pork-other",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Pork-producing states (IA, NC, MN); miscellaneous pork cuts",
        None,
    ),
    (
        "ham-boneless",
        "medium", "mekonnen2012",
        "medium", "usda_storage2023",
        "Common in pork-producing states (IA, NC, MN); cured and cooked for longer shelf life",
        "Curing extends shelf life relative to fresh pork; whole unopened ham keeps ~1–2 weeks refrigerated",
    ),
    # ── Poultry ───────────────────────────────────────────────────────────────
    (
        "chicken-breast",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Common nationwide (broiler production widespread)",
        "Poultry generally lower water footprint than beef per kg protein",
    ),
    (
        "chicken-whole",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Common nationwide (broiler production widespread)",
        "Poultry generally lower water footprint than beef per kg protein",
    ),
    (
        "chicken-legs",
        "medium", "mekonnen2012",
        "short", "usda_storage2023",
        "Common nationwide (broiler production widespread)",
        "Poultry generally lower water footprint than beef per kg protein",
    ),
    # ── Produce ───────────────────────────────────────────────────────────────
    (
        "bananas",
        "medium", "mekonnen2010",
        "short", "usda_storage2023",
        "Not grown commercially in mainland US (imported, mainly from Latin America)",
        None,
    ),
    (
        "tomatoes",
        "low", "mekonnen2010",
        "short", "usda_storage2023",
        "Common in CA, FL; widely home-grown nationwide in season",
        None,
    ),
    (
        "oranges",
        "low", "mekonnen2010",
        "medium", "usda_storage2023",
        "Grown mainly in FL and CA. Available year-round through regional staggering.",
        None,
    ),
    (
        "potatoes",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Grown widely in ID, WA, WI, ND, CO. Store well in cool dark conditions for months.",
        None,
    ),
    (
        "lettuce",
        "low", "mekonnen2010",
        "short", "usda_storage2023",
        "Grown mainly in CA and AZ. Very short shelf life; highly perishable.",
        None,
    ),
    (
        "lettuce-romaine",
        "low", "mekonnen2010",
        "short", "usda_storage2023",
        "Grown mainly in CA and AZ. Very short shelf life; highly perishable.",
        None,
    ),
    (
        "grapefruit",
        "low", "mekonnen2010",
        "medium", "usda_storage2023",
        "Grown mainly in FL, TX, and CA. Keeps 2–3 weeks refrigerated.",
        None,
    ),
    (
        "lemons",
        "low", "mekonnen2010",
        "medium", "usda_storage2023",
        "Grown mainly in CA and AZ. Keeps 3–4 weeks refrigerated.",
        None,
    ),
    (
        "strawberries",
        "low", "mekonnen2010",
        "short", "usda_storage2023",
        "Grown mainly in CA and FL. Highly perishable; best within 1–3 days of purchase.",
        None,
    ),
    # ── Grains and bread ──────────────────────────────────────────────────────
    (
        "bread-white",
        "low", "mekonnen2010",
        "medium", "usda_storage2023",
        "Wheat grown widely in Midwest/Great Plains; bread itself manufactured nationwide",
        "Water footprint based on wheat; processing adds minimal water",
    ),
    (
        "bread-whole-wheat",
        "low", "mekonnen2010",
        "medium", "usda_storage2023",
        "Wheat grown widely in Midwest/Great Plains; bread manufactured nationwide",
        "Water footprint based on wheat grain; processing adds minimal water",
    ),
    (
        "rice",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Limited US production (AR, CA, LA, MO, TX); much is imported. Dry rice stores for years.",
        "Rice has higher water footprint than most other grains per calorie",
    ),
    (
        "flour",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Wheat grown widely in Midwest/Great Plains; flour milled regionally. Stores 1 year+.",
        None,
    ),
    (
        "pasta",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Wheat-based; manufactured widely. Dry pasta stores 2+ years.",
        None,
    ),
    # ── Dry goods and pulses ──────────────────────────────────────────────────
    (
        "dry-beans",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Common in ND, MI, MN; excellent shelf-stable storage life when kept dry",
        "Pulses have among the lowest water footprints per gram of protein",
    ),
    # ── Pantry and snacks ─────────────────────────────────────────────────────
    (
        "sugar-all-sizes",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Derived from sugarcane (FL, LA, TX) or sugar beets (MN, ID, ND). Indefinite shelf life when dry.",
        "Water footprint reflects sugarcane or beet cultivation; sugarcane is higher",
    ),
    (
        "corn-canned",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Corn grown widely in the Midwest (IA, IL, NE, MN). Canned for long shelf stability.",
        None,
    ),
    (
        "cookies-chocolate-chip",
        "medium", "mekonnen2012",
        "long", "usda_storage2023",
        "Manufactured nationwide; ingredients (wheat, butter, eggs, sugar) sourced regionally",
        "Medium water footprint reflects dairy and sugar inputs; packaged cookies keep 6–9 months",
    ),
    (
        "potato-chips",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Potatoes grown widely in ID, WA, WI; chips manufactured regionally. Keeps ~2–3 months unopened.",
        None,
    ),
    # ── Beverages ─────────────────────────────────────────────────────────────
    (
        "coffee",
        "high", "mekonnen2010",
        "long", "usda_storage2023",
        "Not grown commercially in mainland US; imported mainly from Latin America and Africa.",
        "Coffee has a very high water footprint per kg — among the highest of common beverages",
    ),
    (
        "oj-frozen",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Orange production mainly in FL and CA; frozen concentrate extends shelf life to 1 year+.",
        None,
    ),
    (
        "soft-drinks-2l",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Manufactured nationally; primary ingredient is water with corn-syrup sweetener.",
        "Low direct water footprint as a product; corn syrup adds indirect footprint",
    ),
    (
        "soft-drinks-cans",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Manufactured nationally; primary ingredient is water with corn-syrup sweetener.",
        "Low direct water footprint as a product; corn syrup adds indirect footprint",
    ),
    (
        "beer",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Brewed widely across the US; primary ingredients are malted barley, hops, water.",
        "Water footprint mainly from barley cultivation; beer is lower than wine per liter",
    ),
    (
        "wine",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Produced mainly in CA, WA, OR. Stable for months to years depending on variety.",
        "Water footprint reflects grape cultivation; varies significantly by region and variety",
    ),
    (
        "vodka",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Distilled nationwide from grain (corn, wheat) or potatoes; essentially indefinite shelf life sealed.",
        "Water footprint from grain or potato base; distillation process adds minimal water",
    ),
]


def seed():
    with connect(DEFAULT_DB_PATH) as conn:
        # Upsert sources, collect id lookup by short_key
        source_ids: dict[str, int] = {}
        for s in SOURCES:
            assert s["short_key"] and s["authors"] and s["title"] and s["year"], \
                f"Incomplete source record: {s['short_key']!r}"
            conn.execute(
                """
                INSERT INTO sustainability_sources
                    (short_key, authors, title, year, publisher, url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(short_key) DO UPDATE SET
                    authors=excluded.authors, title=excluded.title,
                    year=excluded.year, publisher=excluded.publisher,
                    url=excluded.url
                """,
                (s["short_key"], s["authors"], s["title"], s["year"], s.get("publisher"), s.get("url")),
            )
            row = conn.execute(
                "SELECT id FROM sustainability_sources WHERE short_key = ?", (s["short_key"],)
            ).fetchone()
            source_ids[s["short_key"]] = row["id"]

        # Ensure foods rows exist as FK targets
        for food in FOODS:
            conn.execute(
                """
                INSERT INTO foods (slug, display_name, category, serving_unit, avg_price_unit, price_verified, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(slug) DO NOTHING
                """,
                (food.slug, food.display_name, food.category, food.serving_unit,
                 food.avg_price_unit, int(food.price_verified), food.notes),
            )

        for (slug, water_tier, water_src, storage_tier, storage_src, local_prod, notes) in SUSTAINABILITY_SEED:
            assert water_src in source_ids, f"Unknown water source key {water_src!r} for {slug!r}"
            assert storage_src in source_ids, f"Unknown storage source key {storage_src!r} for {slug!r}"
            conn.execute(
                """
                INSERT INTO sustainability
                    (food_slug, water_use_tier, storage_life_tier,
                     typical_local_production, water_source_id, storage_source_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(food_slug) DO UPDATE SET
                    water_use_tier=excluded.water_use_tier,
                    storage_life_tier=excluded.storage_life_tier,
                    typical_local_production=excluded.typical_local_production,
                    water_source_id=excluded.water_source_id,
                    storage_source_id=excluded.storage_source_id,
                    notes=excluded.notes
                """,
                (slug, water_tier, storage_tier, local_prod,
                 source_ids[water_src], source_ids[storage_src], notes),
            )

    print(f"Seeded {len(SOURCES)} sources and sustainability data for {len(SUSTAINABILITY_SEED)} foods.")


if __name__ == "__main__":
    init_db()
    seed()
