"""
bls_client.py

Thin client for the BLS Public Data API v2.

Docs: https://www.bls.gov/developers/api_signature_v2.htm
No API key required for light use (25 series/day, 10 years of data).
Free registration key raises limits to 500 queries/day, 50 series/request,
20 years of data -- get one at https://data.bls.gov/registrationEngine/
and set BLS_API_KEY as an environment variable.

This module fetches and returns *raw* observations. It does not interpret
average-price vs CPI semantics -- that's the caller's job (see etl/run_etl.py
and the warning in foods_seed.py about not computing inflation from average
price series).
"""

import os
import time
import requests
from dataclasses import dataclass

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
MAX_SERIES_PER_REQUEST = 50  # with a registration key; 25 without
REQUEST_TIMEOUT_SECONDS = 30


@dataclass
class BlsObservation:
    series_id: str
    year: str
    period: str       # "M01".."M12" for monthly
    period_name: str  # "January", etc.
    value: float
    footnotes: list[str]


class BlsClientError(Exception):
    pass


def _api_key() -> str | None:
    return os.environ.get("BLS_API_KEY")  # None is fine; API works unauthenticated at lower limits


def fetch_series(
    series_ids: list[str],
    start_year: int,
    end_year: int,
    retries: int = 3,
    backoff_seconds: float = 2.0,
) -> dict[str, list[BlsObservation]]:
    """
    Fetch one or more BLS series for a year range.
    Returns {series_id: [BlsObservation, ...]} sorted oldest -> newest.
    Raises BlsClientError on repeated failure or a non-REQUEST_SUCCEEDED status.
    """
    if not series_ids:
        return {}
    if len(series_ids) > MAX_SERIES_PER_REQUEST:
        raise BlsClientError(
            f"{len(series_ids)} series requested, max is {MAX_SERIES_PER_REQUEST}. Batch your calls."
        )

    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    key = _api_key()
    if key:
        payload["registrationkey"] = key

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(BLS_API_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            body = resp.json()
        except requests.RequestException as e:
            last_error = e
            time.sleep(backoff_seconds * attempt)
            continue

        status = body.get("status")
        if status != "REQUEST_SUCCEEDED":
            messages = body.get("message", [])
            last_error = BlsClientError(f"BLS API status={status}: {messages}")
            # Don't retry on a clear rejection (e.g. bad series ID) -- retrying won't help.
            if status == "REQUEST_NOT_PROCESSED":
                time.sleep(backoff_seconds * attempt)
                continue
            raise last_error

        results: dict[str, list[BlsObservation]] = {}
        for series in body.get("Results", {}).get("series", []):
            sid = series["seriesID"]
            obs = []
            for point in series.get("data", []):
                try:
                    value = float(point["value"])
                except (ValueError, TypeError):
                    continue  # skip non-numeric/suppressed values
                obs.append(
                    BlsObservation(
                        series_id=sid,
                        year=point["year"],
                        period=point["period"],
                        period_name=point.get("periodName", ""),
                        value=value,
                        footnotes=[
                            fn["text"] for fn in point.get("footnotes", []) if fn.get("text")
                        ],
                    )
                )
            obs.sort(key=lambda o: (o.year, o.period))
            results[sid] = obs

        # Warn (don't fail) if a requested series came back empty/missing -- likely a bad ID.
        missing = set(series_ids) - set(results.keys())
        if missing:
            print(f"[bls_client] WARNING: no data returned for series: {sorted(missing)}")

        return results

    raise BlsClientError(f"BLS API request failed after {retries} attempts: {last_error}")


def latest_value(observations: list[BlsObservation]) -> BlsObservation | None:
    return observations[-1] if observations else None


def year_over_year_pct_change(observations: list[BlsObservation]) -> float | None:
    """
    % change vs the same month one year prior, using the two most recent
    monthly observations that are exactly 12 periods apart in the list.
    Returns None if there isn't enough history.
    """
    if len(observations) < 13:
        return None
    latest = observations[-1]
    year_ago_candidates = [
        o for o in observations
        if o.period == latest.period and int(o.year) == int(latest.year) - 1
    ]
    if not year_ago_candidates:
        return None
    year_ago = year_ago_candidates[0]
    if year_ago.value == 0:
        return None
    return round((latest.value - year_ago.value) / year_ago.value * 100, 2)


if __name__ == "__main__":
    # Quick manual smoke test: python bls_client.py
    data = fetch_series(["APU0000708111"], start_year=2023, end_year=2026)
    for sid, obs in data.items():
        latest = latest_value(obs)
        print(f"{sid}: {len(obs)} observations, latest = {latest}")
