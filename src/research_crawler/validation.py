import re
from dataclasses import replace
from datetime import date
from urllib.parse import urlsplit, urlunsplit

from research_crawler.items import SourceEvidence, VerifiedMaterial


class ValidationError(ValueError):
    pass


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")


def validate_material(
    material: VerifiedMaterial,
    evidence: SourceEvidence,
    field_sources: dict[str, str],
    *,
    abstract_origin: str = "publisher",
) -> VerifiedMaterial:
    if not _DATE_PATTERN.fullmatch(material.time):
        raise ValidationError("publication date must use YYYY-MM-DD")
    try:
        date.fromisoformat(material.time)
    except ValueError as exc:
        raise ValidationError("publication date must use YYYY-MM-DD") from exc

    for field in ("source", "title"):
        if not getattr(material, field).strip():
            raise ValidationError(f"{field} is required")
    if not material.source_url.strip():
        raise ValidationError("source URL is required")
    if not material.body.strip():
        raise ValidationError("full body is required")
    if not evidence.content_sha256:
        raise ValidationError("body evidence hash is required")
    if not evidence.body_complete:
        raise ValidationError("body must be confirmed complete")
    if not evidence.metadata_verified:
        raise ValidationError("metadata must be verified")
    if evidence.body_format == "markdown" and not evidence.original_page_verified:
        raise ValidationError("markdown extraction requires original-page verification")
    if evidence.status_code < 200 or evidence.status_code >= 300:
        raise ValidationError("source evidence must be a successful response")
    if _canonical_url(evidence.source_url) != _canonical_url(material.source_url):
        raise ValidationError("body evidence must point to the same source")

    required_metadata = {"source", "time", "author", "title"}
    if not required_metadata.issubset(field_sources):
        raise ValidationError("source, time, author, and title metadata must be verified")
    for name in required_metadata:
        if _canonical_url(field_sources[name]) != _canonical_url(material.source_url):
            raise ValidationError(f"{name} metadata must come from the same source")

    if material.abstract and abstract_origin == "derived" and not material.abstract.startswith("据正文整理："):
        raise ValidationError("derived abstract must start with 据正文整理：")
    if material.abstract and abstract_origin == "publisher":
        if _canonical_url(field_sources.get("abstract", "")) != _canonical_url(material.source_url):
            raise ValidationError("abstract metadata must come from the same source")
    if material.abstract and abstract_origin == "none":
        raise ValidationError("abstract text cannot have origin none")
    if material.keywords and _canonical_url(field_sources.get("keywords", "")) != _canonical_url(material.source_url):
        raise ValidationError("keywords metadata must come from the same source")
    if abstract_origin not in {"publisher", "derived", "none"}:
        raise ValidationError("abstract origin must be publisher, derived, or none")
    if _MARKDOWN_LINK.search(material.body):
        raise ValidationError("body contains markdown link syntax")

    author = material.author.strip() or "未注明"
    if author != material.author:
        material = replace(material, author=author)
    return material


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    return urlunsplit((scheme, hostname, parsed.path or "/", parsed.query, ""))
