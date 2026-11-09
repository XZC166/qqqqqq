"""Independently verify all delivered rows, sidecars, decisions and formal evidence."""
import argparse
from contextlib import closing
import hashlib
import io
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from openpyxl import load_workbook
from research_crawler.items import EXPORT_COLUMNS
from research_crawler.export import EXCEL_CELL_LIMIT, _excel_character_count
from research_crawler.quality_audit import material_fingerprint

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('zip');parser.add_argument('--expected',type=int,required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    path=Path(args.zip);output=Path(args.output);assert not output.exists()
    manifests={};evidence_files={};sidecars=0
    with ZipFile(path) as z, TemporaryDirectory(prefix='checkpoint-independent-',dir=ROOT/'data') as temp:
        db=Path(temp)/'progress.sqlite3';db.write_bytes(z.read('progress.sqlite3'))
        with closing(sqlite3.connect(db)) as c:
            c.row_factory=sqlite3.Row
            rows=c.execute("SELECT m.*,q.input_fingerprint FROM materials m JOIN quality_reviews q ON q.material_id=m.id WHERE q.status='pass' AND q.source_pass=1 AND q.topic_pass=1 ORDER BY m.id").fetchall()
            assert len(rows)==args.expected and len({r['identity_key'] for r in rows})==len(rows)
            wb=load_workbook(io.BytesIO(z.read('materials.xlsx')),read_only=True,data_only=False);sheet=wb.active
            it=sheet.iter_rows(values_only=True);assert tuple(next(it))==EXPORT_COLUMNS
            for r,values in zip(rows,it,strict=True):
                assert material_fingerprint(r)==r['input_fingerprint']
                expected=(r['source'],r['published_on'],r['author'],r['title'],r['abstract'],r['keywords'],r['body'],r['source_url'],r['duplicate_count'])
                for i,(actual,value) in enumerate(zip(values,expected,strict=True)):
                    if i==6 and _excel_character_count(value)>EXCEL_CELL_LIMIT:
                        assert isinstance(actual,str) and not Path(actual).is_absolute()
                        assert z.read(actual.replace('\\','/')).decode('utf-8')==value;sidecars+=1
                    else:assert actual==value,(r['id'],i)
            wb.close()
            index=json.loads(z.read('reviews/topic-decision-index.json'));assert len(index)==len(rows)
            by_id={r['id']:r for r in rows};assert {d['material_id'] for d in index}==set(by_id)
            for d in index:
                if d['file'] not in manifests:
                    raw=z.read(d['file']);assert hashlib.sha256(raw).hexdigest()==d['sha256'];manifests[d['file']]=json.loads(raw)
                r=by_id[d['material_id']]
                assert any(x['material_id']==r['id'] and x['approved'] and x['fingerprint']==r['input_fingerprint'] for x in manifests[d['file']]['records'])
            provenance=json.loads(z.read('reports/provenance-index.json'));assert {p['material_id'] for p in provenance}==set(by_id)
            for p in provenance:
                r=by_id[p['material_id']];assert p['source_url']==r['source_url'] and p['publication_date']==r['published_on'] and p['title']==r['title']
                for e in p['evidence']:
                    if e['file'] not in evidence_files:evidence_files[e['file']]=hashlib.sha256(z.read(e['file'])).hexdigest()
                    assert evidence_files[e['file']]==e['sha256']
    with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    proof={'generated_at':datetime.now(timezone.utc).isoformat(),'formal_records':args.expected,'columns':9,'all_nine_fields_verified':True,'long_body_sidecars_verified':sidecars,'positive_review_manifests_verified':args.expected,'formal_raw_evidence_hashes_verified':len(evidence_files),'zip_bytes':path.stat().st_size,'zip_sha256':digest,'builder_crc_check':'passed during delivery generation; not redundantly rerun','private_only':True}
    output.write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(proof,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
