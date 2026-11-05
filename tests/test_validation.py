from dataclasses import replace

import pytest

from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.import_authorized import import_authorized_full_text
from research_crawler.store import ResearchStore
from research_crawler.validation import ValidationError, validate_material


@pytest.fixture
def material():
    return VerifiedMaterial(
        source="Example Agency",
        time="2020-02-03",
        author="A. Author",
        title="Source title",
        abstract="Publisher abstract",
        keywords="China, policy",
        body="Paragraph one.\n\nParagraph two.",
        source_url="https://example.org/story",
    )


@pytest.fixture
def evidence():
    return SourceEvidence(
        source_url="https://example.org/story",
        fetched_at="2026-11-06T00:00:00Z",
        status_code=200,
        content_sha256="sha256-value",
        body_complete=True,
        metadata_verified=True,
    )


def test_accepts_material_with_matching_source_evidence(material, evidence):
    fields = {
        name: material.source_url
        for name in ("source", "time", "author", "title", "abstract", "keywords")
    }
    fields["abstract"] = material.source_url
    fields["keywords"] = material.source_url
    assert validate_material(material, evidence, fields) == material


def test_rejects_unknown_or_invalid_exact_publication_date(material, evidence):
    fields = {
        name: material.source_url
        for name in ("source", "time", "author", "title", "abstract", "keywords")
    }
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        validate_material(replace(material, time="2020-02"), evidence, fields)


def test_rejects_metadata_or_body_without_matching_source_url(material, evidence):
    fields = {
        name: material.source_url
        for name in ("source", "time", "author", "title", "abstract", "keywords")
    }
    fields["title"] = "https://other.example/story"
    with pytest.raises(ValidationError, match="same source"):
        validate_material(material, evidence, fields)


def test_fills_missing_author_with_required_literal(material, evidence):
    fields = {
        name: material.source_url
        for name in ("source", "time", "author", "title", "abstract", "keywords")
    }
    result = validate_material(replace(material, author=""), evidence, fields)
    assert result.author == "未注明"


def test_requires_generated_abstract_prefix(material, evidence):
    fields = {name: material.source_url for name in ("source", "time", "author", "title")}
    with pytest.raises(ValidationError, match="据正文整理："):
        validate_material(material, evidence, fields, abstract_origin="derived")


def test_requires_source_evidence_for_publisher_abstract(material, evidence):
    fields = {name: material.source_url for name in ("source", "time", "author", "title")}
    with pytest.raises(ValidationError, match="abstract metadata"):
        validate_material(material, evidence, fields)


def test_rejects_incomplete_body_and_unverified_metadata(material, evidence):
    fields = {name: material.source_url for name in ("source", "time", "author", "title")}
    with pytest.raises(ValidationError, match="complete"):
        validate_material(material, replace(evidence, body_complete=False), fields)
    with pytest.raises(ValidationError, match="metadata"):
        validate_material(material, replace(evidence, metadata_verified=False), fields)


def test_authorized_full_text_import_records_hash_path_and_material(tmp_path, material):
    source_file = tmp_path / "provided-full-text.txt"
    source_file.write_bytes("Authorized full text.\nSecond paragraph.".encode("utf-8"))
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "research_literature", "authorized")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(
            "https://library.example/record", "2017-2025", "research_literature", "authorized"
        ),
    )
    imported = import_authorized_full_text(
        store=store,
        candidate_id=candidate_id,
        file_path=source_file,
        material=replace(material, body="placeholder", source_url="https://library.example/record"),
        authorization_note="Provided by researcher from university library access.",
        completeness_confirmed=True,
        field_sources={
            name: "https://library.example/record"
            for name in ("source", "time", "author", "title", "abstract", "keywords")
        },
    )

    assert imported.body == "Authorized full text.\nSecond paragraph."
    saved = store.get_verified_materials()[0]
    assert saved == imported
    row = store.connection.execute("SELECT * FROM evidence").fetchone()
    assert row["evidence_path"] == str(source_file)
    assert row["authorization_note"] == "Provided by researcher from university library access."
    assert row["content_sha256"]
    assert row["retrieval_method"] == "authorized_import"
    store.close()


def test_authorized_import_requires_note_and_completeness_confirmation(tmp_path, material):
    source_file = tmp_path / "provided.txt"
    source_file.write_text("Full text", encoding="utf-8")
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "research_literature", "authorized")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://library.example/record", "2017-2025", "research_literature", "authorized"),
    )
    kwargs = dict(
        store=store,
        candidate_id=candidate_id,
        file_path=source_file,
        material=replace(material, source_url="https://library.example/record"),
        authorization_note="",
        completeness_confirmed=False,
        field_sources={
            name: "https://library.example/record"
            for name in ("source", "time", "author", "title", "abstract", "keywords")
        },
    )

    with pytest.raises(ValidationError, match="authorization"):
        import_authorized_full_text(**kwargs)
    store.close()
