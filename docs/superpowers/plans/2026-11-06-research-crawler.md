# Research Crawler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a resumable Scrapy-based system that discovers, legally acquires, verifies, deduplicates, and exports primary-source materials for the 1949-2025 dissertation corpus.

**Architecture:** Scrapy handles polite fetching and source adapters; a SQLite state store tracks batches, candidates, evidence, and unique materials. Only records passing explicit metadata and full-text checks can reach the nine-column Excel exporter. Authorized full texts use a separate import path, and long text is stored as UTF-8 files.

**Tech Stack:** Python 3.11+, Scrapy, openpyxl, SQLite (stdlib), pytest.

---

## File Map

### Latest Verification Pass (2026-11-07)

- [x] Reparse the two existing USTR Section 301 PDFs from stored allowed evidence; preserve their source metadata and complete bodies.
- [x] Add exact URL plus extracted-body SHA-256 gating for body-derived abstracts and keywords; reject changed bytes or unlisted URLs.
- [x] Update the two existing material rows and field-completeness audit without adding a new material.
- [x] Rebuild the workbook and delivery ZIP; 247 tests and `scrapy check` pass.
- [x] Reparse five National Security Archive records across modern, legacy article, and legacy table layouts; preserve publisher abstracts and add hash-gated body-derived fields.
- [x] Rebuild the workbook and delivery ZIP after the archive pass; 248 tests and `scrapy check` pass.
- [x] Reparse six Clinton White House records across archived page and briefing layouts; add separate exact URL plus body SHA-256 metadata gating.
- [x] Rebuild the workbook and delivery ZIP after the Clinton pass; 249 tests and `scrapy check` pass.
- [x] Reparse three American Presidency Project records from 1998-1999; add exact URL plus body SHA-256 metadata gating for derived fields.
- [x] Rebuild the workbook and delivery ZIP after the Presidency Project pass; 250 tests and `scrapy check` pass.
- [x] Reparse two Radio Free Asia articles from 2012 and 2014; add exact URL plus body SHA-256 gating for derived keywords.
- [x] Rebuild the workbook and delivery ZIP after the RFA pass; 251 tests and `scrapy check` pass.
- [x] Reparse four GovInfo hearing transcripts from 2017-2024 with their official detail-page evidence; add exact transcript URL plus body SHA-256 gating for derived fields.
- [x] Rebuild the workbook and delivery ZIP after the GovInfo pass; 252 tests and `scrapy check` pass.
- [x] Add a reviewed Shorenstein Center landing-page/PDF adapter with exact metadata, PDF, and body SHA-256 gates; verify the 2000-01-01 Jonathan Mirsky report and externalize its 84,853-character body for Excel delivery.
- [x] Rebuild the workbook, coverage audit, and delivery ZIP after the Shorenstein pass; 262 tests and `scrapy check` pass. Current verified corpus: 251 unique materials; current field audit: zero empty abstracts, keywords, or other required fields.
- [ ] Continue the three current verification gaps (1949-1972 think tank; 1972-1991 think tank and research literature) only when a lawful source-displayed exact publication date and complete original body can be verified.
- [x] Record the CIA Reading Room historical broadcasting PDF lead under Scrapy robots compliance; the current endpoint returned HTTP 403 and was retained as restricted without promoting any excerpt.
- [x] Add and review the Shorenstein Center 1992 Tiananmen press-coverage report candidate; the landing page metadata and public PDF are accessible, but the scanned PDF has an incomplete text layer, so it remains pending and is excluded from the formal workbook.
- [x] Test the Heritage Foundation 1983 print-display lead under Scrapy robots compliance; the official endpoint returned HTTP 403 and was retained as restricted without using search-result excerpts.
- [x] Add directory-level candidate batching and configurable polite high-throughput Scrapy settings; preserve ROBOTSTXT_OBEY and per-domain concurrency caps.
- [x] Add NCBI PMC open-access discovery with date-bounded pagination; process 2,523 candidate URLs in three multi-period runs at approximately 63-71 pages/minute.
- [x] Repair missing PMC abstracts/keywords only from stored verified source bodies; withdraw seven unresolved/off-topic records with evidence and database backup preserved.
- [x] Expand the formal corpus from 251 to 2,077 unique materials; all nine-column fields are complete and database integrity checks pass.
- [x] Add offline tests for directory CSV merging/deduplication and the polite fast-profile settings; full suite passes (265 tests), `scrapy check` is OK.
- [ ] Continue toward broader source and period balance; the 2,000-record scale has been reached, but coverage is still uneven and the database is not exhaustive.

- `pyproject.toml`: package metadata, dependencies, and test configuration.
- `scrapy.cfg`: Scrapy project settings entry point.
- `src/research_crawler/__init__.py`: package marker and version.
- `src/research_crawler/items.py`: candidate, source evidence, and export record types.
- `src/research_crawler/adapters.py`: source adapter protocol shared by site-specific parsers.
- `src/research_crawler/discovery.py`: period/event/source query planning and candidate URL CSV import.
- `src/research_crawler/policy.py`: URL/response access policy and bounded retry decisions.
- `src/research_crawler/store.py`: SQLite schema and batch/candidate/evidence/dedup operations.
- `src/research_crawler/validation.py`: field provenance and full-text eligibility gates.
- `src/research_crawler/pipelines.py`: Scrapy item validation and state persistence.
- `src/research_crawler/export.py`: nine-column XLSX generation and long-body file handling.
- `src/research_crawler/import_authorized.py`: import user-provided authorized full-text files.
- `src/research_crawler/firecrawl_import.py`: validate saved Firecrawl raw HTML and paired Scrapy PDF evidence through source adapters and the shared verification pipeline.
- `src/research_crawler/settings.py`: Scrapy throttling, robots, retries, and pipeline defaults.
- `src/research_crawler/spiders/government.py`: first public government-source adapter interface and spider.
- `tests/fixtures/government_page.html`: deterministic public-page fixture.
- `tests/fixtures/restricted_page.html`: restricted-access response fixture.
- `tests/test_policy.py`: URL and response policy tests.
- `tests/test_discovery.py`: period query expansion and candidate import tests.
- `tests/test_store.py`: deduplication and batch persistence tests.
- `tests/test_validation.py`: eligibility gate tests.
- `tests/test_export.py`: schema, duplicate counts, and long-body tests.
- `tests/test_spider.py`: adapter extraction tests using local fixtures.
- `README.md`: setup, lawful-use boundary, batch commands, and outputs.

## Task 1: Establish the package and test harness

**Files:** `pyproject.toml`, `scrapy.cfg`, `src/research_crawler/__init__.py`, `src/research_crawler/settings.py`, `tests/`

- [x] Add the package metadata with Python >=3.11, Scrapy, openpyxl, and pytest as a development dependency.
- [x] Configure pytest to discover `tests/` and the source package from `src/`.
- [x] Add a smoke test importing the project settings and checking the configured pipeline path.
- [x] Run `python -m pytest -q`; expect the smoke test to pass.

- [x] Add promotion gates for HTTP(S) source links, HTML-free body text, and normalized body/source correspondence for HTML/JSON captures.

## Task 2: Define records and access policy

**Files:** `src/research_crawler/items.py`, `src/research_crawler/policy.py`, `tests/test_policy.py`

- [x] Define `MaterialCandidate`, `SourceEvidence`, and `VerifiedMaterial` dataclasses. Keep exactly nine user-facing export fields in `VerifiedMaterial`; keep batch/evidence metadata outside that schema.
- [x] Test policy decisions for allowed public HTTP(S) pages, non-HTTP URLs, explicitly restricted responses (401/403/402), and retryable transient failures.
- [x] Implement `AccessDecision` values `ALLOW`, `RESTRICTED`, `RETRY`, and `REJECT`; never retry restricted responses or attempt authentication/paywall workarounds.
- [x] Run `python -m pytest tests/test_policy.py -q`; expect all policy tests to pass.

## Task 2a: Generate batch queries and ingest candidate URLs

**Files:** `src/research_crawler/discovery.py`, `tests/test_discovery.py`, `README.md`

- [x] Test query generation for each of the four periods and source categories, combining source names, event terms, people, years, and the supplied English topic vocabulary without treating a search term as evidence about an article.
- [x] Test CSV candidate import records the original URL, discovery batch, and query label while leaving title, date, author, and body unverified.
- [x] Implement deterministic query-plan generation and candidate CSV import; do not scrape search-result snippets into article fields.
- [x] Run `python -m pytest tests/test_discovery.py -q`; expect query and import tests to pass.

## Task 3: Persist batches, candidates, evidence, and unique materials

**Files:** `src/research_crawler/store.py`, `tests/test_store.py`

- [x] Test creating a batch with period, source category, and query label; reopening the database must retain its state.
- [x] Test canonical URL/platform-ID deduplication: one primary material row remains and each additional discovery increments duplicate count by one.
- [x] Implement a SQLite store with tables for batches, candidates, evidence, and materials, using transactions and unique source identity constraints.
- [x] Keep restricted, incomplete, or pending-verification items out of the verified materials table.
- [x] Run `python -m pytest tests/test_store.py -q`; expect persistence and dedup tests to pass.

## Task 4: Implement the verification gate

**Files:** `src/research_crawler/validation.py`, `tests/test_validation.py`

- [x] Test rejection when publication date is absent or not exactly `YYYY-MM-DD`, title/link/body evidence is absent, body is empty, or completeness is unconfirmed.
- [x] Test that missing author becomes `未注明`, source-provided abstracts are preserved, and agent-written abstracts must start with `据正文整理：`.
- [x] Implement validation so a candidate becomes exportable only after metadata is tied to the same original source and body completeness is explicitly confirmed.
- [x] Reject search snippets, summaries, markdown scrape artifacts, and records with unverified body provenance.
- [x] Run `python -m pytest tests/test_validation.py -q`; expect all gate cases to pass.

## Task 5: Add Scrapy pipeline and safe defaults

**Files:** `src/research_crawler/pipelines.py`, `src/research_crawler/settings.py`, `src/research_crawler/policy.py`, `tests/test_policy.py`

- [x] Configure robots compliance, AutoThrottle, conservative concurrency, finite retries, and a low default request rate.
- [x] Test that `403`, `401`, `402`, and explicit paywall markers are recorded as restricted and stop follow-up requests for that item.
- [x] Implement a pipeline that records raw response evidence and only persists validated materials as exportable.
- [x] Ensure no cookie injection, login flow, proxy rotation for evasion, CAPTCHA solving, or paywall bypass code exists.
- [x] Run `python -m pytest tests/test_policy.py tests/test_validation.py -q`; expect all tests to pass.

## Task 6: Build the nine-column Excel exporter

**Files:** `src/research_crawler/export.py`, `tests/test_export.py`

- [x] Test exact column names and order: 来源, 时间, 作者, 标题, 摘要, 关键词, 正文, 来源链接, 重复计数.
- [x] Test a short body is written verbatim and an over-limit body is saved in full as UTF-8 with a unique relative path in the 正文 cell.
- [x] Test exporter refuses unverified materials and preserves duplicate count excluding the primary row.
- [x] Implement deterministic XLSX output from verified store records only; do not add explanatory columns.
- [x] Run `python -m pytest tests/test_export.py -q`; expect all exporter tests to pass.

## Task 7: Support authorized full-text import

**Files:** `src/research_crawler/import_authorized.py`, `tests/test_validation.py`, `README.md`

- [x] Test importing a local UTF-8 text file with supplied source URL, bibliographic metadata, and user-provided authorization note; retain file hash and original file path in evidence state.
- [x] Reject imports without an exact publication date, source link, title, or explicit completeness confirmation.
- [x] Implement a CLI entry point that imports one file at a time without inferring authorization or fabricating source fields.
- [x] Run `python -m pytest tests/test_validation.py -q`; expect import gate tests to pass.

## Task 8: Add a verified public-source spider and reusable adapters

**Files:** `src/research_crawler/adapters.py`, `src/research_crawler/spiders/government.py`, `tests/fixtures/government_page.html`, `tests/fixtures/restricted_page.html`, `tests/fixtures/whitehouse_fact_sheet.html`, `tests/fixtures/structured_article.html`, `tests/test_spider.py`

- [x] Create fixtures with explicit metadata and body structure, plus restricted and JSON-LD cases.
- [x] Test extraction preserves body order, prefers displayed dates, excludes templates, and requires JSON-LD body equality with visible content.
- [x] Test absent exact publication date or restricted page yields a candidate/restriction event, never a verified full-text record.
- [x] Implement a reusable adapter protocol, White House fact-sheet adapter, strict JSON-LD adapter, and government spider.
- [x] Run `python -m pytest tests/test_spider.py -q`; all fixture tests pass.

## Task 9: Add batch reporting and operating documentation

**Files:** `src/research_crawler/store.py`, `src/research_crawler/report.py`, `README.md`, `tests/test_store.py`

- [x] Test a batch report includes candidate count, verified full-text count, restricted count, duplicate count, and pending/uncovered URLs.
- [x] Implement report generation grouped by period and source category, without claiming exhaustive coverage.
- [x] Document the four periods, source categories, query dimensions, output folders, restart/resume commands, and access restrictions.
- [x] Run the full offline suite with `python -m pytest -q`; 43 tests pass.

## Task 10: Verify a bounded end-to-end batch

**Files:** `tests/test_spider.py`, `README.md`, generated files under `data/sample-batch/`

- [x] Verify parsing behavior with offline fixtures and a one-URL live crawl against a publicly accessible White House page; no bulk requests were sent.
- [x] Export one verified public full-text item; restricted/pending items are excluded from the workbook by unit-tested gates.
- [x] Inspect the generated workbook: exact nine headers, source URL, visible publication date, body content, and evidence hash match.
- [x] Generate and inspect a batch report with actual counts and an explicit non-exhaustive coverage statement.
- [x] Run `python -m pytest -q` (43 passed), `scrapy list`, and `git diff --check`.

## Task 11: Add a State Department archive remarks adapter

**Files:** `src/research_crawler/spiders/government.py`, `tests/fixtures/state_department_remarks.html`, `tests/test_spider.py`, `README.md`

- [x] Use the official archived State Department page structure to define selectors for its visible title, author/bureau line, publication date, and main-body blocks.
- [x] Add offline tests for correct metadata/body extraction and rejection of a same-URL technical-difficulties response.
- [x] Run one Scrapy request against a public remarks URL and inspect the saved response evidence.
- [x] Record the observed batch result: one candidate, zero verified full texts, one pending because direct Scrapy received a Technical Difficulties page.
- [x] Run the full suite; 45 tests pass.

## Task 12: Ingest Firecrawl raw HTML captures

**Files:** `src/research_crawler/firecrawl_import.py`, `src/research_crawler/items.py`, `src/research_crawler/store.py`, `src/research_crawler/cli.py`, `tests/test_firecrawl_import.py`, `tests/test_store.py`, `tests/test_validation.py`, `README.md`

- [x] Add an `import-firecrawl` path that accepts the configured Firecrawl tool's complete `structuredContent` capture, requires the original `rawHtml` field and matching requested/final URL, HTTP status, and scrape ID, then passes it through the same source adapter and verification pipeline. An explicit tool failure is rejected; the tool schema makes its `success` field optional.
- [x] Store retrieval method and Firecrawl scrape ID with evidence; migrate existing SQLite evidence tables with safe defaults.
- [x] Test successful capture ingestion, exact evidence bytes/hash, rejected Markdown-only/unmatched/failed captures, and legacy database migration.
- [x] Run the importer with a saved full Firecrawl capture for the State Department live page; verify batch counts (1 candidate, 1 verified, 0 pending), nine-column workbook, body equality with SQLite, source HTML byte equality, SHA-256, retrieval method, and scrape ID.
- [x] Run the full suite; 52 tests pass.

## Task 13: Add an AP News article adapter

**Files:** `src/research_crawler/spiders/government.py`, `tests/fixtures/ap_news_article.html`, `tests/test_spider.py`, `README.md`

- [x] Use a publicly accessible AP News page to identify its visible title, byline, publication date, and `RichTextStoryBody` structure; preserve raw HTML capture evidence.
- [x] Add tests for publisher metadata, exact displayed date, ordered paragraph extraction, exclusion of ads/page template, and rejection when the visible publication date is missing.
- [x] Implement hostname-specific AP News parsing; require one body container and a source-visible publication date.
- [x] Verify a real complete page through `import-firecrawl`, SQLite, evidence hash, and the nine-column workbook.
- [x] Register a second page that yielded metadata but no verifiable article body as pending; do not promote its description to full text.
- [x] Run the full suite; 54 tests pass; run `scrapy check` and `git diff --check`.

## Task 14: Add a Voice of America article adapter

**Files:** `src/research_crawler/spiders/government.py`, `tests/fixtures/voa_news_article.html`, `tests/test_spider.py`, `README.md`

- [x] Inspect the public VOA News page's visible headline, byline, publication date, NewsArticle metadata, and article content structure in the saved Scrapy response.
- [x] Add tests for headline/date/author cross-checking, ordered body extraction, exclusion of embedded captions and author biography, and rejection of mismatched structured headline.
- [x] Parse only dateline and prose blocks under `#article-content > .wsw`; require source-visible date to agree with structured publication date.
- [x] Reprocess the recorded VOA candidate after fixing space-separated ISO timestamp parsing and selecting the direct story container rather than the nested author bio; batch result is 1 candidate, 1 verified full text, 0 pending.
- [x] Add AP-source follow-up records for three distinct 2019 VOA reports; resolve source-marked publication time vs update time and allow `未注明` when no author is marked. Batch result is 3 candidates, 3 verified full texts, 0 pending.
- [x] Export and inspect the cumulative main workbook; it has the nine required columns and six verified records.
- [x] Run the full suite; 57 tests pass; run `scrapy check` and `git diff --check`.

## Task 15: Collect VOA WTO archive pages, 1992-2016 period

**Files:** `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `README.md`

- [x] Discover five VOA pages related to China's 2001 WTO accession; treat search excerpts as URL leads only.
- [x] Retrieve each page directly with Scrapy after its robots.txt response allowed crawling.
- [x] Verify page headline, structured author/publisher, visible publication timestamp, structured publication date, and complete article body.
- [x] Preserve the page-displayed 2009 publication dates for these archived pages; do not substitute the 2001 event/original-story dates embedded in titles.
- [x] Record batches of 3 and 2 candidates; both batches verified all full texts.

## Task 16: Collect VOA normalization archive pages, 1992-2016 period

**Files:** `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `README.md`

- [x] Discover three VOA archive pages concerning Nixon's China visit and normalization of U.S.-China relations.
- [x] Retrieve the pages directly with Scrapy after robots.txt allowed access.
- [x] Verify title, author/publisher, main story text, and publication timestamp; preserve page-displayed dates.
- [x] Handle the 2004 archive page where a local displayed date and UTC structured timestamp cross midnight but refer to near-identical publication times; retain the displayed 2009-10-29 date.
- [x] Record 3 candidates, 3 verified full texts, 0 pending.
- [x] Run the full suite; 58 tests pass; `scrapy check` and `git diff --check` pass.

## Task 17: Collect Truman Library and FRUS primary documents, 1949-1972

**Files:** `src/research_crawler/spiders/government.py`, `tests/fixtures/truman_public_paper.html`, `tests/fixtures/frus_document.html`, `tests/test_spider.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add a Truman Library public-paper adapter that extracts the source document date and speech text while excluding navigation and footer content; test missing-date rejection.
- [x] Add a Department of State FRUS adapter that extracts the document, annex, signer, and original document date while excluding archive notes and footnotes.
- [x] Re-fetch the Truman Library URL; its current HTTP 404 response remains pending and is not presented as verified full text.
- [x] Verify a public FRUS page allowed by robots.txt; correct the source logo selector after checking the live page, then verify the complete document and annex.
- [x] Mark a Truman Library document dated 1946-12-18 as outside the 1949-2025 scope and keep it out of the workbook; record a separate 404 URL as pending.
- [x] Export the cumulative workbook and confirm 16 verified materials; full suite: 61 passed; `scrapy check` and `git diff --check` pass.

## Task 18: Collect a second FRUS document layout, 1949-1972

**Files:** `src/research_crawler/spiders/government.py`, `tests/fixtures/frus_document.html`, `tests/test_spider.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover an official FRUS document concerning Taiwan policy from 1951; use Firecrawl search only as a URL lead and retrieve the source page directly with Scrapy after robots.txt allowed access.
- [x] Extend FRUS parsing to the `tei-dateline` layout, signed-name element, and inline editorial note markers while retaining support for the earlier opener/attachment layout.
- [x] Add offline coverage for both layouts; verify the live document is complete and metadata agrees with the same source page.
- [x] Add the verified item to the cumulative workbook; full suite and workbook consistency checks are rerun with the cumulative 17-item set.

## Task 19: Collect FRUS broadcasting and Taiwan Strait documents, 1949-1972

**Files:** `src/research_crawler/spiders/government.py`, `tests/fixtures/frus_document.html`, `tests/test_spider.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover three official FRUS leads concerning Voice of America jamming and Taiwan Strait public statements; use search results only to identify original source URLs.
- [x] Retrieve each original source page directly after Scrapy confirmed robots.txt allowed access.
- [x] Extend FRUS parsing to an `h4.tei-head7` title layout; keep excluding archive footnote markers and verify visible document dates, titles, author/signature metadata, source identity, and complete bodies.
- [x] Reprocess the initially pending page after adding the observed layout; final batch result is 3 candidates, 3 verified full texts, 0 pending.
- [x] Export and verify the cumulative 20-item workbook; record cumulative coverage without claiming completeness.

## Task 20: Collect 1960s-1970s FRUS broadcasting records, 1949-1972

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Discover three official FRUS leads concerning Voice of America and U.S. Information Agency policy; treat search excerpts as discovery only.
- [x] Retrieve all three source pages directly with Scrapy after robots.txt allowed access.
- [x] Verify two full documents; keep the Editorial Note pending because its source page has no publication date or document dateline and the date mentioned in its body is an event date.
- [x] Export the 47,553-character verified USIA document through the existing overflow path and compare its UTF-8 sidecar byte content to the SQLite body.
- [x] Export and verify the cumulative workbook with 22 verified records; rerun the full suite, Scrapy check, and diff check.

## Task 21: Collect U.S.-China normalization records, 1972-1991

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover three official FRUS records on the 1978-1979 normalization process; use search results only as original-page leads.
- [x] Retrieve the three original State Department pages directly after Scrapy confirmed robots.txt allowed access.
- [x] Verify source-page document dates, titles, author fields, and complete bodies; the batch has 3 candidates, 3 verified full texts, 0 pending.
- [x] Export the cumulative workbook with 25 verified records and validate every field against SQLite, resolving the existing long-body path exactly.

## Task 22: Check New York Times public-page access, 1972-1991

**Files:** `src/research_crawler/spiders/government.py`, `src/research_crawler/pipelines.py`, `tests/test_spider.py`, `tests/test_pipeline.py`, `README.md`, `data/research.sqlite3`

- [x] Discover three original New York Times page URLs from 1979 and 1989; use search excerpts only as leads.
- [x] Attempt each with Scrapy and robots.txt enforcement; all three target-page requests were blocked before dispatch and remain outside the verified workbook.
- [x] Add request errbacks and pipeline handling so download/robots failures retain an explicit status detail without creating evidence or downgrading verified/pending records.
- [x] Re-run the batch and confirm its report lists all three as unprocessed with `Forbidden by robots.txt`.

## Task 23: Collect a 1982 FRUS China memorandum and test a 1989 NYT page

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover the official FRUS memorandum and a New York Times VOA article page as original-source leads.
- [x] Retrieve the FRUS page with Scrapy after robots.txt allowed access and verify the 1982-09-22 document; add it to the verified workbook.
- [x] Attempt the 1989 New York Times page with robots.txt enforcement; it remains unprocessed with the block reason in the batch report.
- [x] Re-export and verify all 26 workbook rows, nine fields, and the external UTF-8 body file.

## Task 24: Test AP access for Huawei and tariff coverage, 2017-2025

**Files:** `src/research_crawler/pipelines.py`, `tests/test_pipeline.py`, `README.md`, `data/research.sqlite3`

- [x] Discover three AP News original pages related to Huawei restrictions and US-China tariffs; treat search output as URL leads only.
- [x] Request the pages directly; all three returned HTTP 403 and are excluded from the verified workbook.
- [x] Add a pipeline regression test and record HTTP status codes for restricted pages in batch reports.
- [x] Reprocess the three pages and confirm the report lists each as restricted with `HTTP 403: access restricted`.

## Task 25: Check USTR China policy pages, 2017-2025

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover official USTR Section 301 and Phase One pages as URL leads.
- [x] Retrieve three original USTR pages directly after robots.txt allowed access.
- [x] Inspect each page's original markup: one page links to a PDF but does not contain the report body; two have page text but no source-visible full publication date.
- [x] Record the three precise gaps as pending; do not infer publication dates from URL paths or treat a linked report as already fetched.

## Task 26: Retrieve and verify the USTR Section 301 report PDF, 2017-2025

**Files:** `pyproject.toml`, `src/research_crawler/spiders/government.py`, `src/research_crawler/pipelines.py`, `tests/test_spider.py`, `tests/test_pipeline.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Check the USTR robots.txt rule for the public `/sites/default/files/` report path; retrieve the linked original PDF directly with Scrapy.
- [x] Add pypdf text extraction and retain the exact downloaded PDF evidence bytes with a `.pdf` extension and SHA-256.
- [x] Verify cover title, publishing agency, printed full date, and extractable text on every page; do not use PDF creation/modification timestamps as publication dates.
- [x] Keep absent PDF metadata author as `未注明`; derive the title from the printed cover when generic/missing PDF metadata is present.
- [x] Record the 215-page report as verified; its 780,179-character body is exported to a UTF-8 sidecar referenced by the workbook.
- [x] Verify the sidecar byte/text content against SQLite and rerun the full tests and Scrapy checks.

## Task 27: Collect the 2024 USTR Four-Year Review, 2017-2025

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Discover four official USTR original-page leads related to the 2024 Section 301 four-year review.
- [x] Retrieve all four source URLs directly after Scrapy confirmed robots.txt allowed access.
- [x] Verify the directly linked final report PDF against its cover: title, USTR issuer, printed date 2024-05-14, and extractable text on all 187 pages; preserve the original PDF bytes and SHA-256.
- [x] Export the 466,089-character full text to a UTF-8 sidecar and verify it against SQLite.
- [x] Keep the three associated HTML press pages pending because their original page markup does not provide a verifiable full publication date.
- [x] Export and check the cumulative nine-column workbook: 28 verified records among 49 candidates; rerun tests, Scrapy checks, and diff checks.

## Task 28: Check a FRUS Voice of America lead, 1949-1972

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Use Firecrawl search only to locate a possible official FRUS source URL about VOA and China policy.
- [x] Request the original URL directly with Scrapy after robots.txt allowed access.
- [x] Record the 302 response and empty response body as one pending candidate; verified full texts: 0. Do not use the search excerpt as source text.

## Task 29: Avoid storing empty HTTP response bodies as evidence files

**Files:** `src/research_crawler/pipelines.py`, `tests/test_pipeline.py`, `data/research.sqlite3`, `data/evidence/`

- [x] Trace the 302/empty-body record: the spider intentionally sends non-2xx responses through the pipeline for status accounting, and the pipeline previously wrote every response body unconditionally.
- [x] Add a regression test proving an empty response keeps its HTTP status and hash but has no evidence-file path and remains pending.
- [x] Write evidence files only for nonempty response bodies; retain full evidence bytes for nonempty HTML/PDF responses.
- [x] Repair the one generated 0-byte artifact and set its database path to NULL while preserving the evidence row and pending candidate.
- [x] Run the full test suite (68 passed), Scrapy checks, empty-evidence audit, and diff check.

## Task 30: Expand bilingual discovery queries without oversized batches

**Files:** `src/research_crawler/discovery.py`, `tests/test_discovery.py`, `README.md`

- [x] Add a failing test for Chinese source, event, and topic coverage, bounded query count, grouped English topic terms, and unique query labels.
- [x] Add Chinese names for the requested media, government sources, think tanks, new-media accounts, and research-literature categories.
- [x] Add Chinese event and topic vocabulary across all four research periods.
- [x] Group topic terms by language with OR syntax, reducing each period/category plan to 96-192 actionable queries.
- [x] Include source names in query labels so progress can distinguish source/event/language combinations.
- [x] Verify the full test suite (69 passed).

## Task 31: Verify a 2023 State Department China-policy speech

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/state_department_remarks_transcript.html`, `README.md`, `data/research.sqlite3`, `data/captures/`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Discover the original 2023 Blinken SAIS speech URL; treat search results as leads only.
- [x] Request the original page with Scrapy after robots.txt allowed access; retain the HTTP 200 “Technical Difficulties” response as pending evidence.
- [x] Retrieve Firecrawl `rawHtml` for the same original/final URL with HTTP 200 and scrape ID, then pass it through the source-specific adapter and shared verification pipeline.
- [x] Add offline coverage for the observed article-header plus `.entry-content` transcript layout; exclude video-player error/modal text and page metadata from the body.
- [x] Verify the same-page title, author, source-visible publication date 2023-09-13, and 36,722-character transcript; preserve original HTML bytes and SHA-256.
- [x] Export and verify the cumulative nine-column workbook with 29 verified records among 51 candidates; verify the UTF-8 long-body sidecar against SQLite.

## Task 32: Add a second State Department Xinjiang-related speech

**Files:** `README.md`, `data/research.sqlite3`, `data/captures/`, `data/evidence/`, `data/materials.xlsx`

- [x] Request the official 2023 International Religious Freedom Report Rollout page directly with Scrapy after robots.txt allowed access; its response was a technical-difficulties page and remained pending.
- [x] Retrieve the same original page as Firecrawl raw HTML with source URL, final URL, HTTP 200, and scrape ID; import only through the source-specific adapter and verification pipeline.
- [x] Verify the page's title, Blinken byline, publication date 2024-06-26, and complete 14,839-character speech; preserve exact HTML bytes and hash.
- [x] Report batch 27 as 2 candidates, 2 verified, 0 pending; export and verify the cumulative nine-column workbook with 30 verified rows among 52 candidates.

## Task 33: Collect a 2024 State Department China briefing

**Files:** `README.md`, `data/research.sqlite3`, `data/captures/`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Discover the official January 11, 2024 State Department press briefing URL; search excerpts remained discovery-only.
- [x] Request the original URL directly with Scrapy after robots.txt allowed access; preserve the technical-difficulties response as pending evidence.
- [x] Fetch Firecrawl raw HTML for the same source/final URL with HTTP 200 and scrape ID, then run the original HTML through the State Department adapter and verification pipeline.
- [x] Verify the source-page title, Matthew Miller byline, publication date 2024-01-11, and complete 39,701-character briefing transcript.
- [x] Report batch 28 as 1 candidate, 1 verified; verify the exact nine-column workbook and 39,701-character UTF-8 sidecar against SQLite.

## Task 34: Verify five Brookings trade-war articles, 2017-2025

**Files:** `src/research_crawler/spiders/government.py`, `src/research_crawler/store.py`, `tests/test_spider.py`, `tests/test_pipeline.py`, `tests/fixtures/brookings_article.html`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search only to discover Brookings original-page leads; select five direct Brookings article URLs.
- [x] Request each original page with Scrapy after robots.txt allowed access; preserve the exact HTTP 200 HTML and SHA-256.
- [x] Add an observed-layout adapter and offline regression fixture for structured metadata and ordered `wysiwyg-block` text; exclude related content, author biographies, and institutional statements, preserve the editor's-note label, and prefer the visible Authors section order over conflicting JSON-LD creator order.
- [x] Refresh a previously verified material and its evidence reference when the same source URL is verified again, without increasing its duplicate count.
- [x] Verify page title, authors, source metadata, and publication dates/text lengths for five articles: 2020-08-07/14,509; 2019-11-25/1,094; 2019-02-28/7,522; 2019-06-24/1,009; 2019-02-28/14,766.
- [x] Report batches 29-33 as 5 candidates, 5 verified, 0 pending; export and verify the 36-record nine-column workbook against SQLite and evidence.

Further Brookings page layouts and other think tanks, periods, source families, and research literature remain to be searched in later batches.

## Task 35: Verify two CSIS China-policy articles, 2017-2025

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/csis_commentary_article.html`, `tests/fixtures/csis_quote_analysis.html`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search only to discover CSIS original-page leads; select two direct CSIS article URLs.
- [x] Request both original pages with Scrapy after robots.txt allowed access; preserve the exact HTTP 200 HTML and SHA-256.
- [x] Add a CSIS adapter and fixtures for commentary and long analysis layouts; preserve ordered paragraphs, headings, lists, and quote blocks while excluding downloads, media embeds, related content, and author biographies.
- [x] Verify source-page titles, authors, dates (2025-05-13 and 2020-08-03), and complete bodies (7,239 and 106,842 characters).
- [x] Report batches 34-35 as 2 candidates, 2 verified, 0 pending; write the long text to a UTF-8 sidecar and verify the 38-record nine-column workbook against SQLite and evidence.

Additional CSIS formats, other think tanks, periods, source families, and research literature remain to be searched in later batches.

## Task 36: Verify National Security Archive records and classify inaccessible RAND pages

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/nsarchive_briefing_article.html`, `tests/fixtures/nsarchive_legacy_briefing_book.html`, `tests/fixtures/nsarchive_legacy_table_book.html`, `tests/fixtures/nsarchive_legacy_edited_book.html`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover six National Security Archive original pages and two RAND report pages; use search only for discovery.
- [x] Retrieve and verify the 2019 archive exhibit (2019-06-04; 2,294 characters), 1999 briefing book (1999-06-01; 60,757 characters), 2001 Tiananmen Papers briefing book (2001-06-04; 27,550 characters), 2003 Nixon briefing book (2003-12-11; 25,928 characters), and 2004 Nixon diplomacy briefing book (2004-12-21; 14,819 characters) directly from their original pages.
- [x] Add modern and three legacy layout variants; decode declared ISO-8859-1/served Windows-1252 text without replacement characters, preserving sections, nested quotations, document entries, and standalone footnotes.
- [x] Keep the 2002 Beijing-Washington back-channel page pending because its original page does not display an exact publication date; do not substitute the date found on an archive index page.
- [x] Record both RAND pages as HTTP 403 restricted candidates without trying alternate access paths.
- [x] Report batches 36-43 as 5 verified, 2 restricted, and 1 pending; export the cumulative nine-column workbook with 43 verified records among 68 candidates.

Further National Security Archive layouts, remaining periods, source families, and research literature remain to be searched.

## Task 37: Add an official House hearing page and preserve access/date limits

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/house_foreign_affairs_hearing.html`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover a House Foreign Affairs Committee hearing page and a Congress.gov text lead; search results are discovery only.
- [x] Confirm Congress.gov's text path is disallowed by robots.txt and leave that candidate unprocessed without requesting the target page through another tool.
- [x] Add a source-specific adapter for the committee's observed hearing-page layout; use its `article:published_time` metadata and ignore the distinct hearing-event date.
- [x] Verify the original committee page (2018-03-15; 1,653 characters) and preserve its source HTML.
- [x] Retrieve the committee-linked official 60-page transcript PDF, preserve the original bytes, and keep it pending because no exact publication date is displayed.
- [x] Export and verify the cumulative nine-column workbook with 44 verified records among 71 candidates; report 13 pending, 5 HTTP 403 restricted, and 9 unprocessed.

More hearing records, source families, and periods remain to be searched.

## Task 38: Verify a 2016 State Department archived speech

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/state_department_legacy_archive_speech.html`, `README.md`, `data/captures/state-china-growing-pains-2016.json`, `data/captures/state-sed-opening-china-2016.json`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover the official 2016 State Department speech page; search results remained discovery-only.
- [x] Request the original URL with Scrapy after robots.txt allowed it; retain the HTTP 200 Technical Difficulties response without treating it as source text.
- [x] Fetch Firecrawl raw HTML for the same source and final URL with HTTP 200 and scrape ID; preserve the complete capture and import it through the shared verification pipeline.
- [x] Add an observed-layout adapter and fixture; verify the Daniel R. Russel speech (2016-04-22; 18,451 characters) and John Kerry's S&ED opening remarks (2016-06-06; 47,793 characters).
- [x] Report batches 47-48 as 1 candidate, 1 verified each; confirm the longer speech is referenced by a relative UTF-8 sidecar and matches SQLite exactly.
- [x] Export and verify the cumulative nine-column workbook with 46 verified records among 73 candidates; retain 13 pending, 5 HTTP 403 restricted, and 9 unprocessed.

Further coverage is required across all four periods, media, social accounts, and Chinese and English research literature.

## Task 39: Expand VOA coverage across trade, COVID-19, and chip competition

**Files:** `data/candidates-voa-2018-2023.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search only to discover three VOA original-page leads spanning trade negotiations, COVID-19 information claims, and semiconductor restrictions.
- [x] Import all three as one 2017-2025 media batch and crawl their original pages directly with Scrapy after robots.txt allowed access.
- [x] Verify each page's H1, byline, publication timestamp, NewsArticle metadata, complete `#article-content > .wsw` body, and original HTML evidence; record body lengths 2,335, 2,365, and 6,643 characters.
- [x] Report batch 49 as 3 candidates, 3 verified, 0 pending; export and verify the cumulative nine-column workbook with 49 verified rows among 76 candidates.

Further VOA topics and other media/source families remain to be searched.

## Task 50: Add 1955 Taiwan Strait Crisis primary documents

**Files:** `data/candidates-taiwan-strait-1955.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets only to discover two individual FRUS records and one presidential archive statement candidate for the 1954-1955 crisis.
- [x] Import three candidates in the 1949-1972 government batch and crawl their original pages with Scrapy after robots.txt allowed the requests; all three returned HTTP 200.
- [x] Verify two FRUS bodies against their official page structure and preserve evidence; initially retain the Presidency Project statement page as pending until a source-specific adapter is added.
- [x] Add a Presidency Project adapter for the observed document layout; require visible and structured dates to agree and preserve only direct statement paragraphs.
- [x] Confirm the live page's nested layout from saved Scrapy HTML, re-crawl the original URL, and verify the 1958-09-04 statement with an unmarked author recorded as `未注明`.
- [x] Report batch 50 as 3 candidates, 3 verified, 0 pending, 0 restricted and 0 duplicate; update cumulative counts and export the nine-column workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 91: Add Obama-era White House archive adapter

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/obama_whitehouse_archive_article.html`, `data/candidates-obama-china-asia-policy-2013-2016.csv`, `data/captures/`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Register six Obama-era official archive pages located through Firecrawl discovery; keep discovery snippets out of the corpus.
- [x] Add a failing adapter test based on the original Drupal page structure; verify red, then implement the source-specific adapter and pass the test.
- [x] Capture all six exact source pages through Firecrawl raw HTML with matching source/final URLs, HTTP 200 and scrape IDs; Scrapy responses were not used as article bodies.
- [x] Verify visible publication date, page title, issuing office and complete body; use `未注明` for author where no person is identified on the page.
- [x] Add body-derived summaries and keywords and export six verified records; cumulative workbook has 148 unique records and 34 UTF-8 sidecars.
- [x] Verify focused spider tests (52 passed), full suite (100 passed), Scrapy check, and cumulative workbook field/body audit.

## Task 92: Check Clinton-era State Department archive pages

**Files:** `data/candidates-state-clinton-china-asia-2011-2012.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Register eight official State Department speech/interview pages located through Firecrawl discovery.
- [x] Request candidate pages through Scrapy with robots.txt enabled; robots.txt returned HTTP 200, while all eight targets returned the same “Technical Difficulties” page.
- [x] Retrieve each exact original page through Firecrawl raw HTML with matching source/final URL, HTTP 200 and scrape ID; import and verify all eight through the existing adapter.
- [x] Rebuild body text from top-level transcript blocks to exclude the embedded player tree; add body-derived summaries and keywords and export the verified records.
- [x] Audit the cumulative workbook (148 unique records, 34 UTF-8 sidecars) and record coverage limitations.

## Tasks 93-95: Check House Foreign Affairs Taiwan hearing records

**Files:** `data/candidates-house-foreign-affairs-hearings-taiwan-2024.csv`, `data/candidates-govinfo-house-taiwan-hearing-2024.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Verify the House Foreign Affairs Committee page's original publication timestamp (2024-04-24), distinct from its 2025-06-02 modified timestamp; crawl the original page after robots.txt allowed access (both HTTP 200).
- [x] Store the committee hearing page as its own verified 199-character activity listing, not as a transcript; derive a short summary from that page body.
- [x] Fetch the official GovInfo transcript PDF and HTML URLs with Scrapy after robots.txt allowed access (both HTTP 200); inspect the PDF's 42 pages and preserve both transcript candidates as pending because publication date/body completeness are not verified by the current adapter.
- [x] Report batches 93-95 as 3 candidates, 1 verified, 2 pending, 0 restricted/duplicate/unprocessed; cumulative totals are 206 candidates, 152 verified, 31 pending, 10 restricted, 13 unprocessed, and 149 unique workbook rows.

## Tasks 96-98: Expand GovInfo China-related hearing candidates

**Files:** `data/candidates-govinfo-china-discourse-hearings-2011-2024.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Fetch the GovInfo details page for the 2024 Taiwan Relations Act hearing after robots.txt allowed access; preserve its distinction between the held date and a publication date.
- [x] Locate five original GovInfo hearing HTML pages about China-related public diplomacy, Taiwan relations, the Belt and Road Initiative, and CCP political warfare; use search only as URL discovery.
- [x] Crawl all five source HTML pages through Scrapy after robots.txt allowed access; robots.txt and all five target pages returned HTTP 200, with original HTML evidence saved.
- [x] Keep the five transcript candidates pending because the current adapter does not verify body completeness and exact matching metadata; do not use search excerpts or hearing dates as publication dates.
- [x] Report batches 96-98 as 6 candidates, 0 verified, 6 pending, 0 restricted/duplicate/unprocessed; cumulative totals are 212 candidates, 152 verified, 37 pending, 10 restricted, 13 unprocessed, and 149 unique workbook rows.

## Task 99: Expand open-access U.S.-China discourse literature and repair mixed-key deduplication

**Files:** `data/candidates-pmc-us-china-discourse-literature-2017-2023.csv`, `src/research_crawler/store.py`, `tests/test_store.py`, `README.md`, `data/research.sqlite3`, `data/research-before-pmc-dedupe.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Register seven PMC candidates from 2017-2023; crawl their original publication pages through Scrapy after robots.txt allowed access (robots.txt and all seven pages returned HTTP 200).
- [x] Verify and store four new full texts; preserve two previously stored full texts as duplicate discoveries with repeat count +1 each; retain one candidate as pending because the paper studies Japanese online news rather than U.S. discourse.
- [x] Add a failing store test for a repeated original URL when the later record supplies a platform ID; verify the failure, implement identity resolution, then verify the focused and complete test suites.
- [x] Merge two duplicate PMC material rows without deleting candidate or evidence records; retain a SQLite backup before the data repair.
- [x] Add a failing adapter test for PMC pages with separate “Significance” and “Abstract” sections; select the explicitly labeled abstract and verify the PNAS full text.
- [x] Report batch 99 as 7 candidates, 6 verified, 1 pending, 2 duplicate discoveries, 0 restricted/unprocessed; cumulative totals are 219 candidates, 158 verified, 38 pending, 10 restricted, 13 unprocessed, and 153 unique workbook rows.
- [x] Export and audit 153 unique workbook rows, exactly nine columns, every field/body against SQLite, and all 37 referenced UTF-8 long-text sidecars; full suite 102 passed, `scrapy check` OK, and `git diff --check` passes.

## Task 100: Check New York Times access for 1989 Tiananmen coverage

**Files:** `data/candidates-nyt-china-discourse-1989.csv`, `README.md`, `data/research.sqlite3`, `data/materials.xlsx`

- [x] Use Firecrawl search excerpts only to discover four new original 1989 New York Times article URLs; exclude one URL already present in the candidate store.
- [x] Import the four unique candidates in the 1972-1991 media batch and run Scrapy with `ROBOTSTXT_OBEY=True`.
- [x] Record all four as unprocessed because robots.txt forbids access; verify Scrapy issued no target-page requests and did not store search excerpts as article text.
- [x] Report 4 candidates, 0 verified/pending/restricted/duplicate, 4 unprocessed; cumulative totals are 223 candidates, 158 verified, 38 pending, 10 restricted, 17 unprocessed, and 153 unique workbook rows.

## Task 101: Reject incomplete Brookings working-paper page text

**Files:** `data/candidates-brookings-asian-regionalism-cross-strait-2008.csv`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/brookings_excerpt_article.html`, `README.md`, `data/research.sqlite3`, `data/research-before-brookings-excerpt-correction.sqlite3`, `data/materials.xlsx`

- [x] Find and crawl the original Brookings page for Fu-Kuo Liu's 2008 working paper after robots.txt allowed access; both robots.txt and page returned HTTP 200.
- [x] Inspect the raw source response and identify that only an Introduction excerpt is rendered with “See More” and a separate PDF download; reject the excerpt as unverified full text.
- [x] Add a failing regression test and update the Brookings completeness gate; confirm the existing complete-article adapter fixture still passes.
- [x] Re-crawl the original page and retain it as pending; remove the erroneous excerpt material from SQLite and Excel, correct its prior evidence verification flags, preserve raw evidence, and back up SQLite before the repair.
- [x] Report batch 101 as 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed; cumulative totals are 224 candidates, 158 verified, 39 pending, 10 restricted, 17 unprocessed, and 153 unique workbook rows.

## Task 102: Verify the linked Brookings full-text PDF with composite evidence

**Files:** `data/candidates-brookings-asian-regionalism-pdf-2008.csv`, `src/research_crawler/items.py`, `src/research_crawler/discovery.py`, `src/research_crawler/spiders/government.py`, `src/research_crawler/pipelines.py`, `src/research_crawler/store.py`, `src/research_crawler/validation.py`, `tests/test_discovery.py`, `tests/test_spider.py`, `tests/test_pipeline.py`, `tests/test_store.py`, `tests/test_validation.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Register the exact public PDF linked by the original Brookings publication page as a distinct 1992-2016 think-tank candidate.
- [x] Crawl the landing page and PDF through Scrapy with robots.txt enabled; robots.txt and both source pages returned HTTP 200, and preserve the original 32-page PDF bytes.
- [x] Inspect the PDF cover, metadata, and each page's text layer; confirm full text is available but the PDF itself only prints month/year while exact publication date is on the associated landing page.
- [x] Initially keep the PDF candidate pending because the existing evidence model cannot jointly verify the PDF body and exact date on its linked landing page; do not use PDF creation metadata as publication date.
- [x] Add an optional candidate `metadata_url`, fetch it before the body URL, persist both raw responses as separate evidence, and permit field provenance only from successful, allowed, metadata-verified evidence attached to the same candidate.
- [x] Add a Brookings PDF adapter that checks every page's text layer and matches the landing-page title, author and publisher against the PDF cover; use the landing page's exact publication date.
- [x] Add failing tests for candidate import, metadata provenance validation, persistence, pipeline evidence handling, request order and PDF/landing-page cross-checks; verify the tests fail before implementation and pass afterward.
- [x] Reprocess the candidate and verify the 117,142-character complete PDF; report batch 102 as 1 verified, 0 pending/restricted/duplicate/unprocessed; cumulative totals are 225 candidates, 159 verified, 39 pending, 10 restricted, 17 unprocessed, and 154 unique workbook rows.
- [x] Export and audit all 154 rows and nine columns, every field/body against SQLite, and the referenced UTF-8 sidecars; run the full test suite and `scrapy check`.

## Task 103: Verify CSIS report PDFs and congressional testimony

**Files:** `data/candidates-csis-china-discourse-2024-2025.csv`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search only to discover four CSIS source pages; fetch the source pages and linked PDFs with Scrapy while retaining its robots.txt behavior.
- [x] Add regression tests for CSIS report PDF/landing-page provenance and congressional testimony bylines; confirm the tests fail before parser support and pass afterward.
- [x] Verify two CSIS PDFs against their exact landing pages, including publication dates, visible authors, title, linked PDF URL, publisher identification, and a text layer on every page; preserve both original PDF files.
- [x] Extend the existing CSIS adapter to recognize the observed report layout and testimony byline without accepting the landing-page synopsis as full text.
- [x] Report batch 103 as 6 candidates, 4 verified, 2 pending, 0 restricted/duplicate/unprocessed; cumulative totals are 231 candidates, 163 verified, 41 pending, 10 restricted, 17 unprocessed, and 158 unique workbook rows.
- [x] Export and audit all nine columns, 158 rows, every field/body against SQLite, and all 40 referenced UTF-8 sidecars.
- [x] Run the full test suite and `scrapy check` after the CSIS parser changes: 112 tests passed and Scrapy reported 0 contract failures.

## Task 104: Check publisher access for historical US-China media studies

**Files:** `data/candidates-open-literature-us-china-media-1992-2016.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Use search only to identify three publisher-hosted records directly relevant to US media images/discourse about China, including a study covering 2000-2002.
- [x] Fetch candidates through Scrapy with robots.txt enabled; all three publisher pages returned HTTP 403 and were recorded restricted.
- [x] Do not use search excerpts, authenticated pages, or mirrors as article text; leave the nine-column full-text workbook unchanged.
- [x] Report batch 104 as 3 candidates, 0 verified/pending/duplicate/unprocessed, 3 restricted; cumulative totals are 234 candidates, 163 verified, 41 pending, 13 restricted, 17 unprocessed, and 158 unique workbook rows.

## Task 105: Verify Clinton White House China and WTO public records

**Files:** `data/candidates-clinton-china-public-communications-1997-1999.csv`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/clintonwhitehouse4_*.html`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Discover six new 1997-1999 Clinton White House source pages; import them as candidates without using search descriptions as source text.
- [x] Fetch all pages through Scrapy with robots.txt enabled; robots.txt and all six target pages returned HTTP 200.
- [x] Add regression coverage using the saved original HTML for legacy table press releases with different title and weekday/date layouts; verify the test fails before the adapter change.
- [x] Parse the unique Press Secretary release area, exact release date, title, and full source body; reject template navigation and require a visible footer boundary.
- [x] Re-crawl and verify all six materials, taking 1999-11-08 from the release header even though the URL contains 19991109.
- [x] Report batch 105 as 6 verified, 0 pending/restricted/duplicate/unprocessed; cumulative totals are 240 candidate records plus 7 duplicate discoveries (247 URL discoveries), 169 verified, 41 pending, 13 restricted, 17 unprocessed, and 164 unique workbook rows.

## Task 106: Check archived State Department remarks

**Files:** `data/candidates-state-archived-china-remarks-2014-2016.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Register two 2014 and 2016 State Department archive pages as discovery candidates; do not copy search excerpts into formal material fields.
- [x] Fetch both original URLs through Scrapy with robots.txt enabled; robots.txt and target URLs returned HTTP 200.
- [x] Inspect saved response evidence and confirm both bodies are the same “Technical Difficulties” page, without article metadata or source text; leave both pending and keep the workbook unchanged.
- [x] Report batch 106 as 2 candidates, 0 verified, 2 pending, 0 restricted/duplicate/unprocessed; cumulative totals are 242 candidate records plus 7 duplicate discoveries (249 URL discoveries), 169 verified, 43 pending, 13 restricted, 17 unprocessed, and 164 unique workbook rows.

## Task 107: Reverify a previously pending PMC article

**Files:** `data/research.sqlite3`, `data/evidence/`, `data/materials-refreshed.xlsx`, `data/materials-refreshed_bodies/`, `README.md`

- [x] Re-run the original PMC URL through Scrapy with robots.txt enabled; both robots.txt and page returned HTTP 200.
- [x] Verify the exact publication date (2022-08-28), authors, journal, title, and complete 45,287-character body; update the existing batch 99 candidate to verified.
- [x] Export the now-165 unique verified materials; the existing `materials.xlsx` was locked, so preserve it and write a separate refreshed workbook.
- [x] Audit all nine columns, unique links, fields, exact bodies, and 45 UTF-8 long-text sidecars against SQLite. Batch 99 is 7 verified, 0 pending, 2 duplicate; cumulative status is 170 verified, 42 pending, 13 restricted, 17 unprocessed.
- [x] Export and compare all nine workbook fields, full bodies and 44 referenced UTF-8 sidecars; re-parse all six saved HTML responses and match fields/body exactly against SQLite; 113 tests passed and `scrapy check` returned OK.

## Task 108: Add a Reagan China trade memorandum

**Files:** `data/candidates-reagan-china-trade-memorandum-1987.csv`, `src/research_crawler/validation.py`, `src/research_crawler/pipelines.py`, `src/research_crawler/store.py`, `tests/test_validation.py`, `tests/test_pipeline.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search only to locate the original American Presidency Project page; verify it was not previously a candidate.
- [x] Crawl the original page through Scrapy with robots.txt enabled; robots.txt and the target page returned HTTP 200.
- [x] Verify the exact date 1987-08-05, title, source, author status and complete 1,774-character body; add the material to the 1972-1991 government batch.
- [x] Add period-bound validation and regression tests so a material dated outside its candidate period remains pending; clean up one accidental out-of-period test import without touching the valid Reagan record.
- [x] Report batch 108 as 1 verified, 0 pending/restricted/duplicate/unprocessed, and cumulative status as 243 candidate records plus 7 duplicate discoveries (250 URL discoveries), 171 verified, 42 pending, 13 restricted, 17 unprocessed.

## Task 109: Add 1984 and 1988 party platforms

**Files:** `data/candidates-party-platforms-china-1984-1988.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search only to locate two previously unrecorded American Presidency Project platform pages with China policy language.
- [x] Crawl both original pages through Scrapy with robots.txt enabled; robots.txt and both target pages returned HTTP 200.
- [x] Verify exact publication dates 1984-07-16 and 1988-08-16, titles and complete bodies of 237,110 and 232,555 characters.
- [x] Report batch 109 as 2 verified, 0 pending/restricted/duplicate/unprocessed; cumulative totals are 245 candidate records plus 7 duplicate discoveries (252 URL discoveries), 173 verified, 42 pending, 13 restricted, 17 unprocessed, and 168 unique workbook rows.

## Task 110: Correctly classify two 1999 presidential debate pages

**Files:** `data/candidates-1988-presidential-debates-china.csv`, `data/candidates-presidential-debates-china-1999.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Fetch two search-discovered American Presidency Project debate pages with robots.txt enabled; both returned HTTP 200 and complete source bodies.
- [x] Apply exact publication-date verification and leave the candidates pending in the 1972-1991 batch when the pages showed 1999 dates.
- [x] Re-register the same original URLs in the 1992-2016 period for a separate verification batch; preserve the prior discovery as a duplicate count.
- [x] Report batch 110 as 2 pending and batch 111 as 2 verified; cumulative totals are 249 candidate records plus 9 duplicate discoveries (258 URL discoveries), 175 verified, 44 pending, 13 restricted, 17 unprocessed, and 170 unique workbook rows.

## Task 112: Add the 1992 Republican Party platform

**Files:** `data/candidates-republican-platform-china-1992.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search only to locate the previously unrecorded American Presidency Project platform page.
- [x] Crawl the original page through Scrapy with robots.txt enabled; robots.txt and the target page returned HTTP 200.
- [x] Verify publication date 1992-08-17, title, source and complete 183,777-character body.
- [x] Report batch 112 as 1 verified, 0 pending/restricted/duplicate/unprocessed; cumulative totals are 250 candidate records plus 9 duplicate discoveries (259 URL discoveries), 176 verified, 44 pending, 13 restricted, 17 unprocessed, and 171 unique workbook rows.

## Task 113: Check Trump White House archived China communications

**Files:** `data/candidates-trump-archive-china-2018-2019.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search only to locate two previously unrecorded Trump White House archive pages.
- [x] Crawl both original pages through Scrapy with robots.txt enabled; robots.txt and both target pages returned HTTP 200.
- [x] Verify the Pence lecture page's exact date (2019-10-24), title and complete 26,628-character body.
- [x] Keep the ideology page pending because its response did not prove complete article metadata and body; do not use external citations or search excerpts as source text.
- [x] Report batch 113 as 1 verified and 1 pending; cumulative totals are 252 candidate records plus 9 duplicate discoveries (261 URL discoveries), 177 verified, 45 pending, 13 restricted, 17 unprocessed, and 172 unique workbook rows.

## Task 114: Collect 2023 State Department China communications

**Files:** `data/candidates-state-department-china-remarks-2023.csv`, `data/evidence/firecrawl-captures/`, `src/research_crawler/firecrawl_import.py`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search only to locate three official State Department pages; Scrapy obeyed robots.txt and stored the common “Technical Difficulties” target response as unverified evidence.
- [x] Retrieve and save exact original-page raw HTML for all three through Firecrawl, preserving source URL, final URL, status code and scrape ID; use the existing source adapter and verification pipeline.
- [x] Verify the Freedom House remarks (2023-05-09, 21,941 characters) and Han Zheng meeting remarks (2023-09-18, 2,694 characters); leave the June 14 press briefing pending because complete body/metadata checks did not pass.
- [x] Report batch 114 as 2 verified and 1 pending; cumulative totals are 255 candidate records plus 9 duplicate discoveries (264 URL discoveries), 179 verified, 46 pending, 13 restricted, 17 unprocessed, and 174 unique workbook rows.
- [x] Audit the nine-column workbook, unique links, exact fields and bodies, period/date consistency and all 50 UTF-8 body sidecars against SQLite.

## Task 115: Add the 2023 Global Engagement Center report page

**Files:** `data/evidence/firecrawl-captures/state-gec-information-environment-2023.json`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/test_firecrawl_import.py`, `src/research_crawler/firecrawl_import.py`, `src/research_crawler/cli.py`, `data/candidates-state-gec-report-pdf-2023.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover the official State Department Global Engagement Center report landing page; confirm its exact URL is new to the database.
- [x] Request the page through Scrapy with robots.txt enabled; retain its HTTP 200 “Technical Difficulties” response as unverified evidence.
- [x] Save Firecrawl raw HTML with matching source/final URLs, HTTP 200 and scrape ID; verify the landing page's visible title, 2023-09-28 publication date, Global Engagement Center byline and complete 6,574-character page body through the existing adapter and pipeline.
- [x] Add a State Department paired-PDF adapter and CLI path. It requires matching source-page title/date/byline, an exact PDF link, a complete page-text extraction, and title/agency matches on the PDF first page; tests cover both acceptance and a mismatched link rejection.
- [x] Report batch 115 as 1 verified. Cumulative totals after the next PDF batch are 257 candidates plus 9 duplicate discoveries, 180 verified, 47 pending, 13 restricted, 17 unprocessed, and 175 workbook rows.

## Task 116: Attempt the linked official GEC report PDF

**Files:** `data/candidates-state-gec-report-pdf-2023.csv`, `data/research.sqlite3`, `data/evidence/`, `README.md`, `data/materials.xlsx`

- [x] Register the direct English PDF URL and its official report landing page as metadata URL; confirm Scrapy obeyed robots.txt.
- [x] Verify the target returned HTTP 200 but the saved body was the same technical-difficulties HTML, not a PDF; do not treat the status code as successful content retrieval.
- [x] Check Firecrawl's result metadata for exact URL, HTTP 200, `application/pdf`, title and 64 physical pages; because it exposed a parsed HTML extraction rather than original PDF bytes, keep the full report pending and out of Excel.
- [x] Report batch 116 as 1 pending. Cumulative totals: 257 candidate records plus 9 duplicate discoveries (266 URL discoveries), 180 verified, 47 pending, 13 restricted, 17 unprocessed, and 175 unique workbook rows.
- [ ] Continue seeking a legal direct-PDF retrieval path; preserve pending state unless the exact full source body can be verified.

## Task 117: Add 2024 State Department China-visit communications

**Files:** `data/candidates-state-china-visit-communications-2024.csv`, `data/evidence/firecrawl-captures/`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Confirm the three selected official source URLs were not previously registered; import them as 2017-2025 government candidates.
- [x] Crawl all three with Scrapy and robots.txt enabled; all target responses returned HTTP 200 but contained the same unverified technical-difficulties page.
- [x] Save exact raw HTML captures from each matching original State Department URL, retaining source/final URLs, HTTP 200 and scrape IDs; process each through the existing adapter and verification pipeline.
- [x] Verify the April 24, 2024 Department Press Briefing (Vedant Patel; 42,731 characters) and October 30, 2024 modernization remarks (Office of the Spokesperson; 7,489 characters).
- [x] Keep the China-trip page pending because its title's travel dates are not a publication date and the source page has no exact publication date; do not substitute `modifiedTime`.
- [x] Report batch 117 as 2 verified and 1 pending; cumulative totals are 260 candidates plus 9 duplicate discoveries (269 URL discoveries), 182 verified, 48 pending, 13 restricted, 17 unprocessed, and 177 unique workbook rows.
- [x] Export and audit the nine-column workbook against SQLite, including all 51 UTF-8 long-body sidecars; confirm the pending travel page is excluded.
- [ ] Continue expanding coverage of media, official social content, and Chinese/English research literature.

## Task 118: Check an AP News 2024 export-controls article

**Files:** `data/candidates-ap-export-controls-2024.csv`, `data/research.sqlite3`, `README.md`, `data/materials.xlsx`

- [x] Use Firecrawl search only to locate the AP News original URL; verify the URL was new to the database.
- [x] Request the original article through Scrapy after robots.txt allowed the request; record the observed HTTP 403 as restricted.
- [x] Do not retry through Firecrawl or another retrieval path after the source denied access; do not use search excerpts as article body.
- [x] Report batch 118 as 1 restricted. Cumulative totals: 261 candidates plus 9 duplicate discoveries (270 URL discoveries), 182 verified, 48 pending, 14 restricted, 17 unprocessed, and 177 unique workbook rows.

## Task 119: Search 2022 U.S. media-framing research

**Files:** `data/candidates-research-media-framing-anti-china-2022.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add the ScienceDirect original article page as a research-literature candidate.
- [x] Request the original page through Scrapy; record its HTTP 403 response as restricted without substituting search text or another access route.
- [x] Report batch 119 as 1 restricted candidate and 0 verified full texts; preserve the cumulative workbook unchanged.

## Task 120: Check a PMC lead for 2023 media-image research

**Files:** `data/candidates-pmc-nyt-china-image-2023-archive.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add the original PMC page and inspect its source-visible citation metadata and full-text page.
- [x] Confirm it is a different 2026 article, outside the requested period, and keep it pending rather than treating a citation as a full-text match.
- [x] Report batch 120 as 1 pending candidate and 0 verified full texts.

## Task 121: Recheck the 2023 Nature research candidate

**Files:** `data/evidence/firecrawl-captures/nature-2023-nyt-image.json`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Capture raw HTML from the exact original Nature URL and verify matching source/final URLs, HTTP 200, scrape ID, date, authors and DOI metadata.
- [x] Run the capture through the existing strict source adapter; retain the candidate as pending because complete body correspondence was not verified.
- [x] Export and audit the nine-column workbook without adding unverified text.

## Task 122: Add open PMC research on U.S.-China opinion and discourse

**Files:** `data/candidates-pmc-us-china-public-opinion-2020-2023.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover five previously unrecorded PMC source pages and crawl them with Scrapy after robots.txt allowed access; all returned HTTP 200.
- [x] Verify full source text, date and metadata for three directly relevant studies and include them in the workbook.
- [x] Keep two full-text studies focused on Canadian and broader Asian public perceptions pending and exclude them from the formal corpus as not directly U.S.-focused; preserve their source evidence.
- [x] Report batch 121 as 5 candidates, 3 verified, 2 pending, and 0 restricted/duplicate/unprocessed; export and audit the nine-column workbook and UTF-8 sidecars.

## Task 123: Verify GovInfo hearing transcripts against package metadata

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/govinfo_hearing.html`, `tests/fixtures/govinfo_details.html`, `data/candidates-govinfo-china-discourse-hearings-2011-2024.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add fixture tests for transcript/metadata matching, missing-date rejection, completion boundaries, and preservation of both responses through the spider callback.
- [x] Add a GovInfo adapter and paired-detail request path; derive bibliographic fields only from the matching package's official detail page and body text only from the single transcript `<pre>`.
- [x] Re-fetch five source pages and five detail pages through Scrapy after robots.txt allowed access; all responses returned HTTP 200.
- [x] Verify four complete 2017-2025 hearings and preserve the 2012 hearing as pending because its final source marker does not establish complete text.
- [x] Report batch 98 as 4 verified and batch 97 as 1 pending; cumulative totals are 268 candidates plus 9 duplicate discoveries, 189 verified, 47 pending, 15 restricted, 17 unprocessed, and 184 unique workbook rows.
- [x] Export and audit the nine-column workbook and all long-body sidecars.

## Task 124: Add Truman-era China public statements

**Files:** `data/candidates-truman-china-public-statements-1949.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover three original 1949 presidential document pages and confirm the URLs were not previously registered.
- [x] Crawl through Scrapy with robots.txt enabled; all three target source pages returned HTTP 200. The two site robots.txt responses were HTTP 200 and HTTP 404; neither target was blocked.
- [x] Verify the 1949-10-27 and 1950-01-05 presidential news conferences from the exact source pages; exclude the 1945-12-15 statement from the corpus.
- [x] Report batch 122 as 2 verified and 1 pending; cumulative totals are 271 candidates plus 9 duplicate discoveries, 191 verified, 48 pending, 15 restricted, 17 unprocessed, and 186 unique workbook rows.
- [x] Recheck FRUS d173 through the original URL; both Scrapy and Firecrawl returned only the 200-status JavaScript shell, so retain pending and do not infer document text from an older note.
- [x] Export and audit the nine-column workbook.

## Task 125: Check a Peking University journal article for 1990s U.S.-China media research

**Files:** `data/candidates-chinese-us-media-china-image-1995.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Locate the original Peking University journal record and its publicly accessible six-page PDF for 范士明, “美国媒体敌视中国的原因”.
- [x] Verify author, title, journal, 1997 issue 3, pages 48–53 and source-provided abstract from the publisher record; confirm that neither publisher record nor PDF shows a precise YYYY-MM-DD publication date.
- [x] Inspect all scanned PDF pages and test PDF text extraction; retain the candidate as pending because the OCR output has gaps and cannot support a complete verbatim body. Do not add the record to Excel.
- [x] Report batch 123 as 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed; update cumulative counts.
- [x] Keep the nine-column workbook unchanged because the record failed exact-date and complete-body verification.

## Task 126: Check an open-access route for a U.S. print media study

**Files:** `data/candidates-us-print-media-china-threat-1992-2006.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Locate the publisher's original article page for Yang and Liu, “The 'China Threat' through the Lens of US Print Media: 1992–2006”, with a search result indicating online publication on 2012-04-05.
- [x] Import and request the original URL through Scrapy with robots.txt enabled; robots.txt returned HTTP 200 and the article page returned HTTP 403.
- [x] Record the candidate as restricted; do not use alternate access methods or include search-result excerpts as article text.
- [x] Report batch 124 as 1 candidate, 0 verified, 0 pending, 1 restricted, 0 duplicate/unprocessed; update cumulative counts.
- [x] Leave the formal workbook unchanged because the original page denied access.

## Task 127: Add 1994 Clinton administration China trade policy communications

**Files:** `data/candidates-clinton-china-public-communications-1994.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add four previously unregistered American Presidency Project records on the 1994 China MFN debate: a presidential statement, presidential memorandum, administration policy statement, and presidential news conference.
- [x] Crawl the exact original URLs through Scrapy with robots.txt enabled; all four source pages returned HTTP 200.
- [x] Verify the displayed publication dates, source/title/author fields and complete primary-document text; record unmarked personal authors as `未注明`.
- [x] Report batch 125 as 4 candidates, 4 verified, 0 pending/restricted/duplicate/unprocessed; export and compare all nine workbook columns and long-body files against SQLite.

## Task 128: Add 1996-1999 Clinton administration China trade status records

**Files:** `data/candidates-clinton-china-mfn-1996-1998.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add five previously unregistered American Presidency Project records concerning annual China MFN/NTR status in 1996, 1998 and 1999.
- [x] Fetch the exact source URLs through Scrapy with robots.txt enabled; all five article pages returned HTTP 200.
- [x] Verify each source page's displayed date, title, source/author labels and complete article text.
- [x] Report batch 126 as 5 candidates, 5 verified, 0 pending/restricted/duplicate/unprocessed; export and compare all workbook fields and sidecar bodies to SQLite.

## Task 129: Add Clinton administration WTO communications from 1999

**Files:** `data/candidates-clinton-china-wto-1999.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add four previously unregistered official archive pages concerning China-WTO accession and 1999 trade negotiations.
- [x] Fetch the exact pages through Scrapy with robots.txt enabled; each source page returned HTTP 200.
- [x] Verify the page-displayed publication date, title/source metadata and complete body for each document.
- [x] Report batch 127 as 4 candidates, 4 verified, 0 pending/restricted/duplicate/unprocessed; export and compare all nine columns and long-body files against SQLite.

## Task 130: Add 2000 Clinton China PNTR and WTO records

**Files:** `data/candidates-clinton-china-pntr-2000.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add five previously unregistered original archive pages on PNTR and China's WTO accession.
- [x] Request all five pages through Scrapy with robots.txt enabled; three returned HTTP 200 and passed metadata/body verification, while two returned HTTP 404.
- [x] Keep only the three verified full texts in the formal workbook; leave the 404 records pending without substituting search excerpts.
- [x] Report batch 128 as 5 candidates, 3 verified, 2 pending, 0 restricted/duplicate/unprocessed; export and audit the nine-column workbook and sidecars against SQLite.

## Task 131: Parse early Obama White House China communications

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/obama_whitehouse_2009_hu_london.html`, `tests/fixtures/obama_whitehouse_2009_hu_new_york.html`, `tests/fixtures/obama_whitehouse_2010_wen.html`, `data/candidates-obama-china-public-communications-2009-2010.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Add five previously unregistered 2009-2010 White House source pages and fetch them with Scrapy after robots.txt checks; all target responses returned HTTP 200.
- [x] Add failing regression coverage from saved source HTML for 2009 legacy-content and 2010 block-div layouts; extend the adapter to extract those blocks and require an explicit terminal `END` marker.
- [x] Reprocess the three initially pending saved responses through the existing verification pipeline without adding duplicate candidate discoveries; all five records now verify.
- [x] Report batch 129 as 5 candidates, 5 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook and long-body sidecars against SQLite.
- [x] Run the full test suite (122 passed) and Scrapy check.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 132: Verify 2011 Obama and Biden public communications

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/obama_whitehouse_2011_*.html`, `data/candidates-obama-china-public-communications-2011.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Fetch five new source pages through robots-aware Scrapy; preserve original HTTP responses.
- [x] Demonstrate a failing regression before supporting the Office of the Vice President label and split END/time blocks; retain negative tests with END removed.
- [x] Reprocess saved source responses within their existing batch, without counting retries as discoveries; four transcripts verify and one video page stays pending.
- [x] Add body-grounded derived abstracts and keywords, preserving original body text.
- [x] Export and audit 211 unique records in exactly nine columns, including 60 complete UTF-8 sidecar bodies.
- [x] Verify all four batch records against saved source responses, run 123 passing tests and Scrapy check, and package the workbook, required sidecars, and batch report in `data/materials-delivery.zip`.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 133: Review PMC scope and remove platform modules

- [x] Discover and fetch two new PMC papers in batch 131, inspect their own research corpora, and exclude both from the formal workbook as insufficiently direct to the dissertation topic.
- [x] Add a failing regression for nested keywords in abstracts and generated associated-data modules; fix both extraction paths while retaining author data statements.
- [x] Reparse 17 existing PMC records from their saved source HTML; seven body tails and thirteen abstracts were corrected without changing bibliographic metadata or counting reprocessing as duplicate discoveries.
- [x] Preserve database backups and an explicit review/change manifest under `data/reviews/pmc-cleanup-2026-11-06/`.

## Task 134: Add directly relevant narrative research and enforce FRUS publication dates

- [x] Fetch three new PMC papers on US-China nationalism, narrative competition and Trump COVID rhetoric in batch 132; verify original source abstracts, authors, dates, titles and complete bodies.
- [x] Demonstrate failing FRUS regressions: creation datelines cannot establish exact publication dates. Stop promoting that layout without independent publication-date evidence.
- [x] Withdraw 40 existing FRUS materials from the formal workbook, set all 42 corresponding candidate discoveries pending, and preserve original evidence, snapshots and a pre-change SQLite backup.
- [x] Export and audit the corrected 174-record workbook with exactly nine columns and 55 referenced long-body files; verify all 20 current PMC records against saved source HTML and the delivery ZIP against its files. Full tests: 124 passed; Scrapy check: OK (0 contracts).

Further source coverage and publication-date review remain required; earlier batch totals are historical and superseded by the current README audit.

## Task 135: Record media access limits and support public PBS AP reports

- [x] Fetch two new AP URLs in batch 133: both HTTP 403; preserve restriction evidence, with zero full-text rows.
- [x] Resolve all previously unprocessed candidates' known robots exclusions or attempt original URLs; record restrictions without requesting blocked bodies.
- [x] Add a failing regression for robots exclusions misreported as unprocessed; classify only explicit robots denial as restricted, retaining ordinary network errors as retryable.
- [x] Add source-fixture regressions and a PBS-specific adapter: unique matching H1/metadata title; visible and structured publication dates must agree; side-rail authors; unique article body; exclude READ MORE recommendations and funding block; require the observed complete closing credit and funding boundary.
- [x] Verify three PBS/AP reports in batch 134, preserve each actual publisher URL as an independent record, export exactly nine columns, and audit all bodies/sidecars and the delivery ZIP: 177 unique rows, 55 referenced sidecars, 127 passing tests and Scrapy check OK (0 contracts).

## Task 136: Verify public official-account social records

- [x] Register batch 135 X post and batches 136/137 DVIDS videos with original IDs; record robots denial or HTTP 403 without bypassing restrictions.
- [x] Inspect three White House video pages in batch 138; retain pending because their unlabeled dates do not independently establish publication dates despite available transcripts.
- [x] Add failing store tests for X/Twitter alias IDs and legacy keys, then normalize only known aliases for identity comparison while preserving original URLs and platform isolation.
- [x] Implement a narrow Bluesky adapter for the two known domain-verified media accounts in batch 139. Fetch the documented unauthenticated getPosts endpoint as declared supporting evidence; require one matching URI, record key, DID, account handle and original page text. Body is exact record.text, publication is record.createdAt (not indexedAt), title is original page title, source is account institution. Exclude linked article previews and replies.
- [x] Add positive/negative fixture tests including truncated page text, mismatched record URI or timestamp, and missing public record; preserve both HTML and JSON; export and audit workbook, sidecars and source correspondence. 132 tests pass; Scrapy check OK (0 contracts).
- [x] Run the unmodified CLI CSV workflow in an independent live database with robots.txt enabled: both public API and original HTML are fetched automatically, both candidates verify, and body/date/title/author match production.
- [x] Deliver 179 unique nine-column records, 55 referenced UTF-8 bodies, batch/coverage reports and a provenance index covering every formal material; verify original evidence hashes and ZIP contents.

## Task 90: Add Bush-era China policy and Asia-Pacific primary sources

**Files:** `data/candidates-presidency-bush-china-policy-2001-2008.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search results only to identify six previously unrecorded 2001–2008 presidential archive pages.
- [x] Crawl the original American Presidency Project pages through Scrapy with robots.txt enabled; robots.txt and all six target pages returned HTTP 200.
- [x] Verify title, publication date, author status, and full body against saved source-page evidence.
- [x] Since no publisher abstracts or keywords were present, derive concise summaries prefixed with `据正文整理：` and keywords from each body.
- [x] Report batch 90 as 6 candidates, 6 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook (134 unique records and 30 sidecars).

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 89: Add Clinton-era China trade policy primary sources

**Files:** `data/candidates-presidency-china-policy-1993-2000.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl discovery results only to identify six previously unrecorded presidential archive pages from 1993 and 2000.
- [x] Crawl the original American Presidency Project pages through Scrapy with robots.txt enabled; robots.txt and all six target pages returned HTTP 200.
- [x] Verify exact source, page title, date, author status and full body from the saved original-page evidence.
- [x] Since no publisher abstracts or keywords were present, derive concise summaries prefixed with `据正文整理：` and keywords from each body.
- [x] Report batch 89 as 6 candidates, 6 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook (128 unique records and 28 sidecars).

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 88: Add open PMC research on U.S./English-language media and China discourse

**Files:** `data/candidates-research-pmc-us-china-media-2022-2023.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials_bodies/`

- [x] Use Firecrawl search results only to identify five previously unrecorded PMC-hosted open research articles published before 2025.
- [x] Crawl all five original PMC pages through Scrapy with robots.txt enabled; robots.txt and target pages returned HTTP 200.
- [x] Verify source, exact publication date, author, title, publisher abstract/keywords when present, and complete article body from saved source-page HTML.
- [x] Preserve publisher abstracts; derive keywords for the one record without a keyword field from its abstract.
- [x] Report batch 88 as 5 candidates, 5 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook and long-text sidecars (122 unique materials; 28 sidecars).

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 65-66: Verify State Department 2022 China policy remarks

**Files:** `data/candidates-state-blinken-china-approach-2022.csv`, `data/captures/firecrawl-state-blinken-approach-2022.json`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/state_department_remarks_translation_links.html`

- [x] Add the State Department's May 26, 2022 Blinken policy remarks as a 2017-2025 government candidate; direct Scrapy retrieval returned a technical-difficulties page and remained pending in batch 65.
- [x] Retrieve the exact original page through Firecrawl rawHtml; preserve the complete capture, matching source/final URL, HTTP 200 and scrape ID, then verify title, displayed publication date, author and complete source body.
- [x] Add a regression fixture after the real page exposed translation navigation and video player text inside `.entry-content`; exclude those template nodes from the extracted transcript and reimport the source into batch 66.
- [x] Report batch 66 as 1 candidate, 1 verified, 1 duplicate, 0 restricted/pending/unprocessed; export the nine-column workbook. The unique record contains 42,410 body characters and repeat count 1.
- [x] Audit cumulative counts: 109 candidates, 76 verified, 17 pending, 7 restricted, 9 unprocessed and 75 unique workbook records.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 67: Add Clinton White House PNTR signing remarks

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/clinton_whitehouse_pntr_remarks.html`

- [x] Discover the original Clinton White House Archives page for the October 10, 2000 China PNTR signing event; confirm the URL was not already in the database.
- [x] Fetch the exact public page through Scrapy with `ROBOTSTXT_OBEY=True`; the page and robots.txt both returned HTTP 200.
- [x] Add a focused adapter for this archive layout; verify the unique `<PRE>` transcript, exact title, “For Immediate Release” date, issuing office and end marker, and leave absent author as `未注明`.
- [x] Confirm the extracted body matches the saved original response exactly at 28,822 characters and excludes archive banner and footer; reject a transcript missing the publication date or end marker.
- [x] Report batch 67 as 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook.
- [x] Audit cumulative counts: 110 candidates, 77 verified, 17 pending, 7 restricted, 9 unprocessed and 76 unique workbook records.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 68: Add Clinton White House China WTO briefing page

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/clinton_whitehouse_wto_briefing.html`

- [x] Discover the original March 8, 2000 Clinton White House China WTO page and verify the URL was new to the corpus.
- [x] Request the exact page through Scrapy with robots compliance; both robots.txt and the page returned HTTP 200.
- [x] Extend the Clinton archive adapter for the observed 354px briefing column; require the issuing office, visible title, release-date table and footer boundary, while excluding navigation and footer text.
- [x] Detect a misdeclared Windows-1252 response and re-decode the original bytes when UTF-8 replacement characters occur; verify six source punctuation bytes are preserved without U+FFFD.
- [x] Verify the 2000-03-08 date, source title, unmarked author and complete 4,887-character body; reject missing release date/end marker cases as appropriate to each supported layout.
- [x] Report batch 68 as 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; update the cumulative workbook and audit counts.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 69: Add FRUS Carter-era China normalization records

**Files:** `data/candidates-frus-normalization-1977-1979.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use official FRUS search results only to identify three file-level records in *Foreign Relations, 1977-1980, Volume XIII: China*; exclude the volume-level timeline page.
- [x] Import the candidates into one 1972-1991 government batch and fetch all three original URLs with Scrapy and robots.txt enabled; the site and all target pages returned HTTP 200.
- [x] Verify the Jan 8, 1977 memorandum (25,600 characters), Feb 8, 1977 memorandum (16,614 characters) and Jan 11, 1979 telegram (21,390 characters) against the official FRUS page metadata and complete document region.
- [x] Preserve the already-known d191 URL as a duplicate discovery, incrementing that primary record's repeat count by one.
- [x] Report batch 69 as 3 candidates, 3 verified, 0 pending/restricted/unprocessed and 1 duplicate; export and audit cumulative records.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 70: Check Reagan Library China speech record

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the Reagan Library's individual 1984 Beijing speech page through Firecrawl; treat the result only as a source lead.
- [x] Fetch the original page through Scrapy with robots.txt enabled; both robots.txt and the page returned HTTP 200, and save its complete source HTML as evidence.
- [x] Inspect the visible date metadata and complete speech region; the page labels `04/27/1984` only as `Date`, the speech date, and exposes no independent publication date.
- [x] Keep the candidate pending under the no-event-date-substitution rule; do not add its text to the verified materials workbook.
- [x] Report batch 70 as 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed, and update cumulative counts.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 71: Add Clinton 1999 foreign policy speech

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/clinton_whitehouse_foreign_policy_remarks.html`

- [x] Discover the original Clinton White House page for the April 7, 1999 foreign policy speech; search results were discovery leads only.
- [x] Request the exact page with Scrapy and robots.txt enabled; both robots.txt and page returned HTTP 200.
- [x] Extend the Clinton archive adapter for the old press-release content column; require its immediate-release publication date, issuing office, main content column, title token correspondence and footer boundary.
- [x] Preserve only the visible speech title, excluding venue/location lines; exclude archive navigation and footer from the source body.
- [x] Verify publication date 1999-04-07 and the complete 26,556-character body; update the same candidate in batch 71 from pending to verified.
- [x] Report batch 71 as 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 72: Add Clinton 2000 China press briefing

**Files:** `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/clinton_whitehouse_press_briefing_wrapped_date.html`

- [x] Discover the original Clinton White House Archives September 14, 2000 press briefing page as a source lead.
- [x] Fetch the source through Scrapy with robots.txt enabled; both robots and page returned HTTP 200.
- [x] Extend release-date parsing to support a line break inside “For Immediate Release”; derive Joe Lockhart from the page title and retain the complete `<PRE>` transcript through its end-of-briefing marker.
- [x] Verify the displayed publication date 2000-09-14, title, byline, body and complete `END 2:00 P.M. EDT` marker; preserve the 27,121-character body.
- [x] Report batch 72 as 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 73: Add Reagan-era FRUS China policy records

**Files:** `data/candidates-frus-reagan-china-1982-1986.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use official FRUS search results to locate file-level China policy documents in the 1981-1988 volume I; do not treat the Reagan volume index or volumes still marked “Being Cleared” as acquired materials.
- [x] Fetch three original file pages with Scrapy and robots.txt enabled; the site and all target pages returned HTTP 200.
- [x] Verify the 1982-09-22 Wolfowitz memorandum (12,848 characters), 1985-05-28 Rodman memorandum (13,241 characters), and 1986-04-22 Solomon memorandum (7,058 characters).
- [x] Deduplicate the previously recorded 1982 URL, preserving one primary record and recording repeat count 1; add the 1985 and 1986 materials as unique rows.
- [x] Correct the batch label to cover the verified publication years 1982-1986. Report batch 73 as 3 candidates, 3 verified, 1 duplicate, 0 pending/restricted/unprocessed; export and audit the workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 74: Add VOA Tiananmen public communication records

**Files:** `data/candidates-voa-tiananmen-discourse-2009-2013.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/voa_tiananmen_2009_editorial.html`, `tests/fixtures/voa_tiananmen_2013_br_layout.html`

- [x] Use public search results only as leads to two document-level VOA records and crawl their original URLs with Scrapy; both robots.txt and target pages returned HTTP 200.
- [x] Route the VOA editorials subdomain to the VOA adapter and extract body text separated by `<br>` while excluding embedded media and image markers.
- [x] Verify the displayed local publication dates, source labels, titles, and complete bodies: 2009-06-02 (1,935 characters) and 2013-06-04 (2,225 characters).
- [x] Report batch 74 as 2 candidates, 2 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook (85 unique rows across 122 candidates).

Further coverage remains required across the four periods, sources, official social accounts, and Chinese and English research literature.

## Task 75: Add early 1950s U.S. international information policy records

**Files:** `data/candidates-frus-voa-china-broadcasting-1952-1954.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use search results only to discover two document-level FRUS pages related to U.S. international information activity and China broadcasting; confirm both URLs were not previously recorded.
- [x] Crawl the original pages with Scrapy and robots.txt enabled; robots.txt and both target pages returned HTTP 200.
- [x] Verify the original-page source, document date, title, author labels, and complete document body: the 1953-06-30 committee report (196,378 characters) and the 1953-10-01 memorandum (42,803 characters).
- [x] Report batch 75 as 2 candidates, 2 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook (87 unique records among 124 candidates).

Further coverage remains required across the four periods, media, official social accounts, and Chinese and English research literature.

## Task 79: Add Bush administration 1989 China statements

**Files:** `data/candidates-bush-china-public-statements-1989.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/bush41_public_paper_statement.html`

- [x] Use public search results only to identify three Presidency Project press conferences and a Bush Library press secretary statement; all four URLs were new candidates.
- [x] Crawl the originals with Scrapy and robots.txt enabled; both robots.txt requests and all target pages returned HTTP 200.
- [x] Add a Bush Library adapter after a fixture test failed; verify the 1989-06-20 page date, title, and complete 1,173-character three-paragraph statement, then recrawl the original page.
- [x] Verify the other complete records dated 1989-05-21, 1989-06-08, and 1989-06-27 with body lengths 20,526, 30,254, and 39,434 characters.
- [x] Report batch 79 as 4 candidates, 4 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook (101 unique records among 140 candidates).

Further coverage remains required across the four periods, media, official social accounts, and Chinese and English research literature.

## Task 80: Add 2018-2023 U.S. government China policy speeches

**Files:** `data/candidates-us-china-policy-speeches-2018-2023.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/trump_whitehouse_pence_statement.html`

- [x] Discover official U.S. government speech and press-availability pages; add four distinct original URLs to the 2017-2025 government batch.
- [x] Crawl with Scrapy and robots.txt enabled; verify Pence's 2018-10-04 speech (29,542 characters) from the original page.
- [x] Add a Trump White House archive adapter using a failing fixture test, and require the exact end marker before marking the source body complete.
- [x] Keep both Pompeo State Department URLs pending because they returned a technical-difficulties page; record Blinken's China mission page as restricted after HTTP 403 on the source and robots endpoint.
- [x] Report batch 80 as 4 candidates, 1 verified, 2 pending, 1 restricted, 0 duplicate/unprocessed; export and audit the nine-column workbook (102 unique records among 144 candidates).

Further coverage remains required across the four periods, media, official social accounts, and Chinese and English research literature.

## Task 81: Add 1949-1954 FRUS China information-policy records

**Files:** `data/candidates-frus-china-information-records-1949-1954.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use official-source search results only to discover four previously unrecorded FRUS document URLs.
- [x] Crawl the four original pages with Scrapy and robots.txt enabled; all target pages and robots.txt returned HTTP 200.
- [x] Reparse the saved original HTML with the FRUS adapter and confirm source metadata and each complete body match the stored record exactly.
- [x] Add body-grounded Chinese abstracts prefixed `据正文整理：` and content-based keywords to the four verified materials.
- [x] Report batch 81 as 4 candidates, 4 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook (106 unique records among 148 candidates).

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 82: Check SAGE U.S.-media/China-image research pages

**Files:** `data/candidates-sage-us-media-china-image-2024-2025.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Use search results only to discover two previously unrecorded SAGE publisher pages about U.S. media coverage of China.
- [x] Request the publisher pages with Scrapy and robots.txt enabled; robots.txt returned HTTP 200 and both target pages returned HTTP 403.
- [x] Keep both records restricted, with 0 verified full texts; do not retry through another access path or use excerpts as body text.
- [x] Report batch 82 as 2 candidates, 2 restricted, 0 verified/pending/duplicate/unprocessed; leave the 106-row workbook unchanged.

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 83: Verify Frontiers U.S.-China discourse literature

**Files:** `data/candidates-frontiers-us-china-discourse-literature-2023-2025.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover three publisher-hosted full-text candidates about U.S. trade-policy discourse, U.S./Chinese newspaper representations, and Chinese/American diplomatic discourse.
- [x] Request the publisher PDF and two publisher HTML pages with Scrapy and robots.txt enabled; robots.txt and all three pages returned HTTP 200.
- [x] Keep all three pending because the current adapters did not verify the publication metadata and complete body; do not add search snippets to Excel.
- [x] Report batch 83 as 3 candidates, 3 pending, 0 verified/restricted/duplicate/unprocessed; leave the 106-row workbook unchanged.

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 84: Check CNN and Reuters trade coverage

**Files:** `data/candidates-media-us-china-trade-2018-2025.csv`, `README.md`, `data/research.sqlite3`

- [x] Discover four original CNN and Reuters article URLs from 2018-2025, without using search excerpts as body text.
- [x] Run Scrapy with robots.txt enabled; both robots.txt files returned HTTP 200 and all four target paths were forbidden by robots.txt, so article pages were not requested.
- [x] Keep the four candidates unprocessed with `Forbidden by robots.txt` details; do not retry through another access path.
- [x] Report batch 84 as 4 candidates, 4 unprocessed, 0 verified/pending/restricted/duplicate; the workbook remains at 106 records.

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 85: Add 1955-1957 FRUS China public-information records

**Files:** `data/candidates-frus-china-public-information-1955-1957.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover five previously unregistered original documents in FRUS Volume II, China, 1955-1957.
- [x] Crawl with Scrapy and robots.txt enabled; robots.txt and all five original pages returned HTTP 200.
- [x] Verify complete original-page metadata and body for the 1955-03-16 DCI memorandum (8,826 characters) and 1955-05-24 Dulles telegram (2,365 characters); add body-derived abstracts and keywords.
- [x] Keep two Editorial Notes pending because their pages do not display a single exact publication date; keep the 1955-03-27 document pending because the current parser does not support the page's exact `27 March, 1955` dateline.
- [x] Report batch 85 as 5 candidates, 2 verified, 3 pending, 0 restricted/duplicate/unprocessed; export and audit the nine-column workbook (108 unique records among 162 candidates).

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 86: Add 1958 Taiwan Strait crisis FRUS records

**Files:** `data/candidates-frus-taiwan-strait-public-discourse-1958.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover five previously unregistered original documents in FRUS Volume XIX, China, 1958-1960.
- [x] Crawl with Scrapy and robots.txt enabled; robots.txt and all five source pages returned HTTP 200.
- [x] Verify all five complete records dated 1958-08-25, 1958-09-04, 1958-09-12, 1958-10-23, and 1958-10-24; body lengths 5,325, 2,224, 4,110, 4,438, and 5,027 characters.
- [x] Reparse saved original HTML and confirm metadata and body equality; add body-grounded abstracts prefixed `据正文整理：` and content-based keywords.
- [x] Report batch 86 as 5 candidates, 5 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook (113 unique records among 167 candidates).

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 87: Add recent VOA coverage of China-U.S. competition

**Files:** `data/candidates-voa-china-us-competition-2023-2025.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover five new VOA News original pages about Taiwan election narratives, U.S. chip policy, and Taiwan-U.S. semiconductor investment.
- [x] Crawl with Scrapy and robots.txt enabled; robots.txt and all five source pages returned HTTP 200.
- [x] Verify four complete articles dated 2023-09-28, 2024-04-25, 2024-12-02, and 2025-03-06; body lengths 5,255, 4,058, 1,240, and 5,734 characters.
- [x] Keep the remaining page pending because it exposes only video metadata and no complete article text or transcript.
- [x] Report batch 87 as 5 candidates, 4 verified, 1 pending, 0 restricted/duplicate/unprocessed; export and audit the nine-column workbook (117 unique records among 172 candidates).

Further coverage remains required across all four periods, media, official social accounts, and Chinese and English research literature.

## Task 78: Add Carter's 1978 China-normalization public materials

**Files:** `data/candidates-carter-china-normalization-announcement-1978.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use search results only to locate four previously unrecorded original document pages on the December 1978 normalization announcement.
- [x] Crawl all original pages through Scrapy with robots.txt enabled; robots.txt and all target pages returned HTTP 200.
- [x] Verify the December 15 national address (5,578 characters), U.S. statement (1,730), White House briefing (5,325), and December 30 presidential memorandum (2,541), including each page's displayed date, title, and complete body.
- [x] Report batch 78 as 4 candidates, 4 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the nine-column workbook (97 unique records among 136 candidates).

Further coverage remains required across the four periods, media, official social accounts, and Chinese and English research literature.

## Task 77: Add 1973-1975 FRUS public-opinion records

**Files:** `data/candidates-frus-china-public-opinion-1973-1975.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use search results only to find four previously unrecorded single-document pages in FRUS Volume XVIII, China, 1973-1976.
- [x] Crawl the original pages with Scrapy and robots.txt enabled; robots.txt and target pages returned HTTP 200.
- [x] Verify three complete records dated 1973-11-12 (47,468 characters), 1975-07-03 (32,525 characters), and 1975-11-20 (48,025 characters).
- [x] Keep Document 12 pending because its original dateline spans February 17-18, 1973 and does not establish one exact YYYY-MM-DD date.
- [x] Report batch 77 as 4 candidates, 3 verified, 1 pending, 0 restricted/duplicate/unprocessed; export and audit the nine-column workbook (93 unique records among 132 candidates).

Further coverage remains required across the four periods, media, official social accounts, and Chinese and English research literature.

## Task 76: Add FRUS records from the Nixon opening to China

**Files:** `data/candidates-frus-china-public-communication-1969-1972.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use search results only to discover four previously unrecorded document-level pages in FRUS Volume XVII, China, 1969-1972.
- [x] Crawl all four original pages through Scrapy with robots.txt enabled; the site and target pages returned HTTP 200.
- [x] Verify three complete documents dated 1972-01-03 (28,491 characters), 1972-02-22 (67,829 characters), and 1972-03-09 (6,975 characters).
- [x] Keep Document 165 pending because its original page explicitly says “Washington, undated” and therefore lacks a qualifying exact publication date.
- [x] Report batch 76 as 4 candidates, 3 verified, 1 pending, 0 restricted/duplicate/unprocessed; export and audit the nine-column workbook (90 unique records among 128 candidates).

Further coverage remains required across the four periods, media, official social accounts, and Chinese and English research literature.

## Task 55: Test an open-access New York Times discourse-analysis paper

**Files:** `data/candidates-research-literature-nyt-image-2023.csv`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the original 2023 Humanities and Social Sciences Communications article page through Firecrawl research-category search.
- [x] Import and request the original publisher URL directly with Scrapy; the page returned HTTP 406 and remains restricted/unavailable, not verified.
- [x] Search for repository copies; no accessible repository source with independently verifiable full text and publication date was found in this batch.

## Task 56: Test the repository record for a 2015 NYT media-discourse paper

**Files:** `data/candidates-literature-made-in-china-2015.csv`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the original Sinología Hispánica journal record and its Buleria repository record; search indexing indicated a 2015 publication year, not a confirmed exact day.
- [x] Request the journal record with Scrapy; HTTP 403 was recorded as restricted, and no mirror or search excerpt was used as body text.

## Task 57: Verify an open PMC comparative media article

**Files:** `data/candidates-research-covid-media-2021.csv`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/pmc_article.html`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Discover a PMC-hosted open full-text article comparing Chinese and American media coverage of COVID-19.
- [x] Add a PMC-specific adapter and offline fixtures; require exact title, journal, authors, publication date agreement between citation display and metadata, article body, and separate abstract/keywords.
- [x] Preserve article section order while excluding repeated abstract/keywords, references, declarations, footnotes, and page modules.
- [x] Re-crawl the original URL through Scrapy after robots.txt allowed it; verify publication date 2021-09-09 and the complete 50,899-character article body.
- [x] Report batch 57 as 1 candidate, 1 verified, 0 pending/restricted/duplicate; export and audit the cumulative nine-column workbook.

Further coverage remains required for Chinese and English research literature, official social accounts, and the remaining requested media and periods.

## Task 58: Add early Cold War information-policy records

**Files:** `data/candidates-frus-information-policy-1950s.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets only to identify two document-level FRUS records from 1951 and 1952.
- [x] Import both candidates in the 1949-1972 government period and crawl their exact original pages through Scrapy after robots.txt allowed access; both target responses returned HTTP 200.
- [x] Verify document title, FRUS date, source identifier, and complete TEI body; source pages did not identify a personal author, so record `未注明`.
- [x] Confirm the 1951 memorandum's annexes discuss VOA, radio, political warfare, and public support; the 1952 briefing concerns oversight of China covert programs.
- [x] Report batch 58 as 2 candidates, 2 verified, 0 pending/restricted/duplicate; update period coverage and cumulative workbook.

Further coverage remains required across media, social accounts, and Chinese and English research literature.

## Task 59: Add Truman administration public statements on Korea and China

**Files:** `data/candidates-truman-korea-china-public-1950.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets only to discover three individual Truman public statements/pages from June-July 1950.
- [x] Import the original Presidency Project URLs in the 1949-1972 government batch and crawl them with Scrapy after robots.txt allowed access; all three returned HTTP 200.
- [x] Verify visible and structured publication dates, titles, complete source bodies and author labels; use `未注明` where the page has no distinct author.
- [x] Report batch 59 as 3 candidates, 3 verified, 0 pending/restricted/duplicate; update the cumulative workbook and historical-period notes.

Further coverage remains required across media, social accounts, and Chinese and English research literature.

## Task 60: Recheck a 2018 AP trade-war article and deduplicate

**Files:** `data/candidates-ap-trade-war-2018.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search only to locate the original AP News article page and a source-visible 2018-07-06 publication date; do not use its excerpt as article text.
- [x] Import the original URL as a 2017-2025 media candidate and request it through Scrapy with `ROBOTSTXT_OBEY=True`; this request returned HTTP 403.
- [x] Match the URL to an existing verified AP record; retain that original verified body and add one repeat discovery rather than replacing it with the restricted response.
- [x] Report batch 60 as 1 candidate, 0 newly verified, 1 restricted, 1 duplicate and 0 pending/unprocessed; re-export the workbook with the updated repeat count.

Further coverage remains required across media, social accounts, and Chinese and English research literature.

## Task 61: Add 1949-1950 FRUS broadcasting and China records

**Files:** `data/candidates-frus-voa-china-1949-1950.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets only to discover two document-level FRUS pages; confirm neither exact URL was already in the database.
- [x] Import and crawl both original URLs through Scrapy with robots.txt enabled; both target responses returned HTTP 200.
- [x] Verify the 1950 memorandum's title, date 1950-06-02, unmarked author, and complete 13,128-character body; preserve the 1949 candidate as pending because its metadata/body completeness checks failed.
- [x] Report batch 61 as 2 candidates, 1 verified, 1 pending, 0 restricted/duplicate/unprocessed; export the nine-column workbook and update cumulative counts.

Further coverage remains required across media, social accounts, and Chinese and English research literature.

## Task 54: Add think-tank analyses on China narratives and policy

**Files:** `data/candidates-thinktank-china-narratives-2019-2022.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search only to discover four Brookings and CSIS original-page leads on public attitudes, U.S.-China competition and China policy.
- [x] Import and crawl the four original pages with Scrapy after robots.txt allowed access; all target responses were HTTP 200.
- [x] Verify all four complete source bodies and page publication dates; report 4 verified, 0 pending, 0 restricted, and 1 duplicate discovery.
- [x] Preserve the already-existing CSIS material as one unique Excel row and increment its repeat-discovery count; add the other three unique records.
- [x] Export and audit the workbook with 63 unique source URLs.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 53: Add 2011 U.S.-China S&ED remarks

**Files:** `data/candidates-sed-2011.csv`, `data/captures/state-sed-2011-162976.json`, `data/captures/state-sed-2011-162881.json`, `data/captures/state-sed-2011-162925.json`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets to discover three original 2011 State Department remarks pages; exclude the related index page.
- [x] Import all three as candidates; Scrapy returned a technical-difficulties page (HTTP 200) for each, which remained pending and was not treated as source text.
- [x] Fetch each exact public URL via Firecrawl rawHtml; preserve the complete tool result, matching source/final URLs, HTTP 200, and scrape IDs.
- [x] Import the raw captures through the shared adapter and verification pipeline; verify the title, author, page publication date, and full body for all three records.
- [x] Report batch 53 as 3 candidates, 3 verified, 0 pending, 0 restricted and 0 duplicate; export and audit the cumulative workbook with 60 verified records among 87 candidates.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 52: Add Bush administration statements on Tiananmen

**Files:** `data/candidates-tiananmen-1989-1990.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets only to discover a 1989 presidential news conference and a 1990 anniversary statement.
- [x] Import two candidates in the 1972-1991 government batch and crawl both original Presidency Project pages with Scrapy after robots.txt allowed access; both returned HTTP 200.
- [x] Verify the page title, visible/structured publication date and complete document body; report 2 verified, 0 pending, 0 restricted and 0 duplicate.
- [x] Update the cumulative status and coverage notes; export and audit the nine-column workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 51: Expand 1972 Nixon China-visit public records

**Files:** `data/candidates-nixon-china-1972.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search snippets only to identify three individual Presidency Project pages on the China visit, foreign-policy report and presidential interview.
- [x] Import and crawl all three original URLs with Scrapy after robots.txt allowed access; all target responses were HTTP 200.
- [x] Verify visible title/date against the page's structured date and preserve only the document's source text; record body lengths 8,290, 483,085 and 54,261 characters.
- [x] Report batch 51 as 3 candidates, 3 verified, 0 pending, 0 restricted and 0 duplicate; export and audit the cumulative nine-column workbook with 55 verified rows among 82 candidates.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 62: Support PMC Cloud viewer research articles

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/pmc_cloud_article.html`, `data/candidates-research-western-news-china-image-2025.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Capture the current original PMC page through Scrapy; its Cloud viewer layout combines the main manuscript and nested peer-review sub-articles, which the old adapter conservatively left pending.
- [x] Add a failing fixture-based test, then extend parsing to isolate the main PMC article and preserve the exact publication-date, title-match, and complete-body gates.
- [x] Re-run the original PMC URL after the adapter change; verify publication date 2025-06-18, author Lei Sun, title, and the complete 55,493-character body, excluding abstracts, references, and review correspondence from the正文 field.
- [x] Report batch 62 as 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 63: Add 1951 FRUS Korea and China records

**Files:** `data/candidates-frus-voa-korea-china-1951.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl search excerpts only to identify two document-level FRUS pages mentioning Voice of America and China/Korea discourse; confirm both URLs were new to the database.
- [x] Import and crawl the original pages through Scrapy with robots.txt enabled; both target responses returned HTTP 200.
- [x] Verify the May 3, 1951 memorandum's title, date, author label and complete 23,288-character body; leave the second page pending because full-text/metadata checks did not pass.
- [x] Report batch 63 as 2 candidates, 1 verified, 1 pending, 0 restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Task 64: Add open PMC research on media cultivation and country image

**Files:** `data/candidates-pmc-us-media-china-image-2022-2023.csv`, `README.md`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`

- [x] Use Firecrawl research-category results only to identify two previously unrecorded open PMC articles relevant to U.S. media and China image/public attitudes.
- [x] Crawl both original PMC pages through Scrapy with robots.txt enabled; both returned HTTP 200.
- [x] Verify each source page's exact title, authors, journal, publication date, abstract/keywords and complete main article body; exclude references, review material and page modules.
- [x] Report batch 64 as 2 candidates, 2 verified, 0 pending/restricted/duplicate/unprocessed; export and audit the cumulative nine-column workbook.

Further coverage remains required across the four periods, media, social accounts, and Chinese and English research literature.

## Batches 141–145: Earlier media and Chinese/English research

- [x] Save Firecrawl discovery results and raw journal publication pages; treat snippets only as discovery.
- [x] Observe robots restrictions for both NYT Chinese pages and record two restricted candidates without requesting forbidden bodies.
- [x] Retrieve public AAU and IJoC PDFs with Scrapy and source publication pages; inspect all 40 rendered pages, source metadata and final content.
- [x] Import one Chinese and one historical English research paper with publisher summaries, explicit author/date and full original body; distinguish annual volume date from article publication date.
- [x] Retrieve and review two public pre-2017 PBS articles, retaining original paragraph text and excluding funding modules.
- [x] Export exactly nine columns and rebuild evidence-hash-checked ZIP: 187 materials, 56 body sidecars, 207 raw evidence files.

Four new verified materials, two restricted candidates. Pending 99 and restricted 40 remain excluded. Goal remains active; earlier media, primary named media and broader Chinese literature still need expansion.

## Batch 146 and exact verification provenance

- [x] Add exact promotion snapshots for field-source URLs, abstract origin and supporting evidence IDs, atomically with material writes; migration does not guess historical associations.
- [x] Verify persistence, replacement, rollback and exact/legacy package selection; 148 full tests and Scrapy checks pass; independent scoped review found no important defects.
- [x] Crawl and review three 1955/1958 Taiwan Strait communications; use the letter release date 1958-09-13, not its 1958-09-12 dateline.
- [x] Audit date notes in 55 existing APP records; quarantine 1972 chronology and 1984 Democratic platform because original publication day is unverified and source admits assigning an event date.
- [x] Reverify last batch's four materials to record this verification's exact support associations; rebuild package with 188 materials, 55 body sidecars and 208 raw evidence files.

Pending 101 and restricted 40 remain outside formal workbook. Goal continues; additional early media, named major media, research and new-media coverage still required.


## Batch 147: Early public communication and broadcasts

- [x] Save ten Firecrawl discovery searches and one raw-HTML VOA capture; snippets are discovery only.
- [x] Retrieve five original APP pages through robots-obeying Scrapy; all target and robots responses HTTP 200.
- [x] Review full texts and original metadata. Admit Truman 1951-04-11 radio report (13,773 characters) and Johnson 1966-07-12 nationwide Asian-policy remarks (14,270 characters), preserving source text and deriving clearly labelled summaries.
- [x] Withhold two general information-policy speeches lacking direct China content and one Kennedy campaign transcript with a visible mid-sentence gap. Do not promote staging results automatically to the formal corpus.
- [x] Register two already-known URLs rediscovered in saved searches as duplicates; retain original formal rows without claiming fresh body retrieval.
- [x] Export and verify 190 unique formal materials, 55 referenced sidecars, 210 raw evidence files, nine exact provenance snapshots and 181 explicitly labelled legacy associations. Database integrity and ZIP CRC pass.

Batch: seven candidate status rows, four verified including two existing records, three pending, two duplicate discoveries, zero restricted/unprocessed. Two new formal materials. Cumulative pending 104 and restricted 40 remain outside the formal workbook. Earlier media, the named primary media, broader Chinese/English research and new-media coverage still require expansion; goal remains active.


## Batch 148: Pre-2017 PBS media and reviewed-body gates

- [x] Save six searches and five original HTTP-200 article pages with robots enabled; preserve one Firecrawl transport failure and one successful raw-HTML retry.
- [x] Build real source-derived tests before code; five new source cases fail before the extension. Add exact reviewed URL/date/title/byline/body SHA-256 snapshots while retaining general contributor-ending and metadata gates.
- [x] Preserve pullquotes, substantive direct text tails, inline punctuation and br separators; reject list text that would be silently omitted. Independent review's two findings reproduced as failing tests and fixed.
- [x] Import five source-reviewed 2009/2015/2016 articles with publisher-provided summaries and body-grounded keywords. Main-source character sequence independently matches full article content after only documented funding/recommendation exclusions.
- [x] Reverify id 218 against saved original HTML, removing two parser-inserted spaces before commas; retain original source, publication date, title, author, publisher summary and keywords.
- [x] Full suite 165 passed; Scrapy check OK; eight supported formal PBS articles reparse exactly, two earlier manually reviewed layouts remain manual. Database integrity/foreign-key checks pass.
- [x] Deliver 195 formal materials, 55 referenced long-body files and 215 original evidence files; 15 exact verification snapshots and 180 explicitly labelled legacy associations.

Batch: five candidates and five new verified unique materials, zero pending/restricted/duplicate/unprocessed. Cumulative 344 candidate status rows, 200 verified, 104 pending, 40 restricted, zero unprocessed; 11 duplicate discoveries. Major named media, earlier periods, broader Chinese/English research and official social content remain insufficiently covered. Goal remains active.

## Batches 149–152: Historical discourse and Chinese policy studies

- [x] Save five Firecrawl searches, three original journal metadata pages and three linked issue pages; snippets remain discovery only. Two failed DOI lookups are not publication-date or access-restriction evidence.
- [x] Retrieve three public PDFs and publisher metadata through robots-obeying Scrapy, HTTP 200. Distinguish article Published/DC.Date.created from issue Published/DC.Date.issued and incomplete citation years.
- [x] Render and visually inspect all 45 pages; independently compare non-whitespace character multisets for each page and the whole extracted body, retaining notes/references and original paragraph order. Copy actual publisher titles/authors and record source variants without guesses.
- [x] Admit IJoC embassy-apology study (2007-07-11, 61,756 characters), Chinese transnational-challenge study (2019-01-31, 39,527) and Chinese Trump-policy study (2019-12-01, 22,344). Each has an exact primary/metadata/issue evidence association and publisher abstract.
- [x] Register three actual saved search appearances of the existing OJS article/galley 1311/1066; one candidate status row, no new unique body, no claim of fresh retrieval.
- [x] Export and hash/round-trip/CRC-check 198 unique formal materials, 57 long-body sidecars and 224 original evidence files; 18 exact and 180 explicitly labelled legacy associations. SQLite integrity and foreign-key checks pass.

Each of batches 149–151: one candidate and one new verified material, other statuses zero. Batch 152: one existing verified candidate, three duplicate discoveries, no new body. Cumulative 348 candidate status rows: 204 verified, 104 pending, 40 restricted, zero unprocessed. Fourteen historical duplicate discoveries include two belonging to withdrawn records; the current formal workbook duplicate-count sum is 12. Major named media, earlier media, broader research and official new-media coverage remain insufficient. Goal stays active.

## Batches 153–154: VOA China coverage and broadcasting

- [x] Save three Firecrawl search results and three publisher page captures. Use search excerpts only for discovery and retain the page captures as auxiliary evidence.
- [x] Crawl three original pages through robots-obeying Scrapy, all HTTP 200. Capture two articles not previously held and identify one existing 2013 article.
- [x] Extend the VOA adapter to include `www.insidevoa.com`, safely reconcile an H1 title with a shorter same-page JSON-LD/og:title using the exact JSON-LD source URL, and exclude standalone reporter-credit/contact-footer paragraphs. Add source-derived tests before implementation.
- [x] Verify visible dates, JSON-LD publication instants, page titles, authors, article paragraphs and end boundaries. The 2009 visible page date is Feb. 18 local time despite a Feb. 19 UTC date, URL slug and body dateline; use the visible source-page date.
- [x] Keep the 2019 page in 2017–2025, merge a misclassified/retry candidate into its corrected period record, and remove the false retry-as-duplicate accounting. The 2013 rediscovery remains one actual duplicate.
- [x] Rebuild and audit the delivery package; run 167 tests and Scrapy check.

Batch 153 final period assignment: two candidates, two verified records (one new 2009 full text and one previously held 2013 full text), one duplicate discovery. Batch 154: one candidate and one new verified 2019 full text. This turn adds two unique materials total and leaves 200 formal unique materials. Search coverage remains limited; earlier named-media, research and new-media work continues.

## Batch 155: 1989–1990 U.S. public statements on China

- [x] Save four Firecrawl discovery searches and three original Presidency Project page captures. Search excerpts were discovery leads only.
- [x] Retrieve three source pages through robots-obeying Scrapy; robots.txt and target responses were HTTP 200.
- [x] Verify visible and machine-readable dates agree; re-extract and compare all ordered source blocks and complete body text for each record.
- [x] Reverify the already-held 1989-06-05 presidential news conference and 1990-06-04 Tiananmen anniversary statement; add the 1989-11-30 Chinese immigration bill disapproval memorandum. Preserve original titles, author labels and page text; do not infer ideological classifications.
- [x] Export the cumulative nine-column workbook and rebuild the raw-evidence delivery package.

Batch: three candidates, three verified rows (one new unique material, two existing materials reverified), two duplicate discoveries, zero pending/restricted/unprocessed. The 1972–1991 period has 15 unique government records; media and international broadcasting content for that period remain thin and require further collection.

## Batch 156: Deng visit and cultural exchange (1979–1984)

- [x] Save three Firecrawl discovery searches and five original Presidency Project page captures; check all five URLs against the existing corpus before crawling.
- [x] Retrieve all five pages through robots-obeying Scrapy; robots.txt and target pages returned HTTP 200.
- [x] Verify exact visible/machine dates and re-extract all 141 body blocks. Each saved body matches the source adapter's full ordered body text exactly.
- [x] Add three distinct 1979 Deng-visit public records, the 1984 bilateral cultural-exchange accord explicitly discussing VOA/Radio Beijing exchanges, and Reagan's Fudan University remarks.
- [x] Export and verify the cumulative workbook, UTF-8 sidecars, raw evidence hashes, database integrity and ZIP CRC.

Batch: five candidates, five new unique verified full texts, zero pending/restricted/duplicate/unprocessed. The 1972–1991 period now has 20 unique government records; named media and international broadcasting remain insufficiently covered, so the overall corpus goal remains active.

## Batch 157: VOA English-language Tiananmen legacy reports

- [x] Save four Firecrawl searches and two original VOA page captures; search-result excerpts remain discovery only.
- [x] Exclude the AP 2019 photo gallery because it is not an article body; do not infer a 1972–1991 publication date from the pictured events.
- [x] Crawl two public VOA source pages with robots.txt enabled; both source pages and robots.txt responses were HTTP 200.
- [x] Verify original visible publication dates, bylines, title, article language, complete source body and period assignment; both are 1992–2016 records.
- [x] Export and verify the cumulative nine-column workbook and evidence package.

Batch: two candidates, two verified unique full texts, zero pending/restricted/duplicate/unprocessed. These post-1989 anniversary/legacy reports add relevant coverage but do not fill the contemporaneous named-media gap in 1972–1991.

## Follow-up: Nature research article candidate

- [x] Add a failing source-layout test for Nature research pages, including nested sections, separate data-availability/references regions, visible Published metadata, publisher abstract and CC BY 4.0 rights text.
- [x] Implement a Nature-only adapter that verifies the exact original URL, title, journal, DOI, visible authors, exact publication date, publisher abstract, open-license statement and article boundaries. Exclude recommendation/related-topic blocks and page-level author-information templates.
- [x] Reprocess the saved official-page Firecrawl raw HTML capture for the existing batch-55 candidate. The capture is HTTP 200 for the exact original URL and retains its retrieval ID; an attempted Scrapy refresh received HTTP 406 for robots.txt and the page and supplied no content.
- [x] Verify the same-page bibliographic fields and 58,418-character extracted body through the adapter, then promote the existing candidate to verified; do not add a duplicate candidate row.
- [x] Rebuild the nine-column workbook and delivery package. Verify 218 rows, 63 long-body sidecars, body equality with SQLite, ZIP CRC, SQLite integrity and foreign keys; full test suite passes (176 tests).

The follow-up adds one unique full text. Cumulative database: 373 candidate rows, 227 verified, 103 pending, 43 restricted, 17 historical duplicate discoveries; formal workbook: 218 unique materials. Coverage remains incomplete across early periods, named media, additional think tanks, social sources and Chinese/English literature.

## Batch 168: CCSE open PDF research article

- [x] Add a source-derived failing test for the observed CCSE PDF layout; require a source-published exact online date, journal/title/authors/DOI, publisher abstract and keywords, CC BY 4.0 license, all 15 pages and page numbers 16–30.
- [x] Add a narrowly routed PDF adapter that reads the original publication artifact when its OJS landing page returns 404; do not treat the missing page or search result as bibliographic evidence.
- [x] Crawl with Scrapy and robots.txt enabled. The robots file and original PDF returned HTTP 200; the metadata landing page returned HTTP 404. Verify publication fields and completeness directly against the original PDF.
- [x] Record and include “Neighbor by Miles and Neighbor by Steps: A Comparative Study of China’s National Image Construction” (2025-08-26; 63,275 extracted characters), whose source abstract states that it compares The Moscow Times and The New York Times.
- [x] Rebuild the cumulative delivery package and verify exact nine-column schema, both new long-body UTF-8 round-trips, 219 provenance entries, ZIP CRC, SQLite integrity/foreign keys, and full suite (177 tests).

Batch: one candidate, one verified new unique full text, zero pending/restricted/duplicate/unprocessed. Current cumulative state: 374 candidate rows, 228 verified, 103 pending, 43 restricted, 17 duplicate discoveries and 219 unique formal materials. The delivery workbook contains 219 rows with 64 referenced UTF-8 body sidecars. Additional periods and named media remain undercovered.

## Batch 169: PBS NewsHour Tiananmen transcript completeness check

- [x] Use Firecrawl search only to identify an unrecorded PBS NewsHour source page; retain the search result as discovery, not transcript evidence.
- [x] Crawl the original PBS page through Scrapy with robots.txt enabled; both robots.txt and source page returned HTTP 200.
- [x] Verify the visible page date (2001-01-11), matching `article:published_time`, source title and absence of an explicit byline.
- [x] Inspect the transcript DOM block by block. The page body ends mid-answer with the standalone text “ANDREW”; retain the source capture and leave the candidate pending rather than certify or export incomplete text.
- [x] Record the batch result and coverage limitation: 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed; formal corpus remains 219 unique materials.

This is a later retrospective broadcast transcript about 1989, not a contemporaneous 1989 media item. The transcript is not admitted until a complete, legally accessible original transcript can be verified.

## Batch 170: PBS NewsHour video transcript adapter

- [x] Reuse the saved Firecrawl discovery lead and confirm the transcript URL was not already in the corpus.
- [x] Retrieve the original PBS page with Scrapy and robots.txt enabled; robots and page both returned HTTP 200.
- [x] Add a failing test from the captured source page, then implement a PBS transcript adapter gated to the exact reviewed URL, visible/structured publication date, matching title metadata, transcript container, paragraph order, complete-text hash and final transcript block.
- [x] Verify that changing the page text, title, date, URL or truncating the final answer prevents promotion; all reviewed PBS tests pass.
- [x] Re-crawl through the production pipeline. Promote the one existing candidate from pending to verified and add one unique transcript dated 2019-06-04; preserve the source's missing-byline value as “未注明”.
- [x] Record 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed. The 2019 anniversary transcript is retrospective and does not fill the contemporaneous 1972–1991 named-media gap.

Formal corpus: 220 unique materials. Current database: 376 candidate rows (229 verified, 104 pending, 43 restricted). Additional period/source coverage remains necessary.

## Batches 171–173: 1999 embassy-bombing communications

- [x] Search first-party government archives for contemporaneous material and check each URL against the corpus.
- [x] Crawl the original State Department URL under Scrapy robots policy. Its HTTP 200 body was a “Technical Difficulties / Exception: forbidden” page; classify it restricted and do not use the search excerpt as full text.
- [x] Check the official U.S. Embassy archive URL. robots and page returned HTTP 403; stop without proxy or mirror workarounds and retain it as restricted.
- [x] Crawl the APP Clinton press-question transcript with robots enabled; robots and original page returned HTTP 200. Verify its visible May 8, 1999 date, source title/byline and full body through the existing APP adapter.
- [x] Promote one unique 5,122-character record and report the two blocked candidates separately: batch 171 1 restricted; batch 172 1 restricted; batch 173 1 verified.

Formal corpus: 221 unique materials. Current database: 379 candidate rows (230 verified, 104 pending, 45 restricted). These one-item searches are not exhaustive; additional periods and media sources remain undercovered.

## Batch 174: Clinton White House response briefing

- [x] Check the APP source URL for an existing row; none existed before this batch.
- [x] Crawl with Scrapy and robots.txt enabled; both robots and source page returned HTTP 200.
- [x] Verify the source-page date (1999-05-10), APP attribution, exact title, full question-and-answer body and terminal `END 4:00 P.M. EDT` marker.
- [x] Promote one unique 17,248-character full transcript; preserve the source archive's William J. Clinton person attribution and keep this distinct URL separate from the May 8 transcript.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.

Formal corpus: 222 unique materials. Current database: 380 candidate rows (231 verified, 104 pending, 45 restricted). Further source and period coverage remains required.

## Batch 175: PBS NewsHour Tiananmen legacy interview

- [x] Use Firecrawl search for discovery only and check the exact PBS URL against the formal corpus.
- [x] Retrieve the original page with Scrapy and robots.txt enabled; both robots and source page returned HTTP 200. Preserve the raw source capture and response hash.
- [x] Check the original page metadata: visible/structured publication time is 2021-06-04; visible bylines identify Nick Schifrin and Dan Sagalyn; title is “Tiananmen Square massacre casts a long shadow over modern Chinese politics.”
- [x] Add an exact reviewed transcript gate after inspecting all 56 ordered paragraph/speaker blocks, the two visible authors, visible and structured dates, and the final PBS sign-off. The 6,357-character body SHA-256 must match the inspected source.
- [x] Add regression coverage rejecting body, title, date, URL and terminal-block changes/truncation; full test suite passes (189 tests).
- [x] Re-fetch the same candidate under Scrapy robots policy; robots and source page both returned HTTP 200. Promote it to verified; report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh the nine-column workbook and delivery ZIP; both contain 223 unique materials and the ZIP CRC check passes.

Discovery results and the source-capture review are saved under `research/firecrawl/` and `data/reviews/`. This is one 2021 retrospective, not a substitute for contemporaneous coverage; additional 1972–1991 and media-source coverage remains necessary.

## Batch 176: 1992 presidential debate on China policy

- [x] Use Firecrawl search as discovery only; check the exact American Presidency Project URL against existing candidates/materials.
- [x] Retrieve the source page with Scrapy and robots.txt enabled; both robots and page returned HTTP 200.
- [x] Verify the page's 1992-10-11 publication date, byline, title and complete 91,421-character transcript through the APP adapter. Confirm its closing program sign-off and explicit “China-U.S. Relations” section.
- [x] Keep the abstract empty because the source page provides no abstract; do not substitute a search excerpt. Preserve the source's “George Bush” attribution.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 224 unique materials.

Discovery and source review are saved under `research/firecrawl/` and `data/reviews/`. This one-item batch does not establish exhaustive coverage of the 1992–2016 period.

## Batch 177: 2023 Republican primary debate on Taiwan and China

- [x] Use Firecrawl search only to identify the original APP page; confirm the exact URL was not already represented in candidates/materials.
- [x] Retrieve the original page with Scrapy and robots.txt enabled; both returned HTTP 200.
- [x] Verify APP publication date 2023-09-27, source attribution, title, complete 103,680-character debate transcript and closing program sign-off. The full original transcript includes references to Taiwan and China.
- [x] Do not use the search excerpt as body or abstract; preserve the source's “Presidential Candidate Debates” author attribution and blank source-abstract field.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 225 unique materials.

Discovery and review evidence are saved under `research/firecrawl/` and `data/reviews/`. This does not establish exhaustive coverage of the 2017–2025 period.

## Coverage gap check: contemporaneous 1989 media

- [x] Search for the original PBS NewsHour/MacNeil-Lehrer June 5, 1989 coverage and Tom Raum's AP report.
- [x] Determine that search results expose a YouTube item whose description says portions are removed and a PBS FRONTLINE newspaper-excerpt page, not a verified complete AP source page.
- [x] Do not create a formal material or use snippets/excerpts as full text; record zero eligible candidates and zero materials from this check.
- [x] Leave the 2001 PBS transcript pending because its transcript container ends mid-speaker segment; it does not cover contemporaneous 1989 reporting.

Search evidence is saved under `research/firecrawl/early-media-tiananmen-1989-gap-20261107/`. The 1972–1991 contemporaneous media-source gap remains open.

## Batch 178: State Department archive access denial

- [x] Check the discovered State Department archive URL against the corpus and crawl it with Scrapy while obeying robots.txt; robots and page each returned HTTP 200.
- [x] Inspect the raw response rather than trust the HTTP status: it is a “Technical Difficulties” page explicitly stating “Exception: forbidden,” not a transcript.
- [x] Mark the candidate and evidence restricted; do not retry, use a proxy/mirror, or treat the search excerpt as source text.
- [x] Add a regression test for explicit `Exception: forbidden` error pages returned with HTTP 200; test 94 focused spider/policy tests.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; no material was added.

## Batch 179: 1962 presidential news conference on the Taiwan Strait

- [x] Use Firecrawl search only to discover an unrecorded original APP page; verify the exact URL was absent from candidates/materials.
- [x] Retrieve through Scrapy with robots.txt enabled; robots and page both returned HTTP 200.
- [x] Verify APP publication date 1962-06-27, John F. Kennedy attribution, title, complete 30,438-character transcript and the terminal reporter sign-off. Confirm direct relevance through the Taiwan Strait, Communist China, Quemoy and Matsu discussion in the original text.
- [x] Preserve the blank abstract/keyword values because the source supplied none; do not substitute search-result excerpts.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 226 unique materials.

## Batch 180: TMG research on VOA and Chinese-language radio

- [x] Identify the original TMG Journal for Media History landing page and PDF for Donald Santacaterina's DOI 10.18146/tmg.778 article; check the exact PDF and metadata URLs against the corpus.
- [x] Save Firecrawl source-page metadata as discovery evidence only: publisher metadata displays 2021-12-08 and CC BY-SA 4.0.
- [x] Submit the PDF/metadata pair through Scrapy; the publisher's robots.txt denied the metadata-page request before the PDF was requested.
- [x] Mark the candidate restricted, retain no article body in the formal corpus, and do not use Firecrawl extraction to bypass the crawler's robots denial.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 226 unique materials.

## Batch 181: Nixon 1972 China-trip press conference archive page

- [x] Discover the USC U.S.-China Institute transcript and check the source URL against the corpus.
- [x] Retrieve with Scrapy and robots.txt enabled; robots and page both returned HTTP 200.
- [x] Inspect the visible date/title and page: February 10, 1972 is shown, but no source publication-date evidence is present and no byline is specified.
- [x] Retain as pending and exclude from the workbook rather than treating the event date as a publication date.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed.

## Batch 182: Nixon and Zhou Enlai Peking banquet toasts

- [x] Discover the original APP page and verify its URL was absent from candidates/materials.
- [x] Retrieve through Scrapy with robots.txt enabled; both returned HTTP 200.
- [x] Verify APP date 1972-02-21, Richard Nixon attribution, exact title and complete 3,291-character source transcript through the APP adapter.
- [x] Keep missing abstract/keywords empty; do not use search excerpts as body text.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 227 materials.

## Batch 183: FRUS Shanghai Communique source-page date check

- [x] Discover the Office of the Historian FRUS record and check the exact source URL against existing candidates and materials; no match existed.
- [x] Retrieve with Scrapy and robots.txt enabled; robots and the original page both returned HTTP 200.
- [x] Confirm the adapter extracted the source title and document body, but found no independently verifiable exact source publication date. The document's February 27, 1972 dateline is not treated as the page's publication date.
- [x] Retain the candidate as pending and exclude it from the workbook.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed; formal corpus remains 227 unique materials.

## Batch 184: AP archival reprint of 1989 Tiananmen coverage

- [x] Discover the AP News “AP Was There” reprint page and confirm its exact URL is not in candidates or materials; preserve search output as discovery evidence only.
- [x] Request the original AP page through Scrapy with robots.txt enabled; robots.txt returned HTTP 200 and the article page returned HTTP 403.
- [x] Mark the candidate restricted. Do not retry through Firecrawl or treat the search excerpt as article text; the discovery result's “first published on June 5, 1989” description is not used as the current source page publication date.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 227 unique materials.

## Batch 185: VOA Learning English on the 2018 U.S.-China trade dispute

- [x] Discover the original VOA Learning English article and confirm the exact URL is not in the corpus.
- [x] Retrieve the original article through Scrapy with robots.txt enabled; robots and article page both returned HTTP 200.
- [x] Verify the visible publication date and structured `datePublished` both identify 2018-06-15; verify publisher, byline, title and the complete 3,319-character source body through the VOA adapter.
- [x] Preserve publisher-provided abstract and keywords, and keep the body verbatim in the nine-column workbook.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 228 unique materials.

## Batch 186: VOA report on reciprocal U.S.-China tariffs

- [x] Check the second contemporaneous VOA source URL from the 2018 trade-dispute search; no candidate or formal material used this exact URL.
- [x] Retrieve the original page through Scrapy with robots.txt enabled; robots and article page both returned HTTP 200.
- [x] Verify VOA source-page publication date 2018-07-06, source attribution, author, exact headline and complete 4,143-character source body through the VOA adapter.
- [x] Preserve the page-provided abstract/keywords and source text; retain this URL as a distinct article from batch 185.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 229 unique materials.

## Batch 187: VOA Learning English on the costs of the trade war

- [x] Check the VOA Learning English explainer URL from the same targeted search; confirm it is a new source URL.
- [x] Retrieve through Scrapy with robots.txt enabled; robots and source page both returned HTTP 200.
- [x] Verify the displayed and structured publication date (2019-05-06), source, byline, title, and complete 4,333-character body through the VOA adapter.
- [x] Retain it as a distinct VOA article; source body and metadata are from the original page.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed; formal corpus now contains 230 unique materials.

## VOA keyword metadata correction

- [x] Review the original HTML evidence for batches 185 and 187 after detecting that the publisher's `keywords` values were program labels (“Lessons of the Day” and “As It Is”), not thematic keywords.
- [x] Re-run both exact source captures through the VOA adapter and verification gate; replace those labels with themes supported by each page's title/body and update the existing verification snapshots without creating rediscovery rows.
- [x] Add regression coverage that reviewed topical keywords are used for the two examined pages and unreviewed program labels are omitted.

## Batch 188: CNN Tiananmen anniversary page access check

- [x] Discover the original CNN 2019 Tiananmen retrospective page and check the exact URL against candidates and materials.
- [x] Start a Scrapy request with robots.txt enabled; robots returned HTTP 200 and denied the article path before the page was requested.
- [x] Mark the candidate restricted; do not use Firecrawl or search-result excerpts to obtain or replace the source body.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 230 unique materials.

## Coverage check: UCLA 1989 broadcast archive

- [x] Inspect the UCLA OAC finding aid for digital text, access terms and links to original items.
- [x] Confirm the guide indexes 388 ABC, NBC, CBS and CNN stories but is available only for on-site consultation; indexed video tapes are held at UCLA for on-site viewing.
- [x] Do not create material records from the finding aid or its summaries because no online full transcript was located.
- [x] Record the access limitation as discovery evidence; zero candidates and zero formal materials from this check.

## Batch 189: RFA report on Chinese Internet controls

- [x] Discover the original Radio Free Asia article through the site's URL map and confirm the exact URL is not already in candidates or materials.
- [x] Retrieve the original page through Scrapy with robots.txt enabled; the original path returned HTTP 200 after redirects.
- [x] Add an RFA adapter and regression tests for the legacy page structure, exact agreement between visible `2012.09.24` and structured `2012-09-24T22:40:00Z`, title agreement, article container boundaries, and terminal reporter credit.
- [x] Reprocess the saved Scrapy HTML. Preserve the original failed parse as incomplete evidence and add a same-hash verified evidence record after the adapter confirms the page metadata and full article body.
- [x] Verify source Radio Free Asia, date 2012-09-24, byline Parameswaran Ponnudurai, title, publisher description, and the 6,019-character article body. Move the explicit terminal `Reported by` credit to the author field and exclude related-content templates.
- [x] Promote the existing candidate without adding a duplicate discovery; report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed. Formal corpus now contains 231 unique materials.

## Batch 190: RFA report on Internet freedom in China and Vietnam

- [x] Check the RFA map result for the exact 2014 URL against candidates and formal materials; no prior record used this URL.
- [x] Retrieve the original RFA page through Scrapy with robots.txt enabled; robots and page returned HTTP 200.
- [x] Verify the page-visible date (`2014.12.04`), byline (Joshua Lipes), headline, publisher, description, and article container from the saved source HTML. The structured UTC timestamp is `2014-12-05T00:31:00Z`; use the page-visible publication date `2014-12-04` in the workbook.
- [x] Extend the RFA adapter to accept this UTC date rollover only when the structured UTC timestamp is the following date before 06:00, and to read the page's explicit byline; retain rejection for materially mismatched dates.
- [x] Reprocess the saved HTML and retain its original incomplete parse plus the verified same-hash evidence. Confirm the 6,297-character body comes from the single RFA article container and excludes page chrome.
- [x] Report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed. Formal corpus now contains 232 unique materials.

## Batch 191: NYT 1949 PRC proclamation archive access check

- [x] Locate the original NYT archive page for “Proclamation of China's Communist Government” with Firecrawl search; use the result only as a URL lead.
- [x] Run the original URL through Scrapy with robots.txt enabled. robots.txt returned HTTP 200 and denied the article path before the article page was requested.
- [x] Record the source URL as restricted. Do not retrieve the body through Firecrawl, and do not use search-result text or summaries in the formal corpus.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 232 unique materials.

## Redirect handling and challenge classification

- [x] Trace an AAPB catalog URL returning HTTP 302 to the saved response and identify the redirect middleware's `handle_httpstatus_all` guard as the cause of stopping at the redirect.
- [x] Replace catch-all status handling with an explicit 400-599 list across spider entry, metadata, and follow-up requests so normal redirects are followed while error statuses remain classifiable.
- [x] Add a regression test for request metadata and a policy test for HTTP 200 Cloudflare Turnstile pages; keep Scrapy robots checks enabled.
- [x] Confirm the AAPB redirect lands on a Cloudflare Turnstile verification page, classify it as restricted, and do not solve or submit the challenge.

## Batch 192: American Archive of Public Broadcasting catalog access check

- [x] Discover an AAPB catalog result for “A Public Affair; A New Majority” that references Nixon and China; use the search result only to locate the original catalog URL.
- [x] Retrieve the catalog URL through Scrapy with robots.txt enabled; follow the ordinary 302 redirect to the challenge endpoint.
- [x] Detect the Turnstile form and classify the page as restricted despite HTTP 200; preserve response evidence without attempting verification or retrieving media.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 232 unique materials.

## Batch 193: C-SPAN 1989 China call-in access check

- [x] Locate the original C-SPAN program page for “Situation in China” dated June 9, 1989, using Firecrawl search only as a discovery lead.
- [x] Request the exact program URL with Scrapy and robots.txt enabled; the robots endpoint and program path returned HTTP 403.
- [x] Mark the candidate restricted; do not use Firecrawl to retrieve a page blocked by the site's access policy.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 232 unique materials.

## Batches 194-196: Dan Rather archive transcript discovery

- [x] Inspect the Dan Rather archive's Tiananmen report index and its transcript compilation page through their public URLs; both returned HTTP 200.
- [x] Identify individual document links, including a May 15, 1989 CBS Evening News transcript page. Keep index/compilation records pending where the page itself provides no exact publication date or full original text.
- [x] Retrieve the individual transcript metadata page with Scrapy; confirm the page title names the CBS Evening News May 15, 1989 transcript and links to its PDF attachment.
- [x] Retrieve the linked PDF directly through Scrapy after robots allowed the requests; the PDF returned HTTP 200 and contains 3 scanned pages with no selectable text layer.

## Batch 197: CBS Evening News transcript from May 15, 1989

- [x] Add a reviewed scanned-PDF adapter that requires an exact PDF hash, page count, matching metadata-page title, and source-page link before accepting a visually checked transcription.
- [x] Render all three original pages; compare the OCR-assisted transcription against each page and retain original wording, speaker labels, sequence and source spellings.
- [x] Save the original PDF as body evidence and save the landing-page HTML as separate metadata evidence; use the page title and PDF header to verify the broadcast date 1989-05-15.
- [x] Verify CBS News, Dan Rather, title, derived abstract, keywords and the complete 5,761-character body; report 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed. Formal corpus now contains 233 unique materials.

## Batch 198: VOA and China broadcasting research discovery

- [x] Search for source leads on Voice of America broadcasting about China during 1949-1972; preserve the Firecrawl result as discovery metadata only.
- [x] Submit the open-journal research result to Scrapy with `ROBOTSTXT_OBEY` enabled. The site's robots policy denied the target path before the article request was sent.
- [x] Mark candidate 405 restricted. Do not use Firecrawl's search excerpt as body text or retrieve the blocked page through another tool.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed; formal corpus remains 233 unique materials.

## Batches 199-202: Dan Rather archive CBS transcripts

- [x] Inspect the archive's linked transcript pages 0 and 2-8; retain pages without exact-date or full-text verification as pending.
- [x] Retrieve the publicly linked "48 Hours in Beijing" scan through Scrapy; confirm the three-page PDF has no selectable text layer. OCR review found transcript text, but no exact publication date is established on its page, so candidate 407 remains pending.
- [x] Inspect seven additional document pages. Four CBS Evening News records identify May 16, 17, 18 and 19, 1989 in their page descriptions and link individual PDFs.
- [x] Retrieve the four PDFs and metadata pages through Scrapy; each PDF returned HTTP 200 and is an image-only scan with 2-5 pages.
- [x] Promote the 5/16, 5/17, and 5/19 CBS Evening News transcripts after matching their archive-page descriptions, PDF headers, original attachment links, page counts, page titles, date markers and SHA-256 values; compare every scanned page against OCR-assisted text. Materials 279-281 contain 5,634, 4,848, and 5,642 characters.
- [x] Verify the May 18 PDF against all five rendered pages, preserve source spellings, and promote only after matching the exact archive title/date, attachment URL, page count and PDF/body SHA-256 fingerprints. Material 282 contains 8,743 characters; the transcript fits one Excel cell.
- [x] Batch 202 reports 4 candidates, 4 verified, 0 pending/restricted/duplicate/unprocessed. Batches 199-201 still contain one undated scan and eight archive/index pages pending. Formal corpus now contains 237 unique materials.

## Batch 203: VOA institutional-history relevance screen

- [x] Discover the official InsideVOA article “VOA's Mission in the 1960s and 1970s” as a lead while searching historical public broadcasting material.
- [x] Crawl with Scrapy and `ROBOTSTXT_OBEY`; robots and source page returned HTTP 200.
- [x] Verify the page's displayed publication date (2007-02-13), byline (VOA), title and complete 2,978-character body.
- [x] Review the complete body for thesis relevance. It covers VOA history but contains no China/PRC or China-directed broadcasting content; keep it pending relevance screening and remove it from the formal materials table while retaining its source evidence.
- [x] Report 1 candidate, 0 included as verified, 1 pending relevance, 0 restricted/duplicate/unprocessed. Formal corpus remains 237 unique materials; candidate totals are 418 (246 verified, 119 pending, 53 restricted).

## Batch 204: Truman news conference on Communist China and Korea

- [x] Discover the Truman Library source page through a targeted Firecrawl search; use the result only as a URL lead.
- [x] Crawl the original page with Scrapy and `ROBOTSTXT_OBEY`; robots returned HTTP 404 and the source page returned HTTP 200.
- [x] Verify the page title and complete 14,989-character transcript. The text directly addresses Communist China, the Korean ceasefire proposal, a possible UN aggressor designation and Formosa.
- [x] Keep the candidate pending and remove it from formal materials because `1951-01-18` is stated as the date the news conference was held; no separate publication date is displayed on the source page.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed. Formal corpus remains 237 unique materials; candidate totals are 419 (246 verified, 120 pending, 53 restricted).

## Batch 205: 1951 Congressional Record segment

- [x] Discover a GovInfo Congressional Record segment through Firecrawl search; use the result only as a locator.
- [x] Retrieve the official detail page and PDF with Scrapy and `ROBOTSTXT_OBEY`; robots returned 404 and both source URLs returned HTTP 200.
- [x] Confirm the detail page identifies the January 12, 1951 issue and the 22-page PDF discusses Communist China and the Korean War.
- [x] Keep pending because the captured PDF segment ends mid-sentence on its final page; do not treat the partial segment as a complete source text.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed. Formal corpus remains 237 unique materials; candidate totals are 420 (246 verified, 121 pending, 53 restricted).

## Publication-date audit: Truman Library

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `data/research.sqlite3`, `data/reviews/truman-china-news-conference-1951-20261107/publication-date-audit.json`, `README.md`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Reproduce the date error: the adapter promoted a transcript whose only date appears in its body, despite no publication-date field or publication metadata.
- [x] Add a regression test that rejects the body date as a publication date, observe it fail, then add a test for an explicitly labelled publication date and observe it fail against the prior parser.
- [x] Restrict date extraction to explicit publication-date fields or semantically labelled publication metadata.
- [x] Re-audit and withdraw two previously verified Truman Library materials whose source dates were only body dates; retain their original HTML evidence and mark both candidates pending.
- [x] Refresh the workbook and delivery package. Formal corpus now contains 235 unique materials; 420 candidates are 244 verified, 123 pending, and 53 restricted.
- [x] Run the full test suite (200 passed) and delivery integrity audit (235 workbook rows, exact nine columns, 66 body sidecars, 270 evidence files, ZIP CRC valid).

## Batch 206: Acheson's 1950 Asia policy speech

**Files:** `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `tests/fixtures/worldjpn_acheson_speech.html`, `tests/fixtures/frus_acheson_speech_reference.html`, `data/candidates-acheson-crisis-in-asia-1950.csv`, `data/reviews/acheson-crisis-in-asia-1950-20261107.json`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Discover the full public WorldJPN transcript and confirm its `robots.txt` permits retrieval; use search only to locate the source.
- [x] Pair the database transcript with the official FRUS note that cites the National Press Club speech and its Department of State Bulletin issue.
- [x] Add a reviewed adapter and tests that separate the speech date (1950-01-12) from the Bulletin publication date (1950-01-23), require matching title/source/date metadata, and reject incomplete text.
- [x] Retrieve both pages with Scrapy and `ROBOTSTXT_OBEY`; both source pages returned HTTP 200. Save both raw captures and their SHA-256 values.
- [x] Verify the 78-paragraph, 35,775-character full text begins at `[Full text]`, ends with the source's final sentence, and contains no page labels or database chrome. Batch 206 reports 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh the workbook and delivery package; run full tests and integrity audit (202 tests passed; workbook has 236 rows and exactly nine columns; ZIP CRC passed with 67 body sidecars and 272 evidence files).

## Batch 207: Early US media discovery gap

**Files:** `research/firecrawl/early-us-media-1949-1972-20261107/`

- [x] Search for public US newspaper/AP reporting on China and the Korean War, including the Library of Congress historical-newspaper domain.
- [x] Inspect the University of Maryland Digital Archive's China and Korean War collection page; its displayed documents are diplomatic/military records, not US news articles or transcripts.
- [x] Keep search results as discovery evidence only. Two 1950 newspaper issue pages were discovered, but their `robots.txt` rules disallow page requests and the hits identify whole-page OCR, not individually verifiable articles.
- [x] Report 0 new unique materials, 0 new full texts, 2 restricted newspaper discovery leads, and 1 verified duplicate discovery (1958 Eisenhower address already in the corpus); early-period media coverage remains open.

## Batch 208: 1964 public television record

**Files:** `data/candidates-aapb-dialogue-red-china-1964.csv`, `data/reviews/aapb-dialogue-red-china-1964-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the February 3, 1964 National Educational Television program "Dialogue on Red China" through public AAPB/Digital Commonwealth catalog records.
- [x] Check the catalog host's robots policy and fetch the exact catalog URL with Scrapy; robots and target returned HTTP 200.
- [x] Detect that the response is a browser-verification challenge, add a regression test, and classify the response as restricted without attempting to pass the challenge.
- [x] Keep the catalog's title/date/creator as discovery metadata only; no transcript/full text was obtained and no record was added to the corpus. Batch report: 1 candidate, 0 verified, 1 restricted.
- [x] Refresh delivery outputs after the preceding duplicate-count update; formal corpus remains 236 unique materials and candidate status totals are 423 (246 verified, 123 pending, 54 restricted).

## Batch 209: Johnson's China and Vietnam press conference

**Files:** `data/candidates-johnson-news-conference-china-vietnam-1965.csv`, `data/reviews/johnson-china-vietnam-news-conference-1965-20261107.json`, `src/research_crawler/reviewed_sources.py`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `data/research.sqlite3`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Discover and retrieve the APP original with Scrapy under `ROBOTSTXT_OBEY`; robots and page returned HTTP 200.
- [x] Verify title, author, visible publication date, matching structured timestamp, and the complete 30,913-character body across 135 paragraphs.
- [x] Confirm direct China relevance in both the presidential statement and a reporter's question. Correct the discovery-year label to 1965 using the original page.
- [x] Add a URL-specific reviewed abstract and body-grounded keywords; test exact-URL behavior while unreviewed APP documents remain unchanged.
- [x] Add 1 unique verified material. Batch 209 reports 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh the Excel and delivery ZIP; verify 237 workbook rows and exact nine columns, 67 body sidecars, 251 evidence files, and valid ZIP CRC.
- [x] Run the full test suite (204 passed) and `scrapy check`.

## Batch 210: Kennedy-Republic of China joint statement

**Files:** `data/candidates-kennedy-roc-un-representation-1961.csv`, `data/reviews/kennedy-roc-un-joint-statement-1961-20261107.json`, `src/research_crawler/reviewed_sources.py`, `tests/test_spider.py`, `data/research.sqlite3`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Discover and retrieve the APP source page under `ROBOTSTXT_OBEY`; robots and source page returned HTTP 200.
- [x] Verify the source-visible date and matching structured date (1961-08-02), title, author, and the complete 5,081-character body across ten paragraphs.
- [x] Confirm the statement directly addresses China representation at the United Nations and U.S. opposition to admission of the Chinese Communist regime.
- [x] Add a URL-specific reviewed abstract and body-grounded keywords; test the exact source mapping.
- [x] Add one unique verified material. Batch 210 reports 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh Excel and delivery ZIP; verify 238 workbook rows and exact nine columns, 67 body sidecars, 252 evidence files, and valid ZIP CRC.
- [x] Run the full test suite (205 passed) and `scrapy check`.

## Batch 211: China Leadership Monitor strategic competition article

**Files:** `data/candidates-clm-ryan-hass-china-strategic-competition-2021.csv`, `data/reviews/clm-ryan-hass-strategic-competition-2021-20261107.json`, `src/research_crawler/reviewed_sources.py`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `data/research.sqlite3`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Discover the original China Leadership Monitor article and retrieve it with Scrapy under `ROBOTSTXT_OBEY`; robots and source page returned HTTP 200.
- [x] Verify the source-visible date (2021-03-01), author, title, and body; record that the JSON-LD UTC timestamp falls on the next calendar day without inferring a timezone conversion.
- [x] Extract the 109-paragraph, 41,612-character article body, exclude PDF controls, photo credit and page tags, and pin the exact URL to the reviewed body SHA-256.
- [x] Add regression tests for body boundaries and rejection of changed dates, authors, and body text.
- [x] Add one unique verified material. Batch 211 reports 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh Excel and delivery ZIP; verify 239 workbook rows, exactly nine columns, 68 body sidecars, 275 evidence files, and valid ZIP CRC.
- [x] Run the full test suite (206 passed) and `scrapy check` (0 contracts, OK).

## Batch 212: Carnegie U.S.-China relations report

**Files:** `data/candidates-carnegie-us-china-2030s-2024.csv`, `data/reviews/carnegie-us-china-2030s-2024-20261107.json`, `src/research_crawler/reviewed_sources.py`, `src/research_crawler/spiders/government.py`, `tests/test_spider.py`, `data/research.sqlite3`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Discover the Carnegie original page with Firecrawl, then retrieve it with Scrapy under `ROBOTSTXT_OBEY`; robots and source page returned HTTP 200.
- [x] Verify visible title, 14-author byline, publication date and matching citation/JSON-LD metadata.
- [x] Extract all 12 report sections with headings, paragraphs and notes; exclude table-of-contents/navigation, author biography panels and the institution disclaimer. Verify the 531-block, 330,934-character body SHA-256.
- [x] Add exact-URL regression coverage for metadata agreement, report boundaries and rejection of changed date, authors or body text.
- [x] Add one unique verified material. Batch 212 reports 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh Excel and delivery ZIP; verify 240 workbook rows, exactly nine columns, 69 body sidecars, 276 evidence files, and valid ZIP CRC.
- [x] Run the full test suite (207 passed) and `scrapy check` (0 contracts, OK); SQLite integrity and foreign-key checks pass.

## Batch 213: USCC hearing transcript date review

**Files:** `data/candidates-uscc-chinese-view-strategic-competition-transcript-2020.csv`, `data/reviews/uscc-chinese-view-strategic-competition-transcript-2020-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover and retrieve the official 218-page transcript PDF under `ROBOTSTXT_OBEY`; robots and PDF returned HTTP 200.
- [x] Compare the PDF cover and PDF CreationDate with the official hearing page. The cover date is the hearing date; the creation property is not a source-issued publication date.
- [x] Keep 1 candidate pending because the official page does not establish an exact publication day and the parser did not verify a complete, attributable full-text material. Add no formal table row.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed.

## Batch 214: USCC official hearing page date review

**Files:** `data/candidates-uscc-chinese-view-strategic-competition-page-2020.csv`, `data/reviews/uscc-chinese-view-strategic-competition-source-page-2020-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Retrieve the exact official event page with Scrapy under `ROBOTSTXT_OBEY`; robots and page returned HTTP 200.
- [x] Verify that “Wednesday, June 24, 2020” is shown as the hearing date in the agenda; the page exposes no precise publication day or author.
- [x] Keep 1 candidate pending and exclude the agenda page from the formal materials table.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed.
- [x] Refresh delivery reports and verify the current pending counts are represented; recheck the 240-row, nine-column workbook, candidate counts, and ZIP CRC.

## Batch 215: OUP article access review

**Files:** `data/candidates-oup-strategic-competition-us-china-2023.csv`, `data/reviews/oup-strategic-competition-us-china-2023-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the OUP article as a relevant research-literature lead and request its exact publisher page with Scrapy under `ROBOTSTXT_OBEY`.
- [x] Confirm robots.txt returned HTTP 200 and the original source page returned HTTP 403.
- [x] Do not use login or alternate access methods; keep the candidate restricted and exclude search-result excerpts from formal metadata/body.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed.
- [x] Refresh delivery reports and verify current candidate status counts, workbook schema and ZIP CRC.

## Batch 216: Nature Portfolio article access review

**Files:** `data/candidates-nature-china-us-national-military-image-2025.csv`, `data/reviews/nature-china-us-national-military-image-2025-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the Nature Portfolio article as an academic-literature lead and request the exact page under `ROBOTSTXT_OBEY`.
- [x] Record HTTP 406 from both robots.txt and the source page; do not retry with alternate request methods.
- [x] Keep the candidate pending because 406 does not establish whether the page is access-restricted; exclude search excerpts from formal metadata and body.
- [x] Report 1 candidate, 0 verified, 1 pending, 0 restricted/duplicate/unprocessed.
- [x] Refresh delivery reports and verify current candidate status counts, workbook schema and ZIP CRC after batches 217-220.

## Batch 217: RAND 2025 AI competition report access review

**Files:** `data/candidates-rand-us-china-ai-competition-2025.csv`, `data/reviews/rand-us-china-ai-competition-2025-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the RAND report as a relevant 2017-2025 research lead; treat search output as discovery only.
- [x] Request the official RAND landing page under `ROBOTSTXT_OBEY`; robots.txt and source page returned HTTP 403.
- [x] Keep 1 candidate restricted; add no formal metadata/body from search excerpts.
- [x] Report 1 candidate, 0 verified, 1 restricted, 0 pending/duplicate/unprocessed.

## Batches 218-219: USCC 2025 annual report date and body review

**Files:** `data/candidates-uscc-2025-annual-report-page.csv`, `data/candidates-uscc-2025-annual-report-pdf.csv`, `data/reviews/uscc-2025-annual-report-page-20261107.json`, `data/reviews/uscc-2025-annual-report-pdf-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Retrieve the official report page and PDF with Scrapy under `ROBOTSTXT_OBEY`; robots and both sources returned HTTP 200.
- [x] Distinguish year-level JSON-LD publication metadata and the hidden livestream `contentDate` from an exact report publication date; do not use the transmittal-letter date as a substitute.
- [x] Inspect the 745-page PDF. Generic extraction produced 2,438,530 characters but emitted an XForm decoding warning and yielded no text on 14 pages; do not certify the body complete.
- [x] Keep both records pending and exclude them from the nine-column formal materials table.
- [x] Report one pending candidate in each batch; no verified material added.

## Batch 220: Air University article retrieval review

**Files:** `data/candidates-air-university-deep-bench-2025.csv`, `data/reviews/air-university-china-deep-bench-2025-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the 2025 Strategic Horizons article as a relevant public research lead.
- [x] Request the official PDF under `ROBOTSTXT_OBEY`; connection failures prevented retrieval of robots.txt and the source PDF.
- [x] Do not retry through another route; retain the candidate as unprocessed rather than inferring a restriction.
- [x] Report 1 candidate, 0 verified, 1 unprocessed.
- [x] Refresh final delivery and verify workbook schema, candidate counts and ZIP CRC after batches 221-222.

## Batches 221-222: 2025 U.S. public diplomacy and Senate hearing leads

**Files:** `data/candidates-state-acpd-prc-public-diplomacy-2025.csv`, `data/candidates-senate-hearing-china-behavior-2025.csv`, `data/reviews/state-acpd-prc-public-diplomacy-2025-20261107.json`, `data/reviews/senate-hearing-china-behavior-2025-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the State Department meeting minutes and Senate hearing transcript as relevant official-source leads.
- [x] Request both originals under `ROBOTSTXT_OBEY`; State Department robots/page returned HTTP 403, and Congress.gov robots.txt explicitly disallowed its transcript page.
- [x] Do not use search excerpts as formal fields/body or try another route; note that 2025-10-07 is an event date only.
- [x] Report one restricted candidate in each batch; add no verified material.
- [x] Refresh the delivery after batches 221-223 and reverify counts, nine-column workbook, 69 body attachments, 276 evidence files, 222 batch reports and ZIP CRC; full test suite passes (207), `scrapy check` is OK, and SQLite integrity/foreign keys pass.

## Batch 223: AP 2025 trade-war reporting access review

**Files:** `data/candidates-ap-us-china-trade-war-2025.csv`, `data/reviews/ap-us-china-trade-war-2025-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the AP original article as a relevant 2017-2025 major-media lead; treat the search excerpt as discovery only.
- [x] Request the exact AP page under `ROBOTSTXT_OBEY`; robots.txt returned HTTP 200 and the page returned HTTP 403.
- [x] Do not use alternate access methods; keep the candidate restricted and exclude all search-result text from formal fields/body.
- [x] Report 1 candidate, 0 verified, 1 restricted.
- [x] Refresh delivery and confirm the 240-row nine-column workbook, current candidate counts, batch report, attachment/evidence counts and ZIP CRC.

## Batches 224-226: Brookings Taiwan discourse and public opinion

**Files:** `data/candidates-brookings-beijing-trump-bait-2026.csv`, `data/candidates-brookings-taiwan-baseline-2026.csv`, `data/candidates-brookings-public-opinion-taiwan-2025.csv`, `data/reviews/brookings-beijing-trump-bait-2026-20261107.json`, `data/reviews/brookings-taiwan-baseline-2026-20261107.json`, `data/reviews/brookings-chinese-public-opinion-taiwan-2025-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Retrieve all three original Brookings pages under `ROBOTSTXT_OBEY`; robots and pages returned HTTP 200.
- [x] Exclude the 2026-09-09 and 2026-03-20 articles as outside the requested period.
- [x] Verify the 2025-12-18 article title, visible publication date, two-author byline, publisher abstract, and complete 8,361-character body against the original page; record body SHA-256 `278f008504ea5423902c2e274bf7601e56c326cf7c9ed363437f33098d35df7a`.
- [x] Add one unique verified material. Batch 226 reports 1 candidate, 1 verified, 0 pending/restricted/duplicate/unprocessed.
- [x] Refresh final delivery and verify the 241-row nine-column workbook, 69 body attachments, 277 evidence files, 225 batch reports and ZIP CRC; full test suite passes (207), `scrapy check` is OK, and SQLite integrity/foreign keys pass.

## Batches 227-237: Coverage, access reviews and historical transcript

**Files:** `data/reviews/`, `data/research.sqlite3`, `data/evidence/`, `data/materials.xlsx`, `data/materials-delivery.zip`

- [x] Add the verified 2025 CSIS article in batch 227; recheck CNN, AP and Reuters originals in batches 228-231 and preserve robots/403 restrictions without using snippets as body text.
- [x] Check research-literature, RAND, ERIC and Foreign Affairs leads in batches 232-236; retain records as restricted or pending where full-text access, exact publication date, or source relevance is not established.
- [x] Recheck the USC-hosted Nixon press-conference transcript. Preserve it as pending because its displayed date is the event date and does not establish the USC page publication date.
- [x] Add the 1972-02-10 Nixon news-conference transcript from The American Presidency Project as one verified government material. Scrapy fetched the permitted source page under `ROBOTSTXT_OBEY`; the source adapter verified its page title, exact date, author/citation and complete body. Add a reviewed, body-grounded abstract and keywords for this exact URL.
- [x] Rebuild and verify the 243-row, nine-column workbook; long-body sidecar, provenance evidence, batch reports, coverage audit and ZIP CRC. Full suite passes (220), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [ ] Continue the six applicable period/category gaps without verified full text: 1949-1972 media, think tank and research literature; 1972-1991 think tank and research literature; and 1992-2016 new media. Do not treat search snippets, event dates, or restricted copies as verified materials.

## Batches 238-239: Official social post access and White House transcript

**Files:** `data/reviews/obama-whitehouse-x-us-china-cooperation-2015-20261107.json`, `data/reviews/obama-xi-arrival-remarks-2015-09-25-20261107.json`, `data/research.sqlite3`, `data/evidence/`

- [x] Discover the NARA-maintained @ObamaWhiteHouse X post and test the original URL with Scrapy. Robots.txt disallows the page, so retain it as restricted and exclude Firecrawl-transformed text from the formal corpus.
- [x] Retrieve the distinct White House archive arrival-ceremony transcript under `ROBOTSTXT_OBEY`; verify the visible date, title, publisher and complete 6,396-character text.
- [x] Add a body-grounded abstract and keywords for that exact archived transcript URL; preserve author as `未注明` because the source page has no author byline.
- [x] Audit all verified materials for blank summary/keyword fields and save an itemized repair queue in `data/reviews/field-completeness-20261107.json` (93 empty summaries, 109 empty keyword fields across 109 records).
- [x] Verify the current 244-row nine-column workbook, 70 long-body sidecars, 271 formal evidence files, 148 review files, 238 batch reports, 3 index/audit reports and ZIP CRC; full suite passes (221), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [ ] Audit and remediate legacy empty fields from their original source evidence. Current database audit finds 93 empty abstracts and 109 empty keyword fields; no placeholders may be used.
- [x] Remediate nine high-relevance American Presidency Project records by recrawling the original pages through Scrapy and recording source-grounded abstracts/keywords in exact verification snapshots. No material rows were added; blank legacy fields decrease to 84 abstracts and 100 keyword fields. See `data/reviews/presidency-metadata-repair-1949-1991-20261107.json`.
- [x] Refresh delivery and verify the unchanged 244-row, nine-column workbook, 70 long-body sidecars, 271 formal evidence files, 150 review files, 238 batch reports, 3 index/audit reports and ZIP CRC; full suite passes (223), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Re-crawl four Clinton White House archive pages (1997-2000) and fill body-grounded summaries/keywords for exact source URLs. Preserve all four existing verified records; correct the visible multi-line WTO article title and cover it with a regression test. Record audit in `data/reviews/clinton-whitehouse-metadata-repair-1997-2000-20261107.json`.
- [x] Refresh the itemized completeness audit: 244 verified materials, 80 empty abstracts, 96 empty keyword fields, and 96 records with at least one blank field. Full suite passes (223), `scrapy check` is OK, and SQLite integrity/foreign-key checks pass.
- [ ] Continue the remaining legacy-field repair queue, now listing 96 records with at least one empty summary/keyword field.
- [x] Re-crawl the five existing 1979-1984 American Presidency Project pages about Deng Xiaoping's visit, cultural exchange and the Fudan University address in their existing batch. Add exact-URL, body-reviewed summaries and keywords; add no candidate or material rows. Audit in `data/reviews/deng-cultural-exchange-metadata-repair-1979-1984-20261107.json`.
- [x] Refresh field completeness: 244 verified materials, 75 empty abstracts, 91 empty keyword fields, 91 records with at least one blank. Full suite passes (224), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Rebuild and inspect the delivery ZIP: 244 workbook rows with exact nine columns; 70 long-body attachments, 271 evidence files, 151 review files, 238 batch reports, 3 index/audit reports; all five repaired rows have summaries and keywords; JSON audit parses and ZIP CRC passes.
- [ ] Continue the remaining legacy-field repair queue, now listing 91 records with at least one empty summary/keyword field.
- [x] Re-crawl seven existing 1989-1990 Bush administration records in their existing candidate batches, including the Bush41 Library sanctions statement. Add exact-URL body-reviewed summaries and keywords; do not add candidate or material rows. Audit in `data/reviews/bush-tiananmen-metadata-repair-1989-1990-20261107.json`.
- [x] Refresh completeness: 244 verified materials, 68 empty abstracts, 84 empty keyword fields, 84 records with at least one blank. Full suite passes (226), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Rebuild and inspect delivery: 244 workbook rows with the exact nine columns, all seven repaired rows have summaries and keywords, 70 body attachments, 271 evidence files, 152 review files, 238 batch reports, 3 index/audit reports, and a valid ZIP CRC.
- [ ] Continue the remaining legacy-field repair queue, now listing 84 records with at least one empty summary/keyword field.
- [x] Re-crawl the 1949 Truman news conference and three 1950 Korea statements through Scrapy under `ROBOTSTXT_OBEY`, reusing their existing candidate batches. Add exact-URL body-reviewed summaries/keywords; no candidate or material rows added. Audit in `data/reviews/truman-china-korea-metadata-repair-1949-1950-20261107.json`.
- [x] Refresh completeness: 244 verified materials, 64 empty abstracts, 80 empty keyword fields, and 80 records with at least one blank. Full suite passes (227), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Rebuild and inspect delivery: 244 workbook rows with the exact nine columns, all four repaired rows have summaries and keywords, 70 body attachments, 271 evidence files, 153 review files, 238 batch reports, 3 index/audit reports, and a valid ZIP CRC.
- [ ] Continue the remaining legacy-field repair queue, now listing 80 records with at least one empty summary/keyword field.
- [x] Re-crawl the seven 1994-1996 Clinton MFN records in their existing candidate batches. Add exact-URL body-reviewed summaries/keywords for the press conference, memoranda, administration positions and House vote statement. No new candidates or materials. Audit in `data/reviews/clinton-mfn-metadata-repair-1994-1996-20261107.json`.
- [x] Refresh completeness: 244 verified materials, 57 empty abstracts, 73 empty keyword fields, and 73 records with at least one blank. Full suite passes (228), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Rebuild and inspect delivery: 244 workbook rows with exactly nine columns; all seven repaired rows have summaries and keywords; 70 body attachments, 271 evidence files, 154 review files, 238 batch reports, 3 index/audit reports, and valid ZIP CRC.
- [ ] Continue the remaining legacy-field repair queue, now listing 73 records with at least one empty summary/keyword field.
- [x] Re-crawl six 1999-2000 Clinton NTR/WTO/PNTR records in their existing candidate batches. Add exact-URL body-reviewed summaries and keywords; do not add candidates or materials. Audit in `data/reviews/clinton-wto-pntr-metadata-repair-1999-2000-20261107.json`.
- [x] Refresh completeness: 244 verified materials, 51 empty abstracts, 67 empty keyword fields, and 67 records with at least one blank. Full suite passes (229), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Rebuild and inspect delivery: 244 workbook rows with exactly nine columns; all six repaired rows have summaries and keywords; 70 body attachments, 271 evidence files, 155 review files, 238 batch reports, 3 index/audit reports, valid ZIP CRC.
- [ ] Continue the remaining legacy-field repair queue, now listing 67 records with at least one empty summary/keyword field.
- [x] Re-crawl three existing historical American Presidency Project records: Nixon's 1972 Dan Rather interview, the 1987 China acid-import memorandum and the 1988 Republican Party platform. Add exact-URL body-reviewed summaries and keywords without adding candidate/material rows. Audit in `data/reviews/nixon-reagan-republican-china-records-metadata-repair-1972-1988-20261107.json`.
- [x] Refresh completeness: 244 verified materials, 48 empty abstracts, 64 empty keyword fields, and 64 records with at least one blank. Full suite passes (230), `scrapy check` is OK, and SQLite integrity/foreign keys pass.
- [x] Rebuild and inspect delivery: 244 workbook rows with exact nine columns; all three repaired rows have summaries/keywords; 1988 platform body is a verified relative sidecar (234,842 source characters / 235,786 UTF-8 bytes); 70 body attachments, 271 evidence files, 156 review files, 238 batch reports, 3 index/audit reports and valid ZIP CRC.
- [ ] Continue the remaining legacy-field repair queue, now listing 64 records with at least one empty summary/keyword field.
- [ ] Continue the six applicable period/category gaps without verified full text: 1949-1972 media, think tank and research literature; 1972-1991 think tank and research literature; and 1992-2016 new media.
- [x] Re-crawl five 2009-2010 Obama White House records in existing batch 129. Repair summaries/keywords with exact-URL provenance. The joint statement needs no transcript END marker: accept its reviewed date/title/full-body hash, and reject changed/truncated copies. All five bodies match older source captures. Audit: `data/reviews/obama-china-metadata-repair-2009-2010-20261107.json`.
- [x] Refresh completeness to 43 empty abstracts / 59 empty keywords out of 244 records. Run 232 tests, Scrapy check, SQLite integrity/foreign keys. Inspect local and ZIP workbooks for 244 rows and exact nine columns; five repaired rows complete. ZIP: 740 files, including 70 body attachments, 271 evidence files, 157 reviews, 238 batch reports and 3 index/audit reports; CRC valid.
- [ ] Continue 59 remaining records with empty fields and the six source-coverage gaps; do not claim the corpus exhaustive or complete.
- [x] Repair five 2011/2016 State Department records using their original stored allowed HTML evidence; verify raw hashes and unchanged title/date/author/body before updating summaries/keywords. Re-crawl attempts returned HTTP 200 error pages with Exception: forbidden, so retain restricted status and original evidence capture IDs/times. Audit: `data/reviews/state-china-metadata-repair-2011-2016-20261107.json`.
- [x] Exclude flex-video player controls from archived State body extraction; original 2016 transcript remains 47,368 characters. Tests cover source provenance, unreviewed URLs and video UI exclusion. Full suite 234 passes; Scrapy check OK. Database integrity/foreign keys pass. Local and packaged workbooks: 244 rows, exactly nine columns, five repaired records populated. Package has 741 files, 70 body sidecars, 271 evidence files, 158 reviews and 238 batch reports; CRC valid.
- [ ] Continue 54 remaining field-repair records (38 empty abstracts, 54 empty keywords) and six source-coverage gaps. Corpus remains incomplete.
- [x] Withdraw material 177: GEC 2023 report landing page was only an executive summary plus download menu. Preserve prior record/raw evidence in withdrawal audit, mark candidate pending, exclude from workbook/provenance index. Reject such State landing pages as full reports. Official PDF recheck returned HTTP 200 forbidden HTML; classify restricted and source_text instead of PDF. Audit: `data/reviews/gec-executive-summary-withdrawal-20261107.json`.
- [x] Verify 236 tests, Scrapy check, SQLite integrity and foreign keys. Refresh coverage matrix: six gaps persist. Verify local/ZIP workbooks both contain 243 records and exact nine columns, withdrawal absent, provenance index 243 records, ZIP CRC valid. ZIP: 741 files, 70 body attachments, 270 evidence files, 159 reviews, 238 batch reports and 3 index/audit reports.
- [ ] Continue the 53 records with missing fields (37 empty abstracts / 53 empty keywords); also audit remaining legacy bodies for excerpt/summary/template contamination and continue six coverage gaps. Corpus is not complete.
- [x] Withdraw four hearing/podcast landing pages (materials 33, 35, 44, 149), preserving prior records/raw evidence. House hearing adapter now verifies announcement metadata without treating witness lists as full transcripts; regression tests include actual 2018 HTML and an existing Brookings podcast excerpt that current extraction rejects.
- [x] Recheck the 2018 official transcript under ROBOTSTXT_OBEY: PDF HTTP 200, robots 404, 60 pages with extracted text. Keep pending: hearing date and 2018 publication year do not prove exact publication day. Discover two linked Brookings transcripts in batch 240: one verified nine-page Prasad transcript (2019-11-25, 27,582 chars); Huang transcript remains pending because PDF/page titles differ. Audit: `data/reviews/hearing-podcast-landing-withdrawals-20261107.json`.
- [x] Verify 238 tests, Scrapy check and SQLite integrity/foreign keys. Rebuild/inspect local and ZIP workbooks: 240 rows, exact nine columns, four withdrawn URLs absent, actual transcript present; 240 provenance entries, valid ZIP CRC. Package: 741 files, 70 body attachments, 268 raw evidence files, 160 reviews, 239 batch reports, 3 index/audit reports.
- [ ] Continue 52 field-repair records (36 empty abstracts / 52 empty keywords), legacy body audits, Huang PDF title/date review, and six period/source gaps. Do not claim exhaustive coverage.
- [x] Resolve Huang transcript title/date provenance without rewriting the title: PDF cover title retained, original linked page publication date 2019-06-24 verified, 14 pages/24,954 characters. Exact reviewed URL/page headline/date/PDF hash/body hash gates permit this source-specific correspondence; all Brookings PDF records now require the declared page to actually link their PDF. New source test rejects an unlinked page. Audit: `data/reviews/brookings-huang-transcript-2019-20261107.json`.
- [x] Re-crawl under ROBOTSTXT_OBEY: robots/page/PDF HTTP 200. New material 293 uses evidence 839 plus metadata evidence 838; no new candidates or duplicates. Full tests 239 pass, Scrapy check OK, SQLite integrity/foreign keys pass. Local and ZIP workbooks have 241 records, exactly nine columns, PDF title/date/full body retained; provenance index 241; CRC valid. ZIP: 744 files, 70 long-body attachments, 270 evidence files, 161 reviews, 239 batch reports and 3 index/audit reports.
- [ ] Continue 52 field-repair records (36 empty abstracts / 52 empty keywords), legacy body audit, exact publication date for the 2018 hearing, and six period/source coverage gaps.
- [x] Repair nine 2022-2024 State Department summaries/keywords from existing original HTML; verify unchanged source/date/author/title/body, retain original evidence IDs/times and claim no new retrieval. Bind reviewed fields to exact URL/full-body SHA-256; tests reject changed bodies and unrelated URLs. Audit: `data/reviews/state-metadata-repair-2022-2024-20261107.json`.
- [x] Refresh completeness: 241 materials, 27 empty abstracts, 43 empty keywords. Full tests 240 pass, Scrapy check OK, SQLite integrity/foreign keys pass. Local/ZIP workbooks both have 241 rows and exact nine columns; all nine repaired field pairs match audit; provenance 241 and ZIP CRC valid. Package: 745 files, 70 body attachments, 270 evidence files, 162 reviews, 239 batch reports and 3 index/audit reports.
- [ ] Continue 43 remaining field-repair records, legacy full-text audits, exact hearing publication date and six period/source coverage gaps. Corpus remains incomplete.

- [x] Repair missing keywords for six existing research articles using original HTML/PDF and publisher-page evidence. Exact URL/body SHA-256 required; publisher keywords take priority. Preserve source/date/author/title/publisher abstract/body and original evidence IDs/times; no new network request. Each derived keyword has a body excerpt. Flag the existing PMC retraction notice for material 119 in the separate audit without changing the nine-column schema. Audit: `data/reviews/research-literature-keywords-repair-20261107.json`.
- [x] Verify 241 tests, Scrapy check (0 contracts), SQLite integrity/foreign keys, local and ZIP workbooks (241 records, exactly nine columns), repaired keywords/publisher abstracts and ZIP CRC. Package: 746 files, 70 body attachments, 270 raw evidence files, 163 reviews, 239 batch reports and 3 index/audit reports.
- [ ] Continue 37 records with missing fields (27 empty abstracts, 37 empty keywords), legacy body/date audits and six coverage gaps. Corpus remains incomplete.

- [x] Correct Brookings JSON-LD taxonomy/program/format keyword contamination for nine existing records, preserving source/date/author/title/publisher abstract/body. Exact URL/full-body hashes gate reviewed body-derived themes; old keywords and verbatim keyword evidence retained in audit. Test unknown/changed bodies receive no reviewed keywords.
- [x] Withdraw legacy material 36 (14,766-character condensed report page) and replace it with material 294: official 25-page/80,921-character PDF in batch 241, page/PDF/robots HTTP 200 under ROBOTSTXT_OBEY. Exact publication 2019-02-28 and authors/title verified against directly linked page. A source-specific raw/body hash gate admits the reviewed PDF without a first-page institution marker; truncated files are rejected. Batch: 1 verified / 0 pending / 0 restricted / 0 duplicate. Audit: `data/reviews/brookings-keywords-and-full-brief-repair-20261107.json`.
- [x] Verify 243 tests, Scrapy check (0 contracts), SQLite integrity/foreign keys, six remaining coverage gaps. Inspect both workbooks: 241 rows, exact nine columns, condensed URL absent, full PDF present; every body and nonempty field matches DB; all 241 provenance entries/evidence hashes and ZIP CRC pass. Package: 750 files, 71 full-body sidecars, 271 evidence files, 164 reviews, 240 batch reports and 3 index/coverage reports.
- [ ] Continue 37 records with missing fields (27 empty abstracts, 37 empty keywords), legacy body/date audits and six coverage gaps. Goal remains active; do not claim exhaustive coverage.

- [x] Repair six CSIS records missing keywords from stored allowed source HTML/PDF. Exact URL + complete extracted-body SHA-256 gates each set; every keyword has a supporting body excerpt. Publisher abstracts and all source metadata retained; category tags are no longer treated as themes.
- [x] Correct reading order of a reviewed 10-page CSIS two-column PDF cover: coordinate-order cover/title/byline/date/issue box, then original article-column stream; omit repeated page furniture. Compare extracted words with the source and reject truncated PDF by exact raw hash/page count. No network retrieval claimed. Audit: `data/reviews/csis-keywords-and-pdf-order-repair-20261107.json`.
- [x] Verify 246 tests; Scrapy check OK (0 contracts); SQLite integrity/foreign keys; refresh six remaining coverage gaps. Inspect local/package workbooks: 241 rows, exact nine columns, all material fields and full body text/sidecars match DB. Verify all 241 provenance records and source evidence hashes plus ZIP CRC. Delivery: 751 files (71 body sidecars, 271 evidence, 165 reviews, 240 batch reports, 3 index/coverage reports, workbook).
- [ ] Continue 31 records with empty fields (27 abstracts, 31 keywords), legacy body/date audits and six period/source gaps; corpus is not exhaustive.

- [x] Reparse seven additional American Presidency Project records from 1992-2023 with exact URL and complete extracted-body SHA-256 gates; preserve source metadata and full bodies. Audit: `data/reviews/presidency-additional-metadata-repair-1992-2023-20261107.json`.
- [x] Reparse the two remaining Trump White House records from 2018-2019 with exact URL and complete extracted-body SHA-256 gates; preserve source metadata and full bodies. Audit: `data/reviews/trump-whitehouse-metadata-repair-2018-2019-20261107.json`.
- [x] Refresh completeness and delivery: 241 verified materials, zero empty abstracts/keywords/body fields, 254 tests passed, `scrapy check` OK, exact nine-column workbook, 71 long-body sidecars, 271 evidence files, 172 review files, 240 batch reports, three index/coverage reports, and ZIP CRC valid.
- [ ] Continue the six period/source coverage gaps and legacy body/date audits; do not claim exhaustive coverage.

- [x] Add a reviewed Obama White House video-transcript adapter and promote three existing 2009-2013 video candidates using exact page title/date and complete extracted-body SHA-256 gates. Preserve prior incomplete evidence rows and add complete evidence snapshots. Audit: `data/reviews/obama-whitehouse-video-transcripts-2009-2013-20261107.json`.
- [x] Refresh coverage and delivery state: 244 verified materials, no empty abstract/keyword/body fields, 255 tests passed, `scrapy check` OK, 72 long-body sidecars, 274 evidence files, 173 review files, and the `1992-2016/new_media` verification gap closed.
- [ ] Continue the five remaining verification gaps (early media, early think-tank and research-literature sources) and legacy body/date audits; do not claim exhaustive coverage.

- [x] Promote the existing public VOA Office of Public Relations archive page “VOA's Mission in the 1960s and 1970s” using the saved allowed HTML, exact visible date/source/title/body checks and a complete evidence snapshot. Audit: `data/reviews/insidevoa-mission-2007-promotion-20261107.json`.
- [x] Refresh delivery: 245 verified materials, 256 tests passed, 72 long-body sidecars, 275 evidence files, 174 review files, and ZIP CRC valid; five early-period verification gaps remain.
- [x] Promote three existing public PMC research articles from 2020-2024 with exact publication date, publisher metadata and complete body checks. Audit: `data/reviews/pmc-research-promotion-2021-2024-20261107.json`.
- [x] Refresh delivery: 248 verified materials, 257 tests passed, 75 long-body sidecars, 278 evidence files, 175 review files, and ZIP CRC valid; five earlier-period verification gaps remain.
- [x] Run a lawful follow-up for the five remaining early coverage cells: add the public Columbia/CIAO, U.S. Naval Institute, and JSTOR candidates, preserve exact pending/restricted outcomes, and write batch reports 242-244 without promoting unverified text.
- [x] Refresh delivery after batches 242-244: 248 verified materials, 257 tests passed, 75 long-body sidecars, 278 evidence files, 175 review files, 775 ZIP files, and valid ZIP CRC; five early verification gaps remain.
- [ ] Continue searching for lawful full texts with source-displayed YYYY-MM-DD publication dates in the five early cells; current formal corpus remains incomplete.

## Follow-up: 2026-11-08 early retry and balanced open-literature batches

- [x] Re-fetch the 91 existing 1949-1991 pending candidates under Scrapy robots compliance and the fast profile. The crawl received 94 HTTP 200 page responses, 6 HTTP 404 responses, 2 HTTP 420 responses, and 1 connection with no response; none of the rechecked early materials passed the full-text promotion gate. Do not count accepted Scrapy items as verified materials.
- [x] Recheck Daily Iowan historical PDF candidates and existing 1994-2012 White House / 2002-2020 VOA candidates. These runs produced no new unique formal records; retained pending and duplicate states.
- [x] Crawl targeted open-research candidates across both post-1991 periods. Promote only after the source pages passed exact date, metadata, and complete-body checks: 3 new materials dated 1992-2016 and 4 dated 2017-2025.
- [x] Refresh the formal-record count and field audit: 2,453 unique materials, with no blank abstracts, keywords, or bodies and no invalid publication dates. Counts by publication date: 1949-1972 40; 1973-1991 25; 1992-2016 694; 2017-2025 1,694. Current candidate status totals: 2,492 verified candidates (including duplicate discoveries), 560 pending, 99 restricted, 90 excluded, and 3 candidate.
- [x] Re-export the workbook after detecting the prior 2,446-row workbook lagged the 2,453-row database, rebuild the delivery ZIP, and verify 2,453 workbook rows, exact nine-column headers, SQLite integrity and foreign keys, and ZIP CRC.
- [ ] Continue early media / think-tank / research-literature discovery while maintaining parallel collection for 1992-2025 sources; do not claim exhaustive coverage.

## Follow-up: 2026-11-08 PMC 2017-2025 queue

- [x] Re-fetch the targeted 118-row PMC media/research candidate CSV with robots compliance and the polite fast profile. Skip 38 already-verified source URLs; fetch 80 candidates, all with HTTP 200 responses and accepted page items.
- [x] Promote 54 additional unique full-text research materials after the source date, metadata, and complete body checks passed. The remaining fetched items did not add unique formal rows. Current total: 2,507 unique materials; the 2017-2025 period has 1,748 records.
- [x] Reconcile final candidate statuses after this batch: 2,546 verified candidates (including duplicates), 569 pending, 99 restricted, 27 excluded, and 3 candidate. Refresh workbook, coverage audit and delivery ZIP before reporting these totals.
- [x] Verify the regenerated workbook has 2,507 data rows and exactly the required nine columns; abstracts, keywords and bodies are nonempty for every row. SQLite integrity passes with zero foreign-key errors; all 7,846 ZIP entries pass CRC validation.
- [ ] Continue early-period discovery and concurrent 1992-2025 source collection. The volume goal has been reached; quality, source balance and unresolved access gaps remain active.

## Follow-up: 2026-11-08 expanded discourse search

- [x] Re-crawl the expanded 1949-1960 GovInfo broadcasting candidate set. Three public PDFs returned HTTP 200, including a roughly 51 MB Congressional Record volume; no new unique complete single-material text passed verification. A second 1966 volume of roughly 55 MB remained in transfer for several minutes and was stopped; retain it as unresolved and retry only through a more granular lawful source representation.
- [x] Screen an expanded 2017-2025 PMC search (176 candidates): 8 entered the full-text queue, 64 remain for manual review, and 104 were excluded by title/abstract metadata. Full-text rechecks added 2 unique verified records from this group.
- [x] Screen a second 2017-2025 PMC search (13 candidates): 4 entered the full-text queue, 7 remain for manual review, and 2 were excluded. A full-text recheck added 1 unique verified record.
- [x] Screen a 1992-2016 PMC discourse search (13 candidates): 11 remain for manual review because the U.S. connection is unclear or citation abstracts are missing; 2 were excluded by metadata and none entered full-text crawling. A 1973-1991 PMC search under these terms found 0 candidates.
- [x] Refresh corpus and candidate totals: 2,510 unique materials; period counts are 40 (1949-1972), 25 (1973-1991), 694 (1992-2016), and 1,751 (2017-2025). Candidate statuses: 2,550 verified, 570 pending, 99 restricted, 27 excluded, and 2 candidate. Formal records still have no blank abstracts, keywords, or bodies.
- [x] Rebuild and verify the 2,510-row nine-column workbook and delivery ZIP; SQLite integrity passes with zero foreign-key errors and all 7,855 ZIP entries pass CRC validation.
- [ ] Continue source discovery across all periods; pursue granular early primary sources and keep 1991+ media, government, think-tank and research literature in parallel. Manual-review PMC candidates must be assessed for topical relevance before any full-text crawl.
