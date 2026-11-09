"""Public aggregate checkpoint; verifies every formal workbook cell and review manifest."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from research_crawler.store import ResearchStore
from research_crawler.items import VerifiedMaterial
from research_crawler.quality_audit import material_fingerprint
from research_crawler.delivery import _verify_workbook

ROOT=Path(__file__).resolve().parents[2]
def main():
 s=ResearchStore(ROOT/'data/research.sqlite3');c=s.connection
 rows=c.execute("SELECT m.*,q.input_fingerprint,q.checks_json,c.period,c.source_category FROM materials m JOIN quality_reviews q ON q.material_id=m.id JOIN evidence e ON e.id=m.evidence_id JOIN candidates c ON c.id=e.candidate_id WHERE q.status='pass' AND q.source_pass=1 AND q.topic_pass=1 ORDER BY m.id").fetchall()
 formal=[]
 for r in rows:
  assert material_fingerprint(r)==r['input_fingerprint']
  decision=json.loads(r['checks_json'])['topic_decision'];raw=Path(decision['evidence_path']).read_bytes()
  assert hashlib.sha256(raw).hexdigest()==decision['evidence_sha256']
  manifest=json.loads(raw)
  assert any(x['material_id']==r['id'] and x['approved'] and x['fingerprint']==r['input_fingerprint'] for x in manifest['records'])
  formal.append(VerifiedMaterial(r['source'],r['published_on'],r['author'],r['title'],r['abstract'],r['keywords'],r['body'],r['source_url'],r['duplicate_count']))
 long_count=_verify_workbook(ROOT/'data/materials.xlsx',formal)
 urls={r['url'] for r in csv.DictReader((ROOT/'data/candidates-app-fulltext-early-next300b-20261109.csv').open(encoding='utf-8-sig'))}
 candidate_rows=[dict(r) for r in c.execute('SELECT id,source_url,status,status_detail FROM candidates').fetchall() if r['source_url'] in urls]
 candidate_ids={r['id'] for r in candidate_rows}
 evidence=[dict(r) for r in c.execute('SELECT candidate_id,source_url,status_code,fetched_at FROM evidence').fetchall() if r['candidate_id'] in candidate_ids and r['source_url'] in urls and r['fetched_at']>='2026-11-09T10:29:00']
 working=[dict(r) for r in c.execute('SELECT id,source_url FROM materials').fetchall() if r['source_url'] in urls]
 q={r['material_id']:r['status'] for r in c.execute('SELECT material_id,status FROM quality_reviews').fetchall()}
 batch_formal=sum(q.get(r['id'])=='pass' for r in working)
 categories=Counter(r['source_category'] for r in rows);periods=Counter(r['period'] for r in rows)
 period_category=defaultdict(Counter)
 for r in rows:period_category[r['period']][r['source_category']]+=1
 names=['research-media-core24','app-next300b-third50','app-next300b-fourth50','app-next300b-fifth50','app-next300b-sixth44']
 batches=[]
 for name in names:
  v=json.loads((ROOT/f'data/reviews/{name}-quality-review-20261109.json').read_text(encoding='utf-8'))
  batches.append({'name':name,**{k:v[k] for k in ('reviewed_records','new_candidates','formal_fulltexts','new_formal_promotions','pending','withdrawn_formal','duplicate_discoveries','restricted','http_failed')}})
 event_terms={
  'Korean War':['Korean War','Korea','Chinese Communist aggression'],
  'Taiwan / Strait':['Taiwan','Formosa','Quemoy','Matsu'],
  'Nixon visit / opening':['Peking','visit to China','opening to China'],
  'Normalization':['normalization','normalize relations','normal relations with China'],
  '1989 / Tiananmen':['Tiananmen','June 4','June 1989'],
  'WTO':['WTO','World Trade Organization'],
  'South China Sea':['South China Sea'],
  'cybersecurity':['cybersecurity','cyber attack','cybersecurity'],
  'trade conflict':['tariff','trade war','trade conflict'],
  'Huawei / 5G':['Huawei','5G'],
  'COVID-19':['COVID','coronavirus'],
  'Xinjiang / Hong Kong':['Xinjiang','Hong Kong','Uyghur','Uighur'],
  'chips / AI':['semiconductor','artificial intelligence','CHIPS'],
  'broadcasting / public diplomacy':['Voice of America','public diplomacy','broadcasting','people-to-people'],
 }
 result={'generated_at':datetime.now(timezone.utc).isoformat(),'quantity_goal':10000,'previous_formal':1145,'formal_unique_fulltext':len(rows),
 'net_formal_increase':len(rows)-1145,'reviewed_this_checkpoint':sum(b['reviewed_records'] for b in batches),
 'new_formal_promotions':sum(b['new_formal_promotions'] for b in batches),'withdrawn_formal':sum(b['withdrawn_formal'] for b in batches),
 'review_pending_this_checkpoint':sum(b['pending'] for b in batches),'newly_discovered_candidates':0,'working_material_rows':c.execute('SELECT count(*) FROM materials').fetchone()[0],
 'quality_review_counts':[dict(r) for r in c.execute('SELECT status,source_pass,count(*) AS count FROM quality_reviews GROUP BY status,source_pass')],
 'formal_by_period':dict(periods),'formal_by_category':dict(categories),'formal_by_year':dict(sorted(Counter(r['published_on'][:4] for r in rows).items())),
 'formal_by_source':dict(Counter(r['source'] for r in rows)),'formal_period_category':{k:dict(v) for k,v in period_category.items()},
 'candidate_status_counts':dict(c.execute('SELECT status,count(*) FROM candidates GROUP BY status').fetchall()),
 'period_boundary':'1972 belongs to first period; second begins 1973.',
 'completed_app300b':{'queued_existing_candidates':300,'newly_discovered_candidates':0,'unique_primary_page_responses':len({e['source_url'] for e in evidence}),
 'working_materials':len(working),'individually_reviewed_working_records':sum(r['id'] in q for r in working),'formal_fulltexts':batch_formal,'pending_pages':300-batch_formal,
 'not_yet_fetched':300-len({e['source_url'] for e in evidence}),'restricted':0,'http_response_counts':dict(Counter(str(e['status_code']) for e in evidence)),
 'http_failed':0,'duplicate_discoveries':0,'pipeline_commit_failures':4,'saved_response_recoveries':4,'unresolved_recovery_failures':0,
 'source_extraction_unverified_pages':len(candidate_rows)-len(working),'scrapy_items_scraped':296,'robotstxt_responses':1,
 'pending_without_material':[{'url':r['source_url'],'status':r['status'],'reason':r['status_detail']} for r in candidate_rows if r['source_url'] not in {m['source_url'] for m in working}]},
 'review_batches':batches,'workbook':{'formal_records':len(rows),'columns':9,'all_fields_exact_roundtrip':True,'long_body_files':long_count,'all_review_manifest_hashes_verified':True,'xlsx_sha256':hashlib.sha256((ROOT/'data/materials.xlsx').read_bytes()).hexdigest()},
 'remaining_gaps':[
  'All remaining working materials need individual final review; source-pass alone is not formal.',
  'FRUS, Congress/GovInfo, NARA, historical VOA, contemporary historical media and Five Eyes media remain incompletely covered.',
  'Other failed archive index variants and unresolved pagination remain documented; success of one fulltext-search index does not resolve all previous failures.',
  'NYT/AP/Reuters/CNN, Chinese comparison sources, official social accounts and open research remain in scope.',
  'Video/podcast descriptions, official video summaries, directories, short search excerpts and biomedical false positives are not formal fulltexts.',
  'Selected records have exact publication-day, byline, supplementary boilerplate, author-biography or multi-speech boundary issues.',
  'Event cue counts below are not completed historical event coding; source availability and rights remain uneven.',
  'No plateau or exhaustion has been established and the 10,000-formal-fulltext goal remains unmet.'
 ],'event_cues_method':'Nonexclusive case-insensitive literal body references using listed terms only. Not completed event classification or political labeling; broad cues such as Korea do not prove a specific historical event.',
 'event_cue_terms':event_terms,'event_literal_cues':{name:sum(any(t.lower() in r['body'].lower() for t in terms) for r in rows) for name,terms in event_terms.items()}}
 result['pending_or_unreviewed_working_materials']=result['working_material_rows']-len(rows)
 result['not_yet_source_audited_working_materials']=result['working_material_rows']-sum(v['count'] for v in result['quality_review_counts'])
 path=ROOT/'docs/reports/2026-11-09-quality-continued2-batch.json';assert not path.exists();path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:result[k] for k in ('generated_at','formal_unique_fulltext','working_material_rows','reviewed_this_checkpoint','new_formal_promotions','review_pending_this_checkpoint','formal_by_period','formal_by_category','not_yet_source_audited_working_materials','workbook')},ensure_ascii=False,indent=2));s.close()
if __name__=='__main__':main()
