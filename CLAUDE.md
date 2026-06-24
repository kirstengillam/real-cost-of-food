# Real Cost of Food — Project Memory

## What this is

A content/data site that shows what groceries actually cost *and* what
they're worth — price, protein-per-dollar, calories-per-dollar, and basic
sustainability tiers (water use, storage life), one page per food.

**Origin**: pivoted from a generic "food inflation dashboard" idea after
recognizing (a) nobody searches for "inflation dashboard," they search
"why are eggs so expensive," and (b) a pure CPI chart is trivially
copyable by content-farm/AI sites. The nutrition + sustainability layer
is the actual differentiator and moat — it requires real curation work
a scraper bot won't bother doing well.

## Goals (in priority order)

1. **MVP first.** ~12-40 hand-curated foods, not thousands of thin
   programmatic pages. Earn scale after the format proves out.
2. **Eventual small income stream** (likely ad revenue) — so SEO-friendly
   static output, clean URLs, fast pages, and a sitemap matter from day one,
   even while traffic is ~0.
3. **Honesty over precision-theater.** This is the single most important
   constraint in the whole codebase — see "Hard rules" below.
4. **Low operating cost / low maintenance.** Monthly batch ETL, not a
   live service. Target <$20-30/mo at small scale (S3 + CloudFront +
   occasional Lambda invocation).

## Architecture (as built)

```
etl/   Python ETL pipeline → SQLite → data/foods_export.json
site/  Astro static site, reads foods_export.json at BUILD time, outputs static HTML
```

- **SQLite**, not Postgres, for the database — deliberate choice given the
  data volume (dozens of foods, monthly snapshots). Don't "upgrade" to
  Postgres without an actual reason (concurrent writers, live queries from
  the site itself, a CMS). Re-read this note before doing it anyway.
- **Astro static output**, not Next.js/React — content site, no need for
  a JS framework or server. Keep the frontend boring on purpose; the
  pipeline is where the engineering effort should go.
- **Monthly batch job**, not real-time — BLS and USDA data don't change
  faster than monthly anyway.
- Data flow is one-directional: `run_etl.py` is the only writer to the DB;
  `foods_export.json` is the only thing the site reads. Don't have the
  site query SQLite directly — keep that seam.

## Hard rules (do not relax these without explicit discussion)

1. **Two different BLS series per food, never one.** BLS Average Price
   series → dollar figure. BLS CPI series → inflation %. BLS itself warns
   against computing % change from the average-price series. Mixing
   these up is the single easiest way to quietly publish wrong numbers.
2. **`price_verified=False` foods get no price shown, ever.** Don't fetch,
   don't estimate-and-label-as-real, don't fill in a "plausible" number.
   The site shows "estimate pending" / nothing rather than a guess. Check
   `foods_seed.py` for which foods still need their BLS series ID verified
   against FRED/data.bls.gov before `price_verified` can flip to True.
3. **Never compute protein-per-dollar or calories-per-dollar from an
   estimated price.** `value_metrics` fields must be `null` unless
   `price_source == 'bls_avg_price'`. This is enforced in `run_etl.py` —
   don't bypass it to "fill in" a metric.
4. **No county/city-level price claims.** There is no federal CPI at that
   granularity. If hyper-local pages are ever built, they need their own
   local data-collection strategy (e.g. scraped grocery prices), clearly
   labeled as distinct from the BLS-sourced national/regional figures —
   never silently blended with BLS data as if equally authoritative.
5. **Sustainability tiers (water use, storage life) are hand-curated, not
   computed**, and every entry requires a `source_citation` — enforced by
   an assertion in `seed_sustainability.py`. Keep tiers coarse (low/medium/
   high), not fake-precise numbers. Primary source so far: Mekonnen &
   Hoekstra water footprint studies (UNESCO-IHE).
6. **Unit conversions live only in `unit_convert.py`.** If a new food needs
   a price unit not yet handled (currently: per lb, per dozen, per gallon),
   add it explicitly there with a comment — don't inline a conversion
   factor elsewhere or silently reuse a wrong one.

## Current state / what's verified vs. not

Verified live (safe to ship) BLS Average Price series, confirmed against
FRED/BLS directly: eggs, ground beef, bacon, whole milk, bananas, tomatoes.

Still needs verification before `price_verified=True`: chicken breast,
bread (white pan), cheddar cheese — series *names* were seen referenced
on FRED but exact numeric IDs weren't independently confirmed.

No BLS series exists at all (will need USDA ERS or manual sampling, and
must display as `price_source='estimate'`): dry beans, lentils, tofu.

CPI series IDs (for YoY inflation %) are mostly still unverified placeholders
— only blocks the inflation-% stat, not the price itself. Check
`foods_seed.py` `cpi_series_id` fields before trusting any "+X% vs last year"
number on the live site.

## Useful commands

```bash
# ETL
cd etl
pip install -r requirements.txt --break-system-packages
python run_etl.py                 # real run, needs network + API keys (see .env.example)
python test_etl_offline.py        # offline pipeline test with mocked APIs, also refreshes preview data

# Site
cd site
npm install
npm run dev                       # local preview
npm run build                     # static output to site/dist/
```

API keys (free, register before relying on production rate limits):
- BLS: https://data.bls.gov/registrationEngine/
- USDA FDC: https://fdc.nal.usda.gov/api-key-signup.html

## Open decisions / not yet built

- AWS deployment scaffold (Lambda + EventBridge for the monthly ETL run,
  S3 + CloudFront for hosting) — discussed, not yet implemented.
- Ad monetization integration — deferred until there's real traffic to
  justify it; URL structure and sitemap were built with this in mind
  but no ad code exists yet.
- Expanding beyond the current ~12 foods — do this only after verifying
  remaining BLS series IDs, not before.
