"""Targeted attribution audit across all current formal titles; preserve originals."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import _source_row, audit_material, material_fingerprint
from research_crawler.revalidation import _extract_existing
from research_crawler.spiders.government import GovernmentArticleAdapter

ROOT = Path(__file__).resolve().parents[2]
IDS = {2657,2785,2789,2795,2801,2802,13567}

def main():
    prefix = ROOT / "data/reviews/app-formal-author-conflicts7"
    report = Path(str(prefix) + "-quality-review-20261109.json")
    assert not report.exists(), "Preserve subsequent review decisions."
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    rows = c.execute("SELECT m.*,q.input_fingerprint FROM materials m JOIN quality_reviews q ON q.material_id=m.id WHERE q.status='pass' AND (m.title LIKE '%by Press Secretary%' OR m.title LIKE 'White House Statement%' OR m.title LIKE '%by the Press Secretary%') ORDER BY m.id").fetchall()
    assert {r['id'] for r in rows} == IDS
    backup = ROOT / "data/backups/pre-app-formal-author-conflicts7-review-20261109.sqlite3"
    assert not backup.exists(); b = sqlite3.connect(backup); c.backup(b); b.close()
    decisions, before = [], []
    for row in rows:
        assert material_fingerprint(row) == row['input_fingerprint']
        source = _source_row(store,row['id'])
        raw = Path(source['evidence_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source['content_sha256']
        parsed = _extract_existing(store,source,GovernmentArticleAdapter())[0]['material']
        assert parsed and parsed.title == row['title'] and parsed.author == row['author'] and parsed.body == row['body']
        reason = "Attribution conflict: explicit press-secretary or White House institutional statement title versus presidential collection author. Preserve source unchanged; actual release author cannot be confirmed from collection attribution alone. Pending author review, not a claim that source is fabricated or inaccessible."
        decisions.append({'material_id':row['id'],'approved':False,'fingerprint':material_fingerprint(row),'source_url':row['source_url'],'body_sha256':hashlib.sha256(row['body'].encode()).hexdigest(),'reason':reason})
        before.append({'material':dict(row),'evidence_path':source['evidence_path'],'source_sha256':source['content_sha256']})
    manifest = Path(str(prefix) + "-topic-decisions-20261109.json")
    assert not manifest.exists(); raw = json.dumps({'records':decisions,'preserved_previous_records':before,'scope':'Targeted author-attribution screen of every current formal title; seven conflicts deferred. Not a new whole-body/thematic review of every formal record.'},ensure_ascii=False,indent=2).encode(); manifest.write_bytes(raw)
    results = [audit_material(store,d['material_id'],{**d,'evidence_path':str(manifest),'evidence_sha256':hashlib.sha256(raw).hexdigest()}) for d in decisions]
    assert all(r['status']=='pending' for r in results)
    value = {'generated_at':datetime.now(timezone.utc).isoformat(),'reviewed_records':7,'review_scope':'targeted author conflict check, all formal titles screened','new_candidates':0,'formal_fulltexts':0,'new_formal_promotions':0,'pending':7,'withdrawn_formal':7,'duplicate_discoveries':0,'restricted':0,'http_failed':0,'backup':str(backup.relative_to(ROOT)),'records':results}
    report.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({k:v for k,v in value.items() if k!='records'},ensure_ascii=False,indent=2)); store.close()

if __name__ == '__main__':
    main()
