from test_quality_audit import populated, approval, RAW
from research_crawler.quality_audit import audit_material


def test_unchanged_export_check_rechecks_evidence_without_rewriting_review(tmp_path):
    store,mid,path=populated(tmp_path)
    decision=approval(store,mid)
    assert audit_material(store,mid,decision)['status']=='pass'
    before=store.connection.total_changes
    prior=dict(store.connection.execute('SELECT * FROM quality_reviews WHERE material_id=?',(mid,)).fetchone())
    assert audit_material(store,mid,decision)['status']=='pass'
    assert store.connection.total_changes==before
    current=dict(store.connection.execute('SELECT * FROM quality_reviews WHERE material_id=?',(mid,)).fetchone())
    assert current==prior
    # Skipping an unchanged database write must never skip reading/hashing the
    # actual source. A later changed raw file must withdraw the prior pass.
    path.write_bytes(RAW+b'changed')
    assert audit_material(store,mid,decision)['status']=='pending'
    assert store.connection.total_changes>before
    assert store.connection.execute('SELECT source_pass FROM quality_reviews WHERE material_id=?',(mid,)).fetchone()[0]==0
    store.close()
