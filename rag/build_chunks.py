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


def format_value_metrics(vm: dict, price_unit: str) -> str:
    if not vm or vm.get("protein_g_per_dollar") is None:
        return "Value metrics unavailable (price not verified)."
    parts = []
    if vm.get("protein_g_per_dollar") is not None:
        parts.append(f"{vm['protein_g_per_dollar']:.1f}g protein per dollar")
    if vm.get("calories_per_dollar") is not None:
        parts.append(f"{vm['calories_per_dollar']:.0f} calories per dollar")
    if vm.get("fiber_g_per_dollar") is not None and vm["fiber_g_per_dollar"] > 0:
        parts.append(f"{vm['fiber_g_per_dollar']:.1f}g fiber per dollar")
    if vm.get("iron_mg_per_dollar") is not None:
        parts.append(f"{vm['iron_mg_per_dollar']:.1f}mg iron per dollar")
    if vm.get("zinc_mg_per_dollar") is not None:
        parts.append(f"{vm['zinc_mg_per_dollar']:.1f}mg zinc per dollar")
    if vm.get("vitamin_b12_mcg_per_dollar") is not None and vm["vitamin_b12_mcg_per_dollar"] > 0:
        parts.append(f"{vm['vitamin_b12_mcg_per_dollar']:.2f}mcg B12 per dollar")
    if vm.get("folate_mcg_per_dollar") is not None and vm["folate_mcg_per_dollar"] > 0:
        parts.append(f"{vm['folate_mcg_per_dollar']:.0f}mcg folate per dollar")
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
    if n.get("iron_mg"):
        micros.append(f"{n['iron_mg']:.2f}mg iron")
    if n.get("zinc_mg"):
        micros.append(f"{n['zinc_mg']:.2f}mg zinc")
    if n.get("vitamin_b12_mcg") and n["vitamin_b12_mcg"] > 0:
        micros.append(f"{n['vitamin_b12_mcg']:.2f}mcg B12")
    if n.get("folate_mcg") and n["folate_mcg"] > 0:
        micros.append(f"{n['folate_mcg']:.0f}mcg folate")
    result = "Per 100g: " + ", ".join(parts) + "."
    if micros:
        result += " Micronutrients per 100g: " + ", ".join(micros) + "."
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
