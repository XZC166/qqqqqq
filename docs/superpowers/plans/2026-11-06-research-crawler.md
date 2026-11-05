# Research Crawler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a resumable Scrapy-based system that discovers, legally acquires, verifies, deduplicates, and exports primary-source materials for the 1949-2025 dissertation corpus.

**Architecture:** Scrapy handles polite fetching and source adapters; a SQLite state store tracks batches, candidates, evidence, and unique materials. Only records passing explicit metadata and full-text checks can reach the nine-column Excel exporter. Authorized full texts use a separate import path, and long text is stored as UTF-8 files.

**Tech Stack:** Python 3.11+, Scrapy, openpyxl, SQLite (stdlib), pytest.

---

## File Map

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
- [x] Add an `import-firecrawl` path that accepts the configured Firecrawl tool's complete `structuredContent` capture, requires the original `rawHtml` field and matching source URL/status/scrape ID, then passes it through the same source adapter and verification pipeline.
- [x] Store retrieval method and Firecrawl scrape ID with evidence; migrate existing SQLite evidence tables with safe defaults.
- [x] Test successful capture ingestion, exact evidence bytes/hash, rejected Markdown-only/unmatched/failed captures, and legacy database migration.
- [ ] Run the importer with a saved full Firecrawl capture for the State Department live page. The MCP result was inspected in the previous batch but its raw response was not saved locally, so this live end-to-end ingestion remains unverified.
