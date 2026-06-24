"""
db.py

SQLite schema for the MVP. SQLite is the right choice at this scale:
~15-50 foods, one snapshot per month, single writer (the monthly ETL job),
many readers (the static site build step). No hosted DB needed for v1.

Migrate to RDS Postgres later only if/when you add:
  - multiple concurrent writers (e.g. a CMS for editorial commentary)
  - a need for the site itself to query live (vs. reading a build-time export)
  - data volume that makes SQLite file size/locking a real problem (unlikely
    for a few hundred foods x a few hundred months)

Tables:
  foods            -- one row per curated food (mirrors foods_seed.py)
  price_snapshots  -- one row per (food, year, month): $ price + inflation %
  nutrition        -- one row per food: nutrient profile per 100g (mostly static)
  sustainability   -- one row per food: hand-curated tiers + source citation
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "real_cost_of_food.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS foods (
    slug              TEXT PRIMARY KEY,
    display_name      TEXT NOT NULL,
    category          TEXT NOT NULL,
    serving_unit      TEXT NOT NULL,
    avg_price_unit    TEXT,
    price_verified    INTEGER NOT NULL DEFAULT 0,
    notes             TEXT
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    food_slug         TEXT NOT NULL REFERENCES foods(slug),
    year              INTEGER NOT NULL,
    month             INTEGER NOT NULL,   -- 1-12
    avg_price_usd     REAL,               -- from BLS Average Price series; NULL if unavailable
    price_source      TEXT NOT NULL,      -- 'bls_avg_price' | 'estimate' | 'usda_ers'
    yoy_pct_change    REAL,               -- from BLS CPI series, NOT computed from avg_price
    fetched_at        TEXT NOT NULL,      -- ISO timestamp of when this row was pulled
    UNIQUE(food_slug, year, month)
);

CREATE TABLE IF NOT EXISTS nutrition (
    food_slug         TEXT PRIMARY KEY REFERENCES foods(slug),
    fdc_id            INTEGER,
    fdc_description   TEXT,
    fdc_data_type      TEXT,
    energy_kcal       REAL,
    protein_g         REAL,
    fat_g             REAL,
    carbs_g           REAL,
    fiber_g           REAL,
    sugars_g          REAL,
    sodium_mg         REAL,
    fetched_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sustainability (
    food_slug          TEXT PRIMARY KEY REFERENCES foods(slug),
    water_use_tier      TEXT,   -- 'low' | 'medium' | 'high'
    storage_life_tier   TEXT,   -- 'short' | 'medium' | 'long'
    typical_local_production TEXT,  -- free text, e.g. 'common in most US regions'
    source_citation     TEXT NOT NULL  -- REQUIRED: where this tier judgment came from
);
"""


@contextmanager
def connect(db_path: Path = DEFAULT_DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


if __name__ == "__main__":
    init_db()
    print(f"Initialized database at {DEFAULT_DB_PATH}")
