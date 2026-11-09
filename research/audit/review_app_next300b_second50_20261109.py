"""Next APP batch second-50 review: individually judged topic and field evidence."""
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
 '面向广播业界的演说以中国核能力及潜在攻击风险说明保障反导系统的政策理由。': [14069],
 '记者会讨论中国核能力对美国太平洋外交可信度的影响，并据此解释保障反导系统。': [14071],
 '致国会的科技咨文说明对华科技交流、卫星通信、教育往来与关系正常化之间的联系。': [14074],
 '空军学院毕业演说回应通过削弱联盟和单方面裁军改善与苏联及中国关系的主张。': [14075],
 '面向国际交换学生的讲话讨论中国未转播登月的情况，并表达增进中美人民沟通和开放交流的愿望。': [14076],
 '面向报刊编辑的问答以中美关系等变化论述美国国际影响力及与苏联竞争中的外交位置。': [14077],
 '党内晚宴讲话将与中国建立友好关系和维持台湾贸易、文化及和平生活的承诺相联系。': [14079],
 '联合国大会演说表明在中国领导人选择结束孤立时，美国愿进行坦诚而认真的对话。': [14080],
 '纪念人民对人民计划的讲话主张把人员交流扩展至中国大陆，促进相互认识与和平。': [14082],
 '越战全国讲话将中国和苏联对北越的支持，纳入解释美国介入越南战争的叙事。': [14084],
 '美日联合声明讨论中国对外关系、美国对台湾的条约承诺以及台湾地区安全与日本的关系。': [14086],
 '记者会表明在符合法律条件下支持给予中国最惠国待遇，并说明贸易往来与双边关系的关联。': [14087],
 '美日联合公报评价对华建交与地区稳定的关系，并回应中越及柬埔寨冲突。': [14089],
 '对日本记者的问答讨论中国现代化、美日对华市场竞争与合作，以及地区和平与难民问题。': [14097],
 '日本广播协会采访说明美国对华政策、台湾安全与交往，并介绍预期访华安排。': [14099],
 '外交政策记者会回应对华关系正常化、台湾在联合国的地位及北京入联问题。': [14100],
 '报纸编辑协会采访讨论结束中国孤立、关系正常化、放宽贸易旅行限制及媒体报道的政策敏感性。': [14102],
 '记者问答以保持对华政策连续性解释让伍德科克继续担任驻华职位的考虑。': [14103],
 '记者会讨论乒乓外交后的对华政策、联合国代表权、两岸关系及访华意愿。': [14104],
 '面向南方媒体的讲话讨论乒乓外交、人员与贸易交流，并以中国未来核能力和国际参与解释政策。': [14106],
 '面向编辑的问答将发展对华友谊、保留与台湾联系及美苏竞争中的外交变化相联系。': [14107],
 '西点军校讲话将结束二十多年敌对与孤立后的中美关系变化，纳入争取世界和平的公开论述。': [14108],
 '致国会领导人的信说明中美索赔协议、解冻中国资产及延续相关管制权限的安排。': [14109],
 '记者会解释中国在联合国的代表权磋商、放宽非战略物项贸易及结束中国孤立的目标。': [14110],
 '面向青年代表的讲话将新外交倡议与开放世界、增进同中国大陆人民的了解相联系。': [14112],
 '面向编辑和广播界的问答回应对日对华农产品出口问题，并介绍贸易和出口促进工作。': [14113],
 '面向东部媒体的讲话以中国未来人口、经济潜力及核风险说明逐步正常化关系的政策理由。': [14114],
 '面向中西部媒体的讲话讨论中国经济潜力、人员与思想交流，以及结束中国孤立后的经济竞争。': [14116],
}
DEFER = {
 14068:'White House daily digest; publication day, authorship and individual release boundaries remain unresolved.',
 14070:'Chinese vice-premier visit is only a passing timing reference in a Canadian bilateral ceremony.',
 14072:'China Lake is a US geographic facility name, not China-related subject matter.',
 14073:'Republic of China occurs only among aid recipient countries; a direct China-discourse relationship remains unresolved.',
 14078:'Relevant Guam background briefing, but opening restricts direct quotation; first publication day needs evidence distinct from delivery day.',
 14081:'China occurs only in a generic list of diplomatic human-rights difficulties; specific China argument not established.',
 14083:'Relevant exchange announcement embedded in daily digest; publication-day, byline and document boundaries need separate verification.',
 14085:'Chinese guerrilla service is a World War II biographical detail in an unrelated personnel nomination.',
 14088:'China is an itinerary entry; no specific China-related message content disclosed.',
 14090:'China is an itinerary entry; specific China-related diplomatic content not provided.',
 14091:'Daily White House meeting diary, not the substantive China meeting text; byline/day unresolved.',
 14092:'No direct China-related text; source/keyword gate failed.',
 14093:'Daily White House meeting diary, not the substantive China meeting text; byline/day unresolved.',
 14094:'Chinese leadership change is only an analogy for speculation about the Egyptian succession.',
 14095:'China is only in a generic list of strengthened diplomatic friendships.',
 14096:'Paired-toast title but stored source main field contains only Nixon toast; whole-document boundaries require clarification.',
 14098:'Indo-China refers to Vietnam/Laos/Cambodia POWs rather than China-related discourse.',
 14101:'Daily digest of appointments; no independently verified individual China committee release or publication day.',
 14105:'China appears only in a roll call of visiting countries.',
 14111:'Determination explicitly says it shall be published in Federal Register; signing/filing day not verified as publication day.',
 14115:'China appears only as a brief achievement item in a general party agenda; direct substantive relevance unresolved.',
 14117:'Combined Carter/Kreps letters have different dates and authors while header attributes Carter; publication day and field correspondence unresolved.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300b-second50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300b-second50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300b-second50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300b-second50-topic-decisions-20261109.json"
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
