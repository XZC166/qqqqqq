import hashlib
from pathlib import Path

from research_crawler.items import MaterialCandidate, SourceEvidence
import research_crawler.revalidation as revalidation
from research_crawler.store import ResearchStore


def test_revalidation_promotes_only_an_exact_adapter_match(tmp_path):
    database = tmp_path / "research.sqlite3"
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    raw = (Path(__file__).parent / "fixtures" / "government_page.html").read_bytes()
    source_url = "https://example.org/story"
    evidence_path = evidence_dir / f"{hashlib.sha256(raw).hexdigest()}.html"
    evidence_path.write_bytes(raw)

    store = ResearchStore(database)
    batch_id = store.create_batch("2017-2025", "government", "legacy-review")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(source_url, "2017-2025", "government", "legacy-review"),
    )
    evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url,
            "2026-11-07T00:00:00Z",
            200,
            hashlib.sha256(raw).hexdigest(),
            evidence_path=evidence_path,
            body_complete=True,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    store.connection.execute(
        """INSERT INTO materials(
               identity_key, source, published_on, author, title, abstract,
               keywords, body, source_url, duplicate_count, evidence_id
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "url:https://example.org/story",
            "Example U.S. Agency",
            "2020-02-03",
            "A. Author",
            "Source title",
            "Publisher-provided abstract.",
            "",
            "First source paragraph.\n\nSecond source paragraph.",
            source_url,
            0,
            evidence_id,
        ),
    )
    store.connection.commit()

    report = revalidation.revalidate_legacy_materials(store)

    assert report["exact"] == [1]
    assert report["mismatch"] == []
    assert store.connection.execute(
        "SELECT COUNT(*) FROM material_verifications"
    ).fetchone()[0] == 1
    store.close()


def test_revalidation_leaves_a_mismatch_without_snapshot(tmp_path):
    database = tmp_path / "research.sqlite3"
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    raw = (Path(__file__).parent / "fixtures" / "government_page.html").read_bytes()
    source_url = "https://example.org/story"
    evidence_path = evidence_dir / "source.html"
    evidence_path.write_bytes(raw)

    store = ResearchStore(database)
    batch_id = store.create_batch("2017-2025", "government", "legacy-review")
    candidate_id = store.connection.execute(
        "INSERT INTO candidates(batch_id,source_url,period,source_category,query_label,identity_key) VALUES(?,?,?,?,?,?)",
        (batch_id, source_url, "2017-2025", "government", "legacy-review", "url:https://example.org/story"),
    ).lastrowid
    evidence_id = store.connection.execute(
        """INSERT INTO evidence(candidate_id,source_url,fetched_at,status_code,content_sha256,
           evidence_path,body_complete,metadata_verified,access_status)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (candidate_id, source_url, "2026-11-07T00:00:00Z", 200, hashlib.sha256(raw).hexdigest(),
         str(evidence_path), 1, 1, "allow"),
    ).lastrowid
    store.connection.execute(
        """INSERT INTO materials(identity_key,source,published_on,author,title,abstract,
           keywords,body,source_url,duplicate_count,evidence_id)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        ("url:https://example.org/story", "Example U.S. Agency", "2020-02-03", "A. Author",
         "Wrong title", "Publisher-provided abstract.", "", "Different body", source_url, 0, evidence_id),
    )
    store.connection.commit()

    report = revalidation.revalidate_legacy_materials(store)

    assert report["exact"] == []
    assert report["mismatch"] == [1]
    assert store.connection.execute(
        "SELECT COUNT(*) FROM material_verifications"
    ).fetchone()[0] == 0
    store.close()


def test_pending_revalidation_promotes_only_reproducible_complete_source_evidence(tmp_path):
    assert hasattr(revalidation, "revalidate_pending_candidates")
    database = tmp_path / "research.sqlite3"
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    raw = (Path(__file__).parent / "fixtures" / "government_page.html").read_bytes()
    source_url = "https://example.org/story"
    evidence_path = evidence_dir / "source.html"
    evidence_path.write_bytes(raw)

    store = ResearchStore(database)
    batch_id = store.create_batch("2017-2025", "government", "pending-review")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(source_url, "2017-2025", "government", "pending-review"),
    )
    store.update_candidate_status(candidate_id, "pending", "prior parse incomplete")
    store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url,
            "2026-11-07T00:00:00Z",
            200,
            hashlib.sha256(raw).hexdigest(),
            evidence_path=evidence_path,
            body_complete=False,
            metadata_verified=False,
        ),
        access_status="allow",
    )

    report = revalidation.revalidate_pending_candidates(store)

    assert report["verified"] == [candidate_id]
    assert report["pending"] == []
    assert store.connection.execute(
        "SELECT status FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()["status"] == "verified"
    assert len(store.get_verified_materials()) == 1
    store.close()


def test_pending_revalidation_does_not_promote_restricted_evidence(tmp_path):
    assert hasattr(revalidation, "revalidate_pending_candidates")
    database = tmp_path / "research.sqlite3"
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    raw = (Path(__file__).parent / "fixtures" / "government_page.html").read_bytes()
    source_url = "https://example.org/story"
    evidence_path = evidence_dir / "source.html"
    evidence_path.write_bytes(raw)

    store = ResearchStore(database)
    batch_id = store.create_batch("2017-2025", "government", "pending-review")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(source_url, "2017-2025", "government", "pending-review"),
    )
    store.update_candidate_status(candidate_id, "pending", "prior parse incomplete")
    store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url,
            "2026-11-07T00:00:00Z",
            200,
            hashlib.sha256(raw).hexdigest(),
            evidence_path=evidence_path,
            body_complete=False,
            metadata_verified=True,
        ),
        access_status="restricted",
    )
    report = revalidation.revalidate_pending_candidates(store)

    assert report["verified"] == []
    assert report["pending"] == []
    assert store.connection.execute(
        "SELECT status FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()["status"] == "restricted"
    assert store.get_verified_materials() == []
    store.close()
