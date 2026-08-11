# The Polite Scraper

A small scraping pipeline that downloads the first three catalogue pages of
[Books to Scrape](https://books.toscrape.com/), visits all 60 book pages, and turns messy HTML into
clean, schema-validated JSON — politely, without crashing on a broken page, and with an honest
report at the end of every run.

> FlyRank Internship · Backend Development Track · Week 5 · Assignment A9

```
fetch ──▶ extract ──▶ normalize ──▶ validate ──▶ store ──▶ report
```

---

## Target classification

| | |
|---|---|
| **Site** | `https://books.toscrape.com/` |
| **Why this site** | It is a **sandbox** — [toscrape.com](https://toscrape.com/) states it exists specifically so people can practise scraping on it. It hosts no real users, no real commerce and no personal data. |
| **Scope** | The **first 3 catalogue pages only**, and the 60 book detail pages they link to. Nothing else on the domain is touched. |
| **Data collected** | Per book: title, product URL, price, availability, rating, description, plus the source page and fetch timestamp. All of it is public catalogue information about fictional products. |
| **robots.txt** | Requested once on 2026-08-11: **`HTTP/1.1 404 Not Found`** — the site serves no robots file. A missing robots file is **not** permission; it means the site has published no crawler rules. The permission here comes from the sandbox's stated purpose, not from the absence of a file. |
| **Why this is appropriate** | The site was built and published for exactly this exercise, the volume is trivial (63 requests, cached thereafter), and every request identifies itself with a contact link. |

**I will not reuse this code on another site without checking its rules and terms first.**

---

## Politeness rules

Every real request to the site follows all four:

| Rule | Implementation |
|---|---|
| **Identify yourself** | `User-Agent: FlyRankInternship-A9/1.0 (+https://github.com/MTahaR-dev/polite-scraper)` — a site owner reading their logs can find out who this is |
| **Give up eventually** | 10 second timeout; a request never hangs forever |
| **Go slowly** | at least 500 ms between real requests; cached reads have no delay because they never leave this computer |
| **Ask once** | every response is cached to `cache/`; re-runs read the saved copy instead of the site |

**Retries are deliberate, not automatic.** A timeout or a `5xx` gets one second attempt — those are
the site having a bad moment. A `404` is never retried (the page does not exist; asking again will
not create it) and neither is a `403` (the site said no; asking again is how a polite robot becomes
a pest).

---

## Why no browser

The data is already in the HTML the server sends — the titles, prices and descriptions are present
in the raw response, so a plain HTTP request is enough. Driving a headless browser would launch a
full rendering engine to obtain bytes we already have, costing seconds and hundreds of megabytes
per page for nothing. A browser is only warranted when the content is assembled by JavaScript after
load, which is not the case here.

---

## Setup and run

**Requirements:** Python 3.10+

```bash
git clone https://github.com/MTahaR-dev/polite-scraper.git
cd polite-scraper

python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
```

**One command runs the whole pipeline:**

```bash
python src/main.py
```

The first run makes 63 real requests and takes roughly 40 seconds (that is the 500 ms delay, not
slow code). Every run after that reads from `cache/` and finishes in about two seconds. Delete the
`cache/` folder to force a fresh fetch.

**Lane:** Python — `requests` (fetch) · `BeautifulSoup` + `lxml` (extract) · `pydantic` (validate) ·
`json` (store).

### Output

| File | Contents |
|---|---|
| `output/books.json` | the 60 validated records |
| `output/errors.json` | records that failed schema validation, each with the reason |
| `output/run-report.json` | counts, failures, cache hits and duration for the run |
| `cache/` | saved HTML, gitignored — regenerated on demand |

---

## Record schema

Enforced by Pydantic in `src/models.py`. Nothing reaches `books.json` without passing it.

| Field | Type | Notes |
|---|---|---|
| `title` | `str` | required, non-blank |
| `product_url` | `str` | required, must start with `https://` — this is the record's **canonical URL** and its identity |
| `price_text` | `str` | the raw value as printed on the page, e.g. `"£51.77"` |
| `price_gbp` | `float ≥ 0` | the clean value, e.g. `51.77` |
| `availability_text` | `str` | e.g. `"In stock (22 available)"` |
| `rating_text` | `str` | `"One"`…`"Five"` — read from the CSS class, not the text |
| `description` | `str \| null` | **optional**; books with no description store `null`, never invented text |
| `source_page` | `str` | the catalogue page this book was found on |
| `fetched_at` | `str` | UTC ISO-8601 timestamp of the fetch |

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "It's hard to imagine a world without A Light in the Attic...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-11T12:15:52Z"
}
```

**Raw and clean live side by side.** `price_text` is kept next to `price_gbp` on purpose: when a
value looks wrong three weeks from now, the raw string is the evidence of what the page actually
said. Discarding it destroys your ability to debug your own parser.

`source_page` and `fetched_at` are **provenance** — the receipt showing where and when each fact
came from.

**Idempotency:** the canonical `product_url` is each record's identity, duplicates are dropped
before fetching, records are sorted by that URL, and the output file is overwritten rather than
appended. Running the scraper twice produces the same 60 records and a byte-identical file — never
120.

---

## Proof: a real run report

Pasted verbatim from `output/run-report.json`, with one deliberately broken URL included in the
list to prove the run survives it:

```json
{
  "started_at": "2026-08-11T12:15:52Z",
  "duration_seconds": 1.89,
  "catalogue_pages": 3,
  "urls_attempted": 61,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
      "reason": "HTTP 404"
    }
  ]
}
```

`urls_attempted` is 61 because `DELIBERATELY_BROKEN_URLS` in `src/main.py` appends one URL that
does not exist. It failed with `HTTP 404`, was logged and skipped without a retry, and the 60 good
records were unaffected. Failure was tested **on our own side** — never by hammering the real site.

`pages_fetched: 0` and `cache_hits: 63` show this particular run touched the network zero times.

A scraper that reports nothing can fail silently for weeks. The report is how you notice.

---

## Ethics note

Use an official API whenever one exists — it is faster, more stable, and unambiguous about
permission. Never bypass a login, a paywall, or a block: those are the site saying no, and routing
around them is not a technical problem but an answer being ignored. Collect only the fields you
actually need, identify yourself honestly in every request, and go slowly enough that the site
never notices you. A scraper that a site owner would be annoyed to find in their logs is a scraper
written badly.

---

## Known limitation

**The parser is coupled to Books to Scrape's current HTML.** Selectors like
`article.product_page .product_main p.price_color` are scoped to the product area rather than the
whole document, which is better than grabbing "the first thing that looks like a price" — but a
redesign of the site would still break extraction, and nothing here would notice until the schema
started rejecting records. There are no parser fixtures or unit tests, so the first sign of trouble
would be a run where `invalid_records` suddenly jumps. Saved HTML fixtures and a small test suite
are the honest next step.

Second, smaller: the cache never expires. Once a page is saved it is used forever, so the scraper
will happily report stale prices until `cache/` is deleted by hand.
