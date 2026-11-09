"""Fourth bounded APP review: individually judged topic and field evidence."""
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
SUMMARIES = {'记者会说明中印边境冲突与美国对印度援助的立场，并回应有关中苏关系的问题。': [13915],
 '对日本贸易代表团的讲话讨论中国在亚洲的影响，并主张美日合作应对其认为存在的扩张风险。': [13916],
 '媒体问答以对华等敏感外交议题为例，说明公开政策目标、让公众参与讨论的理由。': [13917],
 '经济俱乐部问答为对外援助辩护，并讨论中国、印度及台湾在美国全球战略中的位置。': [13918],
 '电视广播访谈比较中苏对国际冲突与战争的态度，讨论朝鲜战争误判、中印冲突和中苏分歧。': [13920],
 '记者会解释对华关系正常化、台湾安全与上海公报之间的政策关系，并介绍对华沟通渠道和万斯访华安排。': [13923],
 '对意大利总统的讲话比较中国及其他社会主义国家与西方的发展状况，阐述其对民主和经济进步的看法。': [13926],
 '电视访谈通过中国政局变化和多米诺判断解释越南政策，讨论中国在东南亚的影响及美国援助。': [13928],
 '媒体问答介绍万斯访华前的政策准备与政府内部议程讨论安排。': [13929],
 '讲话讨论中苏及其他社会主义国家之间的分化，并将其与美国安全及国际力量格局相联系。': [13930],
 '记者会通报万斯在华与中国领导人会谈的进程，并说明尚待会谈结束后报告结果。': [13937],
 '媒体问答解释万斯访华的议题、双方领导人接触、关系正常化与台湾问题，并讨论公众对政策的支持。': [13939],
 '电视广播访谈说明美国对法国承认中华人民共和国及中国联合国席位问题的立场。': [13940],
 '农业媒体问答说明对华农产品贸易、历史索赔及台湾问题对双边关系和贸易的影响。': [13943],
 '美联社午餐会演说阐述对中国大陆和台湾的不同政策，说明对华关系与其对中国言辞和行为的判断之间的联系。': [13946],
 '报业电话问答说明争取对华小麦销售的目标，并回应移民政策及华裔居民权利问题。': [13948],
 '否决法案的咨文说明兔肉检验规定对中国出口及双边关系的影响，并解释其否决理由。': [13950],
 '悼念声明评价布鲁斯作为首任驻中华人民共和国代表在落实上海公报和关系正常化中的作用。': [13952],
 '记者会面对关于中国力量与中苏摩擦的提问，表示不愿对其他国家的行为作推测。': [13953]}
DEFER = {13919: 'Nomination compilation contains multiple submission dates; individual publication date and document '
        'boundaries need verification.',
 13921: 'China Lake is a California geographic name in a nomination biography, not China-policy content.',
 13922: 'Executive-order signing/effective dates do not independently establish publication day; direct '
        'topic relationship also unresolved.',
 13924: 'No substantive China-related body content; keyword/source gate failed.',
 13925: 'Announcement digest requires individual-document boundaries and publication-day verification.',
 13927: 'China is only one nuclear participant in a generic list, without substantive China-focused '
        'discussion.',
 13931: 'China visit is incidental biographical context in an unrelated energy appointment ceremony.',
 13932: 'No substantive China-related body content; keyword/source gate failed.',
 13933: 'China is one item in a list of difficult policy decisions; direct dissertation relevance not '
        'established.',
 13934: 'China is only briefly listed among unspecified Communist setbacks; substantive China-focused '
        'relationship unresolved.',
 13935: 'Announcement digest does not independently establish the meeting report publication day and byline.',
 13936: 'Prepared but undelivered address: scheduled event date does not establish its first publication '
        'day.',
 13938: 'Editorial event timeline uses presidency start date; not a contemporaneously dated original '
        'document.',
 13941: 'Announcement digest needs independent publication-day/byline verification.',
 13942: 'Republic of China appears only in a generic military-aid recipient list; direct communication '
        'relevance not established.',
 13944: 'China appears only in the agenda for a forthcoming speech, rather than substantive discussion in '
        'this body.',
 13945: 'South China Sea is a geographic reference in an Indochina refugee letter; no substantive '
        'China-policy discussion.',
 13947: 'China appears only in a generic nuclear-weapons-state list; direct topic relevance not established.',
 13949: 'China is mentioned in a question about general Indochina withdrawal; answer provides no substantive '
        'China-focused discussion.',
 13951: 'No substantive China-related body content; keyword/source gate failed.',
 13954: 'China appears in agricultural market and consultation lists without substantive discussion of China '
        'policy.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300-fourth40-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300-fourth40-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 40
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300-fourth40-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300-fourth40-topic-decisions-20261109.json"
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
