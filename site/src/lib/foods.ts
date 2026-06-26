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
  carbs_g: number | null;
  fiber_g: number | null;
  sugars_g: number | null;
  source_fdc_id: number | null;
}

export interface FoodValueMetrics {
  protein_g_per_dollar: number | null;
  calories_per_dollar: number | null;
  fiber_g_per_dollar: number | null;
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
