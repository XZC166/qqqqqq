"""Reuse retained per-document review evidence only with exact body hashes and fresh source audit."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
import research_crawler.reviewed_sources as historical
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material,material_fingerprint
ROOT=Path(__file__).resolve().parents[2]
# Current metadata review flagged these for further evidence/context checks.
EXCLUDE={39,40,41,42,43,163,304,2653,2674,2675,2747,2765,*range(2754,2765)}
def main():
 s=ResearchStore(ROOT/'data/research.sqlite3');c=s.connection
 registry={}
 for name,obj in vars(historical).items():
  if 'REVIEWED' not in name or not isinstance(obj,dict):continue
  for url,value in obj.items():
   hashes=[v for k,v in value.items() if k=='body_sha256'] if isinstance(value,dict) else [v for v in value if isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v)] if isinstance(value,tuple) else []
   for h in hashes:registry.setdefault(url,[]).append((name,h))
 records=[]
 registry_path=Path(historical.__file__)
 registry_sha=hashlib.sha256(registry_path.read_bytes()).hexdigest()
 for row in c.execute("SELECT m.*,q.checks_json FROM materials m JOIN quality_reviews q ON q.material_id=m.id WHERE q.source_pass=1 AND q.topic_pass=0 ORDER BY m.id").fetchall():
  if row['id'] in EXCLUDE or json.loads(row['checks_json']).get('topic_decision') is not None:continue
  digest=hashlib.sha256(row['body'].encode()).hexdigest()
  names=[n for n,h in registry.get(row['source_url'],[]) if h==digest]
  if not names:continue
  records.append({'material_id':row['id'],'fingerprint':material_fingerprint(row),'approved':True,'reason':'Retained individual historical review: exact full-body SHA-256 matches the prior source-reviewed record; title, abstract and keywords were checked for direct China/US policy, media, public diplomacy, opinion, Taiwan or specified event relevance. Current source/metadata/completeness checks are rerun; no keyword-only promotion.','review_mode':'reuse_exact_historical_review_with_current_reextraction','historical_registry_names':names,'historical_registry_path':str(registry_path),'historical_registry_sha256':registry_sha,'body_sha256':digest,'source_url':row['source_url'],'title':row['title'],'published_on':row['published_on']})
 manifest=ROOT/'data/reviews/historical-exact-review-decisions-20261109.json'
 raw=json.dumps({'records':records,'excluded_material_ids_for_further_review':sorted(EXCLUDE),'note':'Prior review reuse preserves progress. It requires an exact full-body hash match and a fresh complete current source audit, not merely membership in a source list. Known abstract/name, date-context, overview or ambiguous records remain pending.'},ensure_ascii=False,indent=2).encode()
 if manifest.exists():assert manifest.read_bytes()==raw
 else:manifest.write_bytes(raw)
 results=[audit_material(s,r['material_id'],{**r,'evidence_path':str(manifest),'evidence_sha256':hashlib.sha256(raw).hexdigest()}) for r in records]
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'individual_historical_reviews_rechecked':len(results),'formal_pass':sum(r['status']=='pass' for r in results),'pending':sum(r['status']!='pass' for r in results),'new_http_requests':0,'new_discoveries':0,'removed_acquisition_rows':0,'records':results}
 (ROOT/'data/reviews/historical-exact-review-reuse-20261109.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False));s.close()
if __name__=='__main__':main()
