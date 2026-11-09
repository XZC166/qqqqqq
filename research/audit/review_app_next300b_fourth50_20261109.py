"""Fixed APP fourth50 review: individually judged topic and field evidence."""
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
 '志愿行动颁奖晚宴讲话介绍访华安排，强调让中国人民了解美国寻求和平、关心儿童及受困民众，并讨论人民之间的信息传递。': [14169],
 '在明十三陵与记者交谈时，尼克松评价中国历史文化，主张恢复中美人民访问与相互认识，并回应赴华旅游问题。': [14173],
 '科技政策咨文回顾访华期间促进科学技术等领域联系与交流的约定，并期待进一步进展。': [14179],
 '亚太裔民主党人晚宴讲话说明中美建交及对台关系，引用对台贸易增长数据，主张发展亚洲友谊和交流。': [14180],
 '与德国记者交谈时回应访华采访团名额问题，并介绍联邦德国与中国的贸易及相关会谈。': [14184],
 '面向纽豪斯报业编辑的采访介绍中美关系正常化，强调同时维持对台关系，并以对台贸易增长说明政策效果。': [14186],
 '美土联合声明介绍尼克松访华及将访苏的讨论，记述土耳其总理对相关和平努力的支持。': [14187],
 '记者会讨论美中苏力量关系、访华与越战、对华谈判及交流安排，说明中国可能发展的国际作用。': [14189],
 '奥克兰社区讲话介绍建交与西海岸出口增长、中国港务人员访美及维持对台贸易的关系。': [14192],
 '抵达渥太华讲话回顾访华前同加拿大磋商，比较长城与开放边界，并主张通过沟通和谈判处理国家分歧。': [14193],
 '波托拉谷筹款晚宴讲话把中美建交与西海岸出口及对台贸易增长联系起来，说明对以往非友好国家开放的意义。': [14194],
 '莫德斯托筹款讲话说明承认中华人民共和国带来的友谊与出口机会，并强调同时维持对台友谊和贸易。': [14196],
 '加拿大议会演说说明访华恢复长期中断的沟通，表示改善中美及美苏关系不针对其他国家，并主张讨论分歧而不诉诸战争。': [14197],
 '在东京接受日本记者采访时介绍将与华国锋会谈，说明中美和中日关系、亚洲稳定及避免结成针对苏联的联合行动。': [14198],
 '康纳利牧场问答讨论对华贸易机会与限制，强调现实融资条件，并将访华和访苏置于争取和平的外交政策中。': [14201],
 '蓝厅重新开放讲话回顾美国总统首次接待中国外交代表的历史，并将房间的象征意义与重新开启中美对话联系起来。': [14203],
 '对记者介绍访苏行程时比较访华采访条件，说明缺少外交关系及正在进行的谈判如何影响记者获取每日实质新闻。': [14205],
 '向奥运游泳队颁奖时谈及队员将赴中国，称其为外交使者，并希望运动员在访问中为美国增光。': [14208],
 '签署法律声明说明授权海外私人投资公司在中国开展业务，把保险支持的私人投资与中美互利经济关系联系起来。': [14210],
 '向国会报告出访成果时回顾中美长期隔绝与对抗，主张通过北京及莫斯科之行发展理解、尊重和分歧解决机制。': [14211],
 '致参议院领导人的信把减少同中国及苏联直接对抗的风险列为争取和平的进展，并就对外援助立法寻求支持。': [14213],
 '美国建国二百周年筹备讲话把访华和访苏的目的之一说明为促进人民接触，减少恐惧与无知并培养信任合作。': [14214],
 '蒙代尔接受副总统提名的演说把对华正常化解释为体现美国价值与利益、制衡苏联的政策，并回顾在华交流经历。': [14215],
}
DEFER = {
 14168:'China normalization and Taiwan friendship occur in a general achievements paragraph; remaining direct thematic scope needs assessment.',
 14170:'China occurs in broad Third World friendship/achievements comparisons; assess the complete speech context before thematic approval.',
 14171:'Dock-strike statement has no China/Taiwan body reference and fails the missing abstract/keywords source gate.',
 14172:'China is briefly named among new friendships in a wide-ranging townhall; direct study linkage remains to be assessed.',
 14174:'Brief China/Taiwan achievements reference in general policy interview; retain pending fuller scope review.',
 14175:'Paired Nixon/Nan Ping toast title but body only supplies Nixon remarks; complete same-item scope/authorship not verified.',
 14176:'China appears only in a list of national Olympic committees joining the boycott; direct China-topic substance uncertain.',
 14177:'Paired Nixon/Chang Chun-chiao toast title but only Nixon remarks in extracted body; do not claim both toasts complete.',
 14178:'China appears only as an appointee birthplace; no substantive theme connection.',
 14181:'Foreign-correspondents interview has only a passing China opening among general foreign policy achievements; direct scope uncertain.',
 14182:'Paired Nixon/Heath remarks title but extracted main body contains only presidential response; boundaries unresolved.',
 14183:'China appears in a hypothetical list of states joining the Soviet Olympic boycott; direct China-policy substance uncertain.',
 14185:'Paired Nixon/Erim toast scope not established, and China is principally an anecdote about a previous banquet.',
 14188:'Multi-item White House digest mixes meetings and announcements; individual publication/author/body boundaries need review.',
 14190:'China normalization occurs briefly among global diplomacy achievements; further thematic context review needed.',
 14191:'Great Wall anecdote is used for a domestic moral-education point rather than a clearly established China communication-policy discussion.',
 14195:'China opening appears in a brief list of youth-conference recommendations; direct contribution of this administrative letter needs review.',
 14199:'China chiefly occurs in global East-West comparisons and a banquet joke; the full OAS dinner remarks require further direct-scope assessment.',
 14200:'Very long Republican platform: substantial China/Taiwan section identified, but whole-platform boundaries and completeness still require further review.',
 14202:'Checklist is a directory of press releases, not the underlying China meeting news conference fulltext.',
 14204:'China/Taiwan friendship is briefly listed among general campaign achievements; direct research contribution needs further scope review.',
 14206:'China occurs only as a potential future application of coal technology; direct dissertation relevance unconfirmed.',
 14207:'China is briefly named among efforts for peace in a mainly US-Soviet public address; further direct scope review needed.',
 14209:'Paired Nixon/Shah toast authorship and complete-item boundaries unresolved; preserve source evidence pending.',
 14212:'List of approved acts is a directory record; linked legislation text has not been obtained as this body.',
 14216:'Very long Democratic platform contains a substantive China-policy section, but whole-document boundaries/completeness still need further review.',
 14217:'China occurs mainly in a brief claim about Soviet encirclement; the complete opposition-candidate address requires further China-scope review.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300b-fourth50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300b-fourth50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300b-fourth50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300b-fourth50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed next fifty acquired APP records individually reviewed. Original full body re-extracted and byte-for-byte compared, metadata and document boundaries checked, substantive topical passages reviewed. Directory records, incidental names, ambiguous paired speeches and long platforms requiring further boundary review retained pending. Four records recovered from saved evidence after database-lock pipeline failures are included; no HTTP retry or fabricated text."}, ensure_ascii=False, indent=2).encode()
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
