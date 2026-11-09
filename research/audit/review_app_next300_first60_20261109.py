"""Fixed first-60 review within the ongoing APP crawl; preserve every capture."""
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
    "竞选讲话比较共产主义国家的发展与美国的国际影响，并以中国为例说明其对美国政策的批评。": [13738],
    "总统候选人辩论讨论中国在联合国的席位、金门马祖防务与美国对华政策。": [13740],
    "电视问答解释反对中华人民共和国加入联合国的理由，并讨论金门马祖政策。": [13742],
    "记者会回应访华是否讨论石油与粮食贸易的问题，说明会谈议程尚未确定。": [13743],
    "讲话将即将访华描述为依据上海公报延续中美新关系的举措。": [13744],
    "竞选讲话以中国在联合国的席位表决讨论美国国际声望与亚非国家态度。": [13745, 13747, 13754, 13762, 13766, 13774, 13784, 13788, 13790],
    "国会咨文提出安全援助计划，其中说明向中华民国提供军事销售贷款的安排。": [13746],
    "记者会讨论美国驻华代表的人事安排、访华计划及对华政策的延续。": [13748],
    "电视访谈说明政府将发展对华关系列为外交政绩，并回应有关人事调整的提问。": [13749],
    "竞选声明批评对手有关金门马祖政策的主张，并阐述其对台海防务的立场。": [13750],
    "问答批评美国外交对弱小国家的忽视，比较美国与中国等国在国际影响方面的处境。": [13751],
    "纪念中华民国成立的声明讨论中美人民友谊、台湾防务与对中华人民共和国政府的立场。": [13752],
    "记者会在访华前讨论中美领导人会晤的意义，强调磋商而非对抗。": [13753],
    "讲话在访华前说明恢复中美关系的背景及深化交往、避免对抗的目的。": [13755],
    "竞选讲话围绕金门马祖防务批评对手，并将其主张与对华及朝鲜战争政策相联系。": [13756],
    "赴亚洲前的讲话说明访华旨在加强新关系与相互理解，并强调美国对亚洲的持续关注。": [13757],
    "讲话在赴华途中讨论两国制度差异、共同利益与反对亚洲军事扩张等原则。": [13759],
    "总统候选人辩论集中讨论台湾海峡离岸岛屿的防务承诺、战争风险及对华政策分歧。": [13760],
    "演说提出新的太平洋政策，将中美关系正常化列为基本原则，并回顾与中国领导人的会谈。": [13763],
    "竞选讲话讨论国际影响力竞争，并比较美国之音、北京与其他地区的广播活动。": [13764, 13772],
    "访亚归途的记者问答说明访华会谈的收获，并回应总统亲自出访是否必要的质疑。": [13765],
    "记者会讨论发展对华关系的政策，并说明尼克松再次访华属于私人访问。": [13767, 13771],
    "讲话说明中国的制度与美国不同，但主张继续谈判并保持开放交往。": [13769],
    "公众问答说明中美关系状况，并回应有关台湾关系与尼克松访华的问题。": [13773],
    "记者问答讨论尼克松访华对美国选举的可能影响，以及向政府转达访问信息的渠道。": [13775],
    "竞选讲话批评对手的金门马祖防务主张，并强调军事行动的风险。": [13776, 13778],
    "问答讨论以谈判而非对抗处理对华关系，并回应尼克松访华是否影响美国外交的问题。": [13779],
    "问答说明尼克松访华的私人身份，回应其选举影响及政府安保支出问题。": [13781],
    "问答阐述美国对华国家利益、关系正常化与合作及分歧。": [13783],
    "外交事务问答说明对华关系正常化的进展，并讨论如何维持与台湾的关系。": [13785],
    "竞选讲话以中国在联合国的席位、国际交流和广播活动批评美国外交表现。": [13786, 13794],
    "问答说明美国分别处理对苏及对华关系的原则，并讨论合作与制度分歧。": [13787],
    "记者会回应驻台美军减少及秘密交易的说法，说明其与上海公报及地区形势的关系。": [13789],
    "外交演讲批评秘密外交，讨论扩大对华经贸与政治关系以及中苏关系的政策意义。": [13791],
}
DEFER = {
    **{mid: "Source explicitly labels this a partial transcript or excerpts; a complete original speech has not been established." for mid in [13735, 13758, 13768, 13770, 13780, 13782, 13792]},
    13736: "Editorial event timeline rather than the dated original presidential document; displayed presidency start date does not establish timeline publication day.",
    13737: "Only a passing China/Cuba analogy inside a question about Vietnam; direct dissertation relevance not approved.",
    13739: "Petroleum museum dedication; no substantive China-related discussion in the body.",
    13741: "Science award ceremony with no supported topic keywords; source gate did not pass.",
    13761: "China is only one stop in a list of Pacific travels; direct topic relevance remains unresolved.",
    13777: "China appears only as an analogy in a question about Cuba; no substantive China policy answer.",
    13793: "China appears only as the prior location of an announcement about Vietnam; direct topic relevance not approved.",
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "foreign policy", "public opinion", "normalization", "trade", "Korean War")


def main():
    report_path = ROOT / "data/reviews/app-next300-first60-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300-first60-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 60
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300-first60-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300-first60-topic-decisions-20261109.json"
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
