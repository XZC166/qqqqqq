import sqlite3

from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.store import ResearchStore


def test_batch_candidate_and_evidence_survive_reopening(tmp_path):
    database = tmp_path / "research.sqlite3"
    store = ResearchStore(database)
    batch_id = store.create_batch("1949-1972", "government", "voa-broadcasts")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(
            "https://example.org/a",
            "1949-1972",
            "government",
            "voa-broadcasts",
        ),
    )
    evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url="https://example.org/a",
            fetched_at="2026-11-06T00:00:00Z",
            status_code=200,
            content_sha256="abc",
            body_complete=True,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    store.close()
    reopened = ResearchStore(database)
    summary = reopened.batch_summary(batch_id)
    assert summary == {
        "candidate": 1,
        "verified": 0,
        "restricted": 0,
        "duplicate": 0,
        "pending": 0,
        "unprocessed": 1,
    }
    assert evidence_id > 0
    reopened.close()


def test_existing_evidence_schema_is_migrated_with_retrieval_provenance(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE evidence (
            id INTEGER PRIMARY KEY,
            candidate_id INTEGER NOT NULL,
            source_url TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            content_sha256 TEXT NOT NULL,
            evidence_path TEXT,
            body_complete INTEGER NOT NULL,
            metadata_verified INTEGER NOT NULL,
            body_format TEXT NOT NULL DEFAULT 'source_text',
            original_page_verified INTEGER NOT NULL DEFAULT 0,
            access_status TEXT NOT NULL,
            authorization_note TEXT NOT NULL DEFAULT ''
        )"""
    )
    connection.execute(
        """INSERT INTO evidence VALUES
           (1, 1, 'https://example.org/a', '2026-11-06T00:00:00Z', 200, 'hash',
            NULL, 1, 1, 'source_text', 0, 'allow', '')"""
    )
    connection.commit()
    connection.close()

    store = ResearchStore(database)

    columns = {
        row["name"] for row in store.connection.execute("PRAGMA table_info(evidence)")
    }
    assert {"retrieval_method", "retrieval_id"}.issubset(columns)
    migrated = store.connection.execute(
        "SELECT retrieval_method, retrieval_id FROM evidence WHERE id = 1"
    ).fetchone()
    assert tuple(migrated) == ("scrapy", "")
    store.close()


def test_duplicate_material_keeps_one_row_and_increments_count(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "media", "trade-war")
    candidate = MaterialCandidate(
        "https://EXAMPLE.org/story#top",
        "2017-2025",
        "media",
        "trade-war",
    )
    candidate_id = store.add_candidate(batch_id, candidate)
    evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url=candidate.source_url,
            fetched_at="2026-11-06T00:00:00Z",
            status_code=200,
            content_sha256="body-hash",
            body_complete=True,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    material = VerifiedMaterial(
        source="Example",
        time="2018-01-01",
        author="未注明",
        title="Example title",
        abstract="",
        keywords="trade",
        body="Full body",
        source_url="https://example.org/story#top",
    )

    first_id, first_inserted = store.add_verified_material(
        candidate_id,
        evidence_id,
        material,
        field_sources={name: material.source_url for name in ("source", "time", "author", "title", "keywords")},
    )
    duplicate_batch_id = store.create_batch("2017-2025", "media", "trade-war-copy")
    duplicate_candidate_id = store.add_candidate(
        duplicate_batch_id,
        MaterialCandidate(
            "https://example.org/story", "2017-2025", "media", "trade-war-copy"
        ),
    )
    duplicate_evidence_id = store.add_evidence(
        duplicate_candidate_id,
        SourceEvidence(
            source_url="https://example.org/story",
            fetched_at="2026-11-06T00:00:00Z",
            status_code=200,
            content_sha256="body-hash-2",
            body_complete=True,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    duplicate_id, duplicate_inserted = store.add_verified_material(
        duplicate_candidate_id,
        duplicate_evidence_id,
        material,
        field_sources={name: material.source_url for name in ("source", "time", "author", "title", "keywords")},
    )

    assert first_inserted is True
    assert duplicate_inserted is False
    assert first_id == duplicate_id
    assert store.get_verified_materials()[0].duplicate_count == 1
    store.close()


def test_duplicate_discovery_is_counted_even_if_second_copy_is_not_verified(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "media", "two-queries")
    first_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/a", "2017-2025", "media", "q1"),
    )
    second_batch = store.create_batch("2017-2025", "media", "q2")
    second_id = store.add_candidate(
        second_batch,
        MaterialCandidate("https://EXAMPLE.org/a#top", "2017-2025", "media", "q2"),
    )

    assert first_id != second_id
    assert store.batch_summary(second_batch)["duplicate"] == 1
    store.close()


def test_tracking_query_parameters_do_not_prevent_url_deduplication(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "media", "q1")
    store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/a?utm_source=feed", "2017-2025", "media", "q1"),
    )
    duplicate_batch = store.create_batch("2017-2025", "media", "q2")
    store.add_candidate(
        duplicate_batch,
        MaterialCandidate("https://example.org/a?utm_source=social", "2017-2025", "media", "q2"),
    )

    assert store.batch_summary(duplicate_batch)["duplicate"] == 1
    store.close()


def test_resuming_batch_and_candidate_does_not_create_duplicate_discovery(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "media", "resume-query")
    repeated_batch_id = store.create_batch("2017-2025", "media", "resume-query")
    candidate = MaterialCandidate("https://example.org/a", "2017-2025", "media", "resume-query")

    first_id = store.add_candidate(batch_id, candidate)
    resumed_id = store.add_candidate(repeated_batch_id, candidate)

    assert batch_id == repeated_batch_id
    assert first_id == resumed_id
    assert store.batch_summary(batch_id)["candidate"] == 1
    assert store.batch_summary(batch_id)["duplicate"] == 0
    store.close()


def test_platform_ids_are_scoped_to_the_platform_domain(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "new_media", "same-numeric-id")
    first = store.add_candidate(
        batch_id,
        MaterialCandidate(
            "https://www.youtube.com/watch?v=123",
            "2017-2025",
            "new_media",
            "video",
            platform_id="123",
        ),
    )
    second = store.add_candidate(
        batch_id,
        MaterialCandidate(
            "https://www.x.com/status/123",
            "2017-2025",
            "new_media",
            "post",
            platform_id="123",
        ),
    )

    assert store.batch_summary(batch_id)["duplicate"] == 0
    assert first != second
    store.close()


def test_verified_duplicate_is_counted_in_its_own_batch(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    url = "https://example.org/a"
    material = VerifiedMaterial(
        "Example", "2020-01-01", "未注明", "Title", "", "", "Full text", url
    )
    batch_one = store.create_batch("2017-2025", "government", "query-one")
    candidate_one = store.add_candidate(
        batch_one, MaterialCandidate(url, "2017-2025", "government", "query-one")
    )
    evidence_one = store.add_evidence(
        candidate_one,
        SourceEvidence(url, "2026-11-06T00:00:00Z", 200, "hash-1", body_complete=True, metadata_verified=True),
        "allow",
    )
    store.add_verified_material(candidate_one, evidence_one, material)
    store.update_candidate_status(candidate_one, "verified")

    batch_two = store.create_batch("2017-2025", "government", "query-two")
    candidate_two = store.add_candidate(
        batch_two, MaterialCandidate(url, "2017-2025", "government", "query-two")
    )
    evidence_two = store.add_evidence(
        candidate_two,
        SourceEvidence(url, "2026-11-06T00:00:00Z", 200, "hash-2", body_complete=True, metadata_verified=True),
        "allow",
    )
    store.add_verified_material(candidate_two, evidence_two, material)
    store.update_candidate_status(candidate_two, "verified")

    summary = store.batch_summary(batch_two)
    assert summary["verified"] == 1
    assert summary["duplicate"] == 1
    store.close()


def test_incomplete_evidence_cannot_be_promoted(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("1992-2016", "think_tank", "wto")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/a", "1992-2016", "think_tank", "wto"),
    )
    evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url="https://example.org/a",
            fetched_at="2026-11-06T00:00:00Z",
            status_code=200,
            content_sha256="snippet",
            body_complete=False,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    material = VerifiedMaterial(
        "Think tank", "2001-01-01", "未注明", "Title", "", "keyword", "snippet",
        "https://example.org/a",
    )

    try:
        store.add_verified_material(candidate_id, evidence_id, material)
    except ValueError as exc:
        assert "complete" in str(exc)
    else:
        raise AssertionError("incomplete evidence must not be promoted")
    store.close()


def test_database_gate_rejects_unverified_publication_date(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("1992-2016", "think_tank", "wto")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/a", "1992-2016", "think_tank", "wto"),
    )
    evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url="https://example.org/a",
            fetched_at="2026-11-06T00:00:00Z",
            status_code=200,
            content_sha256="body-hash",
            body_complete=True,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    material = VerifiedMaterial(
        "Think tank", "2020-02", "未注明", "Title", "", "keyword", "full body",
        "https://example.org/a",
    )

    try:
        store.add_verified_material(candidate_id, evidence_id, material)
    except ValueError as exc:
        assert "YYYY-MM-DD" in str(exc)
    else:
        raise AssertionError("invalid publication date must not be promoted")
    store.close()
