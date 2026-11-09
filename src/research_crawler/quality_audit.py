"""Record-by-record offline checks and an explicitly reviewed export boundary.

The acquisition materials table remains an evidence-backed working pool. A
source adapter pass alone never grants final thematic approval. Reviews bind
all nine exported values except the separately checked discovery counter.
"""

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.items import SourceEvidence, VerifiedMaterial
from research_crawler.policy import AccessDecision
from research_crawler.revalidation import _extract_existing
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import canonicalize_url
from research_crawler.validation import validate_material


FIELDS = ("source", "published_on", "author", "title", "abstract", "keywords", "body", "source_url")


def material_fingerprint(row) -> str:
    return hashlib.sha256(json.dumps([row[k] for k in FIELDS],ensure_ascii=False,separators=(",", ":")).encode()).hexdigest()


def ensure_review_schema(store):
    store.connection.execute("""CREATE TABLE IF NOT EXISTS quality_reviews(
        material_id INTEGER PRIMARY KEY, identity_key TEXT NOT NULL,
        input_fingerprint TEXT NOT NULL, body_sha256 TEXT NOT NULL,
        source_sha256 TEXT NOT NULL, status TEXT NOT NULL,
        source_pass INTEGER NOT NULL, topic_pass INTEGER NOT NULL,
        reason TEXT NOT NULL, checks_json TEXT NOT NULL,
        reviewed_at TEXT NOT NULL, review_version TEXT NOT NULL
    )""")
    store.connection.commit()


def _source_row(store, material_id):
    return store.connection.execute("""SELECT m.*, e.candidate_id, e.evidence_path,
        e.status_code, e.content_sha256, e.body_format,e.access_status,
        e.metadata_verified, e.body_complete, e.original_page_verified,
        e.fetched_at,e.source_url AS evidence_source_url,
        c.source_url AS candidate_source_url,c.identity_key AS candidate_identity_key,
        c.period,c.source_category,c.query_label,c.platform_id,c.metadata_url
        FROM materials m LEFT JOIN evidence e ON e.id=m.evidence_id
        LEFT JOIN candidates c ON c.id=e.candidate_id WHERE m.id=?""",(material_id,)).fetchone()


def audit_material(store, material_id: int, topic_decision: dict | None = None) -> dict:
    ensure_review_schema(store)
    row = _source_row(store,material_id)
    if row is None:
        raise ValueError("Unknown material")
    fingerprint = material_fingerprint(row)
    checks = {"topic_decision":topic_decision}
    source_pass = False
    topic_pass = False
    status = "pending"
    reason = "Source checks have not completed."
    try:
        if not row["evidence_path"] or not row["candidate_id"]:
            raise ValueError("Missing source evidence or owning candidate")
        if (canonicalize_url(row["source_url"]) != canonicalize_url(row["evidence_source_url"])
                or canonicalize_url(row["source_url"]) != canonicalize_url(row["candidate_source_url"])
                or row["identity_key"] != row["candidate_identity_key"]):
            raise ValueError("Material, original evidence and candidate URL/identity ownership mismatch")
        raw = Path(row["evidence_path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["content_sha256"]:
            raise ValueError("Raw source evidence SHA-256 hash mismatch")
        checks["primary_raw_sha256"] = row["content_sha256"]
        checks["primary_evidence_path"] = row["evidence_path"]
        if row["access_status"] != "allow" or not 200 <= row["status_code"] < 300:
            raise ValueError("Source evidence is not an allowed successful response")
        duplicate_rows = store.connection.execute("SELECT count(*) FROM materials WHERE identity_key=?",(row["identity_key"],)).fetchone()[0]
        if duplicate_rows != 1:
            raise ValueError("Material identity is not unique")
        discoveries = store.connection.execute("SELECT count(*) FROM duplicate_discoveries WHERE identity_key=?",(row["identity_key"],)).fetchone()[0]
        checks["duplicate_count_recorded"] = row["duplicate_count"]
        checks["duplicate_discoveries"] = discoveries
        if discoveries != row["duplicate_count"]:
            raise ValueError("Duplicate discovery count mismatch")
        supporting_rows = store.connection.execute("""SELECT e.* FROM evidence e
            JOIN material_metadata_evidence x ON x.evidence_id=e.id
            WHERE x.material_id=?""",(material_id,)).fetchall()
        checked_support = []
        for support in supporting_rows:
            if (support["candidate_id"] != row["candidate_id"] or support["access_status"] != "allow"
                    or not 200<=support["status_code"]<300 or not support["metadata_verified"]):
                raise ValueError("Supporting metadata evidence ownership or access invalid")
            supporting_raw = Path(support["evidence_path"]).read_bytes()
            if hashlib.sha256(supporting_raw).hexdigest() != support["content_sha256"]:
                raise ValueError("Supporting metadata evidence SHA-256 hash mismatch")
            checked_support.append({"id":support["id"],"url":support["source_url"],"sha256":support["content_sha256"],"path":support["evidence_path"]})
        checks["supporting_evidence"] = checked_support
        # _extract_existing selects the most recent declared metadata capture;
        # verify that capture too, even if an older snapshot linked another ID.
        if row["metadata_url"]:
            latest=store.connection.execute("""SELECT * FROM evidence WHERE candidate_id=?
                AND source_url=? AND metadata_verified=1 ORDER BY id DESC LIMIT 1""",
                (row["candidate_id"],row["metadata_url"])).fetchone()
            if latest is None or latest["access_status"] != "allow" or not 200<=latest["status_code"]<300:
                raise ValueError("Declared metadata capture missing or restricted")
            if hashlib.sha256(Path(latest["evidence_path"]).read_bytes()).hexdigest()!=latest["content_sha256"]:
                raise ValueError("Latest declared metadata evidence hash mismatch")
        extracted, metadata_ids = _extract_existing(store,row,GovernmentArticleAdapter())
        parsed = extracted.get("material")
        parsed_evidence = extracted.get("evidence")
        if extracted.get("decision") is not AccessDecision.ALLOW or parsed is None:
            raise ValueError("Current source adapter cannot verify a complete same-article body and metadata")
        if not parsed_evidence.body_complete:
            raise ValueError("Current source adapter cannot confirm completeness")
        mismatches = [name for name,field in (("source","source"),("time","published_on"),("author","author"),("title","title"),("body","body"),("source_url","source_url")) if getattr(parsed,name)!=row[field]]
        if mismatches:
            raise ValueError("Source re-extraction differs in: "+", ".join(mismatches))
        snapshot=store.connection.execute("SELECT * FROM material_verifications WHERE material_id=?",(material_id,)).fetchone()
        if snapshot is None or snapshot["primary_evidence_id"]!=row["evidence_id"]:
            raise ValueError("Missing or mismatched field-provenance snapshot")
        if not row["abstract"].strip() or not row["keywords"].strip():
            raise ValueError("Abstract or keywords missing")
        if snapshot["abstract_origin"]=="publisher" and row["abstract"]!=parsed.abstract:
            raise ValueError("Publisher abstract differs from source re-extraction")
        checks["abstract_origin"] = snapshot["abstract_origin"]
        checks["field_sources"] = json.loads(snapshot["field_sources"])
        checks["reextracted_body_sha256"] = hashlib.sha256(parsed.body.encode()).hexdigest()
        stored = replace(parsed,abstract=row["abstract"],keywords=row["keywords"],duplicate_count=row["duplicate_count"])
        metadata_urls = {s["url"] for s in checked_support}
        if metadata_ids - {s["id"] for s in checked_support}:
            raise ValueError("Re-extraction uses metadata evidence not in checked provenance snapshot")
        validate_material(stored,replace(parsed_evidence,evidence_path=Path(row["evidence_path"])),
            checks["field_sources"],abstract_origin=snapshot["abstract_origin"],
            metadata_evidence_urls=metadata_urls,period=row["period"])
        source_pass = True
        if _approved_topic_evidence(material_id,fingerprint,topic_decision):
            topic_pass = True
            status = "pass"
            reason = topic_decision["reason"]
        else:
            reason = ("Topic/field review pending: "+topic_decision['reason']
                if topic_decision and topic_decision.get('approved') is False and topic_decision.get('reason')
                else "Source checks pass; complete-document topic/abstract/keyword review still pending.")
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
    result={"material_id":material_id,"identity_key":row["identity_key"],"input_fingerprint":fingerprint,
        "body_sha256":hashlib.sha256(row["body"].encode()).hexdigest(),"source_sha256":row["content_sha256"] or "",
        "status":status,"source_pass":source_pass,"topic_pass":topic_pass,"reason":reason,"checks":checks,
        "reviewed_at":datetime.now(timezone.utc).isoformat(),"review_version":"2026-11-09-v1"}
    with store.connection:
        store.connection.execute("""INSERT INTO quality_reviews VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(material_id) DO UPDATE SET identity_key=excluded.identity_key,
            input_fingerprint=excluded.input_fingerprint,body_sha256=excluded.body_sha256,
            source_sha256=excluded.source_sha256,status=excluded.status,source_pass=excluded.source_pass,
            topic_pass=excluded.topic_pass,reason=excluded.reason,checks_json=excluded.checks_json,
            reviewed_at=excluded.reviewed_at,review_version=excluded.review_version""",
            (material_id,row["identity_key"],fingerprint,result["body_sha256"],result["source_sha256"],status,
             int(source_pass),int(topic_pass),reason,json.dumps(checks,ensure_ascii=False),result["reviewed_at"],result["review_version"]))
    return result


def _approved_topic_evidence(material_id, fingerprint, decision):
    if (not decision or decision.get("approved") is not True
            or decision.get("material_id") != material_id
            or decision.get("fingerprint") != fingerprint or not decision.get("reason")):
        return False
    try:
        raw = Path(decision["evidence_path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != decision["evidence_sha256"]:
            return False
        records = json.loads(raw)["records"]
        return any(r.get("material_id")==material_id and r.get("approved") is True
            and r.get("fingerprint")==fingerprint and r.get("reason")==decision["reason"] for r in records)
    except (OSError, ValueError, KeyError, TypeError):
        return False


class ReviewedExportStore:
    """Export view. Never edits or clears the acquisition materials pool."""
    def __init__(self,store):
        self.store=store
        ensure_review_schema(store)

    def get_verified_materials(self) -> list[VerifiedMaterial]:
        rows=self.store.connection.execute("""SELECT m.*,q.input_fingerprint,q.checks_json FROM materials m
            JOIN quality_reviews q ON q.material_id=m.id WHERE q.status='pass'
            AND q.source_pass=1 AND q.topic_pass=1 ORDER BY m.id""").fetchall()
        verified=[]
        for row in rows:
            decision=json.loads(row["checks_json"]).get("topic_decision")
            result=audit_material(self.store,row["id"],decision)
            if result["status"]=="pass":
                current=self.store.connection.execute("SELECT * FROM materials WHERE id=?",(row["id"],)).fetchone()
                if (current is None or material_fingerprint(current)!=result["input_fingerprint"]
                        or current["duplicate_count"]!=result["checks"]["duplicate_count_recorded"]):
                    continue
                verified.append(VerifiedMaterial(current["source"],current["published_on"],current["author"],current["title"],current["abstract"],current["keywords"],current["body"],current["source_url"],current["duplicate_count"]))
        return verified


def build_reviewed_delivery(store, destination):
    """Private research package: formal workbook plus unmodified working progress.

    All filtering happens in a temporary SQLite copy. Neither acquisition rows
    nor review history in the live database are deleted by packaging.
    """
    import os
    import shutil
    import sqlite3
    from tempfile import TemporaryDirectory
    from zipfile import ZipFile, ZIP_DEFLATED
    from research_crawler.delivery import build_delivery
    from research_crawler.store import ResearchStore

    destination=Path(destination).resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    if store.connection.in_transaction:
        raise ValueError("commit pending database changes before delivery")
    with TemporaryDirectory(prefix="reviewed-delivery-",dir=destination.parent) as temporary:
        root=Path(temporary)
        snapshot_path=root / "filtered.sqlite3"
        connection=sqlite3.connect(snapshot_path)
        store.connection.backup(connection);connection.close()
        snapshot=ResearchStore(snapshot_path)
        try:
            if (store.path.parent / "reviews").is_dir():
                shutil.copytree(store.path.parent / "reviews",root / "reviews")
            ReviewedExportStore(snapshot).get_verified_materials()
            decision_directory=root / "reviews/topic-decisions"
            decision_directory.mkdir(parents=True,exist_ok=True)
            decision_index=[]
            for review in snapshot.connection.execute("SELECT material_id,checks_json FROM quality_reviews WHERE status='pass'"):
                decision=json.loads(review['checks_json'])['topic_decision']
                raw=Path(decision['evidence_path']).read_bytes()
                digest=hashlib.sha256(raw).hexdigest()
                if digest!=decision['evidence_sha256']:
                    raise ValueError("Topic decision evidence changed while packaging")
                path=decision_directory / (digest+'.json')
                path.write_bytes(raw)
                decision_index.append({'material_id':review['material_id'],'original_path':decision['evidence_path'],
                    'sha256':digest,'file':'reviews/topic-decisions/'+path.name})
            (root / "reviews/topic-decision-index.json").write_text(json.dumps(decision_index,ensure_ascii=False,indent=2),encoding='utf-8')
            progress=root / "progress.sqlite3"
            connection=sqlite3.connect(progress)
            snapshot.connection.backup(connection);connection.close()
            with snapshot.connection:
                snapshot.connection.execute("CREATE TEMP TABLE delivery_keep AS SELECT material_id FROM quality_reviews WHERE status='pass' AND source_pass=1 AND topic_pass=1")
                snapshot.connection.execute("""UPDATE candidates SET status='pending',
                    status_detail='Quality review pending; acquisition verification is not final approval.'
                    WHERE (status='verified' OR identity_key IN (SELECT identity_key FROM materials))
                    AND status NOT IN ('excluded','restricted') AND identity_key NOT IN
                    (SELECT identity_key FROM materials WHERE id IN (SELECT material_id FROM delivery_keep))""")
                for table in ("material_metadata_evidence","material_verifications"):
                    snapshot.connection.execute(f"DELETE FROM {table} WHERE material_id NOT IN (SELECT material_id FROM delivery_keep)")
                snapshot.connection.execute("DELETE FROM materials WHERE id NOT IN (SELECT material_id FROM delivery_keep)")
            staged=root / "private-delivery.zip"
            build_delivery(snapshot,staged)
            with ZipFile(staged,"a",compression=ZIP_DEFLATED) as archive:
                archive.write(progress,"progress.sqlite3")
                archive.writestr("PRIVATE-RESEARCH-USE.txt",
                    "This is a private research copy, not a license for public redistribution.\n"
                    "materials.xlsx contains only current source-and-topic review passes.\n"
                    "progress.sqlite3 preserves the entire acquisition working pool, including pending records.\n"
                    "Candidate evidence and review reports do not constitute verified full text.\n"
                    "Check each source license/authorization before sharing any full text or evidence.\n")
            with ZipFile(staged) as archive:
                if archive.testzip() is not None:
                    raise ValueError("Reviewed ZIP integrity verification failed")
            os.replace(staged,destination)
        finally:
            snapshot.close()
    return destination
