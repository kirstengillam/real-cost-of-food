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
    (
        "eggs",
        "medium", "mekonnen2012",
        "medium", "mekonnen2012",
        "Common in most US regions; backyard production widespread",
        None,
    ),
    (
        "whole-milk",
        "high", "mekonnen2012",
        "short", "mekonnen2012",
        "Common in dairy-producing states (CA, WI, NY, ID)",
        None,
    ),
    (
        "ground-beef",
        "high", "mekonnen2012",
        "short", "mekonnen2012",
        "Common in cattle-producing states (TX, NE, KS, OK)",
        "Beef has the highest water footprint per kg of common proteins",
    ),
    (
        "chicken-breast",
        "medium", "mekonnen2012",
        "short", "mekonnen2012",
        "Common nationwide (broiler production widespread)",
        "Poultry generally lower water footprint than beef per kg protein",
    ),
    (
        "bacon",
        "medium", "mekonnen2012",
        "medium", "mekonnen2012",
        "Common in pork-producing states (IA, NC, MN)",
        None,
    ),
    (
        "bananas",
        "medium", "mekonnen2010",
        "short", "mekonnen2010",
        "Not grown commercially in mainland US (imported, mainly from Latin America)",
        None,
    ),
    (
        "tomatoes",
        "low", "mekonnen2010",
        "short", "mekonnen2010",
        "Common in CA, FL; widely home-grown nationwide in season",
        None,
    ),
    (
        "bread-white",
        "low", "mekonnen2010",
        "medium", "mekonnen2010",
        "Wheat grown widely in Midwest/Great Plains; bread itself manufactured nationwide",
        "Water footprint based on wheat; processing adds minimal water",
    ),
    (
        "cheddar-cheese",
        "high", "mekonnen2012",
        "long", "mekonnen2012",
        "Common in dairy states; aged cheese has long shelf life relative to fresh dairy",
        None,
    ),
    (
        "dry-beans",
        "low", "mekonnen2010",
        "long", "mekonnen2010",
        "Common in ND, MI, MN; excellent shelf-stable storage life when kept dry",
        "Pulses have among the lowest water footprints per gram of protein",
    ),
    (
        "lentils",
        "low", "mekonnen2010",
        "long", "mekonnen2010",
        "Limited US production (mainly ID, WA, ND, MT); excellent dry storage life",
        None,
    ),
    # ── New proteins ──────────────────────────────────────────────────────────
    (
        "frankfurters",
        "medium", "mekonnen2012",
        "medium", "usda_storage2023",
        "Manufactured nationwide; pork/beef sourcing concentrated in Midwest",
        "Processed meat; opens to short shelf life but unopened packages rated medium",
    ),
    (
        "tuna",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Marine catch; not regionally produced in US. Canned for long shelf stability.",
        "Wild-caught fish has lower water footprint than most land proteins per kg",
    ),
    (
        "peanut-butter",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Peanuts grown mainly in GA, TX, AL, NC. Shelf-stable for 1–2 years unopened.",
        "Legume-based; low water footprint per gram of protein",
    ),
    (
        "dry-beans",
        "low", "mekonnen2010",
        "long", "mekonnen2010",
        "Common in ND, MI, MN; excellent shelf-stable storage life when kept dry",
        "Pulses have among the lowest water footprints per gram of protein",
    ),
    (
        "lentils",
        "low", "mekonnen2010",
        "long", "mekonnen2010",
        "Limited US production (mainly ID, WA, ND, MT); excellent dry storage life",
        None,
    ),
    # ── New dairy ─────────────────────────────────────────────────────────────
    (
        "butter",
        "high", "mekonnen2012",
        "medium", "usda_storage2023",
        "Common in dairy states; concentrated dairy fat product",
        "High water footprint inherits from dairy; refrigerated shelf life ~1–3 months",
    ),
    # ── New produce ───────────────────────────────────────────────────────────
    (
        "apples",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Grown widely in WA, NY, MI, PA, CA. Storage varieties last months refrigerated.",
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
        "carrots",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Grown widely in CA, TX, WA. Refrigerated shelf life up to 4–5 weeks.",
        None,
    ),
    (
        "broccoli",
        "low", "mekonnen2010",
        "short", "usda_storage2023",
        "Grown mainly in CA. Highly perishable; best within 3–5 days of purchase.",
        None,
    ),
    # ── New grains ────────────────────────────────────────────────────────────
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
    # ── New pantry ────────────────────────────────────────────────────────────
    (
        "sugar",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Derived from sugarcane (FL, LA, TX) or sugar beets (MN, ID, ND). Indefinite shelf life when dry.",
        "Water footprint reflects sugarcane or beet cultivation; sugarcane is higher",
    ),
    # ── New beverages ─────────────────────────────────────────────────────────
    (
        "coffee",
        "high", "mekonnen2010",
        "long", "usda_storage2023",
        "Not grown commercially in mainland US; imported mainly from Latin America and Africa.",
        "Coffee has a very high water footprint per kg — among the highest of common beverages",
    ),
    (
        "cola",
        "low", "mekonnen2010",
        "long", "usda_storage2023",
        "Manufactured nationally; primary ingredient is water with corn-syrup sweetener.",
        "Low direct water footprint as a product; corn syrup production adds indirect footprint",
    ),
    (
        "oj-frozen",
        "medium", "mekonnen2010",
        "long", "usda_storage2023",
        "Orange production mainly in FL and CA (fresh crop); frozen concentrate extends shelf life to 1 year+.",
        None,
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
