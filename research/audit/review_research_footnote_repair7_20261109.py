"""Seven explicit article decisions following whole-note source reconciliation."""
import hashlib
import json
import re
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material, material_fingerprint, _source_row
from research_crawler.revalidation import _extract_existing
from research_crawler.spiders.government import GovernmentArticleAdapter

ROOT = Path(__file__).resolve().parents[2]
REASONS = {
 120: "Historical COVID-19 analogies, fear and US-China relations. Restore prior individual topic decision only after retaining the original main body and reconciling all 91 original source footnotes.",
 181: "Hard power, soft power and political warfare affecting the United States. Restore prior individual topic decision after byte-identical main-body retention and reconciliation of all 96 source footnotes.",
 2820: "US-China competition and cooperation. Restore prior individual topic decision after byte-identical main-body retention and exact reconciliation of the one article note.",
 2821: "US-China rivalry and Cold War analogies. Restore prior individual topic decision after preserving the original main body and reconciling all ten article notes.",
 2879: "British China views across opinion, parliament and media. Restore prior individual topic decision after preserving the original main body and reconciling all 33 article notes.",
 300: "Complete article individually read: Asian Barometer research on public China perceptions, regime-type and economic attractiveness, media China-threat framing, soft power and implications for US-China rivalry. Main text, tables, conclusion and all ten source notes reconciled; preserve exact publisher abstract.",
 289: "Complete CSIS article individually read: Pacific military/diplomatic messaging, influence, US reliability perceptions, Australia/New Zealand and Pacific Islands responses. Opening, four substantive sections and final paragraph correspond to the primary page. Preserve exact publisher abstract; correctly classify the CSIS analysis as think-tank material.",
}

def main():
    out = ROOT / "data/reviews/research-footnote-repair7-quality-review-20261109.json"
    if out.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    reconciled = {r["material_id"]: r for r in json.loads((ROOT / "data/reviews/pmc-six-footnote-source-reconciliation-20261109.json").read_text(encoding="utf-8"))}
    before = {mid: dict(c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()) for mid in REASONS}
    previous = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'").fetchall()}
    backup = ROOT / "data/backups/pre-research-footnote-repair7-review-20261109.sqlite3"
    assert not backup.exists(); b = sqlite3.connect(backup); c.backup(b); b.close()
    decisions, changes = [], []
    for mid, reason in REASONS.items():
        row = before[mid]; source = _source_row(store, mid)
        result, metadata_ids = _extract_existing(store, source, GovernmentArticleAdapter())
        parsed = result.get("material"); assert parsed
        assert hashlib.sha256(Path(source["evidence_path"]).read_bytes()).hexdigest() == source["content_sha256"]
        for field, value in (("source",parsed.source),("published_on",parsed.time),("author",parsed.author),("title",parsed.title),("source_url",parsed.source_url)):
            assert row[field] == value, (mid,field)
        if mid in reconciled:
            proof = reconciled[mid]
            assert proof["source_sha256"] == source["content_sha256"]
            assert hashlib.sha256(row["body"].encode()).hexdigest() == proof["old_body_sha256"]
            assert hashlib.sha256(parsed.body.encode()).hexdigest() == proof["new_body_sha256"]
            assert parsed.body.startswith(row["body"] + "\n\n")
        else:
            assert parsed.body == row["body"]
        verification = c.execute("SELECT * FROM material_verifications WHERE material_id=?",(mid,)).fetchone()
        abstract_origin = verification["abstract_origin"]
        assert abstract_origin == "publisher" and parsed.abstract == row["abstract"]
        keywords = row["keywords"]
        if mid == 289:
            terms = ("China","United States","Australia","New Zealand","Pacific Islands","Taiwan","diplomacy","influence","development assistance","security")
            keywords = "; ".join(dict.fromkeys(m.group() for t in terms if (m := re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)",row["body"],re.I))))
            candidate = dict(c.execute("SELECT * FROM candidates WHERE id=?",(source["candidate_id"],)).fetchone())
            assert candidate["source_category"] == "research_literature"
            with c:
                c.execute("UPDATE candidates SET source_category='think_tank' WHERE id=?",(source["candidate_id"],))
            changes.append({"material_id":mid,"previous_candidate":candidate,"correct_category":"think_tank"})
        fields = json.loads(verification["field_sources"])
        fields["keywords"] = row["source_url"]
        updated = replace(parsed,abstract=row["abstract"],keywords=keywords)
        saved, created = store.add_verified_material(source["candidate_id"],row["evidence_id"],updated,abstract_origin=abstract_origin,field_sources=fields,metadata_evidence_ids=metadata_ids)
        assert saved == mid and not created
        current = c.execute("SELECT * FROM materials WHERE id=?",(mid,)).fetchone()
        changes.append({"material_id":mid,"previous_fields":row,"new_body_sha256":hashlib.sha256(current["body"].encode()).hexdigest(),"new_keywords":keywords})
        decisions.append({"material_id":mid,"fingerprint":material_fingerprint(current),"approved":True,"reason":reason,"source_url":current["source_url"],"body_sha256":hashlib.sha256(current["body"].encode()).hexdigest()})
    manifest = ROOT / "data/reviews/research-footnote-repair7-topic-decisions-20261109.json"
    assert not manifest.exists();raw = json.dumps({"records":decisions,"field_corrections":changes,"note":"Explicit individual decisions for these seven articles only; no automatic promotion of any other working PMC record. Original publisher abstracts retained. Earlier incomplete bodies retained in prior evidence/review backups."},ensure_ascii=False,indent=2).encode();manifest.write_bytes(raw)
    results = [audit_material(store,d["material_id"],{**d,"evidence_path":str(manifest),"evidence_sha256":hashlib.sha256(raw).hexdigest()}) for d in decisions]
    passed = {r["material_id"] for r in results if r["status"] == "pass"};assert passed == set(REASONS)
    report = {"generated_at":datetime.now(timezone.utc).isoformat(),"reviewed_records":7,"new_candidates":0,"formal_fulltexts":7,"new_formal_promotions":len(passed-previous),"restored_after_completeness_repair":5,"first_formal_acceptances":2,"pending":0,"withdrawn_formal":0,"duplicate_discoveries":0,"restricted":0,"http_failed":0,"new_http_requests":0,"records":results,"backup":str(backup.relative_to(ROOT))}
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False,indent=2));store.close()

if __name__ == "__main__":
    main()
