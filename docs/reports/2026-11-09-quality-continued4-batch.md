# 2026-11-09 continued review checkpoint 4

Snapshot: 2026-11-09 19:55:26 Asia/Singapore (11:55:26 UTC). Collection continues; these are checkpoint counts, not completed queue totals.

Following checkpoint 3, another **50 early presidential-archive records** were individually reviewed: **17 new formal fulltexts, 33 pending, zero former formal withdrawals**. No new discovery, duplicate discovery, restricted response or HTTP failure resulted from these offline reviews. The original evidence, pre-change fields, per-record reasons and database backup were retained. Across checkpoints 3 and 4, **240 records were individually reviewed, 119 newly accepted and 121 left pending**; the previous 1,262 formal records therefore increased to 1,381, rather than treating all working rows as formal.

## Current counts

- Database material rows: **7,059**.
- Individually source-and-topic accepted unique formal fulltexts: **1,381**.
- Other working records requiring resolution or acceptance: **5,678**. Passing source validation alone does not make a record formal. Another 19 newly acquired rows had not yet received source audit at the snapshot.
- Formal government records: **943**; media: **111**; think tanks/research institutions: **84**; research literature: **13**; original institutional social posts: **230**.

| Period label | Actual interval | Accepted fulltexts |
|---|---|---:|
| 1949–1972 | 1949-01-01 through 1972-12-31 | 509 |
| 1972–1991 | 1973-01-01 through 1991-12-31 | 394 |
| 1992–2016 | 1992-01-01 through 2016-12-31 | 134 |
| 2017–2025 | 2017-01-01 through 2025-12-31 | 344 |

The early periods now total **903**, and the later periods **478**. The second label is retained for continuity but excludes 1972 to prevent overlap. Detailed source, year, type-by-period and nonexclusive literal event-cue counts are in the companion JSON. Event cues remain search aids, not complete event coding or political labels.

## This individual-review batch

Accepted records include China/Taiwan policy explanations to Japanese and Southeast Asian newspapers; descriptions of Fudan student exchanges; the 1984 Republican platform; China membership in the IAEA governing structure; the Winston Lord ambassador nomination; science and technology exchanges; a strategic-defense anecdote reporting dialogue with Chinese officials; and the Tibet recognition clarification in an export-bank signing statement. The complete platform is preserved as a long-body text attachment.

Specific institutional biographies were accepted when the body explicitly documents China-related communication work: a USIA Hong Kong cultural officer, a National Committee on United States-China Relations board officer with cultural/people-to-people exchanges, and the planner of Nixon’s China visit. Mere birthplace, university or unrelated past-job references were not sufficient. VOA broadcasting explicitly directed to Soviet listeners was not relabeled as China-directed broadcasting. Multi-speaker attribution, diaries lacking proceedings, unsupported direct relevance and a short administrative statement with missing fields remain pending with individual reasons.

Every positive decision is bound to the complete source-reextracted body and metadata fingerprint and a hashed immutable decision manifest. Derived summaries retain their required prefix; the original body is unchanged. Neither the title-only mention of China nor an archive HTTP 200 response bypasses the formal gates.

## Running 360-candidate queue

At the snapshot, **175 unique target pages returned HTTP 200**. These correspond to **169 working material rows**, of which 150 have individual final-review decisions: 59 accepted, 91 pending. Another 19 working rows await final review. Six fetched target URLs have no corresponding validated material row; their source/candidate reasons remain in SQLite. Another 185 target pages had not yet been fetched. Restricted responses, HTTP failures and duplicate discoveries were zero by this snapshot. These were previously discovered candidates, not 175 newly found URLs.

The same crawl continues at the permitted minimum ten-second host delay. No duplicate same-host job, unlimited retry, database reset or evidence deletion was used. Previously failed archive routes and unfinished pagination outside the successful APP index remain unresolved coverage gaps. After this batch, continue the remaining early queue and individual review backlog; later-period media, government, research and official accounts remain in scope.

## Private workbook and access boundaries

The latest `data/materials.xlsx` contains **1,381 formal records, exactly nine columns and 149 UTF-8 long-body attachments**. All nine fields of every row, every referenced long body and every positive-decision manifest were verified. XLSX SHA-256: `dd699ba47a29848e42a21da1eb81887f78013d7c6b603d4d75c5820e589e653f`.

Excel, bodies, raw HTML/PDF/JSON, individual evidence and the progress database remain private. Git contains audit scripts and aggregate reporting only. Local authorized possession does not imply a right to publicly redistribute. Prior database backups and delivery packages are retained. Whole-backlog individual review, broader FRUS/Congress/GovInfo/NARA/VOA and historical media coverage, Five Eyes sources, X and YouTube transcripts, Chinese comparison materials and open research remain incomplete. No sampling is presented as all-record completion; no plateau or exhaustion is claimed and 10,000 formal fulltexts remains an unmet expansion target.

Private ZIP `materials-quality-reviewed-20261109-1381.zip`: independently verified all nine fields of 1,381 rows, 149 long-body attachments, 1,381 positive decision bindings and 1627 formal raw-evidence files. ZIP CRC passed during generation. Size: 1,049,694,826 bytes; SHA-256: `a504e016572fddad05ca7f9c6d76723aff42f7d3e649adc70e677f75b89d6ca1`. Fixed review script compiled and refused reruns without changing its immutable report.
