# Verifiable corpus delivery implementation plan

**Goal:** Build a repeatable command that exports the verified corpus with exact nine-column Excel, complete long-body files, hash-checked original evidence and honest batch reports.

**Architecture:** A delivery module validates the SQLite references and raw files before staging an export in a temporary directory. It rereads every workbook row and body reference, creates a provenance index and reports, verifies the ZIP, then atomically replaces the destination ZIP. This checks stored artifacts; it does not claim to newly verify the historical source content.

**Tech Stack:** Existing ResearchStore, openpyxl, hashlib, zipfile, pathlib, pytest.

### Task 1: Delivery integrity tests
- [x] Add tests for exact nine columns, long UTF-8 text and source/metadata evidence inclusion.
- [x] Add failure tests for missing/tampered evidence, missing metadata and preservation of an existing destination archive.
- [x] Run tests and confirm the command is missing.

### Task 2: Delivery implementation
- [x] Create `src/research_crawler/delivery.py` with evidence validation, workbook verification, reports/provenance and atomic ZIP publication.
- [x] Add `deliver --db ... --output ...` to `src/research_crawler/cli.py`.
- [x] Run focused tests, then the full suite and Scrapy checks.

### Task 3: Live corpus and earlier-period batch
- [x] Retrieve bounded public original pages with the existing robots-obeying crawler; inspect dates and complete body structure before promotion.
- [x] Report actual additions and unresolved candidates. Do not interpret document dates as verified publication without source evidence.
- [x] Run the delivery command on the live database, verify ZIP contents and document invocation and remaining coverage gaps.

No automatic commit or push: the current checkout contains ongoing changes from many earlier collection batches, which must be preserved together.

## Batch 227: CSIS China’s Power Play Across the Pacific

- [x] Discover the CSIS source page for the 2017—2025 research-literature batch and record its candidate CSV.
- [x] Fetch robots.txt and the source page with Scrapy; both returned HTTP 200.
- [x] Verify the source-page date (2025-04-08), author, title, publisher abstract, visible source tags, and complete 12,576-character body against one source URL.
- [x] Store the verified material as candidate 443 / material 289 and preserve the raw evidence hash in the audit JSON.
- [x] Rebuild and verify the nine-column workbook and delivery archive after the keyword-field correction and media access audit: 242 workbook rows, 69 body sidecars, 269 evidence files, 230 batch reports, CRC pass, 214 tests pass, Scrapy checks pass, and SQLite integrity/foreign-key checks pass.

## Legacy provenance revalidation

- [x] Add a local-only `revalidate` command that reparses legacy materials from stored evidence without issuing network requests.
- [x] Promote only exact field/body matches to verification snapshots; leave mismatches and unparseable records legacy and report them separately.
- [x] Revalidate the current corpus: 122 exact, 48 mismatched, 5 unparseable; package the JSON audit and local review files with the delivery archive.
- [x] Rebuild the archive and verify 214 tests, Scrapy checks, SQLite integrity, workbook round trip, evidence hashes and ZIP CRC.

## Period/source coverage audit

- [x] Add a complete 4-period by 5-source-category matrix that includes zero-candidate cells.
- [x] Add a CLI report with candidate-state counts, unique linked material counts, and explicit no-candidate gaps.
- [x] Include the complete matrix in delivery `reports/coverage.json`; do not infer absence of relevant sources from an empty cell.
- [x] Audit current corpus: 6 cells have no candidate URLs; the two pre-2006 new-media cells are out of scope, leaving 4 applicable early-period think-tank/research-literature cells to search.
- [x] Discover and process one 2004 New York Times/Los Angeles Times China-image study candidate; publisher metadata page returned HTTP 403, so it remains restricted and outside the formal workbook.
- [x] Rebuild batch 232 delivery with 242 workbook rows, 69 body sidecars, 269 verified-material evidence files, 139 review files, 231 batch reports, ZIP CRC pass, and 218 tests pass.
- [x] Process batch 233 RAND P-6590 discovery lead under robots policy; robots.txt returned HTTP 403, no source-page request was made, and no alternate copy was established in the bounded official-domain search.
- [x] Refresh the coverage matrix: 1972—1991 think-tank now has a candidate, leaving 3 applicable zero-candidate cells; rebuild batch 233 delivery with 242 workbook rows, 69 body sidecars, 269 verified-material evidence files, 140 review files, 232 batch reports, and ZIP CRC pass.
- [x] Follow ERIC lead to the public ED073276 record and PDF; verify it is a 1973 abstract compilation, leave it pending and outside the formal workbook, and retain the 1971 Browne paper only as a lead to locate its own original full text.
- [x] Refresh coverage after batch 234: the 1972—1991 research-literature cell now has a candidate, leaving 2 applicable zero-candidate cells; package batch 234 evidence and report.
- [x] Process batch 235 CFR/Foreign Affairs 1965 article lead; publisher page returned HTTP 200 but signaled restricted access, and bounded alternate-copy discovery did not establish authorized open full text.
- [x] Refresh coverage after batch 235: 1949—1972 think-tank has a restricted candidate; only the 1949—1972 research-literature cell remains without a candidate URL.
- [x] Preserve the bounded 1949—1972 literature search and exclusions as a review audit and include it in the delivery archive; no candidate URL or verified text was added.
- [x] Add a pending 1958 Isaacs book catalog lead after fetching only the public Internet Archive catalog page under robots.txt; do not request loan/login/download content because exact publication day and permitted full-text access are unverified.
- [x] Extend coverage audit with `has_verified_materials` and a separate `verification_gaps` report so pending/restricted candidates cannot appear as completed period/category coverage.

Outcome: batch 140 added 4 materials (183 unique total). Corrected explicit attribution in 51 existing APP records and body structure in 23, with original non-whitespace character order checked. 140 tests pass; Scrapy check passes; delivery archive has 55 long bodies and 201 raw evidence files. Broader collection remains active.
