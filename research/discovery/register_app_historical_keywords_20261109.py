"""Register original index observations once; queue only pages with no prior evidence."""
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
from lxml import html
from research_crawler.items import MaterialCandidate
from research_crawler.store import ResearchStore

ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'data/reviews/app-historical-keywords-registration-20261109.json';assert not out.exists()
    report=json.loads((ROOT/'data/candidates-app-fulltext-early-keywords-20261109.json').read_text(encoding='utf-8'))
    s=ResearchStore(ROOT/'data/research.sqlite3');c=s.connection
    previous={r[0] for r in c.execute('SELECT DISTINCT source_url FROM candidates').fetchall()}
    fetched={r[0] for r in c.execute('SELECT DISTINCT source_url FROM evidence').fetchall()}
    backup=ROOT/'data/backups/pre-app-historical-keywords-registration-20261109.sqlite3'
    assert not backup.exists();b=sqlite3.connect(backup);c.backup(b);b.close()
    old_duplicates=c.execute('SELECT count(*) FROM duplicate_discoveries').fetchone()[0]
    observations=[];grouped=defaultdict(list)
    for page in report['pages']:
        raw=(ROOT/page['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==page['raw_sha256'] and page['http_status']==200
        document=html.fromstring(raw)
        for row in document.xpath('//div[contains(@class,"view-content")]//tr[td]'):
            dates=row.xpath('./td[contains(@class,"field-docs-start-date-time-value")]');links=row.xpath('./td[contains(@class,"views-field-title")]/a[contains(@href,"/documents/")]')
            if len(dates)!=1 or len(links)!=1:continue
            date=datetime.strptime(' '.join(dates[0].text_content().split()),'%b %d, %Y').date()
            if not 1949<=date.year<=1991:continue
            url=urljoin('https://www.presidency.ucsb.edu',links[0].get('href'));period='1949-1972' if date.year<=1972 else '1972-1991';label='app-fulltext-early-keywords-20261109:'+page['term']
            candidate=MaterialCandidate(url,period,'government',label)
            grouped[(period,label)].append(candidate)
            observations.append({'url':url,'period':period,'source_category':'government','query_label':label,'platform_id':'','metadata_url':'','index_date':date.isoformat(),'index_title':' '.join(links[0].text_content().split()),'index_evidence':page['path'],'index_sha256':page['raw_sha256']})
    assert len(observations)==437 and len({r['url'] for r in observations})==423
    candidate_ids=[]
    for (period,label),records in grouped.items():
        batch=s.create_batch(period,'government',label);candidate_ids.extend(s.add_candidates(batch,records))
    unique_new={}
    for r in observations:
        if r['url'] not in fetched:unique_new.setdefault(r['url'],r)
    assert len(unique_new)==188 and all(r['url'] not in previous for r in unique_new.values())
    for cid in set(candidate_ids):
        r=c.execute('SELECT * FROM candidates WHERE id=?',(cid,)).fetchone()
        if r['source_url'] in fetched:
            s.update_candidate_status(cid,'pending','Historical-term rediscovery of previously captured source; no new HTTP request. Existing material/quality decision, if any, retains authority. Candidate status does not imply formal acceptance.')
    fields=('url','period','source_category','query_label','platform_id','metadata_url')
    csv_path=ROOT/'data/candidates-app-historical-keywords-fresh188-20261109.csv';assert not csv_path.exists()
    with csv_path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in sorted(unique_new.values(),key=lambda r:(r['index_date'],r['url'])))
    duplicate_delta=c.execute('SELECT count(*) FROM duplicate_discoveries').fetchone()[0]-old_duplicates
    assert duplicate_delta==249
    value={'generated_at':datetime.now(timezone.utc).isoformat(),'index_observations':437,'unique_index_urls':423,'new_candidates':188,'known_unique_urls':235,'duplicate_discoveries_added':duplicate_delta,'restricted':0,'http_failed':0,'new_candidate_fulltexts':0,'queued_unfetched':188,'index_http200':12,'new_by_year':dict(sorted(Counter(r['index_date'][:4] for r in unique_new.values()).items())),'queued_csv':str(csv_path.relative_to(ROOT)),'candidate_ids':candidate_ids,'observations':observations,'backup':str(backup.relative_to(ROOT)),'note':'Only candidates and repeat counters changed. No formal promotion; discovery dates and snippets are not accepted document metadata/fulltext. Prior evidence retained. Known captured URLs will not be refetched.'}
    out.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in value.items() if k not in ('candidate_ids','observations')},ensure_ascii=False,indent=2));s.close()

if __name__=='__main__':main()
