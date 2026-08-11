"""HTML extraction: turn saved pages into raw fields."""

from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

RATING_WORDS = {"One", "Two", "Three", "Four", "Five"}


def parse_catalogue(html: str, page_url: str) -> tuple[list[str], str | None]:
    """Return absolute book URLs on this catalogue page, and the next page URL."""
    soup = BeautifulSoup(html, "lxml")

    book_urls = [
        urljoin(page_url, a["href"])  # urljoin, never string concatenation
        for a in soup.select("section article.product_pod h3 a[href]")
    ]

    next_anchor = soup.select_one("li.next a[href]")
    next_url = urljoin(page_url, next_anchor["href"]) if next_anchor else None

    return book_urls, next_url


def _text_or_none(node) -> str | None:
    return node.get_text(strip=True) if node else None


def parse_book(html: str, product_url: str, source_page: str) -> dict:
    """Return the eight raw fields for one book detail page."""
    soup = BeautifulSoup(html, "lxml")

    # scope every selector to the product area, not the whole document
    product = soup.select_one("article.product_page")
    if product is None:
        raise ValueError("no article.product_page on this page")

    main = product.select_one(".product_main")

    rating_text = None
    star = main.select_one("p.star-rating") if main else None
    if star:
        rating_text = next((c for c in star.get("class", []) if c in RATING_WORDS), None)

    # description is the paragraph after the #product_description heading; often absent
    description = None
    heading = product.select_one("#product_description")
    if heading:
        paragraph = heading.find_next_sibling("p")
        description = _text_or_none(paragraph)

    return {
        "title": _text_or_none(main.select_one("h1") if main else None),
        "product_url": product_url,
        "price_text": _text_or_none(main.select_one("p.price_color") if main else None),
        "availability_text": _text_or_none(main.select_one("p.availability") if main else None),
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
