"""Fixed mixed-source pending records: individual source, field and topic decisions."""
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
 'AP factual explainer covers July 2018 US-China tariffs, technology-transfer accusations, retaliation and their economic effects; all three article sections complete.': [2],
 'Research directly compares China Daily and Time COVID-19 reporting using critical discourse analysis and appraisal theory; article metadata and main-body conclusion checked.': [64],
 'Research examines US-China COVID-19 historical analogies, official statements, media coverage and fear discourse, including Pearl Harbor and Boxer Indemnity comparisons.': [120],
 'VOA report examines state-backed Chinese online commenting, the Harvard study, public-opinion management and interview evidence; original Joyce Lau byline and publication time checked.': [259],
 'Research intervenes in contemporary US-China cold-war policy discourse, comparing advocacy for confrontation with constrained competition and cooperation.': [2820],
 'Research examines the US-China new-Cold-War debate and distinctions from the Soviet-American rivalry, including cyber competition and nuclear deterrence.': [2821],
 'Research directly examines British perceptions of China using 2020 public-opinion surveys, parliamentary debate and media coverage, within the user-authorized Five Eyes scope.': [2879],
}
DEFER = {
 39:'Editorial intro is followed by Read our previous postings related-reading links; stored abstract also ends mid-sentence. Clean source boundaries before approval.',
 40:'Collection page includes Return to the Introduction navigation and an explicit prepared-by credit absent from the author field; metadata and editorial/catalogue boundaries unresolved.',
 41:'Long editorial essay and document annotations require further original-page boundary and publication/byline verification; linked documents must not be represented as acquired fulltexts.',
 42:'Page introduces a television documentary and linked-document annotations; distinguish a complete independent written editorial from the video description before fulltext approval.',
 43:'Stored abstract repeats the title rather than an actual abstract; check explicit editorial byline and complete collection-page boundaries.',
 118:'Main-body extraction ends with author biography and personal homepage; isolate article body and verify boundaries before promotion.',
 153:'Abstract includes supplementary-material boilerplate and main text ends with author biography; relevant study retained pending cleanup.',
 166:'Study focuses on Japanese online news discourse; direct US-China thematic linkage requires further review, and dangling supplementary-data heading needs boundary checking.',
 183:'Abstract appends supplementary-material availability text and body includes a dangling electronic-supplement link placeholder; clean and confirm main-body boundaries.',
 215:'Article extraction includes author biographies, contributor emails and administrative back matter; isolate original main body before promotion.',
 254:'PDF text includes copyright/footer/header material; page-by-page extraction cleaning and completeness verification pending.',
 258:'PDF text includes journal copyright and running-header/footer material; source-faithful page-by-page body cleaning pending.',
 260:'Actual transcript is available, but replacement characters and broadcast-versus-publication date evidence require review; no video downloaded or summary counted as fulltext.',
 301:'Extraction includes Publishers note and supplementary-link boilerplate; verify direct US-China linkage and clean boundaries.',
 304:'January 1 date may be a year-only catalogue default; PDF identifies 2000 but does not yet substantiate exact publication day. Running page numbers also need cleaning.',
 318:'International media-relations paper requires original-page metadata and specific US-China thematic linkage verification before approval.',
 4318:'Relevant comparative Chinese diplomatic discourse study, but current body includes Publishers note boilerplate; clean from original source before promotion.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/research-media-core24-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/research-media-core24-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 24
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-research-media-core24-review-20261109.sqlite3"
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
            abstract = row["abstract"]
            origin = c.execute("SELECT abstract_origin FROM material_verifications WHERE material_id=?", (row["id"],)).fetchone()[0]
            assert origin == "publisher" and abstract == parsed.abstract
            fields = json.loads(c.execute("SELECT field_sources FROM material_verifications WHERE material_id=?", (row["id"],)).fetchone()[0])
            fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
            mid, created = s.add_verified_material(source["candidate_id"], row["evidence_id"], replace(parsed, abstract=abstract, keywords=keywords),
                                                 abstract_origin=origin, field_sources=fields, metadata_evidence_ids=metadata_ids)
            assert not created and mid == row["id"]
            changes.append({"material_id": mid, "previous_fields": dict(row), "new_abstract": abstract, "new_keywords": keywords})
            row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        records.append({"material_id": row["id"], "fingerprint": material_fingerprint(row), "approved": approved,
                        "reason": "Individual topic/field review: " + (summaries[row["id"]] if approved else DEFER[row["id"]]),
                        "source_url": row["source_url"], "body_sha256": observed["body_sha256"]})
    manifest = ROOT / "data/reviews/research-media-core24-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed mixed research/media records reviewed individually. Whole main body re-extracted and byte-for-byte compared; publisher abstracts preserved, article metadata and relevant sections plus ending boundaries checked. Topic decisions do not authorize later records. Explicit pending reasons retained for source-template, date, author and scope issues."}, ensure_ascii=False, indent=2).encode()
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
