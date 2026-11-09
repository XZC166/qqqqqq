"""Fixed APP sixth44 review: individually judged topic and field evidence."""
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
 '弗林特市民问答比较美国与苏联的周边环境，并把新中美外交及贸易关系说明为增强美国实力的因素。': [14268],
 '全国讲话回顾中美新关系与全球和平努力，强调军事力量、国家利益及谈判对于外交进展的作用。': [14269],
 '俄克拉何马竞选声明说明扩大对华及对苏农产品市场可增加和平贸易，并寻求选民支持。': [14271],
 '宾夕法尼亚州居民问答以向中国出售钢材及同日本竞争的事例说明美国工业技术和生产力。': [14272],
 '塔尔萨讲话把访华解释为改善关系与和平机会的重要举措，并强调强大国防和国际尊重对谈判的意义。': [14273],
 '结束竞选的声明把农产品出口增长部分归因于改善中美及美苏关系，并介绍相关经济政策成果。': [14275],
 '外交政策广播讲话回顾结束中美相互隔绝，并说明北京会谈同意推进文化、新闻、教育等交流。': [14277],
 '格林斯伯勒讲话把结束中国隔绝与降低未来敌对风险联系起来，表达中美人民成为朋友的愿景。': [14279],
 '布朗特维尔筹款讲话介绍同中国发展友谊、贸易及战略联系，强调相关合作不应建立在战争或对他国威胁之上。': [14280],
 '阿尔伯克基讲话说明访华旨在降低中国长期对美对抗的风险，并讨论医疗合作及美国谈判实力。': [14281],
 '安大略市讲话解释访华和恢复沟通对于降低长期核冲突危险的作用，同时承认两国制度与利益差异。': [14283],
 '温斯顿-塞勒姆讲话以美国钢厂向中国出口并同日本竞争为例，说明美国生产技术和市场竞争力。': [14284],
 '马里昂讲话介绍正同中国谈判的长期粮食销售安排，把中国市场称为美国农业的重要机会。': [14289],
 '圣路易斯市民问答介绍对华钢材和粮食出口，并强调建交后增加中国市场机会同时保持对台贸易友谊。': [14290],
 '锡考克斯筹款讲话说明与中国建立贸易、咨询及和平合作关系，并强调同一时期对台贸易的增长。': [14291],
 '亨普斯特德市民问答以美国钢厂向中国销售的事例，说明现代化、生产力及同日本的价格竞争。': [14293],
 '纽约亚太裔筹款晚宴讲话讨论语言文化根源对中美沟通的价值，重申一个中国政策，并希望相关社群为政府提供理解和建议。': [14295],
 '扬斯敦直播问答回应对华粮食销售可能推高食品价格的疑问，说明政府对价格、出口、就业及农业收入的判断。': [14296],
 '新奥尔良筹款晚宴讲话讨论中美非军事友谊、东亚稳定、钢材出口，并介绍即将签署长期粮食销售协议。': [14298],
 '面向伯利恒钢铁员工讲话以向中国出口的钢厂为例，讨论美国生产力、运输成本及国际价格竞争。': [14300],
 '韦科市民集会讲话回应建交与当地农业的关系，介绍对华棉花销售和新签四年粮食协议。': [14301],
 '格洛斯特市民问答说明中美正常关系与亚洲稳定的联系，表示没有军事条约，并强调维持对台贸易及其他亚洲联盟。': [14302],
 '沃特维尔镇讲话回顾农业出口政策，介绍开拓中国市场、贸易办事处及对华与对台销售增长。': [14305],
 '杰克逊集会讲话解释中美建交与密西西比农业的关系，介绍中国购买美国棉花和每年粮食的安排。': [14310],
 '休斯敦集会讲话介绍建交及每年向中国销售粮食的新协议，并把对华棉花出口置于农业政策成果中。': [14311],
}
DEFER = {
 14270:'China is a brief example of additional friends in a general vision of Americas future; further direct-scope review needed.',
 14274:'China legislation is briefly mentioned among many congressional accomplishments; no specific China measure explained.',
 14276:'China occurs as one destination in a general science advisers international visits paragraph; specific China exchange substance remains uncertain.',
 14278:'China/Taiwan is mentioned in a broad global achievements paragraph; direct contribution of full campaign speech requires further review.',
 14282:'China/Taiwan friendship is briefly listed among global diplomatic successes; retain pending fuller thematic context.',
 14285:'China is briefly listed among recent international relations changes in a general child-future address.',
 14286:'China occurs in an immigrant-origin list in refugee education remarks; direct China communication-policy relevance not established.',
 14287:'China appears briefly in a broad peace and reelection statement; direct full-record scope requires further assessment.',
 14288:'China is briefly listed in an explanation of foreign-policy decisionmaking; remaining full interview scope uncertain.',
 14292:'China is a passing example of coal resources and customers; no substantive US-China discourse-policy connection established.',
 14294:'China relations occur in a short general foreign-policy summary; direct thematic contribution requires further context review.',
 14297:'Approved-acts listing is a directory rather than full legislation; do not substitute title for statute text.',
 14299:'China is briefly listed among new grain markets; full speech is a general local rally and requires further direct-scope assessment.',
 14303:'China normalization is briefly described among anticipated historical achievements; direct full-record contribution not yet determined.',
 14304:'Press-release checklist is a directory pointing to a China grain fact sheet, not its fulltext.',
 14306:'China friendship is briefly listed among campaign accomplishments without a substantive China-policy passage.',
 14307:'China/Taiwan appears briefly among general achievements; fuller direct scope remains to be assessed.',
 14308:'China/Taiwan occurs briefly in a contrast with Reagans military policy; further China-specific context review pending.',
 14309:'China occurs only in the appointees membership of a trade council; no substantive China-policy discussion.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300b-sixth44-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300b-sixth44-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 44
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300b-sixth44-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300b-sixth44-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed remaining forty-four APP working records individually reviewed after 300-URL queue completion. Whole original body and metadata re-extracted and checked against raw evidence; explicit topic/field decisions per record. Direct China-policy, communication, exchange and public economic arguments approved; directory lists and incidental references pending. Six other fetched pages that never formed working materials are reported separately and cannot enter formal export."}, ensure_ascii=False, indent=2).encode()
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
