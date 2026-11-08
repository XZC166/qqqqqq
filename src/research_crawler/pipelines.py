import hashlib
import html
import re
from dataclasses import replace
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from research_crawler.policy import AccessDecision
from research_crawler.store import ResearchStore
from research_crawler.validation import ValidationError, validate_material


class VerificationPipeline:
    def __init__(
        self,
        database_path: str | Path = "data/research.sqlite3",
        evidence_dir: str | Path = "data/evidence",
    ):
        self.database_path = Path(database_path)
        self.evidence_dir = Path(evidence_dir)
        self.store: ResearchStore | None = None
        self.batch_id: int | None = None
        self.batch_ids: dict[tuple[str, str, str], int] = {}
        self.crawler = None
        self.spider = None

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            crawler.settings.get("DATABASE_PATH", "data/research.sqlite3"),
            crawler.settings.get("EVIDENCE_DIR", "data/evidence"),
        )
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self, spider=None) -> None:
        self.store = ResearchStore(self.database_path)
        if spider is not None:
            self.spider = spider
        elif self.crawler is not None:
            self.spider = self.crawler.spider

    def process_item(self, item: dict, spider=None):
        if self.store is None:
            raise RuntimeError("verification pipeline is not open")

        candidate = item["candidate"]
        batch_key = (candidate.period, candidate.source_category, candidate.query_label)
        if batch_key not in self.batch_ids:
            self.batch_ids[batch_key] = self.store.create_batch(*batch_key)
        self.batch_id = self.batch_ids[batch_key]
        candidate_id = self.store.add_candidate(self.batch_id, candidate)
        if "crawl_error" in item:
            current_status = self.store.connection.execute(
                "SELECT status FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()["status"]
            if current_status == "candidate":
                status = (
                    "restricted"
                    if item["crawl_error"].strip().casefold() == "forbidden by robots.txt"
                    else "candidate"
                )
                self.store.update_candidate_status(
                    candidate_id, status, item["crawl_error"]
                )
            return item

        metadata_evidence_ids = set()
        metadata_evidence_urls = set()
        for supporting in item.get("supporting_evidence", []):
            supporting_record = self._save_evidence_file(
                supporting["evidence"], supporting.get("raw_response", b"")
            )
            supporting_id = self.store.add_evidence(
                candidate_id,
                supporting_record,
                access_status=supporting["decision"].value,
            )
            if (
                supporting["decision"] is AccessDecision.ALLOW
                and 200 <= supporting_record.status_code < 300
                and supporting_record.metadata_verified
            ):
                metadata_evidence_ids.add(supporting_id)
                metadata_evidence_urls.add(supporting_record.source_url)

        raw_response = item.get("raw_response", b"")
        evidence = self._save_evidence_file(item["evidence"], raw_response)
        decision = item["decision"]
        evidence_id = self.store.add_evidence(
            candidate_id,
            evidence,
            access_status=decision.value,
        )

        if decision is AccessDecision.RESTRICTED:
            status_code = evidence.status_code
            detail = (
                f"HTTP {status_code}: access restricted"
                if status_code in {401, 402, 403}
                else "Source response indicates restricted or paywalled access"
            )
            self.store.update_candidate_status(candidate_id, "restricted", detail)
            return item
        if decision is not AccessDecision.ALLOW or item.get("material") is None:
            self.store.update_candidate_status(candidate_id, "pending", "full text or metadata not verified")
            return item

        try:
            if _pdf_is_scan_like(raw_response) and (
                evidence.body_format != "pdf_reviewed_transcript"
                or not evidence.original_page_verified
            ):
                raise ValidationError(
                    "scanned PDF requires a word-for-word reviewed transcript"
                )
            material = validate_material(
                item["material"],
                evidence,
                item.get("field_sources", {}),
                abstract_origin=item.get("abstract_origin", "publisher"),
                metadata_evidence_urls=metadata_evidence_urls,
                period=candidate.period,
            )
            if not _body_matches_source(material.body, raw_response, evidence.body_format):
                raise ValidationError("body does not correspond to source evidence")
            self.store.add_verified_material(
                candidate_id,
                evidence_id,
                material,
                abstract_origin=item.get("abstract_origin", "publisher"),
                field_sources=item.get("field_sources", {}),
                metadata_evidence_ids=metadata_evidence_ids,
            )
        except ValidationError as exc:
            self.store.update_candidate_status(candidate_id, "pending", str(exc))
            return item

        self.store.update_candidate_status(candidate_id, "verified")
        return item

    def _save_evidence_file(self, evidence, raw_response: bytes):
        digest = hashlib.sha256(raw_response).hexdigest()
        evidence_path = None
        if raw_response:
            suffix = {
                "pdf_text": ".pdf",
                "pdf_ocr_text": ".pdf",
                "pdf_reviewed_transcript": ".pdf",
                "json": ".json",
            }.get(evidence.body_format, ".html")
            evidence_path = self.evidence_dir / f"{digest}{suffix}"
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            with evidence_path.open("wb") as handle:
                handle.write(raw_response)
        return replace(
            evidence,
            content_sha256=digest,
            evidence_path=evidence_path,
        )

    def close_spider(self, spider=None) -> None:
        if self.store is not None:
            self.store.close()
            self.store = None


def _pdf_is_scan_like(raw_response: bytes) -> bool:
    if not raw_response.startswith(b"%PDF-"):
        return False
    try:
        pages = list(PdfReader(BytesIO(raw_response), strict=True).pages)
    except Exception:
        return True
    if not pages:
        return True
    image_pages = 0
    for page in pages:
        try:
            image_pages += bool(page.images)
        except Exception:
            return True
    return image_pages * 5 >= len(pages) * 4


def _body_matches_source(body: str, raw_response: bytes, body_format: str) -> bool:
    """Reject an extracted HTML/JSON body that cannot be found in its raw response."""
    if body_format not in {"source_text", "authorized_text", "json"} or not raw_response:
        return True
    raw_text = raw_response.decode("utf-8", errors="replace")
    raw_text = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw_text, flags=re.IGNORECASE | re.DOTALL)
    raw_text = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw_text, flags=re.IGNORECASE | re.DOTALL)
    raw_text = re.sub(r"<[^>]+>", " ", raw_text)
    tokenize = lambda value: re.findall(r"\w+", html.unescape(value).casefold(), flags=re.UNICODE)
    body_tokens = tokenize(body)
    raw_tokens = tokenize(raw_text)
    if not body_tokens:
        return False
    window = 8
    if len(body_tokens) <= window:
        return _contains_token_sequence(raw_tokens, body_tokens)
    return (
        _contains_token_sequence(raw_tokens, body_tokens[:window])
        and _contains_token_sequence(raw_tokens, body_tokens[-window:])
    )


def _contains_token_sequence(haystack: list[str], needle: list[str]) -> bool:
    size = len(needle)
    return any(haystack[index:index + size] == needle for index in range(len(haystack) - size + 1))
