import sqlite3
import json
import pytest

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
        "excluded": 0,
    }
    assert evidence_id > 0
    reopened.close()


def test_candidate_and_material_can_link_separate_metadata_evidence(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    pdf_url = "https://example.org/report.pdf"
    metadata_url = "https://example.org/report-record"
    batch_id = store.create_batch("1992-2016", "think_tank", "paired-pdf")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(
            pdf_url, "1992-2016", "think_tank", "paired-pdf", metadata_url=metadata_url
        ),
    )
    saved_candidate = store.connection.execute(
        "SELECT metadata_url FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()
    assert saved_candidate["metadata_url"] == metadata_url
    body_evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            pdf_url, "2026-11-06T00:00:00Z", 200, "pdf-hash",
            body_complete=True, metadata_verified=False, body_format="pdf_text",
        ),
        access_status="allow",
    )
    metadata_evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            metadata_url, "2026-11-06T00:00:00Z", 200, "page-hash",
            body_complete=False, metadata_verified=True,
        ),
        access_status="allow",
    )
    material = VerifiedMaterial(
        "Example Publisher", "2008-06-11", "A. Author", "Report title", "",
        "", "Complete PDF text.", pdf_url,
    )

    store.add_verified_material(
        candidate_id,
        body_evidence_id,
        material,
        abstract_origin="none",
        field_sources={name: metadata_url for name in ("source", "time", "author", "title")},
        metadata_evidence_ids={metadata_evidence_id},
    )

    assert store.get_verified_materials() == [material]
    saved_evidence = list(store.connection.execute("SELECT source_url, body_complete, metadata_verified FROM evidence ORDER BY id"))
    assert [tuple(row) for row in saved_evidence] == [
        (pdf_url, 1, 0),
        (metadata_url, 0, 1),
    ]
    snapshot = store.connection.execute("SELECT * FROM material_verifications").fetchone()
    assert snapshot["primary_evidence_id"] == body_evidence_id
    assert snapshot["abstract_origin"] == "none"
    assert json.loads(snapshot["field_sources"]) == {name: metadata_url for name in ("source", "time", "author", "title")}
    assert [row[0] for row in store.connection.execute("SELECT evidence_id FROM material_metadata_evidence")] == [metadata_evidence_id]
    replacement_id = store.add_evidence(candidate_id, SourceEvidence(
        metadata_url, "2026-11-06T01:00:00Z", 200, "reviewed-new-page-hash", metadata_verified=True,
    ), access_status="allow")
    store.add_verified_material(candidate_id, body_evidence_id, material, abstract_origin="none",
        field_sources={name: metadata_url for name in ("source", "time", "author", "title")},
        metadata_evidence_ids={replacement_id})
    store.close()
    store = ResearchStore(tmp_path / "research.sqlite3")
    assert [row[0] for row in store.connection.execute("SELECT evidence_id FROM material_metadata_evidence")] == [replacement_id]
    store.close()


def test_migration_keeps_existing_materials_without_fabricating_historical_snapshots(tmp_path):
    from test_export import add_verified
    path = tmp_path / "legacy.sqlite3"
    store = ResearchStore(path)
    add_verified(store, "Previously reviewed source body.")
    before = store.get_verified_materials()
    store.connection.execute("DROP TABLE material_metadata_evidence")
    store.connection.execute("DROP TABLE material_verifications")
    store.connection.commit()
    store.close()
    store = ResearchStore(path)
    assert store.get_verified_materials() == before
    assert store.connection.execute("SELECT COUNT(*) FROM material_verifications").fetchone()[0] == 0
    store.close()


def test_promotion_update_rolls_back_if_verification_snapshot_cannot_be_written(tmp_path):
    from dataclasses import replace
    from test_export import add_verified
    store = ResearchStore(tmp_path / "atomic.sqlite3")
    add_verified(store, "Originally reviewed body.")
    original = store.get_verified_materials()[0]
    snapshot = tuple(store.connection.execute("SELECT * FROM material_verifications").fetchone())
    store.connection.executescript("""CREATE TRIGGER reject_snapshot BEFORE UPDATE ON material_verifications
        BEGIN SELECT RAISE(ABORT, 'test snapshot failure'); END;""")
    with pytest.raises(sqlite3.IntegrityError, match="snapshot failure"):
        store.add_verified_material(1, 1, replace(original, body="Newly reviewed body."),
            field_sources={name: original.source_url for name in ("source", "time", "author", "title", "abstract", "keywords")})
    assert store.get_verified_materials() == [original]
    assert tuple(store.connection.execute("SELECT * FROM material_verifications").fetchone()) == snapshot
    store.close()


def test_store_rejects_metadata_evidence_not_declared_by_candidate(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    pdf_url = "https://example.org/report.pdf"
    declared_url = "https://example.org/report-record"
    unrelated_url = "https://example.org/other-record"
    batch_id = store.create_batch("1992-2016", "think_tank", "paired-pdf")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(
            pdf_url, "1992-2016", "think_tank", "paired-pdf", metadata_url=declared_url
        ),
    )
    body_id = store.add_evidence(
        candidate_id,
        SourceEvidence(pdf_url, "2026-11-06T00:00:00Z", 200, "pdf", body_complete=True, body_format="pdf_text"),
        access_status="allow",
    )
    unrelated_id = store.add_evidence(
        candidate_id,
        SourceEvidence(unrelated_url, "2026-11-06T00:00:00Z", 200, "meta", metadata_verified=True),
        access_status="allow",
    )
    material = VerifiedMaterial(
        "Publisher", "2008-06-11", "A. Author", "Report", "", "",
        "Full text", pdf_url,
    )

    with pytest.raises(ValueError, match="declared metadata URL"):
        store.add_verified_material(
            candidate_id,
            body_id,
            material,
            abstract_origin="none",
            field_sources={name: unrelated_url for name in ("source", "time", "author", "title")},
            metadata_evidence_ids={unrelated_id},
        )
    store.close()


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


def test_url_duplicate_is_recognized_when_later_candidate_adds_platform_id(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/"
    material = VerifiedMaterial(
        "Example Journal", "2023-01-02", "A. Author", "Title", "", "", "Full text", url
    )
    first_batch = store.create_batch("2017-2025", "research_literature", "first")
    first_candidate = store.add_candidate(
        first_batch,
        MaterialCandidate(url, "2017-2025", "research_literature", "first"),
    )
    first_evidence = store.add_evidence(
        first_candidate,
        SourceEvidence(
            url, "2026-11-06T00:00:00Z", 200, "body-one",
            body_complete=True, metadata_verified=True,
        ),
        "allow",
    )
    store.add_verified_material(first_candidate, first_evidence, material)

    second_batch = store.create_batch("2017-2025", "research_literature", "second")
    second_candidate = store.add_candidate(
        second_batch,
        MaterialCandidate(
            url, "2017-2025", "research_literature", "second", platform_id="PMC1234567"
        ),
    )

    assert store.batch_summary(second_batch)["duplicate"] == 1
    assert store.get_verified_materials()[0].duplicate_count == 1
    assert store.connection.execute("SELECT COUNT(*) FROM materials").fetchone()[0] == 1
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


def test_x_and_twitter_aliases_share_post_identity_and_preserve_first_url(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    first_url = "https://twitter.com/StateDept/status/1670748325098975232"
    first_batch = store.create_batch("2017-2025", "new_media", "first")
    first = store.add_candidate(first_batch, MaterialCandidate(
        first_url, "2017-2025", "new_media", "first", platform_id="1670748325098975232"
    ))
    second_batch = store.create_batch("2017-2025", "new_media", "second")
    second = store.add_candidate(second_batch, MaterialCandidate(
        "https://x.com/StateDept/status/1670748325098975232", "2017-2025", "new_media",
        "second", platform_id="1670748325098975232"
    ))
    rows = store.connection.execute("SELECT identity_key,source_url FROM candidates ORDER BY id").fetchall()
    assert rows[0]["identity_key"] == rows[1]["identity_key"]
    assert rows[0]["source_url"] == first_url
    assert first != second
    assert store.batch_summary(second_batch)["duplicate"] == 1
    store.close()


def test_x_alias_deduplication_recognizes_existing_legacy_domain_key(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    first_batch = store.create_batch("2017-2025", "new_media", "first")
    first = store.add_candidate(first_batch, MaterialCandidate(
        "https://mobile.twitter.com/StateDept/status/1670748325098975232",
        "2017-2025", "new_media", "first", platform_id="1670748325098975232"
    ))
    store.connection.execute("UPDATE candidates SET identity_key=? WHERE id=?",
                             ("platform:mobile.twitter.com:1670748325098975232", first))
    store.connection.commit()
    second_batch = store.create_batch("2017-2025", "new_media", "second")
    store.add_candidate(second_batch, MaterialCandidate(
        "https://www.x.com/StateDept/status/1670748325098975232", "2017-2025", "new_media",
        "second", platform_id="1670748325098975232"
    ))
    assert store.batch_summary(second_batch)["duplicate"] == 1
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
