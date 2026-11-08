"""Package stored verified materials; integrity checks do not replace source review."""

import hashlib
import json
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import load_workbook

from research_crawler.export import EXCEL_CELL_LIMIT, _excel_character_count, export_verified
from research_crawler.coverage import (
    coverage_gaps,
    coverage_matrix,
    discovery_batch_coverage,
    verification_gaps,
    yearly_coverage,
)
from research_crawler.items import EXPORT_COLUMNS
from research_crawler.report import render_batch_report
from research_crawler.store import ResearchStore, canonicalize_url


def build_delivery(store: ResearchStore, destination: str | Path) -> Path:
    """Write an atomic ZIP with workbook, referenced bodies, reports and raw evidence.

    Evidence paths are resolved using the same working directory as the crawler.
    Exact promotion snapshots select their recorded supporting evidence IDs.
    Legacy materials retain clearly labelled candidate metadata captures.
    """
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if store.connection.in_transaction:
        raise ValueError("commit pending database changes before delivery")
    store.connection.execute("BEGIN")
    try:
        with TemporaryDirectory(prefix="corpus-delivery-", dir=destination.parent) as temporary:
            root = Path(temporary)
            index = _stage_evidence(store, root)
            candidate_evidence = _stage_candidate_evidence(store, root)
            review_count = _stage_reviews(store, root)
            materials = store.get_verified_materials()
            if len(materials) != len(index):
                raise ValueError("material/evidence record count mismatch")
            workbook = export_verified(store, root / "materials.xlsx")
            body_count = _verify_workbook(workbook, materials)
            reports = root / "reports"
            reports.mkdir()
            _write_json(reports / "provenance-index.json", index)
            _write_json(reports / "candidate-evidence-index.json", candidate_evidence)
            _write_json(reports / "coverage.json", {
                "matrix": coverage_matrix(store),
                "yearly": yearly_coverage(store),
                "discovery_batches": discovery_batch_coverage(store),
                "gaps": coverage_gaps(store),
                "verification_gaps": verification_gaps(store),
            })
            for batch in store.connection.execute("SELECT id FROM batches ORDER BY id"):
                (reports / f"batch-{batch['id']}.txt").write_text(
                    render_batch_report(store, batch["id"]), encoding="utf-8"
                )
            status = dict(store.connection.execute(
                "SELECT status,COUNT(*) FROM candidates GROUP BY status"
            ).fetchall())
            _write_json(reports / "integrity-audit.json", {
                "verified_unique_materials": len(materials),
                "long_body_files": body_count,
                "raw_evidence_files": len(list((root / "evidence").glob("*"))),
                "candidate_evidence_files": sum(bool(row["file"]) for row in candidate_evidence),
                "review_files": review_count,
                "candidate_status_counts": status,
                "checks": ["raw evidence SHA-256", "exact nine-column workbook round trip",
                           "verbatim UTF-8 body sidecars", "candidate evidence hash audit",
                           "ZIP CRC"],
                "limitations": [
                    "Stored-artifact integrity checks do not independently establish source completeness or publication date.",
                    "Coverage counts may overlap across periods/categories and must not be summed as unique totals.",
                    "Exact verification snapshots include only recorded support IDs. Legacy records include candidate metadata captures and do not claim exact historical support associations.",
                    "The collection is not exhaustive. Unverified or restricted captures are not promoted. Previously verified full text may remain based on its original allowed evidence even when a later access attempt is restricted; see review reports.",
                ],
            })
            staged_zip = root / "delivery.zip"
            files = sorted(path for path in root.rglob("*") if path.is_file())
            with ZipFile(staged_zip, "w", compression=ZIP_DEFLATED) as archive:
                for path in files:
                    archive.write(path, path.relative_to(root).as_posix())
            with ZipFile(staged_zip) as archive:
                if archive.testzip() is not None:
                    raise ValueError("ZIP integrity verification failed")
            os.replace(staged_zip, destination)
    finally:
        store.connection.rollback()
    return destination


def _stage_evidence(store: ResearchStore, root: Path) -> list[dict]:
    records = store.connection.execute(
        """SELECT m.id,m.source_url,m.published_on,m.title,m.evidence_id,
                  e.candidate_id,c.metadata_url
           FROM materials m LEFT JOIN evidence e ON m.evidence_id=e.id
           LEFT JOIN candidates c ON c.id=e.candidate_id ORDER BY m.id"""
    ).fetchall()
    index = []
    (root / "evidence").mkdir()
    for record in records:
        primary = store.connection.execute(
            "SELECT * FROM evidence WHERE id=?", (record["evidence_id"],)
        ).fetchone()
        if primary is None or not primary["body_complete"]:
            raise ValueError(f"missing or incomplete primary evidence: material {record['id']}")
        if canonicalize_url(primary["source_url"]) != canonicalize_url(record["source_url"]):
            raise ValueError(f"primary evidence URL mismatch: material {record['id']}")
        captures = [(primary, "primary")]
        verification = store.connection.execute(
            "SELECT * FROM material_verifications WHERE material_id=?", (record["id"],)
        ).fetchone()
        if verification:
            if verification["primary_evidence_id"] != primary["id"]:
                raise ValueError(f"verification primary evidence mismatch: material {record['id']}")
            metadata = store.connection.execute(
                """SELECT e.* FROM material_metadata_evidence link
                   JOIN evidence e ON e.id=link.evidence_id WHERE link.material_id=? ORDER BY e.id""",
                (record["id"],),
            ).fetchall()
            for capture in metadata:
                if capture["candidate_id"] != primary["candidate_id"] or not capture["metadata_verified"]:
                    raise ValueError(f"invalid exact metadata evidence: {capture['id']}")
            if not primary["metadata_verified"] and not metadata:
                raise ValueError(f"missing exact metadata evidence: material {record['id']}")
            field_sources = json.loads(verification["field_sources"])
            allowed_urls = {canonicalize_url(e["source_url"]) for e in metadata}
            allowed_urls.add(canonicalize_url(primary["source_url"]))
            if (not isinstance(field_sources, dict)
                    or not {"source", "time", "author", "title"}.issubset(field_sources)
                    or any(not isinstance(source, str)
                           or (source != "body" and canonicalize_url(source) not in allowed_urls)
                           for source in field_sources.values())):
                raise ValueError(f"field source evidence mismatch: material {record['id']}")
            captures.extend((row, "metadata_used_at_verification") for row in metadata if row["id"] != primary["id"])
        elif record["metadata_url"]:
            metadata = [row for row in store.connection.execute(
                "SELECT * FROM evidence WHERE candidate_id=? AND metadata_verified=1 ORDER BY id",
                (record["candidate_id"],),
            ) if canonicalize_url(row["source_url"]) == canonicalize_url(record["metadata_url"])]
            if not metadata:
                raise ValueError(f"missing declared metadata evidence: material {record['id']}")
            captures.extend((row, "metadata_candidate_capture") for row in metadata
                            if row["id"] != primary["id"])
        elif not primary["metadata_verified"]:
            raise ValueError(f"unverified metadata evidence: material {record['id']}")
        entries = []
        for capture, role in captures:
            if capture["access_status"] != "allow" or not 200 <= capture["status_code"] < 300:
                raise ValueError(f"restricted or unsuccessful evidence {capture['id']}")
            path = Path(capture["evidence_path"] or "")
            if not path.is_file():
                raise ValueError(f"missing evidence file {capture['id']}: {path}")
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != capture["content_sha256"]:
                raise ValueError(f"evidence SHA-256 mismatch: {capture['id']}")
            suffix = path.suffix.lower() if path.suffix.lower() in {".html", ".pdf", ".json", ".txt"} else ".bin"
            relative = f"evidence/{digest}{suffix}"
            (root / relative).write_bytes(raw)
            entries.append({"evidence_id": capture["id"], "role": role,
                            "source_url": capture["source_url"],
                            "http_status": capture["status_code"],
                            "fetched_at": capture["fetched_at"],
                            "sha256": digest, "file": relative})
        index.append({"material_id": record["id"], "source_url": record["source_url"],
                      "publication_date": record["published_on"], "title": record["title"],
                      "verification_provenance": "exact" if verification else "legacy_candidate_captures",
                      "field_sources": field_sources if verification else None,
                      "abstract_origin": verification["abstract_origin"] if verification else None,
                      "evidence": entries})
    return index


def _stage_reviews(store: ResearchStore, root: Path) -> int:
    """Copy local review/audit artifacts alongside the reproducible package."""
    source_root = store.path.parent / "reviews"
    if not source_root.is_dir():
        return 0
    destination_root = root / "reviews"
    count = 0
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        count += 1
    return count


def _stage_candidate_evidence(store: ResearchStore, root: Path) -> list[dict]:
    """Package non-verified source responses separately from formal provenance."""
    rows = store.connection.execute(
        """SELECT e.*,c.status AS candidate_status,c.period,c.source_category,c.query_label
           FROM evidence e JOIN candidates c ON c.id=e.candidate_id
           WHERE c.status IN ('pending','restricted') ORDER BY e.id"""
    ).fetchall()
    index = []
    directory = root / "candidate-evidence"
    directory.mkdir()
    for row in rows:
        entry = {
            "evidence_id": row["id"],
            "candidate_id": row["candidate_id"],
            "candidate_status": row["candidate_status"],
            "verification_status": "not_verified",
            "period": row["period"],
            "source_category": row["source_category"],
            "query_label": row["query_label"],
            "source_url": row["source_url"],
            "http_status": row["status_code"],
            "access_status": row["access_status"],
            "fetched_at": row["fetched_at"],
            "body_complete": bool(row["body_complete"]),
            "metadata_verified": bool(row["metadata_verified"]),
            "body_format": row["body_format"],
            "sha256": row["content_sha256"],
            "authorization_note": row["authorization_note"],
            "retrieval_method": row["retrieval_method"],
            "retrieval_id": row["retrieval_id"],
            "file": None,
            "copy_status": "missing_local_evidence",
        }
        path = Path(row["evidence_path"] or "")
        if path.is_file():
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest != row["content_sha256"]:
                raise ValueError(f"candidate evidence SHA-256 mismatch: {row['id']}")
            suffix = path.suffix.lower() if path.suffix.lower() in {".html", ".pdf", ".json", ".txt"} else ".bin"
            relative = f"candidate-evidence/{digest}{suffix}"
            destination = root / relative
            if not destination.exists():
                destination.write_bytes(raw)
            entry["file"] = relative
            entry["copy_status"] = "copied"
        index.append(entry)
    return index


def _verify_workbook(path: Path, materials: list) -> int:
    workbook = load_workbook(path, read_only=True, data_only=False)
    bodies = set()
    try:
        rows = workbook.active.iter_rows(values_only=True)
        if next(rows, None) != EXPORT_COLUMNS:
            raise ValueError("workbook must contain exactly nine required columns")
        for material in materials:
            row = next(rows, None)
            if row is None or len(row) != 9:
                raise ValueError("workbook row count or column count mismatch")
            body = row[6]
            if _excel_character_count(material.body) > EXCEL_CELL_LIMIT:
                body_path = (path.parent / str(body)).resolve()
                if not body_path.is_relative_to(path.parent.resolve()) or not body_path.is_file():
                    raise ValueError("missing or unsafe body file reference")
                body = body_path.read_bytes().decode("utf-8")
                bodies.add(body_path)
            actual = tuple("" if value is None else value for value in (*row[:6], body, *row[7:]))
            expected = (material.source, material.time, material.author, material.title,
                        material.abstract, material.keywords, material.body,
                        material.source_url, material.duplicate_count)
            if actual != expected:
                raise ValueError(f"workbook differs from stored material: {material.source_url}")
        if next(rows, None) is not None:
            raise ValueError("workbook has unexpected extra rows")
    finally:
        workbook.close()
    return len(bodies)


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
