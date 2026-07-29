# Real Cost of Food

**🔗 [realcostoffood.com](https://realcostoffood.com)**

What groceries actually cost, and what they're worth. For each food:
price, protein-per-dollar, calories-per-dollar, and sustainability tiers
(water use, storage life) — sourced from BLS and USDA data, not guesses.

## Why this exists

Most food-price content is either a raw CPI chart (accurate but nobody
searches for "inflation dashboard") or a content-farm listicle (searchable
but made up). This site aims for the overlap: real BLS/USDA numbers,
presented around the questions people actually ask, like "why are eggs so
expensive" or "what's the cheapest protein."

It's a small, hand-curated set of foods — not thousands of thin
auto-generated pages — with a hard rule against showing any number that
isn't backed by a verified source. See [`CLAUDE.md`](CLAUDE.md) for the
full rationale and the non-negotiables around data honesty.

## How it works

```
etl/   Python ETL pipeline → SQLite → data/foods_export.json
site/  Astro static site, reads foods_export.json at build time
rag/   Q&A add-on (retrieval over the same curated data — see RAG.md)
```

- **Data**: monthly batch pull from BLS (prices + inflation) and USDA
  FoodData Central (nutrition), landing in SQLite, then exported to JSON.
- **Site**: Astro, static output only — no server, no client-side
  framework needed for a content site like this.
- **Deploy**: static build pushed to S3, served via CloudFront, provisioned
  with AWS CDK, CI/CD via GitHub Actions. See [`DEPLOY.md`](DEPLOY.md).

## Local development

```bash
# ETL
cd etl
pip install -r requirements.txt --break-system-packages
python run_etl.py                 # real run, needs network + API keys (see .env.example)
python test_etl_offline.py        # offline pipeline test with mocked APIs

# Site
cd site
npm install
npm run dev                       # local preview
npm run build                     # static output to site/dist/
```

Free API keys needed for a real ETL run:
- [BLS](https://data.bls.gov/registrationEngine/)
- [USDA FDC](https://fdc.nal.usda.gov/api-key-signup.html)

## SEO notes

The sitemap is auto-generated at build time by `@astrojs/sitemap` — new
pages appear automatically on the next deploy, no manual resubmission to
Google Search Console needed.

**URL changes are the one SEO-sensitive refactoring case.** If you rename
or move a page (e.g. `/foods/eggs` → `/eggs`), add a CloudFront redirect
for the old URL before deploying. A 404 on a previously-indexed URL hurts
rankings; Search Console's Coverage report will flag it.

## Before collecting any user data

If the site ever adds forms, accounts, or any user data collection, do the
following before launching:
1. Set up a `privacy@[yourdomain].com` alias via Cloudflare Email Routing
   (free, forwards to your inbox)
2. Uncomment the contact section stub in `site/src/pages/privacy.astro`
   and fill in the alias
