"""All-record source audit. No sampling, network access or evidence deletion."""
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material,material_fingerprint,ReviewedExportStore

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT / "data/reviews/entire-corpus-quality-audit-20261109.json"
APP=ROOT / "data/reviews/app-priority120-source-topic-review-20261109.json"
THINK=ROOT / "data/reviews/thinktank-priority167-source-topic-review-20261109.json"
TIME=ROOT / "data/candidates-time-early-1950s-20261109.csv"


def main():
    store=ResearchStore(ROOT / "data/research.sqlite3")
    c=store.connection
    backup=ROOT / "data/backups/pre-entire-corpus-audit-20261109.sqlite3"
    if not backup.exists():
        b=sqlite3.connect(backup);c.backup(b);b.close()
    approved={}
    for path in (APP,THINK):
        for r in json.loads(path.read_text(encoding="utf-8"))["records"]:
            if not (r.get("scope_decision")=="retain" or r.get("status")=="verified"):
                continue
            row=c.execute("SELECT * FROM materials WHERE source_url=?",(r.get("source_url") or r.get("url"),)).fetchone()
            if row is None or hashlib.sha256(row["body"].encode()).hexdigest()!=r["body_sha256"]:
                continue
            if row["title"]!=r["title"] or row["published_on"]!=r["published_on"]:
                continue
            approved[row["id"]]={"fingerprint":material_fingerprint(row),"reason":r["reason"],"evidence":str(path.relative_to(ROOT))+"#"+str(row["id"])}
    # TIME records were individually source-reviewed and exact-body allowlisted.
    from research_crawler.reviewed_sources import PUBLIC_MEDIA_REVIEWED_ARTICLES
    for row in c.execute("SELECT * FROM materials WHERE source='TIME'"):
        if row["source_url"] not in PUBLIC_MEDIA_REVIEWED_ARTICLES or row["id"]<12900:
            continue
        approved[row["id"]]={"fingerprint":material_fingerprint(row),"reason":"Individually reviewed TIME contemporaneous China/Taiwan/Korean War reporting and complete original paragraphs.","evidence":"ReviewedPublicMediaAdapter exact source/body hash allowlist; tests/test_time_early_china_articles.py"}
    additional=ROOT / "data/reviews/manual-quality-approvals-20261109.json"
    if additional.exists():
        for record in json.loads(additional.read_text(encoding="utf-8"))["records"]:
            row=c.execute("SELECT * FROM materials WHERE id=?",(record["material_id"],)).fetchone()
            if row is not None and material_fingerprint(row)==record["fingerprint"]:
                approved[row["id"]]=record
    topic_manifest=ROOT / "data/reviews/quality-topic-decisions-initial-20261109.json"
    manifest_records=[{"material_id":mid,"fingerprint":r["fingerprint"],"approved":True,"reason":r["reason"],"upstream_evidence":r.get("evidence","")} for mid,r in approved.items()]
    payload={"records":manifest_records,"note":"Positive individual decisions bound to all stored export fields. Upstream source/topic review documents retained."}
    raw=json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8")
    if topic_manifest.exists():
        assert topic_manifest.read_bytes()==raw,"Initial review manifest changed; create a new version instead."
    else:
        topic_manifest.write_bytes(raw)
    approved={r["material_id"]:{**r,"evidence_path":str(topic_manifest),"evidence_sha256":hashlib.sha256(raw).hexdigest()} for r in manifest_records}
    results=[]
    ids=[r[0] for r in c.execute("""SELECT id FROM materials ORDER BY
        CASE WHEN source_url LIKE '%pmc.ncbi%' OR source_url LIKE '%bsky.app%' THEN 0 ELSE 1 END,id""")]
    for i,mid in enumerate(ids,1):
        previous=c.execute("SELECT * FROM quality_reviews WHERE material_id=?",(mid,)).fetchone() if c.execute("SELECT 1 FROM sqlite_master WHERE name='quality_reviews'").fetchone() else None
        # Preserve newer positive/negative decisions when repeating the source
        # audit. audit_material independently rejects stale fingerprints/hashes.
        decision=json.loads(previous["checks_json"]).get("topic_decision") if previous else None
        result=audit_material(store,mid,decision if decision is not None else approved.get(mid));results.append(result)
        if i%100==0:
            print(json.dumps({"processed":i,"total_snapshot":len(ids),"source_pass":sum(r["source_pass"] for r in results),"formal_pass":sum(r["status"]=="pass" for r in results)},ensure_ascii=False),flush=True)
    actual_count=c.execute("SELECT count(*) FROM materials").fetchone()[0]
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"database_material_rows_at_start":len(ids),"database_material_rows_at_end":actual_count,"records_checked":len(results),"unprocessed_new_material_rows":actual_count-len(ids),"source_checks_pass":sum(r["source_pass"] for r in results),"source_checks_pending":sum(not r["source_pass"] for r in results),"formally_reviewed_fulltext":len(ReviewedExportStore(store).get_verified_materials()),"pending_quality_review":sum(r["status"]!="pass" for r in results),"reasons":dict(Counter(r["reason"] for r in results if r["status"]!="pass")),"backup":str(backup.relative_to(ROOT)),"notice":"Every material present at the start was checked individually. Source passes are not final scope approvals. Original evidence and acquisition rows are preserved; official Excel contains only current fingerprint-bound full review passes. Internet reachability has not been reconfirmed for every historical capture.","records":results}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2),flush=True)
    store.close()


if __name__ == "__main__":main()
