"""Fixed individual topic decisions; all source checks rerun against saved bytes."""
import csv, hashlib, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material,material_fingerprint
ROOT=Path(__file__).resolve().parents[2]
GROUPS={
"Public statements on China contact, normalization and diplomatic relations": [13129,13131,13136,13137,13139,13166,13167,13168,13169,13172,13228,13238,13243,13245,13248,13251,13252,13254,13256,13258,13259,13266,13399,13401,13426,13481,13483,13487,13503,13515,13525,13527,13528,13530,13534,13536,13549,13551,13552,13555,13556,13557,13558,13560,13562,13564,13570,13585,13586,13588,13589,13596,13597,13600],
"Public China threat, political-system and regional-security framing": [13134,13140,13144,13146,13150,13152,13154,13156,13158,13164,13237,13239,13241,13250,13253,13270,13318,13446,13480,13484,13489,13522,13535,13539,13541,13576,13580,13594],
"US assistance policy toward China or Taiwan": [13130,13142,13162,13180,13192,13229,13231,13233,13235,13262,13354,13482,13526,13531,13547,13559,13567,13569,13571,13572,13574,13602],
"Science, technology, export-control and cooperation with China": [13151,13257,13490,13546,13550,13598],
"China economic reform and comparisons of political-economic systems": [13159,13161,13227,13329,13587],
"Taiwan Strait or nuclear arms-control discussions involving China": [13160,13409,13431,13532,13592],
"Cultural exchange, media narratives and public communication involving China": [13145,13213,13288,13523,13537,13595],
"1989 aftermath, human rights, Chinese students and continued engagement": [13163,13165,13236,13378,13554,13591,13593],
"China lobby as explicitly discussed in US public campaign discourse": [13563,13604],
}
# Each ID was read in its actual source/topic context; this is not a search-hit rule.
def main():
 report_path=ROOT/'data/reviews/app-next240-quality-review-20261109.json'
 if report_path.exists():raise SystemExit('Fixed batch already reviewed; preserve later approvals and its report.')
 s=ResearchStore(ROOT/'data/research.sqlite3');c=s.connection
 urls={r['url'] for r in csv.DictReader((ROOT/'data/candidates-app-fulltext-early-next240-20261109.csv').open(encoding='utf-8-sig'))}
 rows=[r for r in c.execute('SELECT * FROM materials ORDER BY id') if r['source_url'] in urls]
 ids={r['id'] for r in rows}; reasons={mid:reason for reason,mids in GROUPS.items() for mid in mids if mid in ids}
 manifest=ROOT/'data/reviews/app-next240-topic-decisions-20261109.json'
 records=[]
 for row in rows:
  approved=row['id'] in reasons
  paragraphs=[p for p in row['body'].split('\n\n') if re.search(r'\b(China|Chinese|Taiwan|Formosa|Peking|Beijing)\b',p,re.I)]
  records.append({'material_id':row['id'],'fingerprint':material_fingerprint(row),'approved':approved,'reason':reasons.get(row['id'],'No individual positive decision: incidental biography/geography, bare schedule/list, unsupported future report, index/timeline, or unresolved topic context. Retained pending.'),'source_url':row['source_url'],'title':row['title'],'published_on':row['published_on'],'topic_context_from_same_body':' '.join(paragraphs)[:2200]})
 raw=json.dumps({'records':records,'review_scope':'Fixed batch individual topic context review; full unabridged bodies separately source-reextracted. Original bodies and acquisition rows remain intact.'},ensure_ascii=False,indent=2).encode()
 if manifest.exists():assert manifest.read_bytes()==raw,'Immutable review already exists with different inputs.'
 else:manifest.write_bytes(raw)
 decisions={r['material_id']:{**r,'evidence_path':str(manifest),'evidence_sha256':hashlib.sha256(raw).hexdigest()} for r in records}
 results=[audit_material(s,row['id'],decisions[row['id']]) for row in rows]
 candidate_rows=[r for r in c.execute("SELECT * FROM candidates WHERE query_label='app-fulltext-early-20261109'") if r['source_url'] in urls]
 report={'generated_at':datetime.now(timezone.utc).isoformat(),'discovered_candidates':len(urls),'captured_candidate_statuses':dict(Counter(r['status'] for r in candidate_rows)),'working_fulltext_rows':len(rows),'quality_formal_pass':sum(r['status']=='pass' for r in results),'quality_pending_materials':sum(r['status']!='pass' for r in results),'source_checks_pass':sum(r['source_pass'] for r in results),'restricted':sum(r['status']=='restricted' for r in candidate_rows),'failed':sum(r['status']=='failed' for r in candidate_rows),'removed_acquisition_rows':0,'records':results}
 out=ROOT/'data/reviews/app-next240-quality-review-20261109.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2));s.close()
if __name__=='__main__':main()
