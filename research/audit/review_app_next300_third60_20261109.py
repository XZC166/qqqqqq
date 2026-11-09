"""Third bounded APP review: individually judged topic and field evidence."""
import hashlib
import json
import re
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.quality_audit import audit_material, material_fingerprint, _source_row
from research_crawler.revalidation import _extract_existing
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import ResearchStore

ROOT = Path(__file__).resolve().parents[2]
SUMMARIES = {
    "竞选演说把打开对华交往之门列入亚洲外交成绩，并比较其与对手的地区政策。": [13855],
    "机场记者问答回应向中国出售计算机的批准程序、军事用途与公开说明问题。": [13857],
    "记者会说明核裁军设想，并转述与中国代表讨论减少核武器的情况。": [13859],
    "对国务院员工的讲话说明寻找共同利益、改善与中国等国关系的外交方向。": [13860],
    "记者会回应有关中苏分歧及其对美国关系可能影响的提问。": [13861, 13885],
    "记者会回应中美交换记者及被关押人员的问题，并讨论双方言辞与关系状况。": [13863],
    "记者会比较中苏与美国向第三国提供出版物的规模，讨论美国新闻署、广播及交流活动。": [13865],
    "记者会说明与英国在中国联合国席位问题上的不同政策，并重申对台湾的承诺。": [13867],
    "美日联合声明说明双方就中国及其他亚洲问题交换意见，并同意继续密切磋商。": [13877],
    "记者会讨论对华高层沟通提议、日内瓦与华沙会谈渠道及中国的公开言辞。": [13883],
    "联合国演说表示将依据上海公报发展对华关系，并说明亚洲稳定方面的共同利益。": [13868],
    "记者会将美国农业生产与中国等地的状况比较，并讨论向世界说明美国成就的问题。": [13869],
    "对加拿大议会的演说比较自由社会与中国的发展经验，并阐述援助新兴国家的主张。": [13871],
    "国会特别咨文提出增加对外信息传播经费，并比较中国与美国面向拉美的广播规模。": [13873],
    "巴黎记者问答讨论对华和平关系、联合国席位、中苏关系及中国公开言辞。": [13875],
    "记者问答说明中美在未建立全面外交关系时保持接触，并介绍就限制战略武器交换意见的安排。": [13878],
    "讲话以对华等敏感外交问题为例，主张公开说明政策选项并听取美国公众意见。": [13880, 13884, 13891],
    "签署农业法的讲话比较美国农业生产与中苏农业制度，并说明其国际意义。": [13881],
    "记者会说明通过访华人员传递的友好信息、关系正常化目标与领导人互访的条件。": [13882],
    "记者会讨论对华沟通及关系正常化，并回应是否计划访问日本和中国的问题。": [13886],
    "讲话批评将中国政局变化归咎于高层叛国的简单解释，讨论美国国内政治中的极端言论。": [13887],
    "工会大会讲话说明拟任命伍德科克主持美国驻华联络处的理由与对谈判能力的期待。": [13889],
    "记者会回应关于1949年中国政策的旧讲话，解释对个人人事责任及中国局势的看法变化。": [13890],
    "讲话以中国饥荒等事例讨论独裁、自由与经济发展的关系。": [13892, 13894],
    "外交演说将对华关系正常化视为美国全球政策的重要组成部分，并表达合作意愿。": [13893],
    "对广告委员会的讲话通过日本与中国等比较说明制度竞争，并讨论美国的国际形象与对外责任。": [13896],
    "记者会说明美国企业申请向中国出口小麦的情况，并区分企业申请与中国政府请求。": [13899],
    "记者会讨论香港的中国难民、粮食状况、援助及是否向中国提供剩余粮食的问题。": [13901],
    "和平队问答讨论美国对华粮食政策、被关押美国人及双方公开言辞与形象。": [13903],
    "出版业问答将改善对华等既往敌对关系与和平竞争国际影响的外交主张相联系。": [13904],
    "讲话以中国的公共劳动和建设活动为例，讨论公共服务、社会动员及美国和平队。": [13905],
    "公告介绍美国与台湾签署鞋类出口有序销售协议的限额、协商及其对国内产业的预期影响。": [13906],
    "对巴西学生的讲话比较美国、欧洲与中国等地的经济和公民自由状况，回应其对美国的看法。": [13909],
    "任命公告介绍拟由伍德科克担任美国驻北京联络处主任及其大使衔，并列明其履历。": [13910],
    "记者会说明此前向台湾出口U-2飞机的许可，以及不再授予进一步出口许可的政策。": [13911],
    "致议会间理事会主席的信评论中印边境冲突，并要求向会议宣读美国的立场。": [13913],
}
DEFER = {
    13856: "China appears only in a generic list of global hazards; direct China-focused topic relevance not approved.",
    13858: "Source title explicitly labels excerpts; complete original speech not established.",
    13862: "China is an incidental alternative supplier in a Vietnam normalization answer, without substantive China-focused discussion.",
    13864: "Mushroom import relief concerns Taiwan-specific commodity regulation; direct communication/topic relationship remains unresolved.",
    13866: "China is only the nominee's place of birth; not relevant to the dissertation scope.",
    13870: "China scholarly-communication committee appears only in an unrelated nominee biography; direct topic relevance not established.",
    13872: "China appears only as a nominee's birthplace; not substantive topic material.",
    13874: "Digest of several White House announcements; verify publication day, author and individual-document boundaries before formal promotion.",
    13876: "Japan ambassador nomination gives earlier China visits only as background biography; direct topic relationship unresolved.",
    13879: "China food shortage is only one brief example in a general presidency assessment; direct topic relevance not approved.",
    13888: "China's changed strength is a brief historical analogy inside a Soviet-focused interview; direct topic relevance not approved.",
    13895: "Pakistan ambassador biography includes China and VOA service; may support personnel history, but substantive dissertation relevance needs separate resolution.",
    13897: "China is mentioned only as a location of Carter's earlier submarine service; outside substantive topic scope.",
    13898: "Republic of China appears only in a long aid-recipient list; direct topic relevance not established.",
    13900: "Romania trade agreement gives China only as one of Romania's partners; direct China-focused relationship not approved.",
    13902: "Chip's China visit is one of several family-representation examples; no substantive China discussion.",
    13907: "South China Seas is only a location in a reservist commendation; no substantive China policy discussion.",
    13908: "Checklist of press releases is a directory record, not the named releases' full original bodies.",
    13912: "China is one agenda item in an apology for a late arrival; substantive content concerns White House Fellows.",
    13914: "China appears only as a possible future test-ban participant; China-focused communication relevance not established.",
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300-third60-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300-third60-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 60
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300-third60-review-20261109.sqlite3"
    if not backup.exists():
        b = sqlite3.connect(backup);c.backup(b);b.close()
    prior = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    records, changes = [], []
    adapter = GovernmentArticleAdapter()
    for observed in selected:
        row = c.execute("SELECT * FROM materials WHERE id=?", (observed["id"],)).fetchone()
        for field, reading_key in [("published_on", "date"), ("author", "author"), ("title", "title"), ("source_url", "url")]:
            assert row[field] == observed[reading_key]
        assert hashlib.sha256(row["body"].encode()).hexdigest() == observed["body_sha256"]
        approved = row["id"] in summaries
        if approved:
            source = _source_row(s, row["id"])
            result, metadata_ids = _extract_existing(s, source, adapter)
            parsed = result.get("material")
            assert parsed and parsed.body == row["body"]
            assert hashlib.sha256(Path(source["evidence_path"]).read_bytes()).hexdigest() == source["content_sha256"]
            keywords = "; ".join(dict.fromkeys(m.group() for t in TERMS if (m := re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", row["body"], re.I))))
            assert keywords
            abstract = "据正文整理：" + summaries[row["id"]]
            fields = json.loads(c.execute("SELECT field_sources FROM material_verifications WHERE material_id=?", (row["id"],)).fetchone()[0])
            fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
            mid, created = s.add_verified_material(source["candidate_id"], row["evidence_id"], replace(parsed, abstract=abstract, keywords=keywords),
                                                 abstract_origin="derived", field_sources=fields, metadata_evidence_ids=metadata_ids)
            assert not created and mid == row["id"]
            changes.append({"material_id": mid, "previous_fields": dict(row), "new_abstract": abstract, "new_keywords": keywords})
            row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        records.append({"material_id": row["id"], "fingerprint": material_fingerprint(row), "approved": approved,
                        "reason": "Individual topic/field review: " + (summaries[row["id"]] if approved else DEFER[row["id"]]),
                        "source_url": row["source_url"], "body_sha256": observed["body_sha256"]})
    manifest = ROOT / "data/reviews/app-next300-third60-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Stored-original source/body checks plus individual topic and field decisions. This is a review subset of the ongoing 300-URL crawl, not another discovery batch."}, ensure_ascii=False, indent=2).encode()
    assert not manifest.exists();manifest.write_bytes(raw)
    results = [audit_material(s, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    now = {r["material_id"] for r in results if r["status"] == "pass"}
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0,
              "formal_fulltexts": len(now), "new_formal_promotions": len(now - prior), "pending": len(results) - len(now),
              "withdrawn_formal": len((prior & {r["material_id"] for r in results}) - now),
              "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests_for_offline_review": 0,
              "field_corrections": len(changes), "backup": str(backup.relative_to(ROOT)), "records": results}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2));s.close()


if __name__ == "__main__":
    main()
