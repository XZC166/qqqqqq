"""Explicit decisions for 21 individually read early documents and 20 later posts."""
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
    14660: "杜鲁门记者会回应塔夫脱关于援助台湾的说法，并说明此前台湾声明仍代表其立场。",
    14663: "杜鲁门记者会回应麦克阿瑟被免职及中国参战情报争议，讨论威克岛会谈、中央情报局报告与公众判断所需证据。",
    14671: "艾森豪威尔向广告理事会讨论国际意识形态竞争、争取民众理解和贸易合作，并将台湾列入需要说明美国理念的地区。",
    14677: "艾森豪威尔致国会咨文回顾联合国活动，称被中国关押的美国飞行员获释体现联合国及世界舆论的作用；本条为咨文本身。",
    14693: "肯尼迪缅因州竞选讲话引用盖洛普调查，讨论美国国际形象以及与莫斯科、北京争取外部社会认同的竞争。",
    14694: "肯尼迪密歇根州竞选讲话引用海外调查，讨论美国威望及人们转向莫斯科、北京的风险，并主张重建美国实力。",
    14695: "肯尼迪庞蒂亚克竞选讲话将国内发展与国际形象联系起来，批评美国影响减弱及外部社会转向赫鲁晓夫和北京。",
    14698: "肯尼迪图莱里竞选讲话讨论非洲领导人对北京、莫斯科的关注，主张重建美国威望、实力和国际领导地位。",
    14699: "肯尼迪贝克斯菲尔德讲话讨论非洲领导人对北京和莫斯科的关注，并将美国国内活力与对外吸引力联系起来。",
    14700: "肯尼迪伯班克讲话讨论拉美、亚洲和非洲社会对莫斯科、北京的关注，主张通过改善美国国内发展增强国际影响。",
    14704: "肯尼迪陶森讲话讨论美国国际形象、非洲学生赴北京等地学习以及国内发展与对外吸引力的关系。",
    14705: "肯尼迪约克讲话讨论拉美、非洲、亚洲对美国与苏中道路的选择，将经济、军事能力与国际威望联系起来。",
    3327: "CSIS 帖文称大学研究能把公共资金转为经济、健康和安全收益，并称中国正迅速成为美国的同级竞争者。",
    3329: "CSIS 帖文称美国与拉美及加勒比地区的教育交流有助于经济联系、人力资本、应对中国影响和改善公众态度。",
    3332: "CSIS 帖文讨论大学研究与公共资金的效益，并称中国正迅速成为美国的同级竞争者。",
    3335: "CSIS 帖文转述美国公布的中国大豆采购承诺，并称即使履约，2025 年美国对华大豆销售仍将为 2018 年以来最差。",
}
DEFER = {
    14661: "Complete conference read, but the China-specific passage is an unanswered question on Nationalist troops. The Korean-war speech-control discussion does not establish a sufficiently direct China communication account for this decision.",
    14662: "Complete conference read; original captured transcription splits footnote 4 and inserts its continuation into an unrelated presidential sentence. Resolve original transcription/paragraph fidelity before full-text acceptance.",
    14664: "Complete conference read; Formosa occurs in a question deferred without an answer. Domestic propaganda discussion concerns congressional price controls, not China-directed communication.",
    14668: "Complete speech read; Formosa is only one example of issues public officials must handle. Domestic campaign communication is not demonstrated to concern China.",
    14679: "Complete speech read; Formosa occurs only in a brief list of past crisis locations. Specific China communication substance remains unestablished.",
    14680: "Complete speech read; Formosa appears in a short list of earlier bipartisan decisions; most international messaging concerns Hungary and Egypt.",
    14681: "Complete letter read; pre-1949 Chinese-delegation career background and a Formosa Declaration list entry do not establish a substantive China communication account.",
    14682: "Complete conference read; Formosa is a named aid recipient in a broad mutual-security appropriations appeal; more direct China communication relevance requires assessment.",
    14683: "Complete address read; Formosa appears in opening crisis/outcome lists, whereas the substantive argument concerns defense reorganization and Soviet propaganda.",
    221: "Complete AP post read and directly relevant, but current field-provenance snapshot is missing or mismatched. Retain original captures pending provenance repair.",
    3319: "Complete post read; Chinese automakers and emerging markets alone do not establish the US-centred communication relationship for this decision.",
    3320: "Video promotional post, not the video's transcript or full article; no video processed.",
    3321: "Post quotes a passage and links an analysis; do not promote a quoted excerpt as the full analysis.",
    3322: "Post quotes a passage and links an analysis; linked analysis completeness is not established.",
    3323: "Podcast episode description only; no complete transcript.",
    3324: "Event registration invitation only; no substantive event transcript.",
    3325: "Quoted analysis excerpt in a separate post; not the full linked analysis.",
    3326: "Event video promotion only; no event transcript or video processed.",
    3328: "Podcast description only; neither the episode transcript nor the cited paper full text.",
    3330: "Podcast description only; not a complete transcript.",
    3331: "Podcast episode description only; not a complete transcript.",
    3333: "Question-led preview links a fuller analysis; retain pending as preview, not the linked analysis full text.",
    3334: "Podcast description only; not a complete transcript.",
    3336: "Video/shorts promotion only; no complete source transcript or video processed.",
    3337: "Question-led preview links a fuller analysis; distinct post ID retained, but not accepted as full analysis.",
}
TERMS = ("China", "Chinese", "United States", "U.S.", "Taiwan", "Formosa", "Peking", "Peiping", "Moscow", "Gallup", "United Nations", "propaganda", "ideological", "public opinion", "prestige", "influence", "educational exchanges", "university research", "peer competitor", "soybeans", "trade", "Communists", "Central Intelligence Agency")


def main():
    output = ROOT / "data/reviews/early21-later-posts20-quality-review-20261109.json"
    assert not output.exists(), "Fixed batch already reviewed; preserve subsequent decisions."
    early = json.loads((ROOT / "data/reviews/app-historical188-first50-reading-20261109.json").read_text(encoding="utf-8"))
    later = json.loads((ROOT / "data/reviews/later-social-next20-reading-20261109.json").read_text(encoding="utf-8"))
    ids = SUMMARIES.keys() | DEFER.keys()
    selected = [r for r in early + later if r["id"] in ids]
    assert len(selected) == len(ids) == 41 and SUMMARIES.keys().isdisjoint(DEFER)
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    backup = ROOT / "data/backups/pre-early21-later-posts20-review-20261109.sqlite3"
    assert not backup.exists()
    b = sqlite3.connect(backup); c.backup(b); b.close()
    prior = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'").fetchall()}
    records, changes = [], []
    for observed in selected:
        mid = observed["id"]
        row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        for k in ("source", "published_on", "author", "title", "source_url", "abstract", "keywords", "body"):
            assert row[k] == observed[k], (mid, k)
        assert hashlib.sha256(row["body"].encode()).hexdigest() == observed["body_sha256"]
        approved = mid in SUMMARIES
        if approved:
            source = _source_row(store, mid)
            result, metadata_ids = _extract_existing(store, source, GovernmentArticleAdapter())
            parsed = result.get("material")
            assert parsed and parsed.body == row["body"]
            assert hashlib.sha256(Path(source["evidence_path"]).read_bytes()).hexdigest() == source["content_sha256"]
            for attribute, field in (("source", "source"), ("time", "published_on"), ("author", "author"), ("title", "title"), ("source_url", "source_url")):
                assert getattr(parsed, attribute) == row[field], (mid, field)
            abstract = "据正文整理：" + SUMMARIES[mid]
            keywords = "; ".join(dict.fromkeys(m.group() for t in TERMS if (m := re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", row["body"], re.I))))
            assert keywords
            snapshot = c.execute("SELECT * FROM material_verifications WHERE material_id=?", (mid,)).fetchone()
            assert snapshot and snapshot["abstract_origin"] == "derived"
            fields = json.loads(snapshot["field_sources"])
            fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
            saved, created = store.add_verified_material(source["candidate_id"], row["evidence_id"], replace(parsed, abstract=abstract, keywords=keywords), abstract_origin="derived", field_sources=fields, metadata_evidence_ids=metadata_ids)
            assert saved == mid and not created
            changes.append({"material_id": mid, "previous_fields": dict(row), "new_abstract": abstract, "new_keywords": keywords})
            row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        reason = ("Individually read same-source document: " + SUMMARIES[mid]) if approved else DEFER[mid]
        if approved and mid < 10000:
            reason += " Complete original institutional post only; not its linked article or audiovisual work. Same-text posts with different platform IDs remain distinct."
        records.append({"material_id": mid, "fingerprint": material_fingerprint(row), "approved": approved, "reason": reason, "source_url": row["source_url"], "body_sha256": observed["body_sha256"]})
    manifest = ROOT / "data/reviews/early21-later-posts20-topic-decisions-20261109.json"
    assert not manifest.exists()
    raw = json.dumps({"records": records, "field_corrections": changes, "scope": "21 early full documents and 20 later full posts individually read. No decision implied for the other 29 source-screened early records. No source body changed."}, ensure_ascii=False, indent=2).encode()
    manifest.write_bytes(raw)
    results = [audit_material(store, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    passed = {r["material_id"] for r in results if r["status"] == "pass"}
    assert passed == set(SUMMARIES), [(r["material_id"], r["reason"]) for r in results if r["material_id"] in SUMMARIES and r["status"] != "pass"]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0, "formal_fulltexts": len(passed), "early_formal_full_documents": 12, "later_original_full_posts": 4, "new_formal_promotions": len(passed - prior), "pending": len(results) - len(passed), "withdrawn_formal": len((prior & ids) - passed), "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests_for_review": 0, "backup": str(backup.relative_to(ROOT)), "records": results}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2))
    store.close()


if __name__ == "__main__":
    main()
