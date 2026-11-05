import json
from datetime import datetime, timezone
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate, SourceEvidence
from research_crawler.pipelines import VerificationPipeline
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import canonicalize_url
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
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise ValidationError("Firecrawl capture success must be true")
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

    from research_crawler.store import ResearchStore

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
