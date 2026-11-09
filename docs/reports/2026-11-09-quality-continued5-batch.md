# 2026-11-09 continued review checkpoint 5

Snapshot: 2026-11-09 20:32:52 Asia/Singapore (12:32:52 UTC). This is a reproducible quality checkpoint; collection and whole-backlog review continue.

Since checkpoint 4, **228 review operations covered 223 distinct records**. This included individual topic/field decisions on another **198 early archive records**, a substantive-footnote check of **all 13 then-formal research papers**, seven explicit research/think-tank repair or acceptance decisions, and targeted attribution holds on ten former formal records. These are different review scopes, not a claim that the entire database has finished individual review.

There were **81 first formal acceptances**, **five restorations after completeness repair**, and **15 withdrawal operations**. Five of those withdrawals were subsequently repaired, so **ten records remain withdrawn to pending**. The formal total is **1,452**, a net increase of **71** from 1,381. There are **129 currently pending distinct records in this checkpoint's reviewed selection**; the 134 pending review operations include the five subsequently repaired holds.

## Cumulative working and accepted records

- Database material rows: **7,238**.
- Source-and-topic accepted, unique formal fulltexts: **1,452**.
- Other working rows requiring resolution or final acceptance: **5,786**.
- Every working row has received the source audit, which is distinct from individual final topic/field acceptance. Source-pass alone does not make a record formal.
- Formal source categories: government **1,012**; media **111**; think tanks/institutions **85**; research literature **14**; original institutional social posts **230**.

| Period label | Actual nonoverlapping interval | Formal fulltexts |
|---|---|---:|
| 1949–1972 | 1949–1972 inclusive | 508 |
| 1972–1991 | 1973–1991 inclusive | 469 |
| 1992–2016 | 1992–2016 inclusive | 131 |
| 2017–2025 | 2017–2025 inclusive | 344 |

Early periods total **977**, later periods **475**. The companion JSON gives all years, source institutions, period-by-type coverage and nonexclusive literal event cues. Event cues are not completed historical event coding or political labels. The 10,000-formal expansion target remains unmet; no plateau or exhaustion is claimed.

## Completed 360-candidate early queue

All **360 previously discovered target pages** returned HTTP 200; a separate robots request also returned HTTP 200. **348** produced working records, and **every one of those 348** now has an individual final-review decision: **138 formal, 210 pending**. Another **12 fetched URLs failed fulltext/metadata extraction** and remain pending without a formal material row. At URL level the queue therefore has **138 formal and 222 pending**, zero unfetched, restricted responses, HTTP failures or duplicate discoveries in this queue.

Passing HTTP status did not establish completeness. Deferred examples include an explicitly excerpted congressional report; a speech ending mid-sentence; an explicitly excerpted press statement; unanswered China questions; diaries lacking proceedings; unrelated birthplace or past-job mentions; multi-speaker attribution; and a relevant passage containing unresolved unusual transcription sequences. Accepted records include 1989–1991 public explanations of engagement, MFN, human rights, students, secret diplomacy and news images; VOA/WORLDNET and journalist access; people-to-people and scientific exchanges; and direct presidential statements about China's political and economic changes. Original wording and complete accepted bodies were retained; summaries and keywords were individually grounded in those bodies.

## Substantive footnotes and author attribution

The original PMC adapter read the main body but excluded substantive article footnotes outside that container. A check of **all 13 formal research articles** found **five** affected; those five were first held pending. The adapter now retains original substantive note text in article order while excluding publisher boilerplate and other articles. The main bodies remained byte-identical. Across those five and one newly accepted research article, **all 241 original notes** were reconciled against the original saved HTML, with whitespace normalization only in the independent comparison. Exact publisher abstracts were retained. Eight unaffected formal research bodies remained unchanged. This is a bounded repair, not a claim that all PMC layouts or all pending research papers are now correct.

Five synthetic regression cases were demonstrated failing before their respective fixes and passed afterward; the full suite passed **535 tests**. Independent code review found mixed-content note omission and a nested-quotation duplication case; both were reproduced and fixed, and the follow-up review found no additional actionable issues. After the final code change, **all 14 current formal research records** were re-extracted again and every accepted body remained byte-identical. Synthetic fixtures contain no third-party article text. One separately reviewed CSIS analysis was accepted and correctly classified as think-tank material.

A title-level screen of all then-formal records identified **seven press-secretary/White House statements and three administration policy statements** whose author field merely repeated the presidential collection name. Their actual release-level author attribution remains unresolved; all ten were moved to pending, preserving original evidence and previous decisions. Relevant newly acquired statements with the same conflict were also withheld. No guessed author was substituted.

## Next discovery batch

A separate bounded search used **Peking, Peiping and Formosa**, four pages per term, across 1949–1991. All **12 index pages** returned HTTP 200. They contained **437 hit occurrences, 423 unique URLs**: **235 already known unique URLs**, **188 new unfetched candidate URLs**, and **14 repeat observations within this index**. The combined rediscovery/repeat count is **249**; it is a discovery measure, not extra material rows or formal texts. The index raw files, dates, URLs and hashes are preserved. Individual source pages must still verify dates and fulltext. Registration and the next crawl follow this immutable delivery checkpoint, without refetching the 235 already captured URLs. Historical terms improve early coverage without excluding post-1991 sources.

## Private workbook and remaining work

The checkpoint workbook has **1,452 records, exactly nine columns and 158 UTF-8 long-body attachments**. Every field of every row, every long-body reference and every positive decision's immutable hash binding was verified. XLSX SHA-256: `862ba06c4bb1ac8824468c466ec5758b9e5ae270a7b38b5c7ad3bb35ae1199ad`.

Earlier workbooks and ZIPs remain historical evidence. They are superseded by the current footnote corrections and attribution holds; they must not be presented as current accepted deliveries. Excel, full bodies, individual manifests, raw files and SQLite remain private. Git contains source, synthetic tests and aggregate reports only. Public accessibility is not permission to publicly redistribute a fulltext.

Whole-backlog individual review remains incomplete. FRUS, Congress/GovInfo, presidential archives, NARA, historical VOA and contemporary media need further coverage. Earlier failed archive routes and pagination outside the successful APP fulltext index remain unresolved; they were not silently converted into successes. NYT/AP/Reuters/CNN, Five Eyes sources, later government/think-tank material, official social accounts, Chinese comparison sources and open research remain in scope. Videos are not downloaded; summaries are not counted as complete original texts. Source restrictions and exact-date, byline, body-boundary and topic uncertainties remain recorded as pending/restricted rather than filling the numerical target.

Checkpoint private ZIP `materials-quality-reviewed-20261109-1452.zip`: independently verified all nine fields of 1,452 rows, 158 long-body files, 1,452 positive-decision bindings and 1,698 formal raw-evidence hashes. Builder CRC passed. Size: 1,058,788,651 bytes. SHA-256: `8357346851fd57c877ef2dcbe89fc09d2a95aece604d2e2a94de12a7ff3053a1`. This archive fixes the pre-next-registration checkpoint; subsequent discovery registration updates duplicate counters and the live workbook separately.

提交前另外隔离检验实际暂存的公开代码树：328 项通过，10 项因原始版权页面仅在本地保存而跳过；未将这些页面补入公开仓库。本地保留原始页面的工作目录完整测试为 535 项通过。
