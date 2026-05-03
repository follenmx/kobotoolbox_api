from __future__ import annotations

import argparse
import os
from io import StringIO
import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Supported KoboToolbox API hosts by deployment.
KOBO_SERVERS = {
    "eu": "https://eu.kobotoolbox.org",
    "global": "https://kf.kobotoolbox.org",
}


def build_export_url(base_url: str, form_id: str, settings_id: str, fmt: str = "csv") -> str:
    """Build a KoboToolbox export URL for the provided asset and export settings IDs."""
    return f"{base_url.rstrip('/')}/api/v2/assets/{form_id}/export-settings/{settings_id}/data.{fmt}"


def build_session(timeout: int, retries: int) -> requests.Session:
    """Create a requests session with retries for better reliability and speed."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.request_timeout = timeout
    return session


def get_data(url: str, token: str, timeout: int = 30, retries: int = 3) -> pd.DataFrame:
    """Fetch CSV data from KoboToolbox and return a DataFrame."""
    headers = {"Authorization": f"Token {token}"}
    session = build_session(timeout=timeout, retries=retries)

    response = session.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    decoded = response.content.decode("utf-8")
    csv_data = StringIO(decoded)

    # Automatically detect CSV delimiter to support different export configurations.
    return pd.read_csv(csv_data, sep=None, engine="python")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments with environment-based defaults for easier usage."""
    parser = argparse.ArgumentParser(
        description="Download KoboToolbox export data as CSV and optionally save it."
    )
    parser.add_argument("--server", choices=sorted(KOBO_SERVERS), default=os.getenv("KOBO_SERVER", "eu"))
    parser.add_argument("--base-url", default=os.getenv("KOBO_BASE_URL"), help="Custom Kobo base URL (overrides --server).")
    parser.add_argument("--form-id", default=os.getenv("FORM_ID"), required=os.getenv("FORM_ID") is None)
    parser.add_argument("--settings-id", default=os.getenv("SETTINGS_ID"), required=os.getenv("SETTINGS_ID") is None)
    parser.add_argument("--api-token", default=os.getenv("API_TOKEN"), required=os.getenv("API_TOKEN") is None)
    parser.add_argument("--timeout", type=int, default=int(os.getenv("REQUEST_TIMEOUT", "30")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("REQUEST_RETRIES", "3")))
    parser.add_argument("--output", default=os.getenv("OUTPUT_CSV"), help="Optional local file path to save the CSV.")
    parser.add_argument("--head", type=int, default=5, help="Rows to print as a preview.")
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    base_url = args.base_url or KOBO_SERVERS[args.server]
    url = build_export_url(base_url=base_url, form_id=args.form_id, settings_id=args.settings_id)

    df = get_data(url=url, token=args.api_token, timeout=args.timeout, retries=args.retries)

    if args.output:
        df.to_csv(args.output, index=False)
        print(f"Saved {len(df)} rows to {args.output}")

    if args.head > 0:
        print(df.head(args.head).to_string(index=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
