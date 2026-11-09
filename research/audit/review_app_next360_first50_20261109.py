"""Next 360-URL APP queue, first fifty: individual field and topic decisions."""
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
 '哥伦比亚市民问答把新的中美非军事友谊与贸易关系，同中苏关系变化及亚洲稳定联系起来。': [14312],
 '孟菲斯问答解释建交如何影响美国民众，介绍对华粮食及棉花出口、对台贸易和西太平洋稳定。': [14313],
 '布朗斯维尔集会讲话介绍对华农产品销售机会、当地港口与粮食运输，并说明建交的地方经济意义。': [14314],
 '阿比林集会讲话介绍对华外交及粮食棉花贸易，强调同时增加对台贸易，并讨论发展对第三世界关系。': [14315],
 '沃思堡集会讲话介绍向中国供应粮食及棉花出口的安排，将其同农业政策及选举选择联系起来。': [14316],
 '波特兰集会讲话把对华粮食和棉花出口作为农业政策成果，寻求选民支持继续相关政策。': [14317],
 '西雅图集会讲话把当地港口、对华关系正常化及粮食贸易联系起来，强调其对美国西海岸未来的意义。': [14318],
 '里根选前演说向中国人民表示希望新友谊使两国人民更加接近，并把对外关系置于其美国愿景中。': [14319],
 '败选后记者问答回顾执政中的困难决定，把对华决策列为可能在部分选民中造成政治问题的政策之一。': [14320],
 '出口委员会讲话讨论同中国发展贸易及潜在客户机会，并同时介绍对台贸易增长与出口政策。': [14321],
 '陈香梅出口委员会任命公告记述其中文报业、华盛顿记者及美国之音广播工作经历，为中美传播人物履历提供官方记录。': [14322],
 '美日联合公报把分别扩大对华合作列为双方目标之一，并讨论亚洲安全、经济及区域合作。': [14324],
 '国际交流署副署长提名公告介绍 Conkling 的广播影视行业经历，以及其公司向北京唱片公司提供录音设备建议的工作。': [14326],
 '美国驻华大使提名公告宣布拟由恒安石接替伍德科克，并介绍其汉语能力和中国研究外交经历。': [14328],
 '记者会说明向中国提供技术和防御装备的政策，回应同苏联及波兰问题的关系，并重申台湾关系法义务。': [14329],
 '记者会回应访华邀请及可能时间，同时就有关总统出访与政治处境的报道作出评论。': [14337],
 '记者会说明对华关系及对台军售立场，表示继续发展对华联系并履行台湾关系法，不存在其他秘密协议。': [14346],
 '记者问答回应日本有关侵华与战争历史叙述的提问，强调战后美日友谊及不重提战争情绪的立场。': [14349],
 '面向共和党国会候选人的问答回应对台政策逆转的指责，重申台湾关系法，并批评有关政策被歪曲的报道。': [14350],
 '谈及副总统的采访回顾布什竞选期间访华及涉台问题的沟通，称双方立场不存在分歧，并讨论外界误解。': [14353],
 '记者问答回应对其外交政绩的批评及与卡特政府的比较，并就中美关系改善的历史作出辩解。': [14354],
 '提交国会的国际科技活动年度报告咨文介绍中美联合委员会会议、新合作议定书及中国获取美国技术的政策。': [14357],
 '国际贸易广播讲话解释中美纺织品协议的谈判选择、进口配额与农业出口之间的关系，并强调互利及良好关系。': [14359],
 '瑟蒙德参议员筹款晚宴讲话介绍同中国签订的纺织品协议类别扩大，以及政府对进口和国内市场的政策考虑。': [14361],
}
DEFER = {
 14323:'China trade-mission experience is part of a nominees biography for a different policy role; specific communication-theme linkage requires further review.',
 14325:'China occurs only in the nominees birthplace; no substantive China-policy passage.',
 14327:'China trip is a passing setup to a joke about the Soviet Union; substantive China stance not established.',
 14330:'Multi-item White House digest summarizes meetings; individual authorship and release boundaries need clarification.',
 14331:'China periodical title occurs in a Korea ambassador nominees bibliography; original publications are not supplied.',
 14332:'China/Taiwan relationship is briefly listed among general accomplishments; fuller direct-scope review pending.',
 14333:'China occurs only in the nominees birthplace.',
 14334:'Digest points to an East-West trade report without providing that reports complete text; release boundaries/authorship unresolved.',
 14335:'China occurs in a reference to the previous Pakistan ambassadors new position; not the substance of this nomination.',
 14336:'Digest points to a quarterly East-West trade report; it is not that underlying full report.',
 14338:'Ceremony body includes recipient Walter Judds own remarks and other speakers while author field names only Reagan; clarify complete authorship and boundaries.',
 14339:'Domestic Chinese-American civic organizations appear in an export-council nominees biography; direct US-China international communication linkage uncertain.',
 14340:'China-Burma theatre is a biographical wartime service reference.',
 14341:'White House digest lists a Cancun meeting but supplies no full proceedings; authorship and release boundaries require review.',
 14342:'Short multi-item diary names a Chinese official, without the meeting content or single-release authorship evidence.',
 14343:'China/Taiwan appears in a librarians birthplace and education, not substantive foreign communication policy.',
 14344:'China occurs in an OECD nominees past foreign-correspondent itinerary; direct theme linkage needs further review.',
 14345:'Past China diplomatic postings are biography for a Zambia nomination; no substantive China policy here.',
 14347:'White House diary lists a discussion of China/Taiwan policy without providing the actual policy discussion.',
 14348:'China is briefly named among grain-export destinations in general farm-policy remarks; specific thematic context requires more review.',
 14351:'Past China liaison-office reporting is an Indonesia nominees biography; direct thematic use requires further assessment.',
 14352:'South China Sea is the location of a refugee-rescue story, without substantive China-policy discussion.',
 14355:'China appears only in an appointees birthplace.',
 14356:'China is one location in a list of individual consular assistance cases; direct China discourse-policy relevance unconfirmed.',
 14358:'White House digest summarizes a defense ministers China trip announcement; original release/authorship needs verification.',
 14360:'Repeated are-you-going-to-China questions provide no substantive trip policy detail; direct thematic scope uncertain.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-first50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-first50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-first50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next360-first50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed first fifty working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, media explanation and communication-institution career records approved individually. Birthplaces, incidental jobs, title-only bibliographies, report-directory items and ambiguous multi-speaker attribution remain pending."}, ensure_ascii=False, indent=2).encode()
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
