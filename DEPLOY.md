# Deployment & Setup Guide

## Architecture overview

```
EventBridge cron (2nd of each month)
  → Lambda (etl/ Python 3.12)
      → reads BLS + USDA API keys from SSM Parameter Store
      → runs ETL pipeline
      → writes foods_export.json → S3 data bucket
      → dispatches GitHub Actions workflow_dispatch

GitHub Actions (deploy-site.yml)
  → downloads foods_export.json from S3 data bucket
  → npm run build (Astro static site)
  → aws s3 sync → S3 site bucket
  → CloudFront cache invalidation
```

Two S3 buckets:
- **site bucket** — serves static HTML/CSS/JS via CloudFront (private, OAC)
- **data bucket** — holds `foods_export.json`; versioned for cheap rollback safety

GitHub Actions authenticates to AWS via **OIDC** (no long-lived credentials stored in GitHub).

---

## Prerequisites

- AWS CLI configured (`aws configure` or environment variables)
- Node.js 20+
- Python 3.12 + pip3
- CDK CLI: `npm install -g aws-cdk` (or use `npx cdk` from `infra/`)

---

## One-time setup

### 1. Bootstrap CDK (once per AWS account/region)

```bash
cd infra
npm install
npx cdk bootstrap
```

### 2. Update the GitHub repo reference in the stack

In [`infra/lib/stack.ts`](infra/lib/stack.ts), find the OIDC condition and confirm it matches your GitHub username/repo (it should already say `kirstengillam/real-cost-of-food`):

```ts
'token.actions.githubusercontent.com:sub': 'repo:kirstengillam/real-cost-of-food:ref:refs/heads/main',
```

### 3. Deploy the CDK stack

```bash
cd infra
npx cdk deploy --outputs-file cdk-outputs.json
```

`cdk-outputs.json` is gitignored — it lives on your machine as a reference. The values you'll need for steps 4 and 5:

```
RealCostOfFood.CloudFrontUrl        = https://xxxx.cloudfront.net
RealCostOfFood.SiteBucketName       = real-cost-of-food-site-<account-id>
RealCostOfFood.DataBucketName       = real-cost-of-food-data-<account-id>
RealCostOfFood.DistributionId       = EXXXXXXXXXXXX
RealCostOfFood.DeployRoleArn        = arn:aws:iam::<account-id>:role/...
```

### 4. Store API keys in SSM Parameter Store

These are free-tier public API keys, stored as SecureStrings (encrypted at rest).

```bash
aws ssm put-parameter \
  --name /rcof/bls-api-key \
  --type SecureString \
  --value YOUR_BLS_API_KEY

aws ssm put-parameter \
  --name /rcof/fdc-api-key \
  --type SecureString \
  --value YOUR_FDC_API_KEY

# RAG Q&A — Voyage AI (embeddings) and Anthropic (generation)
aws ssm put-parameter \
  --name /rcof/voyage-api-key \
  --type SecureString \
  --value YOUR_VOYAGE_API_KEY

aws ssm put-parameter \
  --name /rcof/anthropic-api-key \
  --type SecureString \
  --value YOUR_ANTHROPIC_API_KEY

aws ssm put-parameter \
  --name /rcof/langsmith-api-key \
  --type SecureString \
  --value YOUR_LANGSMITH_API_KEY
```

Get API keys:
- BLS: https://data.bls.gov/registrationEngine/ (free)
- USDA FDC: https://fdc.nal.usda.gov/api-key-signup.html (free)
- Voyage AI: https://www.voyageai.com (free tier, for embeddings)
- Anthropic: https://console.anthropic.com (for Claude generation)
- LangSmith: https://smith.langchain.com (free tier, for RAG tracing)

### 5. Add GitHub Actions secrets

In your GitHub repo → Settings → Secrets and variables → Actions, add:

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `DeployRoleArn` output from CDK |
| `SITE_BUCKET_NAME` | `SiteBucketName` output from CDK |
| `DATA_BUCKET_NAME` | `DataBucketName` output from CDK |
| `CLOUDFRONT_DISTRIBUTION_ID` | `DistributionId` output from CDK |
| `ADSENSE_ID` | Your AdSense publisher ID (`ca-pub-XXXXXXXXXXXXXXXX`) — leave blank until ready to monetize |
| `RAG_FUNCTION_NAME` | `RagFunctionName` output from CDK |
| `RAG_FUNCTION_URL` | `RagFunctionUrl` output from CDK |

### 6. First deploy of the site

Push to `main` — GitHub Actions will trigger automatically and deploy the site. Or trigger manually:

```bash
gh workflow run deploy-site.yml --ref main
```

---

## Custom domain (when ready)

1. Register a domain and create a certificate in **ACM in us-east-1** (required for CloudFront).
2. Uncomment the `certificate` and `domainNames` lines in [`infra/lib/stack.ts`](infra/lib/stack.ts).
3. Run `npx cdk deploy` to update the distribution.
4. Point your domain's DNS (CNAME or ALIAS) at the CloudFront domain name.

---

## AdSense monetization (when ready)

Set the `ADSENSE_ID` GitHub secret to your publisher ID (`ca-pub-XXXXXXXXXXXXXXXX`). The AdSense script and ad units are already stubbed in the site — they activate automatically on the next deploy.

To place ad units on specific pages, import `AdUnit` and pass your slot ID:

```astro
import AdUnit from '../../components/AdUnit.astro';

<AdUnit adSlot="1234567890" />
```

---

## Ongoing operations

### ETL runs automatically
EventBridge fires the Lambda on the **2nd of every month at 06:00 UTC**. BLS releases prior-month data on the first Tuesday, so this gives a safe one-day lag.

### Manual ETL run
Trigger from GitHub Actions UI, or via CLI:

```bash
gh workflow run run-etl.yml --ref main
```

To run offline (no API calls, uses mocked data — good for testing):

```bash
gh workflow run run-etl.yml --ref main -f dry_run=true
```

### Update infrastructure

```bash
cd infra
npx cdk diff    # preview changes
npx cdk deploy  # apply
```

### Rollback data export

The data bucket is versioned. To restore a previous `foods_export.json`:

```bash
# List versions
aws s3api list-object-versions \
  --bucket real-cost-of-food-data-<account-id> \
  --prefix foods_export.json

# Restore a specific version
aws s3api get-object \
  --bucket real-cost-of-food-data-<account-id> \
  --key foods_export.json \
  --version-id VERSION_ID \
  /tmp/foods_export.json

aws s3 cp /tmp/foods_export.json \
  s3://real-cost-of-food-data-<account-id>/foods_export.json

# Then redeploy the site to pick it up
gh workflow run deploy-site.yml --ref main
```

---

## Local development

```bash
# ETL (offline, mocked APIs)
cd etl
pip3 install -r requirements.txt
python test_etl_offline.py

# ETL (real APIs — needs keys in environment)
export BLS_API_KEY=...
export FDC_API_KEY=...
python run_etl.py

# Site
cd site
npm install
npm run dev       # http://localhost:4321
npm run build     # static output → site/dist/
```
