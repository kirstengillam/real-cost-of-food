import { defineConfig } from 'astro/config';

// Static output is the right call for this site: the data changes monthly
// (driven by etl/run_etl.py), not per-request, so there's no reason to pay
// for or operate a server. Build -> upload dist/ to S3 -> serve via
// CloudFront, exactly as scoped.
export default defineConfig({
  site: 'https://example.com', // TODO: replace with your real domain before deploying (used for sitemap/canonical URLs)
  output: 'static',
});
