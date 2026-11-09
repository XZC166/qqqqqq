"""Candidate progress scans must not repeatedly scan the entire evidence table."""
from research_crawler.store import ResearchStore
from research_crawler.items import MaterialCandidate, SourceEvidence


def test_candidate_evidence_lookup_is_indexed_after_reopening(tmp_path):
    path = tmp_path / 'research.sqlite3'
    store = ResearchStore(path)
    batch = store.create_batch('1949-1972', 'government', 'synthetic-lookup')
    candidate = store.add_candidate(batch, MaterialCandidate(
        'https://example.org/source', '1949-1972', 'government', 'synthetic-lookup'))
    evidence = store.add_evidence(candidate, SourceEvidence(
        'https://example.org/source', '2026-11-10T00:00:00Z', 200, 'synthetic-hash'),
        access_status='allow')
    # Simulate reopening a database created before the lookup index existed.
    store.connection.execute('DROP INDEX IF EXISTS ix_evidence_candidate')
    store.connection.commit()
    store.close()
    reopened = ResearchStore(path)
    plan = ' '.join(row[3] for row in reopened.connection.execute(
        'EXPLAIN QUERY PLAN SELECT count(*) FROM candidates c WHERE NOT EXISTS '
        '(SELECT 1 FROM evidence e WHERE e.candidate_id=c.id)'))
    assert 'SEARCH e USING' in plan, plan
    assert 'SCAN e' not in plan, plan
    assert reopened.connection.execute('SELECT id FROM evidence WHERE candidate_id=?',
                                       (candidate,)).fetchone()[0] == evidence
    reopened.close()
