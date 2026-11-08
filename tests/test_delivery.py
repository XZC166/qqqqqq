import hashlib
import json
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook

from research_crawler.items import EXPORT_COLUMNS, MaterialCandidate, SourceEvidence
from research_crawler.store import ResearchStore
from test_export import add_verified


def prepared_store(tmp_path, body="First paragraph.\n\nSecond paragraph.", metadata=False):
    store = ResearchStore(tmp_path / "research.sqlite3")
    add_verified(store, body)
    raw = b"<html>Original captured source</html>"
    path = tmp_path / "source.html"
    path.write_bytes(raw)
    store.connection.execute(
        "UPDATE evidence SET evidence_path=?, content_sha256=?",
        (str(path), hashlib.sha256(raw).hexdigest()),
    )
    if metadata:
        url = "https://example.org/metadata"
        store.connection.execute("UPDATE candidates SET metadata_url=?", (url,))
        meta = tmp_path / "metadata.json"
        meta.write_bytes(b'{"published":"2020-01-02"}')
        metadata_id = store.add_evidence(1, SourceEvidence(
            url, "2026-11-06T00:00:00Z", 200,
            hashlib.sha256(meta.read_bytes()).hexdigest(),
            evidence_path=meta, metadata_verified=True, body_format="json",
        ), access_status="allow")
        store.add_verified_material(1, 1, store.get_verified_materials()[0],
            field_sources={name: url for name in ("source", "time", "author", "title", "abstract", "keywords")},
            metadata_evidence_ids={metadata_id})
    store.connection.commit()
    return store, path


def test_delivery_includes_exact_workbook_long_body_and_both_evidence_files(tmp_path):
    import importlib
    delivery = importlib.import_module("research_crawler.delivery")
    body = "原文😀\n\n" * 10000
    store, source = prepared_store(tmp_path, body, metadata=True)
    destination = tmp_path / "delivery.zip"
    delivery.build_delivery(store, destination)
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        archive.extractall(tmp_path / "unpacked")
        index = json.loads(archive.read("reports/provenance-index.json"))
        assert len(index) == 1
        assert len(index[0]["evidence"]) == 2
        for evidence in index[0]["evidence"]:
            assert hashlib.sha256(archive.read(evidence["file"])).hexdigest() == evidence["sha256"]
        assert "reports/batch-1.txt" in archive.namelist()
    workbook = load_workbook(tmp_path / "unpacked/materials.xlsx", read_only=True)
    rows = list(workbook.active.values)
    assert rows[0] == EXPORT_COLUMNS
    assert len(rows) == 2 and len(rows[1]) == 9
    assert (tmp_path / "unpacked" / rows[1][6]).read_text(encoding="utf-8") == body
    workbook.close()
    store.close()


@pytest.mark.parametrize("failure", ["tampered", "missing", "metadata"])
def test_bad_evidence_stops_delivery_and_preserves_previous_zip(tmp_path, failure):
    import importlib
    delivery = importlib.import_module("research_crawler.delivery")
    store, source = prepared_store(tmp_path, metadata=failure == "metadata")
    destination = tmp_path / "delivery.zip"
    destination.write_bytes(b"previous valid delivery")
    if failure == "tampered":
        source.write_bytes(b"changed")
    elif failure == "missing":
        source.unlink()
    else:
        (tmp_path / "metadata.json").unlink()
    with pytest.raises(ValueError, match="evidence"):
        delivery.build_delivery(store, destination)
    assert destination.read_bytes() == b"previous valid delivery"
    store.close()


def test_cli_deliver_creates_archive_without_changing_database(tmp_path):
    from research_crawler.cli import main
    store, source = prepared_store(tmp_path)
    store.close()
    database = tmp_path / "research.sqlite3"
    before = database.read_bytes()
    assert main(["deliver", "--db", str(database), "--output", str(tmp_path / "result.zip")]) == 0
    assert database.read_bytes() == before
    assert (tmp_path / "result.zip").is_file()


def test_exact_delivery_excludes_later_unrelated_metadata_capture(tmp_path):
    from research_crawler.delivery import build_delivery
    store, source = prepared_store(tmp_path, metadata=True)
    later = tmp_path / "later.json"
    later.write_bytes(b'{"published":"2021-04-05"}')
    later_id = store.add_evidence(1, SourceEvidence(
        "https://example.org/metadata", "2026-11-06T02:00:00Z", 200,
        hashlib.sha256(later.read_bytes()).hexdigest(), evidence_path=later,
        metadata_verified=True, body_format="json",
    ), access_status="allow")
    build_delivery(store, tmp_path / "exact.zip")
    with ZipFile(tmp_path / "exact.zip") as archive:
        record = json.loads(archive.read("reports/provenance-index.json"))[0]
        assert record["verification_provenance"] == "exact"
        assert record["field_sources"]["time"] == "https://example.org/metadata"
        assert len(record["evidence"]) == 2
        assert later_id not in {e["evidence_id"] for e in record["evidence"]}
        assert {e["role"] for e in record["evidence"]} == {"primary", "metadata_used_at_verification"}
    store.close()


def test_legacy_delivery_does_not_invent_exact_support_links(tmp_path):
    from research_crawler.delivery import build_delivery
    store, source = prepared_store(tmp_path, metadata=True)
    store.connection.execute("DELETE FROM material_verifications")
    store.connection.execute("DELETE FROM material_metadata_evidence")
    store.connection.commit()
    build_delivery(store, tmp_path / "legacy.zip")
    with ZipFile(tmp_path / "legacy.zip") as archive:
        record = json.loads(archive.read("reports/provenance-index.json"))[0]
        assert record["verification_provenance"] == "legacy_candidate_captures"
        assert record["field_sources"] is None
        assert {e["role"] for e in record["evidence"]} == {"primary", "metadata_candidate_capture"}
    store.close()


def test_exact_delivery_rejects_a_primary_evidence_reference_changed_outside_verification(tmp_path):
    from research_crawler.delivery import build_delivery
    store, source = prepared_store(tmp_path, metadata=True)
    store.connection.execute("UPDATE materials SET evidence_id=2")
    store.connection.commit()
    with pytest.raises(ValueError, match="evidence"):
        build_delivery(store, tmp_path / "bad.zip")
    assert not (tmp_path / "bad.zip").exists()
    store.close()


def test_exact_delivery_accepts_keywords_derived_from_verified_body(tmp_path):
    from research_crawler.delivery import build_delivery

    store, _source = prepared_store(tmp_path)
    fields = {name: "https://example.org/story" for name in ("source", "time", "author", "title")}
    fields["keywords"] = "body"
    store.connection.execute(
        "UPDATE material_verifications SET field_sources=?",
        (json.dumps(fields),),
    )
    store.connection.commit()

    build_delivery(store, tmp_path / "body-keywords.zip")

    with ZipFile(tmp_path / "body-keywords.zip") as archive:
        provenance = json.loads(archive.read("reports/provenance-index.json"))[0]
        assert provenance["field_sources"]["keywords"] == "body"
    store.close()


def test_delivery_includes_local_review_audits(tmp_path):
    from research_crawler.delivery import build_delivery

    store, source = prepared_store(tmp_path)
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / "audit.json").write_text('{"status":"verified"}', encoding="utf-8")

    build_delivery(store, tmp_path / "with-reviews.zip")

    with ZipFile(tmp_path / "with-reviews.zip") as archive:
        assert archive.read("reviews/audit.json") == b'{"status":"verified"}'
    store.close()


def test_delivery_packages_pending_candidate_evidence_outside_verified_provenance(tmp_path):
    from research_crawler.delivery import build_delivery

    store, _source = prepared_store(tmp_path)
    candidate_id = store.add_candidate(1, MaterialCandidate(
        "https://example.org/pending.pdf", "1949-1972", "think_tank", "pending-report"
    ))
    store.update_candidate_status(candidate_id, "pending", "Full report is available, but OCR is unverified.")
    raw = b"%PDF-raw pending candidate"
    path = tmp_path / "pending.pdf"
    path.write_bytes(raw)
    evidence_id = store.add_evidence(candidate_id, SourceEvidence(
        "https://example.org/pending.pdf", "2026-11-07T00:00:00Z", 200,
        hashlib.sha256(raw).hexdigest(), evidence_path=path, body_format="pdf_text",
    ), access_status="allow")
    destination = tmp_path / "pending-evidence.zip"

    build_delivery(store, destination)

    with ZipFile(destination) as archive:
        index = json.loads(archive.read("reports/candidate-evidence-index.json"))
        record = next(row for row in index if row["evidence_id"] == evidence_id)
        assert record["candidate_status"] == "pending"
        assert record["verification_status"] == "not_verified"
        assert record["file"].startswith("candidate-evidence/")
        assert archive.read(record["file"]) == raw
        verified = json.loads(archive.read("reports/provenance-index.json"))
        assert all(evidence["evidence_id"] != evidence_id
                   for material in verified for evidence in material["evidence"])
        workbook = load_workbook(archive.open("materials.xlsx"), read_only=True, data_only=True)
        rows = list(workbook.active.values)
        assert len(rows) == 2
        assert all(row[7] != "https://example.org/pending.pdf" for row in rows[1:])
        workbook.close()
    store.close()
