# real-cost-of-food

Shows what groceries actually cost *and* what they're worth — price,
protein-per-dollar, calories-per-dollar, and sustainability tiers
(water use, storage life), one page per food. Data comes from a monthly
BLS + USDA ETL pipeline; see [`CLAUDE.md`](CLAUDE.md) for the full project
rationale and hard rules, and [`DEPLOY.md`](DEPLOY.md) for infrastructure
and setup.

**Stack**: Python ETL → SQLite → static Astro site, deployed to AWS
(S3 + CloudFront + Lambda) via CDK, with GitHub Actions handling CI/CD.

## SEO notes

The sitemap is auto-generated at build time by `@astrojs/sitemap` — new pages appear automatically on the next deploy, no manual resubmission to Google Search Console needed.

**URL changes are the one SEO-sensitive refactoring case.** If you rename or move a page (e.g. `/foods/eggs` → `/eggs`), add a CloudFront redirect for the old URL before deploying. A 404 on a previously-indexed URL hurts rankings; Search Console Coverage report will flag it.

## Before collecting any user data

If the site ever adds forms, accounts, or any user data collection, do the following before launching:
1. Set up a `privacy@[yourdomain].com` alias via Cloudflare Email Routing (free, forwards to your inbox)
2. Uncomment the contact section stub in `site/src/pages/privacy.astro` and fill in the alias

