// foods.ts
// Loads etl/../data/foods_export.json at BUILD TIME (Astro runs this in
// Node during `astro build`, not in the browser) and provides typed
// accessors for page templates. This file is the single seam between
// the Python ETL pipeline and the site -- if the JSON shape changes,
// update the type here.

import fs from 'node:fs';
import path from 'node:path';

export interface FoodPrice {
  avg_price_usd: number | null;
  avg_price_unit: string | null;
  price_source: 'bls_avg_price' | 'estimate' | 'usda_ers';
  yoy_pct_change: number | null;
  as_of: string | null;
}

export interface FoodNutrition {
  energy_kcal: number | null;
  protein_g: number | null;
  fat_g: number | null;
  saturated_fat_g: number | null;
  trans_fat_g: number | null;
  carbs_g: number | null;
  fiber_g: number | null;
  sugars_g: number | null;
  cholesterol_mg: number | null;
  sodium_mg: number | null;
  iron_mg: number | null;
  zinc_mg: number | null;
  vitamin_b12_mcg: number | null;
  folate_mcg: number | null;
  calcium_mg: number | null;
  potassium_mg: number | null;
  magnesium_mg: number | null;
  vitamin_a_mcg: number | null;
  vitamin_c_mg: number | null;
  vitamin_d_mcg: number | null;
  vitamin_e_mg: number | null;
  vitamin_k_mcg: number | null;
  thiamin_mg: number | null;
  riboflavin_mg: number | null;
  niacin_mg: number | null;
  vitamin_b6_mg: number | null;
  pantothenic_acid_mg: number | null;
  phosphorus_mg: number | null;
  selenium_mcg: number | null;
  copper_mg: number | null;
  manganese_mg: number | null;
  source_fdc_id: number | null;
}

export interface FoodValueMetrics {
  protein_g_per_dollar: number | null;
  calories_per_dollar: number | null;
  fiber_g_per_dollar: number | null;
  iron_mg_per_dollar: number | null;
  zinc_mg_per_dollar: number | null;
  vitamin_b12_mcg_per_dollar: number | null;
  folate_mcg_per_dollar: number | null;
  calcium_mg_per_dollar: number | null;
  potassium_mg_per_dollar: number | null;
  magnesium_mg_per_dollar: number | null;
  vitamin_a_mcg_per_dollar: number | null;
  vitamin_c_mg_per_dollar: number | null;
  vitamin_d_mcg_per_dollar: number | null;
  vitamin_e_mg_per_dollar: number | null;
  vitamin_k_mcg_per_dollar: number | null;
  thiamin_mg_per_dollar: number | null;
  riboflavin_mg_per_dollar: number | null;
  niacin_mg_per_dollar: number | null;
  vitamin_b6_mg_per_dollar: number | null;
  pantothenic_acid_mg_per_dollar: number | null;
  phosphorus_mg_per_dollar: number | null;
  selenium_mcg_per_dollar: number | null;
  copper_mg_per_dollar: number | null;
  manganese_mg_per_dollar: number | null;
  note: string;
}

export interface FoodSustainability {
  water_use_tier: string | null;
  storage_life_tier: string | null;
  typical_local_production: string | null;
  source_citation: string;
}

export interface Food {
  slug: string;
  display_name: string;
  category: string;
  serving_unit: string;
  price: FoodPrice;
  nutrition_per_100g: FoodNutrition | null;
  value_metrics: FoodValueMetrics;
  sustainability: FoodSustainability | null;
}

interface FoodsExport {
  generated_at: string;
  foods: Food[];
}

const DATA_PATH = path.resolve(process.cwd(), '../data/foods_export.json');

let cached: FoodsExport | null = null;

export function loadFoods(): FoodsExport {
  if (cached) return cached;
  if (!fs.existsSync(DATA_PATH)) {
    throw new Error(
      `Missing ${DATA_PATH}. Run the ETL pipeline first: cd ../etl && python run_etl.py`
    );
  }
  const raw = fs.readFileSync(DATA_PATH, 'utf-8');
  cached = JSON.parse(raw) as FoodsExport;
  return cached;
}

export function getAllFoods(): Food[] {
  return loadFoods().foods;
}

export function getFoodBySlug(slug: string): Food | undefined {
  return loadFoods().foods.find((f) => f.slug === slug);
}
