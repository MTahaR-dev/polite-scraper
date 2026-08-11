"""Entry point for the polite scraper."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

import fetcher
from fetcher import FetchError, fetch
from models import Book
from normalize import normalize
from parser import parse_book, parse_catalogue

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3

# a URL that does not exist, included on purpose to prove one bad page cannot kill the run
DELIBERATELY_BROKEN_URLS = [
    "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
]

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def discover_book_urls() -> list[tuple[str, str]]:
    """Walk the catalogue's own 'next' links and collect (book_url, source_page) pairs."""
    page_url = CATALOGUE_PAGE_1
    discovered: list[tuple[str, str]] = []
    pages = 0

    while page_url and pages < MAX_CATALOGUE_PAGES:
        pages += 1
        html = fetch(page_url, f"catalogue-page-{pages}.html")
        book_urls, next_url = parse_catalogue(html, page_url)
        discovered.extend((url, page_url) for url in book_urls)
        page_url = next_url

    # the canonical product_url is each record's identity; keep the first occurrence
    seen: dict[str, str] = {}
    for url, source in discovered:
        seen.setdefault(url, source)
    unique = list(seen.items())

    print(f"catalogue_pages={pages} discovered={len(discovered)} unique_urls={len(unique)}")
    return pages, unique


def cache_name_for(product_url: str) -> str:
    """books.toscrape.com/catalogue/<slug>/index.html -> book-<slug>.html"""
    slug = product_url.rstrip("/").split("/")[-2]
    return f"book-{slug}.html"


def scrape_books(book_urls: list[tuple[str, str]]) -> tuple[list[dict], list[dict]]:
    """Each page is handled on its own, so one failure never stops the others."""
    records, failures = [], []

    for product_url, source_page in book_urls:
        try:
            html = fetch(product_url, cache_name_for(product_url))
            records.append(normalize(parse_book(html, product_url, source_page)))
        except (FetchError, ValueError) as exc:
            failures.append({"url": product_url, "reason": str(exc)})

    print(f"detail_pages={len(records)} failed_pages={len(failures)}")
    return records, failures


def validate(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split records into those that satisfy the schema and those that do not."""
    valid, invalid = [], []
    for record in records:
        try:
            valid.append(Book(**record).model_dump())
        except ValidationError as exc:
            invalid.append({
                "product_url": record.get("product_url"),
                "reason": exc.errors(include_url=False),
            })
    return valid, invalid


def write_json(filename: str, data) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    size = len(data) if isinstance(data, list) else 1
    print(f"wrote {path.name} ({size} records)" if isinstance(data, list) else f"wrote {path.name}")


def main() -> None:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    catalogue_pages, book_urls = discover_book_urls()
    book_urls += [(url, "deliberate-failure-test") for url in DELIBERATELY_BROKEN_URLS]

    records, failures = scrape_books(book_urls)
    valid, invalid = validate(records)

    # sorted by canonical URL so a rerun produces a byte-identical file
    valid.sort(key=lambda r: r["product_url"])

    write_json("books.json", valid)
    write_json("errors.json", invalid)

    write_json("run-report.json", {
        "started_at": started_at,
        "duration_seconds": round(time.perf_counter() - started, 2),
        "catalogue_pages": catalogue_pages,
        "urls_attempted": len(book_urls),
        "pages_fetched": fetcher.stats["fetched"],
        "cache_hits": fetcher.stats["cache_hits"],
        "valid_records": len(valid),
        "invalid_records": len(invalid),
        "failed_pages": len(failures),
        "failures": failures,
    })

    print(f"valid={len(valid)} invalid={len(invalid)} failed={len(failures)}")


if __name__ == "__main__":
    main()
