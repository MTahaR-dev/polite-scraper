"""Polite HTTP fetching with an on-disk cache."""

import time
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/MTahaR-dev/polite-scraper)"
TIMEOUT = 10
DELAY_SECONDS = 0.5
RETRY_WAIT_SECONDS = 1.0
RETRYABLE_STATUS = {500, 502, 503, 504}  # never 404 or 403

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"

stats = {"fetched": 0, "cache_hits": 0, "failed": 0}


class FetchError(Exception):
    """A page could not be retrieved."""


def fetch(url: str, cache_name: str) -> str:
    """Return the HTML for url, from cache if present, otherwise from the site."""
    path = CACHE_DIR / cache_name

    if path.exists():
        html = path.read_text(encoding="utf-8")
        stats["cache_hits"] += 1
        print(f"CACHE HIT  {url}  ({len(html):,} bytes)")
        return html

    last_error = "unknown"

    for attempt in (1, 2):
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        except requests.RequestException as exc:
            last_error = f"request failed: {exc.__class__.__name__}"
            if attempt == 1:
                time.sleep(RETRY_WAIT_SECONDS)
                continue
            break

        if response.status_code == 200:
            # the site sends UTF-8 but declares no charset; without this, requests guesses Latin-1
            response.encoding = response.apparent_encoding or "utf-8"
            html = response.text

            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")
            stats["fetched"] += 1
            print(f"FETCH      {url}  ({len(html):,} bytes)")

            time.sleep(DELAY_SECONDS)  # delay only after a real request
            return html

        last_error = f"HTTP {response.status_code}"

        # retry a server-side problem once; a 404 or 403 is an answer, not a hiccup
        if response.status_code in RETRYABLE_STATUS and attempt == 1:
            time.sleep(RETRY_WAIT_SECONDS)
            continue
        break

    stats["failed"] += 1
    print(f"FAILED     {url}  ({last_error})")
    raise FetchError(last_error)
