# Exact verification provenance and cold-war collection

**Goal:** Preserve exact supporting evidence IDs and field-source URLs at each new material promotion, without inventing historic associations. Continue bounded original-source collection for the 1950s.

**Architecture:** Add verification snapshot and metadata evidence link tables. Existing materials remain legacy until explicitly reviewed again. Promotion/update saves material, field source map, abstract origin and exact supporting IDs in one transaction. Delivery prefers exact snapshots and labels legacy fallback captures honestly; it checks exact links before packaging.

**Tech stack:** SQLite, existing ResearchStore/pipeline/delivery, pytest, Scrapy, Firecrawl discovery.

- [x] Add failing tests for persistent exact links, replacement on re-verification, and excluding unrelated later captures from delivery; preserve a legacy fallback test.
- [x] Implement schema and transactional promotion snapshots; update delivery evidence selection and provenance labels.
- [x] Run focused tests and full suite; back up live database before schema migration.
- [x] Retrieve and individually review a bounded 1950s source batch, then export/verify the updated package and actual batch totals.

Historical associations must never be backfilled using guessed timestamps or latest-capture heuristics. Excel remains exactly nine columns; provenance belongs in separate reports.

Outcome: 148 full-suite tests pass and Scrapy check passes. Independent scoped review passed 34 relevant tests and found no important defects. Batch 146 adds 3 materials; two older undated records were withdrawn (explicitly assigned editorial dates), for 188 verified unique materials. Seven new/re-reviewed records have exact snapshots; 181 legacy records remain explicitly labelled. ZIP contains 55 referenced long-text files and 208 raw evidence files. Broader goal remains active.
