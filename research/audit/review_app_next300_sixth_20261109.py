"""Sixth bounded APP review: individually judged topic and field evidence."""
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
SUMMARIES = {'面对德国媒体的访谈否认使用中国牌对苏施压，并说明依据上海公报发展中美关系的理由。': [13991],
 '面向社论漫画家协会的演说阐述对中国在越南战争中目标的判断，并将其与美国在亚洲的信誉相联系。': [13992],
 '美印联合声明讨论中国对地区和平的影响，呈现双方对亚洲安全的共同表态。': [13996],
 '欢迎中国艺术团的讲话将文化交流、两国人民相互了解与关系正常化相联系。': [13999],
 '竞选筹款演说说明暂停轰炸和外交和平倡议的经过，并介绍中国及北越对倡议的反应。': [14000],
 '记者会说明对华关系正常化的节奏，讨论贸易、传播、学生交流及对中国领导层变化的观察。': [14001],
 '致国会的信解释延长贸易和资产管制授权的理由，说明对华商业交易许可与继续冻结中国资产的区别。': [14003],
 '记者会回应有关美国国务卿与中国外长会面的倡议，并说明政府的审议态度。': [14004],
 '白宫声明介绍总统会见中国驻美联络处主任的情况，以及商业、文化、科技交流和双方沟通安排。': [14005],
 '演说阐述对中国在亚洲和越南战争中作用的判断，同时声明美国不谋取中国领土或利益。': [14006],
 '面向农业广播界的问答介绍对华粮食订单和市场开拓，将其列为扩大农产品出口的进展。': [14007],
 '国际商会演说以贸易促进和平的论点解释扩大对中国及苏联贸易的主张。': [14009],
 '记者会回应对华接触和贸易壁垒问题，提出通过科学家、商人、作者和记者互访增进了解。': [14012],
 '签署法案的讲话介绍向中国提供短期农业信贷、争取对华粮食市场的政策。': [14013],
 '演说评论中国内部权力和政策争论，并表达中国大陆未来与邻国及外部世界改善关系的期待。': [14014],
 '海军协会讲话说明美国和平倡议及其所述中国与北越反应，论证继续坚持越南政策。': [14016],
 '公告介绍两党国会代表团访华安排，并将议会交流与上海公报所载相互了解及文化科学往来相联系。': [14017]}
DEFER = {13993: 'Announcement digest requires independent publication-day, author and individual-document '
        'verification.',
 13994: 'China only identifies a geographic boundary in a Vietnam postal-privileges order; first publication '
        'day also unresolved.',
 13995: 'Chinese restaurant is a local geographic example, not substantive China-related material.',
 13997: 'Checklist is a directory of other press releases, not their original full texts.',
 13998: 'China-war threat is a brief background factor in an India aid proposal; direct China-focused '
        'communication relevance not approved.',
 14002: 'Executive-order signing/effective dates do not establish original publication day.',
 14008: 'China appears only in a question about a third-party magazine report; substantive China-focused '
        'content not established.',
 14010: 'China appears in an unfinished question redirected to a future press conference, without '
        'substantive discussion.',
 14011: 'Memo explicitly says it is to be published in the Federal Register; signing/filing day is not '
        'independently verified publication day.',
 14015: 'China visit is only a scheduling aside in an energy-bill ceremony.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300-sixth-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300-sixth-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 27
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300-sixth-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300-sixth-topic-decisions-20261109.json"
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
