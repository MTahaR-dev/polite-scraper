"""Entry point for the polite scraper."""

from fetcher import fetch

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_PAGE_1 = "https://books.toscrape.com/catalogue/page-1.html"


def main() -> None:
    html = fetch(CATALOGUE_PAGE_1, "catalogue-page-1.html")
    print(f"response_size={len(html):,} bytes")


if __name__ == "__main__":
    main()
