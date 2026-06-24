"""
seed_sustainability.py

Hand-curated sustainability metadata. This is NOT pulled from an API --
there isn't a clean one for water footprint / storage life at this
granularity. Each row requires a source_citation; the loader enforces
that with a hard assertion so nobody (including future-you, in a hurry)
ships an uncited claim.

PRIMARY SOURCE USED HERE: Mekonnen, M.M. & Hoekstra, A.Y. (2010/2012),
"The green, blue and grey water footprint of farm animals and animal
products" / "...of crops and derived crop products", Value of Water
Research Report Series, UNESCO-IHE -- the standard academic source for
water footprint tiers. Tiers below are deliberately coarse (low/medium/
high) because the underlying numbers vary by region/method and a fake-
precise single number would overstate confidence.

Run this once after run_etl.py has populated the foods table (it needs
the foods to already exist as FK targets).
"""

from db import connect, init_db, DEFAULT_DB_PATH
from foods_seed import FOODS

# (slug, water_use_tier, storage_life_tier, typical_local_production, source_citation)
SUSTAINABILITY_SEED = [
    ("eggs", "medium", "medium",
     "Common in most US regions; backyard production widespread",
     "Mekonnen & Hoekstra (2012), water footprint of animal products, UNESCO-IHE"),
    ("whole-milk", "high", "short",
     "Common in dairy-producing states (CA, WI, NY, ID)",
     "Mekonnen & Hoekstra (2012), water footprint of animal products, UNESCO-IHE"),
    ("ground-beef", "high", "short",
     "Common in cattle-producing states (TX, NE, KS, OK)",
     "Mekonnen & Hoekstra (2012), water footprint of animal products, UNESCO-IHE; beef has the highest water footprint per kg of common proteins"),
    ("chicken-breast", "medium", "short",
     "Common nationwide (broiler production widespread)",
     "Mekonnen & Hoekstra (2012); poultry generally lower water footprint than beef per kg protein"),
    ("bacon", "medium", "medium",
     "Common in pork-producing states (IA, NC, MN)",
     "Mekonnen & Hoekstra (2012), water footprint of animal products, UNESCO-IHE"),
    ("bananas", "medium", "short",
     "Not grown commercially in mainland US (imported, mainly from Latin America)",
     "Mekonnen & Hoekstra (2010), water footprint of crops, UNESCO-IHE"),
    ("tomatoes", "low", "short",
     "Common in CA, FL; widely home-grown nationwide in season",
     "Mekonnen & Hoekstra (2010), water footprint of crops, UNESCO-IHE"),
    ("bread-white", "low", "medium",
     "Wheat grown widely in Midwest/Great Plains; bread itself manufactured nationwide",
     "Mekonnen & Hoekstra (2010), water footprint of wheat, UNESCO-IHE"),
    ("cheddar-cheese", "high", "long",
     "Common in dairy states; aged cheese has long shelf life relative to fresh dairy",
     "Mekonnen & Hoekstra (2012), water footprint of animal products, UNESCO-IHE"),
    ("dry-beans", "low", "long",
     "Common in ND, MI, MN; excellent shelf-stable storage life when kept dry",
     "Mekonnen & Hoekstra (2010), water footprint of pulses, UNESCO-IHE; pulses have among the lowest water footprints per gram of protein"),
    ("lentils", "low", "long",
     "Limited US production (mainly ID, WA, ND, MT); excellent dry storage life",
     "Mekonnen & Hoekstra (2010), water footprint of pulses, UNESCO-IHE"),
    ("tofu", "low", "short",
     "Soybeans widely grown in US Midwest, though tofu processing is regionally concentrated",
     "Mekonnen & Hoekstra (2010), water footprint of soybean products, UNESCO-IHE"),
]


def seed():
    with connect(DEFAULT_DB_PATH) as conn:
        # Ensure foods rows exist (FK target) -- safe to run standalone or after run_etl.py.
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
        for slug, water, storage, local_prod, citation in SUSTAINABILITY_SEED:
            assert citation and len(citation) > 10, f"Missing/weak citation for {slug!r} -- refusing to seed uncited data."
            conn.execute(
                """
                INSERT INTO sustainability (food_slug, water_use_tier, storage_life_tier, typical_local_production, source_citation)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(food_slug) DO UPDATE SET
                    water_use_tier=excluded.water_use_tier,
                    storage_life_tier=excluded.storage_life_tier,
                    typical_local_production=excluded.typical_local_production,
                    source_citation=excluded.source_citation
                """,
                (slug, water, storage, local_prod, citation),
            )
    print(f"Seeded sustainability data for {len(SUSTAINABILITY_SEED)} foods.")


if __name__ == "__main__":
    init_db()
    seed()
