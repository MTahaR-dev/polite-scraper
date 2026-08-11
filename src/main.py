"""Entry point for the polite scraper."""

import json
from pathlib import Path

from pydantic import ValidationError

from fetcher import fetch
from models import Book
from normalize import normalize
from parser import parse_book, parse_catalogue

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3

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
    return unique


def cache_name_for(product_url: str) -> str:
    """books.toscrape.com/catalogue/<slug>/index.html -> book-<slug>.html"""
    slug = product_url.rstrip("/").split("/")[-2]
    return f"book-{slug}.html"


def scrape_books(book_urls: list[tuple[str, str]]) -> list[dict]:
    records = []
    for product_url, source_page in book_urls:
        html = fetch(product_url, cache_name_for(product_url))
        records.append(normalize(parse_book(html, product_url, source_page)))
    print(f"detail_pages={len(records)}")
    return records


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
    print(f"wrote {path.name} ({len(data)} records)")


def main() -> None:
    book_urls = discover_book_urls()
    records = scrape_books(book_urls)
    valid, invalid = validate(records)

    # sorted by canonical URL so a rerun produces a byte-identical file
    valid.sort(key=lambda r: r["product_url"])

    write_json("books.json", valid)
    write_json("errors.json", invalid)
    print(f"valid={len(valid)} invalid={len(invalid)}")


if __name__ == "__main__":
    main()
