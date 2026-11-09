"""Six further individually read early campaign documents."""
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
    14697: "肯尼迪弗雷斯诺讲话讨论与中苏和平共处、制度吸引力及海外民意，并主张重建美国国际形象。",
    14706: "肯尼迪格林斯伯勒讲话讨论美国形象、青年群体对北京的关注，以及国内发展和总统领导对国际影响的作用。",
    14707: "肯尼迪夏洛特讲话将经济发展、国际威望与拉美、非洲、亚洲群体对北京和莫斯科的关注联系起来。",
    14708: "肯尼迪纳什维尔讲话以田纳西河流域发展为例，讨论美国制度示范及发展中国家在美国与莫斯科、北京道路间的选择。",
}
DEFER = {
    14696: "Complete advance-release speech read. Formosa Strait occurs only in a list of international crisis locations; the substantive argument concerns domestic human-rights and welfare policies. No inference that a delivered speech is identical to this advance text.",
    14701: "Complete stored/captured speech read and directly relevant, but the transition after '[Applause] upon you to join me' appears to lack a sentence opening. Resolve source transcription/completeness rather than asserting full text or repairing the missing words.",
}
TERMS = ("China", "Chinese", "United States", "U.S.", "Taiwan", "Formosa", "Peking", "Peiping", "Moscow", "Gallup", "United Nations", "propaganda", "ideological", "public opinion", "prestige", "influence", "educational exchanges", "university research", "peer competitor", "soybeans", "trade", "Communists", "Central Intelligence Agency")


def main():
    output = ROOT / "data/reviews/early-campaign-next6-quality-review-20261109.json"
    assert not output.exists(), "Fixed batch already reviewed; preserve subsequent decisions."
    early = json.loads((ROOT / "data/reviews/app-historical188-first50-reading-20261109.json").read_text(encoding="utf-8"))
    later = json.loads((ROOT / "data/reviews/later-social-next20-reading-20261109.json").read_text(encoding="utf-8"))
    ids = SUMMARIES.keys() | DEFER.keys()
    selected = [r for r in early + later if r["id"] in ids]
    assert len(selected) == len(ids) == 6 and SUMMARIES.keys().isdisjoint(DEFER)
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    backup = ROOT / "data/backups/pre-early-campaign-next6-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/early-campaign-next6-topic-decisions-20261109.json"
    assert not manifest.exists()
    raw = json.dumps({"records": records, "field_corrections": changes, "scope": "Six additional early documents individually read. No decision implied for any unreviewed record. No source body changed."}, ensure_ascii=False, indent=2).encode()
    manifest.write_bytes(raw)
    results = [audit_material(store, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    passed = {r["material_id"] for r in results if r["status"] == "pass"}
    assert passed == set(SUMMARIES), [(r["material_id"], r["reason"]) for r in results if r["material_id"] in SUMMARIES and r["status"] != "pass"]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0, "formal_fulltexts": len(passed), "early_formal_full_documents": 4, "later_original_full_posts": 0, "new_formal_promotions": len(passed - prior), "pending": len(results) - len(passed), "withdrawn_formal": len((prior & ids) - passed), "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests_for_review": 0, "backup": str(backup.relative_to(ROOT)), "records": results}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2))
    store.close()


if __name__ == "__main__":
    main()
