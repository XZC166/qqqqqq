"""Recheck legacy materials against the raw evidence already stored locally."""

from pathlib import Path
import hashlib
from dataclasses import replace

from scrapy.http import HtmlResponse, Request, Response

from research_crawler.items import MaterialCandidate, SourceEvidence
from research_crawler.policy import AccessDecision
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import ResearchStore
from research_crawler.validation import ValidationError, validate_material


def revalidate_legacy_materials(store: ResearchStore) -> dict[str, list]:
    """Create exact verification snapshots only for unchanged, reproducible records.

    A material is promoted out of the legacy state only when its current adapter output
    matches every stored export field and all supporting metadata evidence is present.
    No source is fetched by this function.
    """
    rows = store.connection.execute(
        """SELECT m.*, e.id AS evidence_id, e.candidate_id, e.evidence_path,
                  e.status_code, e.body_format, e.access_status, e.metadata_verified,
                  c.period, c.source_category, c.query_label, c.platform_id, c.metadata_url
           FROM materials m
           JOIN evidence e ON e.id = m.evidence_id
           JOIN candidates c ON c.id = e.candidate_id
           LEFT JOIN material_verifications v ON v.material_id = m.id
           WHERE v.material_id IS NULL
           ORDER BY m.id"""
    ).fetchall()
    report: dict[str, list] = {
        "exact": [],
        "mismatch": [],
        "no_material": [],
        "missing_supporting_evidence": [],
        "error": [],
    }
    adapter = GovernmentArticleAdapter()
    for row in rows:
        try:
            result, metadata_ids = _extract_existing(store, row, adapter)
            material = result.get("material")
            if material is None:
                report["no_material"].append(row["id"])
                continue
            if not _same_material_fields(row, material):
                report["mismatch"].append(row["id"])
                continue
            if not row["metadata_verified"] and not metadata_ids:
                report["missing_supporting_evidence"].append(row["id"])
                continue
            store.add_verified_material(
                row["candidate_id"],
                row["evidence_id"],
                material,
                abstract_origin=result.get("abstract_origin", "publisher" if material.abstract else "none"),
                field_sources=result.get("field_sources", {}),
                metadata_evidence_ids=metadata_ids,
            )
            report["exact"].append(row["id"])
        except Exception as exc:  # preserve the queue item for a later targeted review
            report["error"].append({"material_id": row["id"], "detail": str(exc)})
    return report


def revalidate_pending_candidates(store: ResearchStore) -> dict[str, list]:
    """Reparse pending candidates from unchanged, complete source evidence only."""
    candidates = store.connection.execute(
        "SELECT * FROM candidates WHERE status = 'pending' ORDER BY id"
    ).fetchall()
    report = {"verified": [], "pending": []}
    adapter = GovernmentArticleAdapter()
    for candidate_row in candidates:
        evidence_row = store.connection.execute(
            """SELECT e.id AS evidence_id, e.source_url, e.fetched_at, e.status_code,
                      e.content_sha256, e.evidence_path, e.body_complete,
                      e.metadata_verified, e.body_format, e.original_page_verified,
                      c.period, c.source_category, c.query_label, c.platform_id,
                      c.metadata_url
               FROM evidence e JOIN candidates c ON c.id = e.candidate_id
               WHERE e.candidate_id = ? AND e.source_url = c.source_url
                 AND e.status_code >= 200 AND e.status_code < 300
                 AND e.access_status = 'allow'
                 AND e.evidence_path IS NOT NULL
               ORDER BY e.id DESC LIMIT 1""",
            (candidate_row["id"],),
        ).fetchone()
        if evidence_row is None:
            _record_pending(store, report, candidate_row["id"], "no complete, allowed source evidence file")
            continue

        try:
            evidence_path = Path(evidence_row["evidence_path"])
            raw = evidence_path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != evidence_row["content_sha256"]:
                raise ValidationError("stored source evidence hash mismatch")

            result, metadata_ids = _extract_existing(
                store, evidence_row, adapter, candidate_id=candidate_row["id"]
            )
            material = result.get("material")
            if result.get("decision") is not AccessDecision.ALLOW or material is None:
                raise ValidationError("source adapter did not verify a complete material")
            parsed_evidence = result.get("evidence")
            if not isinstance(parsed_evidence, SourceEvidence):
                raise ValidationError("source adapter did not return verifiable evidence")
            if (
                parsed_evidence.source_url != evidence_row["source_url"]
                or parsed_evidence.content_sha256 != evidence_row["content_sha256"]
            ):
                raise ValidationError("reparsed evidence does not match the stored source capture")

            metadata_urls = {
                row["source_url"]
                for row in store.connection.execute(
                    f"SELECT source_url FROM evidence WHERE id IN ({','.join('?' for _ in metadata_ids)})",
                    tuple(metadata_ids),
                ).fetchall()
            } if metadata_ids else set()
            evidence = replace(
                parsed_evidence,
                evidence_path=evidence_path,
                retrieval_method="offline_revalidation",
                retrieval_id=f"candidate-{candidate_row['id']}-evidence-{evidence_row['evidence_id']}",
            )
            material = validate_material(
                material,
                evidence,
                result.get("field_sources", {}),
                abstract_origin=result.get("abstract_origin", "publisher" if material.abstract else "none"),
                metadata_evidence_urls=metadata_urls,
                period=evidence_row["period"],
            )

            from research_crawler.pipelines import _body_matches_source, _pdf_is_scan_like

            if _pdf_is_scan_like(raw) and (
                evidence.body_format != "pdf_reviewed_transcript"
                or not evidence.original_page_verified
            ):
                raise ValidationError("scanned PDF requires a word-for-word reviewed transcript")
            if not _body_matches_source(material.body, raw, evidence.body_format):
                raise ValidationError("body does not correspond to source evidence")

            verified_evidence_id = store.add_evidence(
                candidate_row["id"], evidence, access_status="allow"
            )
            store.add_verified_material(
                candidate_row["id"],
                verified_evidence_id,
                material,
                abstract_origin=result.get("abstract_origin", "publisher" if material.abstract else "none"),
                field_sources=result.get("field_sources", {}),
                metadata_evidence_ids=metadata_ids,
            )
            store.update_candidate_status(candidate_row["id"], "verified")
            report["verified"].append(candidate_row["id"])
        except Exception as exc:
            _record_pending(store, report, candidate_row["id"], str(exc))
    return report


def _record_pending(store: ResearchStore, report: dict[str, list], candidate_id: int, reason: str) -> None:
    store.update_candidate_status(candidate_id, "pending", reason)
    row = store.connection.execute(
        "SELECT source_url, period, source_category FROM candidates WHERE id = ?",
        (candidate_id,),
    ).fetchone()
    report["pending"].append({
        "candidate_id": candidate_id,
        "source_url": row["source_url"],
        "period": row["period"],
        "source_category": row["source_category"],
        "reason": reason,
    })


def repair_pmc_derived_metadata(store: ResearchStore) -> dict[str, list]:
    """Fill missing PMC abstract/keywords from the same stored source body."""
    rows = store.connection.execute(
        """SELECT m.*, e.id AS evidence_id, e.candidate_id, e.evidence_path,
                  e.status_code, e.body_format, e.metadata_verified, c.period,
                  c.source_category, c.query_label, c.platform_id, c.metadata_url
           FROM materials m
           JOIN evidence e ON e.id = m.evidence_id
           JOIN candidates c ON c.id = e.candidate_id
           WHERE m.source_url LIKE 'https://pmc.ncbi.nlm.nih.gov/%'
             AND (trim(m.abstract) = '' OR trim(m.keywords) = '')
           ORDER BY m.id"""
    ).fetchall()
    report = {"repaired": [], "no_material": [], "mismatch": [], "error": []}
    adapter = GovernmentArticleAdapter()
    for row in rows:
        try:
            extracted, _ = _extract_existing(store, row, adapter)
            material = extracted.get("material")
            if material is None:
                report["no_material"].append(row["id"])
                continue
            stable_fields = ("source", "time", "author", "title", "body", "source_url")
            if any(getattr(material, name) != row[name if name != "time" else "published_on"] for name in stable_fields):
                report["mismatch"].append(row["id"])
                continue
            if not material.abstract or not material.keywords:
                report["no_material"].append(row["id"])
                continue
            store.add_verified_material(
                row["candidate_id"],
                row["evidence_id"],
                material,
                abstract_origin=extracted.get("abstract_origin", "publisher"),
                field_sources=extracted.get("field_sources", {}),
            )
            report["repaired"].append(row["id"])
        except Exception as exc:
            report["error"].append({"material_id": row["id"], "detail": str(exc)})
    return report


def _extract_existing(
    store: ResearchStore,
    row,
    adapter: GovernmentArticleAdapter,
    *,
    candidate_id: int | None = None,
):
    evidence_path = Path(row["evidence_path"])
    raw = evidence_path.read_bytes()
    candidate = MaterialCandidate(
        row["source_url"],
        row["period"],
        row["source_category"],
        row["query_label"],
        row["platform_id"],
        row["metadata_url"],
    )
    request = Request(row["source_url"])
    if row["body_format"].startswith("pdf"):
        response = Response(
            url=row["source_url"],
            request=request,
            body=raw,
            status=row["status_code"],
            headers={b"Content-Type": b"application/pdf"},
        )
    else:
        response = HtmlResponse(
            url=row["source_url"],
            request=request,
            body=raw,
            encoding="utf-8",
            status=row["status_code"],
        )

    metadata_ids = set()
    metadata_url = row["metadata_url"]
    if metadata_url:
        metadata_row = store.connection.execute(
            """SELECT * FROM evidence
               WHERE candidate_id = ? AND source_url = ? AND metadata_verified = 1
               ORDER BY id DESC LIMIT 1""",
            (candidate_id or row["candidate_id"], metadata_url),
        ).fetchone()
        if metadata_row and metadata_row["evidence_path"]:
            metadata_raw = Path(metadata_row["evidence_path"]).read_bytes()
            metadata_response = HtmlResponse(
                url=metadata_url,
                request=Request(metadata_url),
                body=metadata_raw,
                encoding="utf-8",
                status=metadata_row["status_code"],
            )
            response.request.meta["metadata_response"] = metadata_response
            metadata_ids.add(metadata_row["id"])

    result = adapter.extract(response, candidate)
    supporting = []
    for item in result.get("supporting_evidence", []):
        evidence = item.get("evidence")
        if evidence is None or item.get("decision") is not AccessDecision.ALLOW:
            continue
        existing = store.connection.execute(
            """SELECT id FROM evidence
               WHERE candidate_id = ? AND source_url = ? AND content_sha256 = ?
                 AND metadata_verified = 1 AND access_status = 'allow'
               ORDER BY id DESC LIMIT 1""",
            (candidate_id or row["candidate_id"], evidence.source_url, evidence.content_sha256),
        ).fetchone()
        if existing:
            supporting.append(existing["id"])
    metadata_ids.update(supporting)
    return result, metadata_ids


def _same_material_fields(row, material) -> bool:
    return (
        row["source"],
        row["published_on"],
        row["author"],
        row["title"],
        row["abstract"],
        row["keywords"],
        row["body"],
        row["source_url"],
    ) == (
        material.source,
        material.time,
        material.author,
        material.title,
        material.abstract,
        material.keywords,
        material.body,
        material.source_url,
    )
