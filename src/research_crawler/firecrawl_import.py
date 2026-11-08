import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from scrapy.http import HtmlResponse, Request, Response

from research_crawler.items import MaterialCandidate, SourceEvidence
from research_crawler.pipelines import VerificationPipeline
from research_crawler.spiders.government import (
    GovernmentArticleAdapter,
    IJocPDFDocumentAdapter,
    OjsJournalPDFDocumentAdapter,
    StateDepartmentReportPDFDocumentAdapter,
)
from research_crawler.store import ResearchStore, canonicalize_url
from research_crawler.validation import ValidationError


def import_firecrawl_capture(
    *,
    capture_path: str | Path,
    source_url: str,
    period: str,
    source_category: str,
    query_label: str,
    database_path: str | Path,
    evidence_dir: str | Path,
) -> str:
    try:
        capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("Firecrawl capture must be readable JSON") from exc

    payload = capture.get("structuredContent", capture)
    if not isinstance(payload, dict) or payload.get("success") is False or payload.get("error"):
        raise ValidationError("Firecrawl capture reports a failed request")
    raw_html = payload.get("rawHtml")
    if not isinstance(raw_html, str) or not raw_html.strip():
        raise ValidationError("Firecrawl capture must contain rawHtml; Markdown is not accepted")
    if "<" not in raw_html or ">" not in raw_html:
        raise ValidationError("rawHtml must contain HTML markup")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValidationError("Firecrawl capture metadata is required")
    captured_url = metadata.get("sourceURL")
    if not captured_url or canonicalize_url(captured_url) != canonicalize_url(source_url):
        raise ValidationError("Firecrawl metadata sourceURL must match the candidate URL")
    final_url = metadata.get("url")
    if not final_url or canonicalize_url(final_url) != canonicalize_url(source_url):
        raise ValidationError("Firecrawl metadata url must match the candidate URL")
    status_code = metadata.get("statusCode")
    if isinstance(status_code, bool) or not isinstance(status_code, int):
        raise ValidationError("Firecrawl metadata statusCode must be an integer")
    scrape_id = metadata.get("scrapeId")
    if not isinstance(scrape_id, str) or not scrape_id.strip():
        raise ValidationError("Firecrawl metadata scrapeId is required")

    raw_bytes = raw_html.encode("utf-8")
    candidate = MaterialCandidate(source_url, period, source_category, query_label)
    request = Request(url=source_url)
    response = HtmlResponse(
        url=source_url,
        request=request,
        body=raw_bytes,
        encoding="utf-8",
        status=status_code,
    )
    extracted = GovernmentArticleAdapter().extract(response, candidate)
    fetched_at = datetime.now(timezone.utc).isoformat()
    evidence = SourceEvidence(
        source_url=source_url,
        fetched_at=fetched_at,
        status_code=status_code,
        content_sha256="",
        body_complete=extracted["evidence"].body_complete,
        metadata_verified=extracted["evidence"].metadata_verified,
        body_format="source_text",
        retrieval_method="firecrawl",
        retrieval_id=scrape_id.strip(),
    )
    item = {
        **extracted,
        "candidate": candidate,
        "evidence": evidence,
        "raw_response": raw_bytes,
    }

    pipeline = VerificationPipeline(database_path, evidence_dir)
    pipeline.open_spider()
    try:
        pipeline.process_item(item)
    finally:
        pipeline.close_spider()

    store = ResearchStore(database_path)
    try:
        row = store.connection.execute(
            """SELECT c.status FROM candidates c JOIN batches b ON b.id = c.batch_id
               WHERE c.source_url = ? AND c.period = ? AND c.source_category = ?
                 AND c.query_label = ?""",
            (source_url, period, source_category, query_label),
        ).fetchone()
        if row is None:
            raise RuntimeError("Firecrawl capture did not create candidate state")
        return str(row["status"])
    finally:
        store.close()


def import_firecrawl_pdf_capture(
    *,
    capture_path: str | Path,
    source_url: str,
    metadata_url: str,
    period: str,
    source_category: str,
    query_label: str,
    database_path: str | Path,
    evidence_dir: str | Path,
) -> str:
    try:
        capture = json.loads(Path(capture_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError("Firecrawl capture must be readable JSON") from exc

    payload = capture.get("structuredContent", capture)
    if not isinstance(payload, dict) or payload.get("success") is False or payload.get("error"):
        raise ValidationError("Firecrawl capture reports a failed request")
    raw_html = payload.get("rawHtml")
    metadata = payload.get("metadata")
    if not isinstance(raw_html, str) or not raw_html.strip() or "<" not in raw_html:
        raise ValidationError("Firecrawl capture must contain rawHtml, not Markdown")
    if not isinstance(metadata, dict):
        raise ValidationError("Firecrawl capture metadata is required")
    if canonicalize_url(metadata.get("sourceURL", "")) != canonicalize_url(metadata_url):
        raise ValidationError("Firecrawl metadata sourceURL must match the metadata page")
    if canonicalize_url(metadata.get("url", "")) != canonicalize_url(metadata_url):
        raise ValidationError("Firecrawl metadata url must match the metadata page")
    if metadata.get("statusCode") != 200:
        raise ValidationError("Firecrawl metadata page must return HTTP 200")
    scrape_id = metadata.get("scrapeId")
    if not isinstance(scrape_id, str) or not scrape_id.strip():
        raise ValidationError("Firecrawl metadata scrapeId is required")

    store = ResearchStore(database_path)
    try:
        row = store.connection.execute(
            """SELECT c.id, c.source_url, c.period, c.source_category, c.query_label,
                      c.platform_id, c.metadata_url, e.status_code, e.evidence_path,
                      e.body_format, e.access_status, e.retrieval_id
               FROM candidates c
               JOIN batches b ON b.id = c.batch_id
               JOIN evidence e ON e.candidate_id = c.id
               WHERE c.source_url = ? AND c.period = ? AND c.source_category = ?
                 AND c.query_label = ? AND e.source_url = c.source_url
                 AND e.status_code >= 200 AND e.status_code < 300
                 AND e.body_format = 'pdf_text' AND e.access_status = 'allow'
                 AND e.evidence_path IS NOT NULL
               ORDER BY e.id DESC LIMIT 1""",
            (source_url, period, source_category, query_label),
        ).fetchone()
        if row is None:
            raise ValidationError("matching successful Scrapy PDF evidence is required")
        if row["metadata_url"] and canonicalize_url(row["metadata_url"]) != canonicalize_url(metadata_url):
            raise ValidationError("candidate metadata_url does not match the Firecrawl page")
        pdf_path = Path(row["evidence_path"])
        try:
            pdf_bytes = pdf_path.read_bytes()
        except OSError as exc:
            raise ValidationError("Scrapy PDF evidence file is missing") from exc
        if not pdf_bytes.startswith(b"%PDF-"):
            detail = "HTTP 200 response was not a PDF; source returned Technical Difficulties HTML"
            store.update_candidate_status(row["id"], "pending", detail)
            raise ValidationError(detail)
        candidate = MaterialCandidate(
            source_url=source_url,
            period=period,
            source_category=source_category,
            query_label=query_label,
            platform_id=row["platform_id"],
            metadata_url=metadata_url,
        )
        pdf_response = Response(
            url=source_url,
            request=Request(source_url),
            body=pdf_bytes,
            status=row["status_code"],
            headers={b"Content-Type": b"application/pdf"},
        )
        metadata_response = HtmlResponse(
            url=metadata_url,
            request=Request(metadata_url),
            body=raw_html.encode("utf-8"),
            encoding="utf-8",
            status=metadata["statusCode"],
        )
        metadata_host = (urlsplit(metadata_url).hostname or "").lower()
        if metadata_host == "ijoc.org":
            extracted = IJocPDFDocumentAdapter().extract(
                pdf_response, candidate, metadata_response
            )
        elif "open journal systems" in " ".join(
            metadata_response.css("meta[name='generator']::attr(content)").getall()
        ).casefold():
            extracted = OjsJournalPDFDocumentAdapter().extract(
                pdf_response, candidate, metadata_response
            )
        else:
            extracted = StateDepartmentReportPDFDocumentAdapter().extract(
                pdf_response, candidate, metadata_response
            )
        extracted["evidence"] = replace(
            extracted["evidence"],
            retrieval_method="scrapy",
            retrieval_id=row["retrieval_id"] or "",
        )
        for supporting in extracted.get("supporting_evidence", []):
            supporting["evidence"] = replace(
                supporting["evidence"],
                retrieval_method="firecrawl",
                retrieval_id=scrape_id.strip(),
            )
        item = {
            **extracted,
            "candidate": candidate,
            "raw_response": pdf_bytes,
        }
    finally:
        store.close()

    pipeline = VerificationPipeline(database_path, evidence_dir)
    pipeline.open_spider()
    try:
        pipeline.process_item(item)
    finally:
        pipeline.close_spider()

    store = ResearchStore(database_path)
    try:
        result = store.connection.execute(
            """SELECT c.status FROM candidates c JOIN batches b ON b.id = c.batch_id
               WHERE c.source_url = ? AND c.period = ? AND c.source_category = ?
                 AND c.query_label = ?""",
            (source_url, period, source_category, query_label),
        ).fetchone()
        if result is None:
            raise RuntimeError("paired PDF capture did not update candidate state")
        return str(result["status"])
    finally:
        store.close()
