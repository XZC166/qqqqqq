"""Next 360-URL APP queue, fourth fifty: individual field and topic decisions."""
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
SUMMARIES = {'就伊朗军售争议发表全国讲话时，里根以尼克松一九七一年秘密接触中国为先例，说明其对秘密外交和谨慎沟通的辩护。': [14462], '面向西欧的卫星电视讲话把中国改革描述为十亿多人初尝自由，并将其纳入全球自由发展趋势的论述。': [14464], '国际科技活动年度报告咨文回顾中美科技协议及二十七项议定书，介绍新合作领域和联合委员会会议安排。': [14465], '悼念商务部长鲍德里奇的讲话把建立对华贸易联系列为其主要政绩，并说明贸易在两国关系中的地位。': [14468], '关于美苏关系的讲话把中国经济改革同其他国家民主进展并列，阐述经济与政治自由联系的看法。': [14469], '联合国大会演说以中国和印度农业市场变化说明经济自由论点，并反对以新世界信息秩序名义控制媒体。': [14470], '在国际货币基金组织和世界银行会议讲话中，里根列举中国改革后的农业和收入变化，以支持其反对国家管制的经济论述。': [14471], '面向美国新闻署国际志愿理事会的讲话介绍美国经济及自由市场主张，并以中国扩大经济自由作为国际变化的例子。': [14472], '面向亚太新闻机构的书面问答介绍美国地区角色，并把降低对华军事威胁列为苏联促进亚洲和平可采取的措施。': [14476], '面向东南亚新闻机构的书面问答评价中国在柬埔寨问题上的作用，并讨论香港和台湾等经济体的市场开放。': [14480], '在莫斯科大学讲话问答中，里根把中国改革和其他亚洲经济体的发展作为经济自由扩展的例子，面向苏联学生阐述相关理念。': [14481], '大西洋理事会讲话将中国、印度和其他地区减少国家经济控制的变化，同美国经济表现及自由市场理念的国际传播联系起来。': [14482], '全国广播讲话把中国等地放松国家经济控制描述为思想竞争进展，并介绍多伦多峰会与尼加拉瓜政策。': [14483], '面向加拿大团体的讲话称自由企业趋势正进入中国和苏联，并以此说明北美经济机会和自由市场政策。': [14484], '商业圆桌会议讲话把中国等国减少经济管制与增长联系起来，阐述经济和个人自由相联系的政策主张。': [14485], '布什接受总统候选人提名的演说回顾其对华任职，并将中国变化纳入自由理念在世界扩展的政治叙事。': [14489], '联合国大会告别演说把中国等国的变化同和平及自由相联系，并说明美国愿意向世界传播自身经验的立场。': [14494], '全国商会基金会讲话把中国、苏联及东欧变化归于美国示范的影响，并将这一判断同布什即将执政联系起来。': [14503], '美国企业研究所讲话批评关于毛泽东时期中国等社会主义制度的知识论述，并把中国自由化视为国家社会主义困境的证据。': [14505], '面向政府官员的国内政策讲话宣称美国私人企业的示范对中国和苏联具有吸引力，并说明其对经济政策遗产的评价。': [14506], '弗吉尼亚大学讲话问答援引自由之家数据评论中国和苏联的自由状况，并讨论社会主义经济理论受到重新审视的趋势。': [14507], '韩联社书面问答解释布什访华与韩国半岛议题的关系，并回应韩国改善对华关系及有关多边会谈的提议。': [14508], '赴亚洲途中在阿拉斯加讲话时，布什强调发展稳定中美关系的重要性，并说明其亚洲行程的外交意义。': [14510], '北京欢迎宴会祝酒辞说明中美三个联合公报、一个中国与台湾立场，评价改革、经贸及教育交流，并强调两国合作和友谊。': [14511]}
DEFER = {14463: 'South China Sea is only the location of a wartime rescue in a Voyager crew ceremony; no relevant post-1949 China-policy content.', 14466: 'China is one old administrative post in a Seychelles nominees biography; no substantive China communication-policy passage.', 14467: 'China is only an example of an old nation in a domestic constitutional-history speech.', 14473: 'Diary lists Deng Pufang meeting without its actual content; individual release authorship unresolved.', 14474: 'China is only an export-volume comparator in an argument about aid to other regions; direct thematic scope unestablished.', 14475: 'Explicitly an excerpt of a congressional report, not the complete report. China/Taiwan chiefly appear in an editorial country-code key; no promotion as full report.', 14477: 'Digest only lists a China trade meeting without actual proceedings; single-release authorship unresolved.', 14478: 'China is only part of Bushs resume in campaign remarks.', 14479: 'China population and queues appear in a joke at a photographers dinner, not substantive China-policy discussion.', 14486: 'China roles form an ILO appointees past research and diplomatic biography; direct communication-theme context requires further assessment.', 14487: 'China is only architect I.M. Peis birthplace in an arts-award ceremony.', 14488: 'China is only a Bush resume entry in campaign remarks.', 14490: 'China is only a Bush resume entry in campaign fundraising remarks.', 14491: 'China is only a Bush resume entry in campaign fundraising remarks.', 14492: 'Appointment concerns property negotiations with China and Bulgaria, but no substantive negotiating position or communication-theme account is provided.', 14493: 'Body is a multi-participant debate but source author field is only the collection label Presidential Candidate Debates; verify actual author attribution before acceptance.', 14495: 'China is only a Bush resume entry in fundraising remarks.', 14496: 'China is only an appointees birthplace; no substantive China policy.', 14497: 'China is only a Bush resume entry in fundraising remarks.', 14498: 'China is one country in a generic immigrant identity analogy; specific US-China international communication relevance unestablished.', 14499: 'South China Sea is only a wartime travel location in a medal citation.', 14500: 'China is only a Bush resume entry in campaign remarks.', 14501: 'The stored/source-extracted body ends mid-sentence at And if I might, Id like to pause here and; completeness cannot be confirmed and no full-text claim is made.', 14502: 'China is only a Bush resume entry in campaign remarks.', 14504: 'China is merely a past posting reference in a news conference introducing several officials; actual authorship also needs multi-speaker review.', 14509: 'Visit to China and a Chinese proverb introduce a domestic volunteerism message; direct thematic substance requires fuller context.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-fourth50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-fourth50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-fourth50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next360-fourth50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed fourth fifty working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, media explanation and communication-institution career records approved individually. Birthplaces, incidental jobs, title-only bibliographies, report-directory items and ambiguous multi-speaker attribution remain pending."}, ensure_ascii=False, indent=2).encode()
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
