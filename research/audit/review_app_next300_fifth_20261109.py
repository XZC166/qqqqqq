"""Fifth bounded APP review: individually judged topic and field evidence."""
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
SUMMARIES = {'讲话以越南沿海军事行动与中国边界的距离为例，说明使用军事力量需要克制。': [13956],
 '公告介绍两党国会代表团访华安排，并将议会交流与上海公报所载增进了解的目标相联系。': [13957],
 '对外援助咨文将台湾减少对美国援助依赖作为援助成效的实例。': [13958],
 '美菲联合声明说明双方对中国在亚洲活动的判断，并重申共同防御及地区安全承诺。': [13960],
 '记者会解释上海公报、一中概念、台湾问题与建立全面外交关系的政策目标。': [13961],
 '竞选讲话讨论中苏分歧，并据此主张以两党共同外交应对国际变化。': [13962],
 '外交讲话区分中国与其他社会主义国家所带来的不同挑战，反对用单一概括代替具体政策判断。': [13964],
 '媒体问答说明布热津斯基访华目的，解释增进了解、扩大贸易、关系正常化与台湾和平解决的关系。': [13965],
 '讲话回应中国核试验及亚洲局势，说明支持亚洲盟友与避免扩大对华战争之间的政策考虑。': [13966],
 '竞选讲话讨论中国核试验与社会主义政治制度可能变化，并阐述美国实力和克制的主张。': [13972],
 '讲话讨论中苏领导权竞争和中国核能力，将其与保持美国外交灵活性及选举选择相联系。': [13974],
 '记者会回应包含中国的国际会议倡议、中苏接触及越南战争是否意在遏制中国扩张的问题。': [13978],
 '欢迎印度总理的讲话评价其改善中印关系的努力，并说明美国所期望的地区和平。': [13981],
 '越南政策演说阐述对中国在亚洲作用的判断，将越南冲突与其所称更广泛的扩张格局相联系。': [13982],
 '记者会否认利用中国对抗苏联，说明对华贸易、科技交流及和平关系的双边目标。': [13983],
 '白宫声明介绍科技代表团访华安排，并将科学技术交流与上海公报所载增进两国人民了解的目标相联系。': [13985],
 '记者会回应中国参与核裁军会议及向越南派遣志愿人员的公开说法。': [13986],
 '面向西欧和日本记者的问答说明对华关系正常化目标、台湾和平解决及双方经贸科技往来。': [13987],
 '追加越南军事拨款咨文解释美国对中国在越南冲突中作用的判断，并以对外承诺和扩张风险论证拨款。': [13988],
 '面向西德记者的问答否认将中国作为对苏杠杆，并说明双边关系与上海公报的政策目标。': [13989]}
DEFER = {13955: 'China appears only in a generic global human-rights list; direct China-focused relevance '
        'unresolved.',
 13959: 'No substantive China-related body content; source/keyword gate failed.',
 13963: 'Digest compilation requires individual document boundaries, publication day and byline '
        'verification.',
 13967: 'China appears only in a list of states ratifying a nuclear protocol; direct topic relevance not '
        'established.',
 13968: 'China is one brief historical analogy in a general election speech; substantive China-focused '
        'relationship not established.',
 13969: 'China consultation appears only in a list of presidential scheduling responsibilities.',
 13970: 'Chinese bomb is a brief introductory example before an economic announcement; direct topic '
        'relevance not established.',
 13971: 'Brzezinski China report is only a scheduling aside in an energy speech.',
 13973: 'China appears as birthplace and diplomatic-service biography in an unrelated Korea nomination.',
 13975: 'China appears only in a generic list of prospective cooperation partners, without substantive China '
        'discussion.',
 13976: 'Source explicitly says remainder of news conference was deep-background briefing; complete original '
        'body not established; China is only biography.',
 13977: 'China is incidental biographical context in praise of an adviser, not substantive China-policy '
        'content.',
 13979: 'China is merely named among diplomatic agenda items without substantive discussion.',
 13980: 'China is listed among charter-amendment votes; direct dissertation communication relationship '
        'unresolved.',
 13984: 'China is only a geographic boundary in an executive order; original publication day also not '
        'established.',
 13990: 'Executive order signing/effective dates do not establish first publication day; retain pending for '
        'date and relevance review.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300-fifth-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300-fifth-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 36
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300-fifth-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300-fifth-topic-decisions-20261109.json"
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
