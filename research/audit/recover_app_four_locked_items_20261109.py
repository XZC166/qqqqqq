"""Recover four saved original responses interrupted by a temporary SQLite lock.
No new discovery, HTTP request, evidence timestamp or final topic approval.
"""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from scrapy.http import HtmlResponse
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE_IDS=(35158,35159,35160,35161)
def main():
 report_path=ROOT / "data/reviews/app-four-lock-recovery-20261109.json"
 if report_path.exists():raise SystemExit("Fixed recovery already recorded; preserve later decisions.")
 s=ResearchStore(ROOT / "data/research.sqlite3");c=s.connection
 backup=ROOT / "data/backups/pre-app-four-lock-recovery-20261109.sqlite3"
 if not backup.exists():
  b=sqlite3.connect(backup);c.backup(b);b.close()
 out=[]
 for eid in EVIDENCE_IDS:
  e=c.execute("SELECT * FROM evidence WHERE id=?",(eid,)).fetchone()
  candidate=c.execute("SELECT * FROM candidates WHERE id=?",(e["candidate_id"],)).fetchone()
  assert not c.execute("SELECT 1 FROM materials WHERE evidence_id=?",(eid,)).fetchone()
  raw=Path(e["evidence_path"]).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==e["content_sha256"]
  assert e["source_url"]==candidate["source_url"] and e["status_code"]==200 and e["access_status"]=="allow"
  assert e["body_complete"] and e["metadata_verified"]
  cand=MaterialCandidate(candidate["source_url"],candidate["period"],candidate["source_category"],candidate["query_label"],candidate["platform_id"],candidate["metadata_url"])
  parsed=GovernmentArticleAdapter().extract(HtmlResponse(e["source_url"],body=raw,encoding="utf-8"),cand)
  assert parsed["material"] is not None and parsed["evidence"].content_sha256==e["content_sha256"]
  mid,created=s.add_verified_material(candidate["id"],eid,parsed["material"],abstract_origin=parsed.get("abstract_origin","publisher"),field_sources=parsed.get("field_sources",{}),metadata_evidence_ids=set())
  assert created
  s.update_candidate_status(candidate["id"],"verified","Recovered stored HTTP 200 response after temporary SQLite commit lock; final quality review pending.")
  quality=audit_material(s,mid)
  assert quality["status"]=="pending" and quality["source_pass"]
  out.append({"material_id":mid,"evidence_id":eid,"candidate_id":candidate["id"],"source_url":e["source_url"],"original_fetched_at":e["fetched_at"],"original_raw_sha256":e["content_sha256"],"quality_status":"pending","reason":"Saved response and technical source checks restored without refetching; individual final field/topic review pending."})
 report={"generated_at":datetime.now(timezone.utc).isoformat(),"pipeline_commit_failures":4,"recovered_working_materials":len(out),"new_candidates":0,"new_http_requests":0,"formal_promotions":0,"duplicate_discoveries":0,"unresolved_recovery_failures":0,"backup":str(backup.relative_to(ROOT)),"records":out}
 report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print(json.dumps({k:v for k,v in report.items() if k!="records"},ensure_ascii=False));s.close()
if __name__=="__main__":main()
