import re
from dataclasses import replace
from datetime import date
from urllib.parse import urlsplit, urlunsplit

from research_crawler.items import SourceEvidence, VerifiedMaterial


class ValidationError(ValueError):
    pass


_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PERIOD_BOUNDS = {
    "1949-1972": (date(1949, 1, 1), date(1972, 12, 31)),
    "1972-1991": (date(1972, 1, 1), date(1991, 12, 31)),
    "1992-2016": (date(1992, 1, 1), date(2016, 12, 31)),
    "2017-2025": (date(2017, 1, 1), date(2025, 12, 31)),
}
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")
_HTML_TAG = re.compile(r"<(?P<closing>/)?(?P<name>[A-Za-z][A-Za-z0-9:-]*)(?P<attributes>\s[^<>]*?)?\s*/?>")
_HTML_ELEMENTS = frozenset((
    "html head title base link meta style body article section nav aside h1 h2 h3 h4 h5 h6 "
    "header footer address main p hr pre blockquote ol ul menu li dl dt dd figure figcaption "
    "div a em strong small s cite q dfn abbr ruby rt rp data time code var samp kbd sub sup "
    "i b u mark bdi bdo span br wbr ins del picture source img iframe embed object param "
    "video audio track map area table caption colgroup col tbody thead tfoot tr td th "
    "form label input button select datalist optgroup option textarea output progress meter "
    "fieldset legend details summary dialog script noscript template slot canvas svg path "
    "g circle rect polygon polyline line text math mrow mi mn mo mfrac msup msub "
    "font center big tt strike frame frameset marquee"
).split())


def _contains_html_markup(text: str) -> bool:
    """Keep literal angle-quoted citations; reject real tags without deleting text."""
    for match in _HTML_TAG.finditer(text):
        name = match['name'].casefold().rsplit(':', 1)[-1]
        attributes = match['attributes'] or ''
        if (name in _HTML_ELEMENTS or match['closing']
                or re.search(r"/\s*>$", match.group())
                or re.search(r"\b[A-Za-z_:][\w:.-]*\s*=", attributes)):
            return True
    return False


def validate_material(
    material: VerifiedMaterial,
    evidence: SourceEvidence,
    field_sources: dict[str, str],
    *,
    abstract_origin: str = "publisher",
    metadata_evidence_urls: set[str] | None = None,
    period: str | None = None,
) -> VerifiedMaterial:
    if not _DATE_PATTERN.fullmatch(material.time):
        raise ValidationError("publication date must use YYYY-MM-DD")
    try:
        publication_date = date.fromisoformat(material.time)
    except ValueError as exc:
        raise ValidationError("publication date must use YYYY-MM-DD") from exc
    if period is not None:
        bounds = _PERIOD_BOUNDS.get(period)
        if bounds is None:
            raise ValidationError(f"unknown research period: {period}")
        if not bounds[0] <= publication_date <= bounds[1]:
            raise ValidationError(f"publication date falls outside research period {period}")

    for field in ("source", "title"):
        if not getattr(material, field).strip():
            raise ValidationError(f"{field} is required")
    if not material.source_url.strip():
        raise ValidationError("source URL is required")
    for label, url in (("source URL", material.source_url), ("evidence URL", evidence.source_url)):
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError(f"{label} must be an HTTP(S) URL")
    if not material.body.strip():
        raise ValidationError("full body is required")
    if not evidence.content_sha256:
        raise ValidationError("body evidence hash is required")
    if not evidence.body_complete:
        raise ValidationError("body must be confirmed complete")
    if not evidence.metadata_verified and not metadata_evidence_urls:
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
    allowed_metadata_urls = {
        _canonical_url(url) for url in (metadata_evidence_urls or set())
    }
    allowed_metadata_urls.add(_canonical_url(material.source_url))
    for name in required_metadata:
        if _canonical_url(field_sources[name]) not in allowed_metadata_urls:
            raise ValidationError(f"{name} metadata must come from verified source evidence")

    if material.abstract and abstract_origin == "derived" and not material.abstract.startswith("据正文整理："):
        raise ValidationError("derived abstract must start with 据正文整理：")
    if material.abstract and abstract_origin == "publisher":
        if _canonical_url(field_sources.get("abstract", "")) not in allowed_metadata_urls:
            raise ValidationError("abstract metadata must come from verified source evidence")
    if material.abstract and abstract_origin == "none":
        raise ValidationError("abstract text cannot have origin none")
    if material.keywords:
        keyword_source = field_sources.get("keywords", "")
        if keyword_source != "body" and _canonical_url(keyword_source) not in allowed_metadata_urls:
            raise ValidationError("keywords metadata must come from verified source evidence or the complete body")
    if abstract_origin not in {"publisher", "derived", "none"}:
        raise ValidationError("abstract origin must be publisher, derived, or none")
    if _MARKDOWN_LINK.search(material.body):
        raise ValidationError("body contains markdown link syntax")
    if _contains_html_markup(material.body):
        raise ValidationError("body contains HTML markup")

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
