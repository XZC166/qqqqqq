"""Individually read complete original social posts; never linked-article full texts."""
import hashlib,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material,material_fingerprint
ROOT=Path(__file__).resolve().parents[2]
APPROVED={222,2880,*range(2885,2890),*range(2892,2897),*range(2898,2913),2913,2914,2915,2916,2917,2919,*range(2920,2932),*range(2933,2943),3170,3174,3176,3193,3196,3211,3213,3214,3216,3217,3221,3223,3224,3230,3231,3232,3233,3236,3239,3240,3241,3243,3244,3246,3248}
ALL_IDS={222,*range(2880,2891),*range(2892,2920),*range(2920,2943),3170,3174,3176,3177,3193,3196,3211,3213,3214,3215,3216,3217,3220,3221,3223,3224,3230,3231,3232,3233,3236,3237,3239,3240,3241,3242,3243,3244,3245,3246,3247,3248}
def main():
 report_path=ROOT/'data/reviews/social-fixed95-quality-review-20261109.json'
 if report_path.exists():raise SystemExit('Fixed batch already reviewed; preserve later approvals and its report.')
 s=ResearchStore(ROOT/'data/research.sqlite3');c=s.connection
 rows=[c.execute('SELECT * FROM materials WHERE id=?',(i,)).fetchone() for i in sorted(ALL_IDS)]
 assert all(rows)
 records=[]
 for row in rows:
  approved=row['id'] in APPROVED
  if approved:assert row['source'] in {'The New York Times','The Associated Press','CSIS'}
  records.append({'material_id':row['id'],'fingerprint':material_fingerprint(row),'approved':approved,'reason':'Entire original post read: direct China image, US-China relations, Taiwan/Hong Kong, trade/technology competition or public-discourse content. Record is the complete post only, not its linked article, video or podcast.' if approved else 'Pending: weak/indirect topic, institution ownership not independently established for a bsky.social handle, body-unsupported keyword, or video/podcast promotional summary.','source_url':row['source_url'],'published_on':row['published_on'],'source':row['source'],'author':row['author'],'body_sha256':hashlib.sha256(row['body'].encode()).hexdigest()})
 manifest=ROOT/'data/reviews/social-fixed95-topic-decisions-20261109.json'
 raw=json.dumps({'records':records,'content_type':'original_social_post','not_linked_article_or_transcript':True},ensure_ascii=False,indent=2).encode()
 if manifest.exists():assert manifest.read_bytes()==raw
 else:manifest.write_bytes(raw)
 results=[audit_material(s,r['material_id'],{**r,'evidence_path':str(manifest),'evidence_sha256':hashlib.sha256(raw).hexdigest()}) for r in records]
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'reviewed_records':len(results),'formal_full_posts':sum(r['status']=='pass' for r in results),'pending':sum(r['status']!='pass' for r in results),'new_candidates':0,'new_http_requests':0,'removed_acquisition_rows':0,'records':results}
 (ROOT/'data/reviews/social-fixed95-quality-review-20261109.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False));s.close()
if __name__=='__main__':main()
