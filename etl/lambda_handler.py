"""
Lambda entry point for the monthly ETL job.

Wraps run_etl.main() with two additions:
  1. Reads BLS_API_KEY and FDC_API_KEY from SSM Parameter Store at cold start.
  2. When EXPORT_TARGET=s3, uploads foods_export.json to DATA_BUCKET after the
     local run completes, then triggers a GitHub Actions workflow dispatch so
     the static site rebuilds with fresh data.

Environment variables (set by CDK stack):
  DATA_BUCKET          — S3 bucket name for the data export
  BLS_API_KEY_PARAM    — SSM parameter name for the BLS API key
  FDC_API_KEY_PARAM    — SSM parameter name for the FDC API key
  EXPORT_TARGET        — 's3' in Lambda, absent/ignored for local runs
  GITHUB_TOKEN_PARAM   — (optional) SSM parameter for a GitHub PAT to trigger
                         workflow dispatch after the ETL completes
  GITHUB_REPO          — (optional) 'owner/repo' e.g. 'kirstengillam/real-cost-of-food'
"""

import json
import os
import boto3
from pathlib import Path


def _load_ssm_key(ssm, param_name: str) -> str | None:
    if not param_name:
        return None
    try:
        resp = ssm.get_parameter(Name=param_name, WithDecryption=True)
        return resp['Parameter']['Value']
    except ssm.exceptions.ParameterNotFound:
        print(f"[lambda] WARNING: SSM parameter {param_name!r} not found.")
        return None


def handler(event, context):
    ssm = boto3.client('ssm')

    bls_key = _load_ssm_key(ssm, os.environ.get('BLS_API_KEY_PARAM', ''))
    fdc_key = _load_ssm_key(ssm, os.environ.get('FDC_API_KEY_PARAM', ''))

    if bls_key:
        os.environ['BLS_API_KEY'] = bls_key
    if fdc_key:
        os.environ['FDC_API_KEY'] = fdc_key

    # Run the ETL pipeline (writes to /tmp/foods_export.json in Lambda)
    import run_etl
    from db import DEFAULT_DB_PATH
    from pathlib import Path

    # Override export path to /tmp (Lambda's only writable directory)
    tmp_export = Path('/tmp/foods_export.json')
    run_etl.EXPORT_PATH = tmp_export
    run_etl.DATA_DIR = Path('/tmp')

    run_etl.main()

    # Upload the export to S3
    if os.environ.get('EXPORT_TARGET') == 's3':
        bucket = os.environ['DATA_BUCKET']
        s3 = boto3.client('s3')
        s3.upload_file(
            str(tmp_export),
            bucket,
            'foods_export.json',
            ExtraArgs={'ContentType': 'application/json'},
        )
        print(f"[lambda] Uploaded foods_export.json to s3://{bucket}/foods_export.json")

        _trigger_site_rebuild()

    return {'statusCode': 200, 'body': 'ETL complete'}


def _trigger_site_rebuild():
    """
    Dispatches a GitHub Actions workflow_dispatch event so the static site
    rebuilds with the fresh foods_export.json from S3.

    Requires:
      GITHUB_TOKEN_PARAM — SSM SecureString with a GitHub PAT (repo scope)
      GITHUB_REPO        — 'owner/repo'
    """
    token_param = os.environ.get('GITHUB_TOKEN_PARAM', '')
    repo = os.environ.get('GITHUB_REPO', '')
    if not token_param or not repo:
        print("[lambda] Skipping site rebuild trigger (GITHUB_TOKEN_PARAM/GITHUB_REPO not set).")
        return

    import urllib.request

    ssm = boto3.client('ssm')
    token = _load_ssm_key(ssm, token_param)
    if not token:
        return

    url = f"https://api.github.com/repos/{repo}/actions/workflows/deploy-site.yml/dispatches"
    payload = json.dumps({'ref': 'main'}).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github+json',
            'Content-Type': 'application/json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
        method='POST',
    )
    with urllib.request.urlopen(req) as resp:
        print(f"[lambda] GitHub dispatch response: {resp.status}")
