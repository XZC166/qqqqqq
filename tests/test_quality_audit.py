import hashlib
import json
from pathlib import Path

from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.store import ResearchStore
from research_crawler.quality_audit import audit_material, material_fingerprint, ReviewedExportStore


URL = "https://example.org/china"
RAW = b'''<html><head><meta property="og:site_name" content="Example Government">
<meta name="author" content="Example Author"><meta name="description" content="China policy statement.">
<meta name="keywords" content="China"><meta property="article:published_time" content="1950-01-02"></head>
<body><article data-full-text="true"><h1>China policy</h1><time>January 2, 1950</time>
<div class="article-body"><p>China policy statement.</p></div></article></body></html>'''


def populated(tmp_path):
    store=ResearchStore(tmp_path / "audit.sqlite3")
    batch=store.create_batch("1949-1972","government","audit")
    candidate=store.add_candidate(batch,MaterialCandidate(URL,"1949-1972","government","audit"))
    path=tmp_path / "source.html";path.write_bytes(RAW)
    eid=store.add_evidence(candidate,SourceEvidence(URL,"2026-11-09T00:00:00Z",200,hashlib.sha256(RAW).hexdigest(),path,True,True),"allow")
    m=VerifiedMaterial("Example Government","1950-01-02","Example Author","China policy","China policy statement.","China","China policy statement.",URL)
    mid,_=store.add_verified_material(candidate,eid,m,field_sources={key:URL for key in ("source","time","author","title","abstract","keywords")})
    return store,mid,path


def approval(store,mid):
    row=store.connection.execute("SELECT * FROM materials WHERE id=?",(mid,)).fetchone()
    decision={"material_id":mid,"fingerprint":material_fingerprint(row),"approved":True,"reason":"Individually reviewed the complete China policy statement."}
    path=store.path.parent / "topic-review.json"
    path.write_text(json.dumps({"records":[decision]}),encoding="utf-8")
    return {**decision,"evidence_path":str(path),"evidence_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}


def test_source_pass_without_topic_review_is_pending_and_never_exported(tmp_path):
    store,mid,_=populated(tmp_path)
    result=audit_material(store,mid)
    assert result["source_pass"]
    assert result["status"] == "pending"
    assert ReviewedExportStore(store).get_verified_materials() == []
    store.close()


def test_source_file_hash_mismatch_blocks_approved_record(tmp_path):
    store,mid,path=populated(tmp_path);decision=approval(store,mid)
    path.write_bytes(RAW+b"changed")
    result=audit_material(store,mid,decision)
    assert result["status"] == "pending"
    assert "hash" in result["reason"].lower()
    assert len(store.get_verified_materials()) == 1
    store.close()


def test_approved_record_exports_until_body_changes(tmp_path):
    store,mid,_=populated(tmp_path)
    result=audit_material(store,mid,approval(store,mid))
    assert result["status"] == "pass"
    assert len(ReviewedExportStore(store).get_verified_materials()) == 1
    store.connection.execute("UPDATE materials SET body='Changed source text' WHERE id=?",(mid,));store.connection.commit()
    assert ReviewedExportStore(store).get_verified_materials() == []
    assert len(store.get_verified_materials()) == 1
    store.close()


def test_old_approval_cannot_approve_changed_metadata(tmp_path):
    store,mid,_=populated(tmp_path);decision=approval(store,mid)
    store.connection.execute("UPDATE materials SET title='Different title' WHERE id=?",(mid,));store.connection.commit()
    result=audit_material(store,mid,decision)
    assert result["status"] == "pending"
    store.close()


def test_export_rechecks_changed_source_file_and_removes_stale_pass(tmp_path):
    store,mid,path=populated(tmp_path)
    assert audit_material(store,mid,approval(store,mid))["status"] == "pass"
    path.write_bytes(RAW+b"altered")
    assert ReviewedExportStore(store).get_verified_materials() == []
    store.close()


def test_evidence_url_and_candidate_ownership_cannot_be_forged(tmp_path):
    store,mid,_=populated(tmp_path);decision=approval(store,mid)
    store.connection.execute("UPDATE evidence SET source_url='https://other.example/other'");store.connection.commit()
    assert not audit_material(store,mid,decision)["source_pass"]
    store.close()


def test_negative_topic_decision_never_grants_approval(tmp_path):
    store,mid,_=populated(tmp_path);decision=approval(store,mid)
    decision["approved"]=False
    assert audit_material(store,mid,decision)["status"] == "pending"
    store.close()


def test_export_rechecks_duplicate_counter(tmp_path):
    store,mid,_=populated(tmp_path)
    assert audit_material(store,mid,approval(store,mid))["status"] == "pass"
    store.connection.execute("UPDATE materials SET duplicate_count=999");store.connection.commit()
    assert ReviewedExportStore(store).get_verified_materials() == []
    store.close()


def test_cli_export_excludes_acquisition_pass_without_quality_review(tmp_path):
    from openpyxl import load_workbook
    from research_crawler.cli import main
    store,mid,_=populated(tmp_path)
    database=store.path
    store.close()
    destination=tmp_path / "formal.xlsx"
    assert main(["export","--db",str(database),"--output",str(destination)]) == 0
    workbook=load_workbook(destination,read_only=True)
    assert len(list(workbook.active.values)) == 1
    workbook.close()


def test_export_uses_counter_actually_checked_during_reaudit(tmp_path,monkeypatch):
    import research_crawler.quality_audit as quality
    store,mid,_=populated(tmp_path)
    assert audit_material(store,mid,approval(store,mid))["status"] == "pass"
    original=quality.audit_material
    def discover_then_audit(*args,**kwargs):
        other=ResearchStore(store.path)
        batch=other.create_batch("1949-1972","government","new-discovery")
        other.add_candidate(batch,MaterialCandidate(URL,"1949-1972","government","new-discovery"))
        other.close()
        return original(*args,**kwargs)
    monkeypatch.setattr(quality,"audit_material",discover_then_audit)
    assert ReviewedExportStore(store).get_verified_materials()[0].duplicate_count == 1
    store.close()


def test_cli_delivery_keeps_pending_out_of_formal_workbook_and_preserves_progress(tmp_path):
    import sqlite3
    from zipfile import ZipFile
    from openpyxl import load_workbook
    from research_crawler.cli import main
    store,mid,_=populated(tmp_path)
    (tmp_path / 'reviews').mkdir()
    (tmp_path / 'reviews/individual-review.json').write_text('{"status":"pending"}',encoding='utf-8')
    database=store.path;store.close();before=database.read_bytes()
    destination=tmp_path / "private-delivery.zip"
    assert main(["deliver","--db",str(database),"--output",str(destination)]) == 0
    assert database.read_bytes() == before
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert 'reviews/individual-review.json' in archive.namelist()
        candidate_index=json.loads(archive.read('reports/candidate-evidence-index.json'))
        assert len(candidate_index) == 1 and candidate_index[0]['file']
        with archive.open('materials.xlsx') as handle:
            workbook=load_workbook(handle,read_only=True)
            assert len(list(workbook.active.values)) == 1
            workbook.close()
        archive.extract('progress.sqlite3',tmp_path / 'unpacked')
    connection=sqlite3.connect(tmp_path / 'unpacked/progress.sqlite3')
    assert connection.execute('SELECT count(*) FROM materials').fetchone()[0] == 1
    connection.close()


def test_delivery_packages_exact_topic_manifest_even_outside_reviews(tmp_path):
    from zipfile import ZipFile
    from research_crawler.quality_audit import build_reviewed_delivery
    store,mid,_=populated(tmp_path);decision=approval(store,mid)
    assert audit_material(store,mid,decision)['status']=='pass'
    destination=tmp_path / 'approved.zip'
    build_reviewed_delivery(store,destination)
    with ZipFile(destination) as archive:
        index=json.loads(archive.read('reviews/topic-decision-index.json'))
        assert index[0]['material_id']==mid
        assert hashlib.sha256(archive.read(index[0]['file'])).hexdigest()==decision['evidence_sha256']
    store.close()
