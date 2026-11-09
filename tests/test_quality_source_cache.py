from test_quality_audit import approval, populated, RAW
from research_crawler.quality_audit import audit_material


def test_unchanged_source_check_reuses_parser_result(tmp_path, monkeypatch):
    import research_crawler.quality_audit as quality
    store, mid, _ = populated(tmp_path)
    decision = approval(store, mid)
    assert audit_material(store, mid, decision)['status'] == 'pass'
    def unexpected(*args, **kwargs):
        raise AssertionError('unchanged source must not be parsed again')
    monkeypatch.setattr(quality, '_extract_existing', unexpected)
    result = audit_material(store, mid, decision)
    assert result['status'] == 'pass'
    assert result['checks']['source_cache_reused'] is True
    store.close()


def test_cached_editorial_risk_check_is_reused_for_unchanged_source(tmp_path, monkeypatch):
    import research_crawler.quality_audit as quality
    store, mid, _ = populated(tmp_path)
    store.connection.execute("UPDATE materials SET source='The American Presidency Project' WHERE id=?", (mid,))
    store.connection.commit()
    # This fixture has another site name, so temporarily provide the expected
    # same-document extraction; the regression concerns editorial parsing reuse.
    original = quality._extract_existing
    from dataclasses import replace
    def extract(*args, **kwargs):
        result, ids = original(*args, **kwargs)
        result['material'] = replace(result['material'], source='The American Presidency Project')
        return result, ids
    monkeypatch.setattr(quality, '_extract_existing', extract)
    decision = approval(store, mid)
    assert audit_material(store, mid, decision)['status'] == 'pass'
    def unexpected(*args):
        raise AssertionError('unchanged editorial evidence must not be parsed again')
    monkeypatch.setattr(quality, '_app_editorial_risks', unexpected)
    assert audit_material(store, mid, decision)['status'] == 'pass'
    store.close()


def test_changed_evidence_still_invalidates_cached_pass(tmp_path):
    store, mid, path = populated(tmp_path)
    decision = approval(store, mid)
    assert audit_material(store, mid, decision)['status'] == 'pass'
    path.write_bytes(RAW + b'changed')
    assert audit_material(store, mid, decision)['status'] == 'pending'
    store.close()


def test_changed_provenance_invalidates_source_cache(tmp_path):
    store, mid, _ = populated(tmp_path)
    decision = approval(store, mid)
    assert audit_material(store, mid, decision)['status'] == 'pass'
    store.connection.execute('DELETE FROM material_verifications WHERE material_id=?', (mid,))
    store.connection.commit()
    assert not audit_material(store, mid, decision)['source_pass']
    store.close()


def test_changed_adapter_version_invalidates_cache(tmp_path, monkeypatch):
    import research_crawler.quality_audit as quality
    store, mid, _ = populated(tmp_path)
    decision = approval(store, mid)
    assert audit_material(store, mid, decision)['status'] == 'pass'
    monkeypatch.setattr(quality, '_adapter_revision', lambda: 'new implementation')
    def changed(*args, **kwargs):
        raise ValueError('new adapter requires revalidation')
    monkeypatch.setattr(quality, '_extract_existing', changed)
    result = audit_material(store, mid, decision)
    assert result['status'] == 'pending'
    assert 'new adapter' in result['reason']
    store.close()


def test_video_target_is_detected_even_when_post_text_does_not_say_video():
    from research_crawler.quality_audit import _has_video_embed
    assert _has_video_embed({'posts': [{'record': {'embed': {
        '$type': 'app.bsky.embed.external',
        'external': {'uri': 'https://www.youtube.com/shorts/example'}}}}]})
    assert _has_video_embed({'posts': [{'record': {'embed': {'$type': 'app.bsky.embed.video'}}}]})
    assert not _has_video_embed({'posts': [{'record': {'embed': None}}]})
    assert not _has_video_embed({'posts': [{'record': {'embed': {
        '$type': 'app.bsky.embed.external',
        'external': {'uri': 'https://example.org/china-policy'}}}}]})
