# The Polite Scraper

A small scraping pipeline that downloads the first three catalogue pages of
[Books to Scrape](https://books.toscrape.com/), visits all 60 book pages, and turns messy HTML into
clean, schema-validated JSON — politely, without crashing on a broken page, and with an honest
report at the end of every run.

> FlyRank Internship · Backend Development Track · Week 5 · Assignment A9

---

## Target classification

| | |
|---|---|
| **Site** | `https://books.toscrape.com/` |
| **Why this site** | It is a **sandbox** — [toscrape.com](https://toscrape.com/) states it exists specifically so people can practise scraping on it. It hosts no real users, no real commerce and no personal data. |
| **Scope** | The **first 3 catalogue pages only**, and the 60 book detail pages they link to. Nothing else on the domain is touched. |
| **Data collected** | Per book: title, product URL, price text, availability text, rating text, description, plus the source page and fetch timestamp. All of it is public catalogue information about fictional products. |
| **robots.txt** | Requested once on 2026-08-11: **`HTTP/1.1 404 Not Found`** — the site serves no robots file. A missing robots file is **not** permission; it simply means the site has published no crawler rules. The permission here comes from the sandbox's own stated purpose, not from the absence of a file. |
| **Why this is appropriate** | The site was built and published for exactly this exercise, the volume is trivial (63 requests total, cached thereafter), and every request identifies itself with a contact link. |

**I will not reuse this code on another site without checking its rules and terms first.**

---

## Politeness rules

Every real request to the site follows all four:

| Rule | Implementation |
|---|---|
| **Identify yourself** | `User-Agent: FlyRankInternship-A9/1.0 (+https://github.com/MTahaR-dev/polite-scraper)` — a site owner reading their logs can find out who this is |
| **Give up eventually** | 10 second timeout; a request never hangs forever |
| **Go slowly** | at least 500 ms between real requests |
| **Ask once** | every response is cached to `cache/`; re-runs during development read the saved copy instead of the site |

---

*(Setup, schema, run report and ethics note are added as the stages are completed.)*
