"""Entry point for the polite scraper."""

import json

from fetcher import fetch
from normalize import normalize
from parser import parse_book, parse_catalogue

CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


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

    # keep the first occurrence of each URL
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


def main() -> None:
    book_urls = discover_book_urls()
    records = scrape_books(book_urls)
    print("\nSample raw record:")
    print(json.dumps(records[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
