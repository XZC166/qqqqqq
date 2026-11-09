from research_crawler import cli
from research_crawler.items import MaterialCandidate
from research_crawler.store import ResearchStore
from test_export import add_verified


def test_filter_resolves_aliases_once_and_keeps_exclusions_and_discovery_counts(tmp_path):
    store = ResearchStore(tmp_path / "progress.sqlite3")
    add_verified(store, "Complete source body.")
    batch = store.create_batch("2017-2025", "new_media", "blocked")
    blocked = MaterialCandidate("https://twitter.com/account/status/42", "2017-2025", "new_media", "blocked", "42")
    blocked_id = store.add_candidate(batch, blocked)
    store.update_candidate_status(blocked_id, "excluded", "Outside thesis scope")
    inputs = [
        MaterialCandidate("https://example.org/story?utm_source=alias", "2017-2025", "government", "again"),
        MaterialCandidate("https://x.com/account/status/42", "2017-2025", "new_media", "again", "42"),
        *[MaterialCandidate(f"https://example.org/new/{i}", "2017-2025", "government", "new") for i in range(20)],
    ]
    before = store.connection.execute("SELECT count(*) FROM duplicate_discoveries").fetchone()[0]
    statements = []
    store.connection.set_trace_callback(statements.append)
    eligible = cli._unverified_candidates(inputs, store)
    store.connection.set_trace_callback(None)
    assert eligible == inputs[2:]
    assert store.connection.execute("SELECT status FROM candidates WHERE id=?", (blocked_id,)).fetchone()[0] == "excluded"
    assert store.connection.execute("SELECT count(*) FROM duplicate_discoveries").fetchone()[0] == before
    # Cost must grow with the pool once, not once for every input URL. This also
    # prevents the pre-crawl eligibility step undoing bulk-import speed gains.
    scans = [q for q in statements if "SELECT identity_key, source_url FROM" in q]
    assert len(scans) <= 2, scans
    store.close()
