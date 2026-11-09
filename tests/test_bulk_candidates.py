import sqlite3

import pytest

from research_crawler.items import MaterialCandidate
from research_crawler.store import ResearchStore


def test_bulk_candidates_keep_canonical_duplicates_and_resume_without_recounting(tmp_path):
    from test_export import add_verified

    store = ResearchStore(tmp_path / "bulk.sqlite3")
    add_verified(store, "Existing verified body.")
    batch = store.create_batch("2017-2025", "government", "bulk")
    candidates = [
        MaterialCandidate("https://EXAMPLE.org/story?utm_source=test#top", "2017-2025", "government", "bulk"),
        MaterialCandidate("https://example.org/new", "2017-2025", "government", "bulk"),
        MaterialCandidate("https://example.org/new#part", "2017-2025", "government", "bulk", metadata_url="https://example.org/details"),
    ]
    ids = store.add_candidates(batch, candidates)

    assert ids[1] == ids[2]
    assert len(set(ids)) == 2
    assert store.connection.execute("SELECT duplicate_count FROM materials").fetchone()[0] == 1
    assert store.connection.execute("SELECT COUNT(*) FROM duplicate_discoveries").fetchone()[0] == 1
    assert store.connection.execute("SELECT metadata_url FROM candidates WHERE id=?", (ids[1],)).fetchone()[0] == "https://example.org/details"
    assert store.add_candidates(batch, candidates) == ids
    assert store.connection.execute("SELECT duplicate_count FROM materials").fetchone()[0] == 1
    store.close()


def test_bulk_candidates_preserve_legacy_platform_alias_identity(tmp_path):
    store = ResearchStore(tmp_path / "bulk.sqlite3")
    first = store.create_batch("2017-2025", "new_media", "first")
    old = store.add_candidate(first, MaterialCandidate("https://mobile.twitter.com/official/status/123", "2017-2025", "new_media", "first", platform_id="123"))
    store.connection.execute("UPDATE candidates SET identity_key='platform:mobile.twitter.com:123' WHERE id=?", (old,))
    store.connection.commit()
    batch = store.create_batch("2017-2025", "new_media", "bulk")
    ids = store.add_candidates(batch, [
        MaterialCandidate("https://x.com/official/status/123", "2017-2025", "new_media", "bulk", platform_id="123"),
        MaterialCandidate("https://youtube.com/watch?v=123", "2017-2025", "new_media", "bulk", platform_id="123"),
    ])
    identities = [store.connection.execute("SELECT identity_key FROM candidates WHERE id=?", (i,)).fetchone()[0] for i in ids]
    assert identities == ["platform:mobile.twitter.com:123", "platform:youtube.com:123"]
    assert store.connection.execute("SELECT COUNT(*) FROM duplicate_discoveries").fetchone()[0] == 1
    store.close()


def test_bulk_failure_rolls_back_candidates_duplicate_counts_and_discoveries(tmp_path):
    from test_export import add_verified

    store = ResearchStore(tmp_path / "bulk.sqlite3")
    add_verified(store, "Existing verified body.")
    batch = store.create_batch("2017-2025", "government", "bulk")
    before = store.connection.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    store.connection.executescript("""CREATE TRIGGER reject_candidate BEFORE INSERT ON candidates
        WHEN NEW.source_url='https://example.org/reject'
        BEGIN SELECT RAISE(ABORT, 'candidate rejected'); END;""")
    with pytest.raises(sqlite3.IntegrityError, match="candidate rejected"):
        store.add_candidates(batch, [
            MaterialCandidate("https://example.org/story", "2017-2025", "government", "bulk"),
            MaterialCandidate("https://example.org/reject", "2017-2025", "government", "bulk"),
        ])
    assert store.connection.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == before
    assert store.connection.execute("SELECT COUNT(*) FROM duplicate_discoveries").fetchone()[0] == 0
    assert store.connection.execute("SELECT duplicate_count FROM materials").fetchone()[0] == 0
    store.close()


def test_reused_platform_id_does_not_create_an_unpersisted_url_alias(tmp_path):
    store = ResearchStore(tmp_path / "bulk.sqlite3")
    batch = store.create_batch("2017-2025", "new_media", "bulk")
    ids = store.add_candidates(batch, [
        MaterialCandidate("https://x.com/a/status/123", "2017-2025", "new_media", "bulk", platform_id="123"),
        MaterialCandidate("https://x.com/b/status/123", "2017-2025", "new_media", "bulk", platform_id="123"),
        MaterialCandidate("https://x.com/b/status/123", "2017-2025", "new_media", "bulk"),
    ])
    assert ids[0] == ids[1]
    assert ids[2] != ids[0]
    assert store.connection.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 2
    store.close()
