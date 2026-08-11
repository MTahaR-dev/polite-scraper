"""Parser tests. No network: everything runs against saved fixtures."""

from pathlib import Path

import pytest

from main import dedupe_by_url
from normalize import to_price_gbp
from parser import parse_book, parse_catalogue

FIXTURES = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_price_normalization():
    assert to_price_gbp("£51.77") == 51.77
    assert to_price_gbp("  £13.50  ") == 13.50
    assert to_price_gbp(None) is None
    assert to_price_gbp("out of stock") is None


def test_relative_urls_become_absolute():
    html = """
    <section><article class="product_pod">
      <h3><a href="../../book-one_1/index.html">One</a></h3>
    </article></section>
    <li class="next"><a href="page-2.html">next</a></li>
    """
    page_url = "https://books.toscrape.com/catalogue/page-1.html"
    book_urls, next_url = parse_catalogue(html, page_url)

    assert book_urls == ["https://books.toscrape.com/book-one_1/index.html"]
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_missing_description_is_null_and_whitespace_is_stripped():
    record = parse_book(
        read_fixture("book-no-description.html"),
        "https://books.toscrape.com/catalogue/x_1/index.html",
        "https://books.toscrape.com/catalogue/page-1.html",
    )

    assert record["description"] is None  # never invented text
    assert record["title"] == "A Book Without A Description"
    assert record["price_text"] == "£13.50"
    assert record["availability_text"] == "In stock (7 available)"
    assert record["rating_text"] == "Four"


def test_duplicate_urls_are_dropped():
    pairs = [
        ("https://x/a", "page-1"),
        ("https://x/b", "page-1"),
        ("https://x/a", "page-2"),  # same book listed twice
    ]
    result = dedupe_by_url(pairs)

    assert len(result) == 2
    assert dict(result)["https://x/a"] == "page-1"  # first occurrence wins


def test_malformed_page_raises_instead_of_returning_junk():
    with pytest.raises(ValueError):
        parse_book(read_fixture("book-malformed.html"), "https://x/a", "https://x/page-1")


def test_last_page_has_no_next_link():
    _, next_url = parse_catalogue("<section></section>", "https://x/page-3.html")
    assert next_url is None
