"""Polite HTTP fetching with an on-disk cache."""

import time
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/MTahaR-dev/polite-scraper)"
TIMEOUT = 10
DELAY_SECONDS = 0.5

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "cache"

stats = {"fetched": 0, "cache_hits": 0, "failed": 0}


class FetchError(Exception):
    """A page could not be retrieved."""


def _cache_file(cache_name: str) -> Path:
    return CACHE_DIR / cache_name


def fetch(url: str, cache_name: str) -> str:
    """Return the HTML for url, from cache if present, otherwise from the site."""
    path = _cache_file(cache_name)

    if path.exists():
        html = path.read_text(encoding="utf-8")
        stats["cache_hits"] += 1
        print(f"CACHE HIT  {url}  ({len(html):,} bytes)")
        return html

    try:
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
        )
    except requests.RequestException as exc:
        stats["failed"] += 1
        raise FetchError(f"request failed: {exc}") from exc

    # Only 200 is a page. Anything else is a failed fetch, not HTML to parse.
    if response.status_code != 200:
        stats["failed"] += 1
        raise FetchError(f"HTTP {response.status_code}")

    html = response.text
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    stats["fetched"] += 1
    print(f"FETCH      {url}  ({len(html):,} bytes)")

    time.sleep(DELAY_SECONDS)  # delay only after a real request
    return html
