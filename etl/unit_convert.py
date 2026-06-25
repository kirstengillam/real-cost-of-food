"""
unit_convert.py

Converts a BLS Average Price (denominated per lb / per dozen / per gallon)
into a price per 100g, so it can be divided against USDA FDC nutrition data
(which is per 100g). This is the calculation that actually produces
"protein per dollar" and "calories per dollar" -- the core differentiator
of the site -- so it gets its own module and its own tests rather than
being inlined and trusted blindly.

Supported avg_price_unit strings (must match foods_seed.py exactly):
    "per lb"       -> 1 lb = 453.592 g
    "per dozen"    -> assumes large eggs, ~50g each (USDA standard) = 600g/dozen
    "per gallon"   -> assumes water-like density for milk (~3.78 kg/gallon;
                      whole milk is close enough to water density for this
                      purpose -- if you add other per-gallon liquids with very
                      different density, add a specific conversion, don't reuse this)
    "per 2 liters" -> cola (2000 ml; density ~1.0 g/ml for water-like soda)
    "per 16 oz"    -> OJ frozen concentrate (16 fl oz = 473.18 ml; density
                      ~1.05 g/ml for juice concentrate)

Anything not in this table raises, rather than silently returning a wrong
number. Add new units explicitly as new foods need them.
"""

LB_TO_GRAMS = 453.592
DOZEN_EGGS_TO_GRAMS = 600.0        # 12 x ~50g large egg (USDA large egg = 50g)
GALLON_TO_GRAMS_WATER_DENSITY = 3780.0  # approx, fine for whole milk
TWO_LITERS_TO_GRAMS = 2000.0       # cola; density ~1.0 g/ml
SIXTEEN_OZ_TO_GRAMS = 496.8        # 16 fl oz x 1.05 g/ml (OJ concentrate density)


class UnsupportedUnitError(Exception):
    pass


def price_per_100g(avg_price_usd: float, avg_price_unit: str) -> float:
    """Convert a $ price denominated in avg_price_unit to $ per 100g."""
    unit = avg_price_unit.strip().lower()
    if unit == "per lb":
        grams_total = LB_TO_GRAMS
    elif unit == "per dozen":
        grams_total = DOZEN_EGGS_TO_GRAMS
    elif unit == "per gallon":
        grams_total = GALLON_TO_GRAMS_WATER_DENSITY
    elif unit == "per 2 liters":
        grams_total = TWO_LITERS_TO_GRAMS
    elif unit == "per 16 oz":
        grams_total = SIXTEEN_OZ_TO_GRAMS
    else:
        raise UnsupportedUnitError(
            f"No conversion defined for avg_price_unit={avg_price_unit!r}. "
            f"Add it explicitly to unit_convert.py -- do not guess."
        )
    price_per_gram = avg_price_usd / grams_total
    return round(price_per_gram * 100, 4)


def nutrient_per_dollar(nutrient_amount_per_100g: float, avg_price_usd: float, avg_price_unit: str) -> float:
    """
    e.g. nutrient_per_dollar(protein_g=12.6, avg_price_usd=2.58, avg_price_unit="per dozen")
    -> grams of protein per dollar spent, for eggs at $2.58/dozen.
    """
    p100 = price_per_100g(avg_price_usd, avg_price_unit)
    if p100 <= 0:
        raise ValueError("Computed price per 100g is zero or negative -- check inputs.")
    dollars_per_100g = p100
    grams_per_dollar = 100.0 / dollars_per_100g
    return round(nutrient_amount_per_100g * (grams_per_dollar / 100.0), 2)


if __name__ == "__main__":
    # Sanity checks against numbers we can eyeball.
    # Eggs: ~$2.58/dozen (Jan 2026, per BLS data found earlier), ~12.6g protein/100g
    egg_protein_per_dollar = nutrient_per_dollar(12.6, 2.58, "per dozen")
    print(f"Eggs: {egg_protein_per_dollar} g protein per $1 (at $2.58/dozen)")
    # Sanity: a dozen eggs = 600g, so $2.58 buys 600g, 12.6g protein/100g => 75.6g protein total
    # => 75.6g / $2.58 = ~29.3 g protein per dollar. Confirm below.
    assert abs(egg_protein_per_dollar - 29.30) < 0.5, f"Sanity check failed: got {egg_protein_per_dollar}"
    print("Sanity check passed.")
