"""Next 360-URL APP queue, third fifty: individual field and topic decisions."""
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
SUMMARIES = {'费尔德曼提名公告记述其任美国新闻署香港文化官员、台北政治官员及国务院涉台事务负责人的经历，提供对外传播人员履历记录。': [14413], '一九八四年共和党纲领说明对华长期关系、台湾关系法和香港立场，并介绍美国之音、国际广播及民主推广政策。': [14415], '阿曼森任命公告介绍其文化交流和民间交往经历，以及担任美中关系全国委员会董事会副主席等职务。': [14416], '联合国大会演说把中美关系的发展作为美国愿同意识形态不同的国家改善关系的例证，并阐述和平合作立场。': [14418], '在鲍灵格林州立大学讲话问答中，里根以中美友谊和该校同复旦的交流为例，回顾与中国学生沟通及其对美国青年的兴趣。': [14419], '记者问答回应朝鲜半岛统一问题，里根表示支持双方接触，并称已同中国、日本等有关国家讨论相关问题。': [14424], '读卖新闻书面问答说明中美苏关系及军控谈判，讨论中苏分歧，并表述对朝鲜半岛和平及有关国家角色的看法。': [14426], '沃克任命公告记述其在尼克松任内协调和筹划访华等出访的工作经历，提供有关历史访问组织人员的官方记录。': [14427], '致参议院咨文建议批准国际原子能机构章程修正案，解释增加理事会席位可容纳中国加入而不替代其他指定成员。': [14432], '洛德驻华大使提名公告宣布其拟接替恒安石，并介绍其外交关系协会、国务院政策规划及对华政策顾问经历。': [14433], '筹款晚宴讲话转述沃尔特斯同中国官员关于战略防御的矛与盾对话，用以说明里根支持防御计划的论点。': [14442], '联合国大会演说在发展政策论述中，把中国同新加坡、台湾等列为提供经济激励而取得进展的例子，并主张信息自由。': [14444], '国际科技活动年度报告咨文介绍对华科技合作的规模、互利基础及中方付费开展的活动，并陈述政府对其改革影响的评价。': [14448], '面向东南亚报纸的书面问答回应中美军事合作与地区竞争问题，解释向中国提供防御能力及东盟稳定作用的政策立场。': [14449], '面向日本新闻机构的书面问答解释中美军事与技术合作，回应台湾和苏联的关切，并说明美国军舰访华磋商情况。': [14450], '面向国际货币基金组织和世界银行的讲话以中国等国农业激励与产出变化支持其自由市场发展论述。': [14460], '进出口银行法修正案签署声明解释对有关国家融资的限制，并澄清美国承认西藏为中华人民共和国一部分的立场。': [14461]}
DEFER = {14412: 'China occurs only in a list of Bushs past positions, without substantive China-policy discussion.', 14414: 'China postings and birthplace are career history for a Singapore nomination; specific communication-theme relevance needs further assessment.', 14417: 'China friendship is a brief generic accomplishment; the substantive speech concerns other issues and lacks specific China explanation.', 14420: 'China visit occurs in a generic list of relationships; no specific China-policy or communication content established.', 14421: 'China is only part of Bushs resume in a debate question; no substantive China answer in this record.', 14422: 'China is an analogy about historical insurgency in a multi-speaker debate attributed solely to Reagan; both scope and authorship need further review.', 14423: 'Interview question proposes joint defense research including China, but answer is about US-Soviet defense generally; specific China-policy response unestablished.', 14425: 'South China Sea appears only as the location of a refugee rescue in a multi-item diary.', 14428: 'China is one brief example among countries discussing general market growth; specific thematic scope requires further review.', 14429: 'Diary only lists presentation of a Chinese ambassadors credentials, without substantive contents and verified release authorship.', 14430: 'Diary lists officials trip to China among other destinations without the actual report; release authorship unresolved.', 14431: 'Diary gives a visit invitation and date without full meeting text; release authorship remains unresolved.', 14434: 'Diary names a nuclear agreement briefing but is not its full text; release authorship unresolved.', 14435: 'China is a nominees birthplace and education location, not substantive China policy.', 14436: 'China occurs only in a nominees birthplace.', 14437: 'China occurs only in a nominees birthplace.', 14438: 'China occurs in a historical Soviet expansionism anecdote; no specific contemporary US-China communication-policy discussion established.', 14439: 'China occurs only in a nominees birthplace.', 14440: 'China occurs only in a nominees birthplace.', 14441: 'China/Taiwan occur in a nominees birthplace and university, not substantive China policy.', 14443: 'China trip and Taiwan are travel references in an India interview without substantive China-policy response.', 14445: 'VOA speech is explicitly directed to Soviet listeners; China occurs only in a WWII burial-location list. It is not China-directed broadcasting evidence.', 14446: 'Source audit fails because abstract/keywords are missing; short resolution response has no substantive China/nuclear discussion in body, and administrative-statement authorship requires verification.', 14447: 'China Sea is a bank management region in a nominees career history.', 14451: 'China/Taiwan occur only in a delegates birthplace and university.', 14452: 'China is one location in general remarks about meeting young people; no substantive bilateral communication account.', 14453: 'Diary names China discussions but supplies no actual discussion text or verified release authorship.', 14454: 'Indo-China Task Force is a historical career reference about Indochina, not a China-policy body passage.', 14455: 'China is only a students birthplace in an immigration celebration; specific international US-China scope unestablished.', 14456: 'China posts occur in a Gambia nominees career history; substantive communication-theme connection requires further review.', 14457: 'China is only a historical tea origin in a sailing ceremony.', 14458: 'China occurs in a WWII Office of Strategic Services service record; substantive post-1949 topic unestablished.', 14459: 'China/Taiwan jobs are part of a Korea nominees career biography; specific thematic relevance needs further review.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-third50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-third50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-third50-review-20261109.sqlite3"
    if not backup.exists():
        b = sqlite3.connect(backup);c.backup(b);b.close()
    prior = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    records, changes = [], []
    adapter = GovernmentArticleAdapter()
    for observed in selected:
        row = c.execute("SELECT * FROM materials WHERE id=?", (observed["id"],)).fetchone()
        for field, reading_key in [(key, key) for key in ("source", "published_on", "author", "title", "source_url", "abstract", "keywords", "body")]:
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
    manifest = ROOT / "data/reviews/app-next360-third50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed third fifty working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, media explanation and communication-institution career records approved individually. Birthplaces, incidental jobs, title-only bibliographies, report-directory items and ambiguous multi-speaker attribution remain pending."}, ensure_ascii=False, indent=2).encode()
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
