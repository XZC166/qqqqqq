import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.items import SourceEvidence, VerifiedMaterial
from research_crawler.store import ResearchStore
from research_crawler.validation import ValidationError, validate_material


def import_authorized_full_text(
    *,
    store: ResearchStore,
    candidate_id: int,
    file_path: str | Path,
    material: VerifiedMaterial,
    authorization_note: str,
    completeness_confirmed: bool,
    field_sources: dict[str, str],
    abstract_origin: str = "publisher",
) -> VerifiedMaterial:
    source_path = Path(file_path)
    if not authorization_note.strip():
        raise ValidationError("authorization note is required")
    if not completeness_confirmed:
        raise ValidationError("full-text completeness must be confirmed")
    try:
        raw_bytes = source_path.read_bytes()
        body = raw_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValidationError("provided full text must be a readable UTF-8 file") from exc
    if not body.strip():
        raise ValidationError("provided full text is empty")

    imported = replace(material, body=body)
    evidence = SourceEvidence(
        source_url=imported.source_url,
        fetched_at=datetime.now(timezone.utc).isoformat(),
        status_code=200,
        content_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        evidence_path=source_path.resolve(),
        body_complete=True,
        metadata_verified=True,
        body_format="authorized_text",
        authorization_note=authorization_note.strip(),
        retrieval_method="authorized_import",
    )
    imported = validate_material(
        imported,
        evidence,
        field_sources,
        abstract_origin=abstract_origin,
    )
    evidence_id = store.add_evidence(candidate_id, evidence, access_status="allow")
    store.add_verified_material(
        candidate_id,
        evidence_id,
        imported,
        abstract_origin=abstract_origin,
        field_sources=field_sources,
    )
    store.update_candidate_status(candidate_id, "verified", "authorized full text provided by user")
    return imported
