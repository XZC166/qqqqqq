"""Aggregate current accepted corpus, completed APP queue, and pending FRUS inventory."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from research_crawler.quality_audit import material_fingerprint
from research_crawler.store import ResearchStore

ROOT = Path(__file__).resolve().parents[2]


def main():
    output = ROOT / "docs/reports/2026-11-09-quality-continued6-batch.json"
    assert not output.exists(), "Preserve immutable checkpoint."
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    rows = c.execute("""SELECT m.*,q.input_fingerprint,c.period,c.source_category FROM materials m
        JOIN quality_reviews q ON q.material_id=m.id JOIN evidence e ON e.id=m.evidence_id
        JOIN candidates c ON c.id=e.candidate_id WHERE q.status='pass' AND q.source_pass=1 AND q.topic_pass=1 ORDER BY m.id""").fetchall()
    assert len(rows) == 1479 and all(material_fingerprint(r) == r["input_fingerprint"] for r in rows)
    workbook_proof = json.loads((ROOT / "data/reviews/quality-checkpoint-current-20261109.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((ROOT / "data/materials.xlsx").read_bytes()).hexdigest() == workbook_proof["excel_sha256"]
    delivery = json.loads((ROOT / "data/reviews/quality-1479-delivery-verification-20261109.json").read_text(encoding="utf-8"))
    discovery_proof = json.loads((ROOT / "data/reviews/quality-1479-discovery-files-verification-20261109.json").read_text(encoding="utf-8"))
    frus = json.loads((ROOT / "data/candidate-evidence/frus-official-git6-20261109/manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "data/reviews/app-historical188-completed-source-audit-20261109.json").read_text(encoding="utf-8"))
    reviews = [json.loads((ROOT / f"data/reviews/{name}-quality-review-20261109.json").read_text(encoding="utf-8")) for name in ("early21-later-posts20", "early-campaign-next6", "early-short-next14")]
    assert sum(r["reviewed_records"] for r in reviews) == 61
    assert sum(r["new_formal_promotions"] for r in reviews) == 27
    reviewed = [r for batch in reviews for r in batch["records"]]
    assert len({r["material_id"] for r in reviewed}) == 61
    urls = {r["url"] for r in csv.DictReader((ROOT / "data/candidates-app-historical-keywords-fresh188-20261109.csv").open(encoding="utf-8-sig"))}
    evidence = [dict(r) for r in c.execute("SELECT source_url,status_code,fetched_at FROM evidence").fetchall() if r["source_url"] in urls and r["fetched_at"] >= "2026-11-09T12:36:20"]
    working = [dict(r) for r in c.execute("SELECT id,source_url FROM materials").fetchall() if r["source_url"] in urls]
    assert len({r["source_url"] for r in evidence}) == 188 and len(working) == 177
    assert len(audit["records"]) == 177
    categories = Counter(r["source_category"] for r in rows); periods = Counter(r["period"] for r in rows)
    cross = defaultdict(Counter)
    for r in rows: cross[r["period"]][r["source_category"]] += 1
    all_reviews = c.execute("SELECT material_id,status,source_pass,checks_json FROM quality_reviews").fetchall()
    unique_final_decisions = sum(bool(json.loads(r["checks_json"]).get("topic_decision")) for r in all_reviews)
    total_working = c.execute("SELECT count(*) FROM materials").fetchone()[0]
    prior = json.loads((ROOT / "docs/reports/2026-11-09-quality-continued5-batch.json").read_text(encoding="utf-8"))
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "quantity_goal": 10000,
        "database_material_rows": total_working, "formal_unique_fulltexts": len(rows), "pending_or_unreviewed_material_rows": total_working - len(rows),
        "source_audited_material_rows": len(all_reviews), "not_yet_source_audited_material_rows": total_working - len(all_reviews),
        "individual_final_decision_material_rows": unique_final_decisions, "not_yet_individually_final_reviewed_material_rows": total_working - unique_final_decisions,
        "previous_checkpoint_formal": 1452, "formal_net_increase": 27, "individual_records_reviewed_this_checkpoint": 61,
        "new_formal_early_documents": 23, "new_formal_later_original_posts": 4, "review_pending_this_checkpoint": 34, "withdrawn_formal_this_checkpoint": 0,
        "new_candidate_unique_urls": frus["new_unique_urls"], "duplicate_discoveries_added": frus["duplicate_discoveries_added"],
        "restricted_responses": 1, "failed_nonrestricted_network_requests": 0, "http_non2xx_responses": 1,
        "response_count_note": "The one GitHub public REST API 403 is a rate-limit response, counted as restricted and within non-2xx, not as two independent failures. No REST retry. Official public Git transport succeeded separately; no HTTP status fabricated for Git.",
        "formal_by_period": dict(periods), "formal_by_source_type": dict(categories),
        "formal_by_year": dict(sorted(Counter(r["published_on"][:4] for r in rows).items())), "formal_by_source": dict(Counter(r["source"] for r in rows)),
        "formal_period_source_type": {p: dict(v) for p, v in cross.items()}, "period_boundary": "1972 is included only in the first period; the second starts in 1973.",
        "source_status_counts": dict(c.execute("SELECT status,count(*) FROM candidates GROUP BY status").fetchall()),
        "app_completed_queue": {"previously_discovered_candidates_processed": 188, "new_candidates_discovered_this_queue": 0,
            "target_responses_http200": 188, "robots_http200": 1, "working_materials": 177, "source_checks_pass": audit["source_pass"],
            "source_checks_pending": 177 - audit["source_pass"], "individually_reviewed_materials": 41, "formal": 23,
            "individually_reviewed_pending": 18, "awaiting_individual_final_review": 136, "pending_without_extracted_material": 11,
            "pending_total_urls": 165, "http_failures": 0, "restricted": 0, "duplicate_refetches": 0, "completed_at": "2026-11-09T13:07:45+00:00"},
        "frus_official_bulk": {k: frus[k] for k in ("commit", "document_inventory_count", "within_scope_dateline_candidates", "registered_candidate_rows", "new_unique_urls", "known_url_rediscoveries", "duplicate_discoveries_added", "formal_added")},
        "frus_volumes": [{k: v[k] for k in ("file", "title", "bytes", "sha256", "document_count", "publication_date_cues")} for v in frus["volumes"]],
        "frus_date_note": "5,553 documentary elements in six full official volumes; 5,272 have historical dateline cues in scope. 5,257 previously unknown URLs plus 15 known rediscoveries. All registered records pending. A dateline is not a verified publication date and no arbitrary day/month is assigned to a volume publication year.",
        "workbook": workbook_proof, "private_delivery": delivery,
        "private_discovery_evidence": {k: v for k, v in discovery_proof.items() if k != "files"},
        "event_cue_method": prior["event_cues_method"], "event_cue_terms": prior["event_cue_terms"],
        "event_literal_cues": {name: sum(any(t.lower() in r["body"].lower() for t in terms) for r in rows) for name, terms in prior["event_cue_terms"].items()},
        "verification": {"local_full_test_suite_passed": 535, "all_formal_nine_fields_checked": True, "all_formal_evidence_hashes_checked": True},
        "remaining_gaps": [
            "Whole-backlog individual thematic/field review remains unfinished; technical source passes alone are not formal records.",
            "136 working records of the just-completed APP queue await individual final review; 11 other responses did not yield accepted working text.",
            "FRUS precise publication-day, author and single-document text/notes/attachments checks remain pending. A full XML volume download grants no formal acceptance.",
            "Other archive index routes and prior failed pagination remain unresolved; eight additional APP term/date index pages are being searched in the next bounded batch.",
            "Congress/GovInfo, NARA, historic VOA, contemporary historical media and Five Eyes archives need further coverage.",
            "NYT/AP/Reuters/CNN, Five Eyes media, later government/think-tank material, official social accounts, Chinese comparison materials and open research remain in scope; library-authorized full text can be imported.",
            "Ten prior author-conflict withdrawals remain pending. Search excerpts, video/podcast summaries, explicit speech excerpts and incidental biomedical matches are not formal full text.",
            "No plateau or exhaustion has been established; 10,000 is an expansion target, not a verified result."
        ], "privacy": "Full texts, raw evidence, workbooks, SQLite, manifests and ZIP remain local/private. Only code and aggregate reports are committed."}
    assert result["formal_by_period"] == {"2017-2025": 348, "1992-2016": 131, "1949-1972": 531, "1972-1991": 469}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = f"""# 资料采集与全库复核：第六个续批检查点

截至 {result['generated_at']}，工作数据库有 **{total_working:,}** 条材料，**1,479** 条通过当前来源与逐条主题、字段复核并进入正式 Excel；另外 **{total_working-1479:,}** 条 pending 或待复核。候选 URL 不属于工作材料数，更不属于正式全文数。当前有 **{unique_final_decisions:,}** 条工作材料绑定了明确的逐条最终复核决定，尚有 **{total_working-unique_final_decisions:,}** 条没有最终决定；其中技术来源检查通过不能替代最终决定。

本检查点逐条阅读并复核 **61** 条：新增正式 **27** 条（早期文献 **23**、后期完整机构帖文 **4**），pending **34**，正式撤出 **0**。前批十条作者归属问题仍保持 pending，没有为数量恢复。帖文仅代表同一平台 ID 的完整原帖，不代表链接文章、视频或播客。两条文字相同而平台 ID 和发布日期不同的机构帖按用户规则分别保存。

| 时期 | 正式记录 |
|---|---:|
| 1949—1972 | 531 |
| 1973—1991 | 469 |
| 1992—2016 | 131 |
| 2017—2025 | 348 |

1972 年只计入第一段。1949—1991 年合计 **1,000** 条；后期新增仍在推进。来源类型累计：政府 **1,035**、媒体 **111**、智库 **85**、研究文献 **14**、完整机构新媒体帖文 **234**。逐年、来源、时期×来源类型和事件字面线索统计见同名 JSON；事件线索可重叠，不是完整事件编码或立场判断。

## 完成的 188 页早期队列

188 个此前发现的来源页和 1 个 robots 请求全部 HTTP 200；形成 **177** 条工作材料，全部完成本地来源证据比对（**167** 通过、**10** pending）。其中 **41** 条已逐篇最终复核：**23** 正式、**18** pending；**136** 条待逐篇最终复核。另外 **11** 个响应未形成可接受的工作文本，保留 pending。因此该队列正式为 **23**，pending URL 合计 **165**，没有 HTTP 失败、受限响应或重复抓取已知页面。

可疑材料继续保留原始证据。例如原始转录将脚注续文插入不相关正文句子、句子开头疑似缺失、标题明确为节选、全文没有中国内容而只有索引匹配，均未获正式通过。长篇预算文献尚未逐篇完整阅读，不会冒称已完成最终核验。

## FRUS 官方整卷资料

从国务院历史学家办公室公开仓库固定版本 `{frus['commit']}` 取得 **6 卷完整 XML**，逐文件核对官方 Git blob 和 SHA-256，保存官方公共领域许可说明。完整目录含 **5,553** 篇文献；**5,272** 篇具有研究范围内的历史文献日期线索，注册为 pending（**5,257** 新 URL、**15** 已知 URL 再发现）。**正式增加为 0**。

档案写成日期不能直接替代发布日期；这些卷册目前只核实到出版年份，未据此猜填年月日。单篇正文、注释、附件、作者和主题也仍需核验。官方 REST API 的一次 HTTP 403 限流响应已保留，未反复请求；独立公开 Git 下载成功，不将 Git 命令成功伪称为 HTTP 200。只把有日期线索的文献纳入候选，未把整卷自动拆成正式全文。

官方来源及 URL 对应、许可说明：[HistoryAtState/frus](https://github.com/HistoryAtState/frus)。

## 本地交付与后续

`data/materials.xlsx` 已更新为 **1,479 行、严格九列**，全部字段和 **158** 份 UTF-8 长正文附件回读一致。Excel SHA-256：`{workbook_proof['excel_sha256']}`。

私有 ZIP `materials-quality-reviewed-20261109-1479.zip` 独立核验全部 **1,479** 行九字段、**158** 份长正文、**1,479** 个正向复核绑定、**1,729** 份正式原始证据哈希；另外保存并逐项核对 **25** 份本批发现证据（含 FRUS 六卷、许可、索引和限流响应），整包 CRC 通过。大小 **{delivery['zip_bytes']:,}** 字节，SHA-256：`{delivery['zip_sha256']}`。ZIP 固定于队列结束前的进度快照；其正式 1,479 条与当前 Excel 一致，最终队列进度以本报告为准。本地完整测试 **535 项通过**。

原始全文、Excel、SQLite、复核清单和 ZIP 仅作本地私有研究交付，未公开上传。旧交付保留为历史证据。后续继续逐条复核上述 136 条、处理主题或字段存疑项，并继续追加 Taiwan、Quemoy、Matsu、Voice of America 的有限分页发现；其他时期和所有指定来源继续保留检索范围。全库最终复核尚未完成，尚未达到平台期或 10,000 条目标，不声称穷尽。
"""
    output.with_suffix(".md").write_text(md, encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("generated_at", "database_material_rows", "formal_unique_fulltexts", "pending_or_unreviewed_material_rows", "individual_final_decision_material_rows", "formal_by_period", "app_completed_queue")}, ensure_ascii=False, indent=2))
    store.close()


if __name__ == "__main__":
    main()
