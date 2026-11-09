# 2026-11-09 continued review checkpoint 3

Snapshot: 2026-11-09 19:47:04 Asia/Singapore (11:47:04 UTC). Live crawling continues; these are immutable checkpoint counts.

The working database contains **7,014 material rows**. **1,364 unique records** satisfy the source, exact publication-day, field/body correspondence, integrity, completeness and individual topic-review gates and were exported. The other **5,650 working rows are not formal fulltexts**: 1,199 have unresolved source validation, 4,427 passed the source gate but remain pending final acceptance, and 24 newly acquired rows await source audit. Candidate status `verified` is a historical extraction status and must never be used as the formal count. The old 2,631 report is not the current fully reviewed count.

## Completed individual review batches

| Batch | Individually reviewed | New formal | Pending | Former formal withdrawn | Newly discovered candidates | Duplicate discoveries | Restricted | HTTP failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Original social posts across 18 institutional domain handles | 90 | 60 | 30 | 0 | 0 | 0 | 0 | 0 |
| Early presidential archive queue, first 50 records | 50 | 24 | 26 | 0 | 0 | 0 | 0 | 0 |
| Same queue, second 50 records | 50 | 18 | 32 | 0 | 0 | 0 | 0 | 0 |
| Total | **190** | **102** | **88** | **0** | **0** | **0** | **0** | **0** |

These batches process existing candidates and saved primary evidence; their 190 offline reviews made no additional HTTP requests. Every accepted record has a body/field fingerprint, raw evidence hash and immutable individual positive decision. Original bodies were preserved; derived summaries and body-supported keywords were corrected before acceptance. Complete single original Bluesky posts count only as posts, never as the linked article, book, report or whole thread. Video/podcast descriptions, documentary synopses, thread fragments and directory previews remain pending. X and YouTube remain separate coverage gaps.

The two early batches include interviews explaining China/Taiwan policy, the 1984 visit, communication with Fudan students, international broadcasting institutions and trade-policy messaging. Mere birthplace references, old jobs, China-shop idioms, ceremonial jokes and unsupported scope were not accepted. Multi-speaker speeches or press-secretary statements attributed solely to a president remain pending correction; diaries referring to reports or meetings are not accepted as those underlying reports or proceedings. No pending record is kept in Excel to preserve a target count.

## Formal coverage

| Period label | Actual interval | Formal |
|---|---|---:|
| 1949–1972 | 1949-01-01 through 1972-12-31 | 509 |
| 1972–1991 | 1973-01-01 through 1991-12-31 | 377 |
| 1992–2016 | 1992-01-01 through 2016-12-31 | 134 |
| 2017–2025 | 2017-01-01 through 2025-12-31 | 344 |

Early periods total 886; later periods total 478. Government: 926; media: 111; think tanks/research institutions: 84; research literature: 13; original institutional social posts: 230. Detailed year, source, period-by-type and nonexclusive literal event-cue counts are in the companion JSON. Literal cues are search aids, not finished event coding or political classification. Uneven coverage remains and is not artificially balanced.

## Running early archive queue

At the snapshot, 125 of 360 existing candidate pages had HTTP 200 responses. They produced 124 working rows: 100 individually reviewed (42 formal, 58 pending), with 24 awaiting individual final review. One fetched page lacks validated material extraction and is not counted as fulltext. Another 235 target pages had not yet been fetched. No restricted response, HTTP failure or duplicate discovery was observed in this queue by the snapshot. The crawler observes a minimum ten-second same-host delay and continues without duplicate jobs or unlimited retries.

This queue follows the recovered complete 17-page APP China fulltext index (1,675 candidate links); its success does not establish that other previously failed presidential/archive indexes or pagination paths are resolved. Existing failure evidence is preserved. The next work is continued early-queue acquisition and individual reviews, followed by the remaining working backlog and source/metadata repairs.

## Private delivery and remaining work

`data/materials.xlsx` contains exactly nine columns and 1,364 accepted records. All nine cells for every record, the 148 long-body UTF-8 attachments and every positive-review manifest were read back and matched. XLSX SHA-256: `bf959651453ae7434a6e4d80d1c51391f285c8d425c4ce34389c97bf54b0fb9b`.

Raw HTML/PDF/JSON, complete bodies, individual review manifests, source/field evidence, the progress database, Excel, sidecars and ZIP remain private. This Git report contains aggregate findings only; a locally accessible corpus is not treated as freely redistributable. All historical evidence and prior delivery checkpoints are retained.

FRUS, Congress/GovInfo, NARA, historical VOA, contemporary historical media, Five Eyes sources, Chinese comparison materials, official X/YouTube text and open literature still need broader coverage and/or final review. NYT/AP/Reuters/CNN remain in scope, including restricted/pending states. Every remaining row still requires its own acceptance decision; neither source-only validation nor a sample is presented as full-record completion. The 10,000 target remains unmet; no plateau or exhaustion is claimed.

The private `materials-quality-reviewed-20261109-1364.zip` was built with CRC verification and then independently checked against its own progress snapshot: all nine fields of all 1,364 rows, 148 long-body attachments, 1,364 positive decision bindings and 1,610 distinct formal raw-evidence files matched. Size: 1,047,432,165 bytes; SHA-256: `e6392797e4dd21c5a6a33d49d25b72d428f4ed10f61753ba70ecaef55d42866d`. The three fixed review scripts compiled successfully and safely refused reruns without changing their immutable reports.
