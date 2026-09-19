"""
Phase 1: Generate text chunks from foods_export.json for RAG embedding.

Each food becomes one chunk with price, nutrition, value metrics, and
sustainability info rendered as plain prose. Chunks are written to
rag/chunks.json for use in Phase 2 (embed + store in Chroma).
"""

import json
import pathlib

DATA_FILE = pathlib.Path(__file__).parent.parent / "data" / "foods_export.json"
OUTPUT_FILE = pathlib.Path(__file__).parent / "chunks.json"


# (nutrition key, decimal places, unit string, prose label) -- shared between
# format_nutrition and format_value_metrics so a new nutrient only needs to
# be listed once. Order here is the order it appears in the chunk text.
MICRONUTRIENT_CHUNK_FIELDS = [
    ("iron_mg", 2, "mg", "iron"),
    ("zinc_mg", 2, "mg", "zinc"),
    ("vitamin_b12_mcg", 2, "mcg", "B12"),
    ("folate_mcg", 0, "mcg", "folate"),
    ("calcium_mg", 0, "mg", "calcium"),
    ("potassium_mg", 0, "mg", "potassium"),
    ("magnesium_mg", 0, "mg", "magnesium"),
    ("vitamin_a_mcg", 0, "mcg RAE", "vitamin A"),
    ("vitamin_c_mg", 1, "mg", "vitamin C"),
    ("vitamin_d_mcg", 1, "mcg", "vitamin D"),
    ("vitamin_e_mg", 2, "mg", "vitamin E"),
    ("vitamin_k_mcg", 1, "mcg", "vitamin K"),
    ("thiamin_mg", 2, "mg", "thiamin"),
    ("riboflavin_mg", 2, "mg", "riboflavin"),
    ("niacin_mg", 1, "mg", "niacin"),
    ("vitamin_b6_mg", 2, "mg", "B6"),
    ("pantothenic_acid_mg", 2, "mg", "pantothenic acid"),
    ("phosphorus_mg", 0, "mg", "phosphorus"),
    ("selenium_mcg", 1, "mcg", "selenium"),
    ("copper_mg", 2, "mg", "copper"),
    ("manganese_mg", 2, "mg", "manganese"),
    ("choline_mg", 0, "mg", "choline"),
]

# "Nutrients of excess" -- informational per-100g only, no "per dollar" value
# metric (nobody wants more sodium/cholesterol/saturated fat per dollar).
# Zero is a real, meaningful value here (unlike the micronutrients above,
# where a bare 0 from FDC usually just means "not analyzed"), so these use
# an `is not None` check rather than truthiness.
EXCESS_NUTRIENT_CHUNK_FIELDS = [
    ("sodium_mg", 0, "mg", "sodium"),
    ("cholesterol_mg", 0, "mg", "cholesterol"),
    ("saturated_fat_g", 1, "g", "saturated fat"),
    ("trans_fat_g", 1, "g", "trans fat"),
    ("monounsaturated_fat_g", 1, "g", "monounsaturated fat"),
    ("polyunsaturated_fat_g", 1, "g", "polyunsaturated fat"),
]

# Omega-3 components are stored separately (FDC has no total-omega-3 value, and
# ALA is missing from many older records), so a bare 0/None means "not reported"
# -- only state the ones that are actually present and nonzero.
OMEGA3_CHUNK_FIELDS = [
    ("omega3_ala_g", 3, "g", "ALA"),
    ("omega3_epa_g", 3, "g", "EPA"),
    ("omega3_dha_g", 3, "g", "DHA"),
]


def format_value_metrics(vm: dict, price_unit: str) -> str:
    if vm and vm.get("suppressed_reason"):
        return f"Per-dollar value metrics are not available for this food: {vm['suppressed_reason']}"
    if not vm or vm.get("protein_g_per_dollar") is None:
        return "Value metrics unavailable (price not verified)."
    parts = []
    if vm.get("protein_g_per_dollar") is not None:
        parts.append(f"{vm['protein_g_per_dollar']:.1f}g protein per dollar")
    if vm.get("calories_per_dollar") is not None:
        parts.append(f"{vm['calories_per_dollar']:.0f} calories per dollar")
    if vm.get("fiber_g_per_dollar") is not None and vm["fiber_g_per_dollar"] > 0:
        parts.append(f"{vm['fiber_g_per_dollar']:.1f}g fiber per dollar")
    for key, decimals, unit, label in MICRONUTRIENT_CHUNK_FIELDS:
        val = vm.get(f"{key}_per_dollar")
        if val is not None and val > 0:
            parts.append(f"{val:.{decimals}f}{unit} {label} per dollar")
    return "Per dollar spent: " + ", ".join(parts) + "."


def format_nutrition(n: dict) -> str:
    parts = []
    if n.get("energy_kcal"):
        parts.append(f"{n['energy_kcal']:.0f} kcal")
    if n.get("protein_g"):
        parts.append(f"{n['protein_g']:.1f}g protein")
    if n.get("fat_g"):
        parts.append(f"{n['fat_g']:.1f}g fat")
    if n.get("carbs_g"):
        parts.append(f"{n['carbs_g']:.1f}g carbs")
    if n.get("fiber_g") and n["fiber_g"] > 0:
        parts.append(f"{n['fiber_g']:.1f}g fiber")
    if n.get("sugars_g") and n["sugars_g"] > 0:
        parts.append(f"{n['sugars_g']:.1f}g sugars")
    micros = []
    for key, decimals, unit, label in MICRONUTRIENT_CHUNK_FIELDS:
        val = n.get(key)
        if val:
            micros.append(f"{val:.{decimals}f}{unit} {label}")
    excess = []
    for key, decimals, unit, label in EXCESS_NUTRIENT_CHUNK_FIELDS:
        val = n.get(key)
        if val is not None:
            excess.append(f"{val:.{decimals}f}{unit} {label}")
    omega3 = []
    for key, decimals, unit, label in OMEGA3_CHUNK_FIELDS:
        val = n.get(key)
        if val:
            omega3.append(f"{val:.{decimals}f}{unit} {label}")
    result = "Per 100g: " + ", ".join(parts) + "."
    if micros:
        result += " Micronutrients per 100g: " + ", ".join(micros) + "."
    if excess:
        result += " Also per 100g: " + ", ".join(excess) + "."
    if omega3:
        result += " Omega-3 fats per 100g: " + ", ".join(omega3) + "."
    return result


def food_to_chunk(food: dict) -> dict:
    name = food["display_name"]
    category = food["category"]
    slug = food["slug"]
    serving_unit = food.get("serving_unit", "")

    price = food["price"]
    price_usd = price.get("avg_price_usd")
    price_unit = price.get("avg_price_unit", "")
    yoy = price.get("yoy_pct_change")
    as_of = price.get("as_of", "")

    sus = food.get("sustainability", {})
    water_tier = sus.get("water_use_tier", "unknown")
    storage_tier = sus.get("storage_life_tier", "unknown")
    local_prod = sus.get("typical_local_production", "")
    sus_notes = sus.get("notes", "")

    # Build prose chunk
    lines = [f"{name} (category: {category}, slug: {slug})"]

    if serving_unit:
        lines.append(f"Serving size reference: {serving_unit}.")

    if price_usd is not None:
        price_line = f"Current price: ${price_usd:.3f} {price_unit} (as of {as_of}, BLS average price series)."
        if yoy is not None:
            direction = "down" if yoy < 0 else "up"
            price_line += f" Price is {direction} {abs(yoy):.1f}% year-over-year."
        lines.append(price_line)
    else:
        lines.append("Price: not yet verified — no price data available.")

    nutrition = food.get("nutrition_per_100g")
    if nutrition:
        lines.append(format_nutrition(nutrition))

    value_metrics = food.get("value_metrics")
    lines.append(format_value_metrics(value_metrics, price_unit))

    lines.append(
        f"Sustainability: water use is {water_tier}, storage life is {storage_tier}."
    )
    if local_prod:
        lines.append(f"Local production: {local_prod}.")
    if sus_notes:
        lines.append(f"Notes: {sus_notes}.")

    text = " ".join(lines)

    return {
        "id": slug,
        "text": text,
        "metadata": {
            "slug": slug,
            "name": name,
            "category": category,
            "price_usd": price_usd,
            "price_unit": price_unit,
            "price_verified": price.get("price_source") == "bls_avg_price",
            "as_of": as_of,
            "water_use_tier": water_tier,
            "storage_life_tier": storage_tier,
        },
    }


def main():
    with open(DATA_FILE) as f:
        export = json.load(f)

    foods = export["foods"]
    chunks = [food_to_chunk(food) for food in foods]

    output = {
        "generated_at": export["generated_at"],
        "chunk_count": len(chunks),
        "chunks": chunks,
    }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(chunks)} chunks to {OUTPUT_FILE}")
    print("\nSample chunk (eggs):")
    sample = next((c for c in chunks if c["id"] == "eggs"), chunks[0])
    print(sample["text"])


if __name__ == "__main__":
    main()
