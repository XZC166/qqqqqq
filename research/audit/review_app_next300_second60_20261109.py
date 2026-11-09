"""Second fixed sixty-record APP review; source snapshots and old fields retained."""
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
    "讲话比较美苏军事部署，并以中苏边境及中国的战略位置解释双方兵力需求的差异。": [13795, 13797, 13799],
    "竞选讲话回应有关中国沿海岛屿防务的争论，并要求对手同时说明古巴政策。": [13796],
    "演说解释台湾海峡防务立场，反对当时接纳中华人民共和国加入联合国，并陈述其理由。": [13798],
    "记者会回应尼克松访华报告是否有实质内容的问题，说明总统对该报告的评价。": [13801],
    "总统候选人辩论讨论台海防务、中国在联合国的席位与美国的国际影响。": [13802],
    "记者问答回应中国领导层变化及美国是否讨论向中国提供军事援助的问题。": [13803],
    "竞选讲话将对华交往列入外交政绩，并说明政府对会谈与关系进展的评价。": [13805],
    "简短记者问答说明尼克松的私人身份，并回应其是否会再次访华及提交报告的问题。": [13806],
    "公众问答比较冷战时期的对华政策与谈判路线，并主张通过谈判而非对抗处理分歧。": [13808],
    "外交事务问答讨论对华关系正常化的进程，以及其与台湾和苏联关系的联系。": [13810],
    "讲话主张继续发展对华新关系，并说明中国参与对全球和平的重要性。": [13811, 13840],
    "竞选讲话以中国在联合国的席位表决、国际态度与美国对外交流讨论美国的国际声望。": [13812, 13815, 13823, 13829, 13845, 13847, 13854],
    "外交演讲讨论中苏冲突及中美关系改善，并说明美国的太平洋安全政策。": [13813],
    "访谈将对华及对苏关系置于民主国家间协调的框架内，说明其设想的外交关系结构。": [13816],
    "竞选讲话比较中美等国的国际影响、发展示范与广播活动，并讨论中国在联合国的席位。": [13817, 13835],
    "记者会回应对华纺织品贸易和台湾参加奥运会等问题，其中就贸易问题指向此前声明。": [13818],
    "竞选讲话以朝鲜战争中的中国为例，说明其对威慑、谈判与避免战争的主张。": [13821],
    "美澳联合声明讨论扩大与中国沟通、参与国际事务及依据上海公报推进中美关系正常化。": [13822],
    "记者简报讨论改善对华关系的机会、中苏竞争，以及通过公开或私下沟通说明政策的必要性。": [13824],
    "向《纽约时报》提交的问答讨论核威慑，并说明其对中国及中苏关系的战略判断。": [13825],
    "访谈说明与中国增进理解的外交目标，并介绍拟就对华及对苏关系发表政策演讲的安排。": [13828],
    "共和党党纲说明对华联系、贸易、关系正常化和对台湾承诺等立场，同时讨论美国对外政策。": [13830],
    "演说讨论与北京等地开展的国际影响竞争，并以中国在联合国的席位表决说明外交与交流问题。": [13831],
    "接受提名演说将对华及其他主要对外关系描述为坚定、警惕并面向未来，阐述以实力求和平的政策。": [13832],
    "竞选讲话赞扬艾森豪威尔处理金门马祖防务的决定，并阐述其对威慑及战争风险的解释。": [13833],
    "悼念毛泽东的讲话评价其历史作用，并回顾中美结束敌对、改善关系的过程。": [13836],
    "竞选讲话批评此前的中国政策，回顾朝鲜战争并说明其对共产党执政的中国与美国关系的看法。": [13837],
    "访谈讨论与中华人民共和国建立外交关系的目标，并提出有关台湾安全及美国承诺的条件。": [13838],
    "竞选讲话批评对手的台海立场，并将金门马祖防务与朝鲜战争及威慑政策相联系。": [13841, 13843],
    "总统候选人辩论讨论对华关系正常化、台湾安全、军事装备与美国的外交立场。": [13846],
    "副总统候选人辩论在评价基辛格的外交记录时讨论对华突破与共和党对外政策。": [13848],
    "电视演说讨论金门马祖政策，并通过香港访问经历表达对中国人民与中美关系的看法。": [13849],
    "竞选演说讨论美国国际形象及影响力，将亚洲部分公众转向中国与美国的外交处境相联系。": [13852],
}
DEFER = {
    13800: "Cuba policy statement mentions China only as a possible goods supplier; direct China-focused dissertation relevance not approved.",
    13804: "Only a brief possible Sino-Soviet split in a generic campaign forecast; direct topic relevance requires further assessment.",
    **{mid: "Original title explicitly says partial transcript or excerpts. Establish complete original material before formal fulltext export." for mid in [13807, 13814, 13826]},
    13809: "Global energy conference proposal lists China among excluded participants, without substantive China policy or communication discussion.",
    13819: "China appears only in a brief alternative-leadership sentence; direct topic relevance remains unresolved.",
    13820: "Nuclear proliferation answer gives China only as a brief nuclear-capability example; direct topic relevance not approved.",
    13827: "China appears only in the phrase India versus China inside broad campaign priorities; direct topic relationship not approved.",
    13834: "Order is dated on signing day and explicitly references later Federal Register publication. Resolve publication-day provenance rather than assuming the signing date is publication date.",
    13839: "General campaign speech mentions possible Chinese atomic capacity only briefly; direct topic relevance remains unresolved.",
    13842: "General nuclear proliferation speech lists China and Taiwan as examples; more specific relationship to the research topic not established.",
    13844: "Carter-labelled interview includes substantial Ford interview responses; inspect original page structure and author/body boundaries before approval.",
    13850: "John Glenn's China trip is a biographical aside; no substantive China discussion in the body.",
    13851: "List of past crises includes Formosa and Indo-China, without substantive China-focused discussion.",
    13853: "China appears only as the location of a visitor's trip in a Yugoslavia response; direct topic relationship not approved.",
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Mao", "Soviet Union")


def main():
    report_path = ROOT / "data/reviews/app-next300-second60-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300-second60-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 60
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300-second60-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300-second60-topic-decisions-20261109.json"
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
