# Reviewed PBS Articles Implementation Plan

> For agentic workers: execute sequentially with the existing approved source-adapter and verification architecture.

**Goal:** Collect the five inspected pre-2017 PBS articles without treating a funding boundary alone as proof of completeness.

**Architecture:** Retain existing metadata and contributor-ending gates. Add exact reviewed URL/body fingerprints for the five fully inspected articles, preserving inline source text and article pullquotes. Unknown structures, missing ending boundaries, modified reviewed bodies and date conflicts remain pending. No general relaxation of the completeness gate.

**Tech Stack:** Python, Scrapy/parsel, hashlib, pytest, SQLite, openpyxl.

### Task 1: Capture and test

- [x] Save source-derived minimal fixtures for the five public HTTP-200 pages, retaining original metadata and article markup.
- [x] Add positive tests for original bodies, bylines, exact dates, inline punctuation and source summaries; add mutation tests for changed/missing paragraphs, boundary removal, date conflict and unknown content containers.
- [x] Run focused tests before implementation and confirm the five original pages fail for the missing reviewed-ending support.

### Task 2: Bounded adapter extension

- [x] Create `src/research_crawler/reviewed_sources.py` with URL/body-SHA256 pairs derived from the reviewed original HTML.
- [x] Modify only `PBSNewsArticleAdapter`: preserve adjacent inline text, support observed pullquote markup, exclude linked MORE recommendations, accept exact reviewed fingerprints alongside existing contributor endings.
- [x] Run focused and full tests; reparse existing stored PBS articles to check for text changes before touching existing formal rows.

### Task 3: Collect and deliver

- [x] Independently check all five source dates, bylines, titles, summaries, full paragraph sequences and final boundaries; retain original evidence hashes and Firecrawl success/failure records.
- [x] Import only reviewed materials into the main store, register actual rediscoveries, export nine columns and rebuild evidence/sidecar package.
- [x] Record actual counts, limitations and source review paths in README and the main progress plan. Keep the overall goal active while coverage gaps remain.

Outcome: five new formal articles in batch 148; 195 unique formal materials total. Preserve source text following pullquotes and br separators; reject unconsumed list content. Full suite 165 passed; Scrapy check OK; eight supported existing/current PBS records reparse exactly. One old record corrected for two parser-inserted spaces. Overall coverage remains incomplete.
