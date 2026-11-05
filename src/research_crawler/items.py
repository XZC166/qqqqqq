from dataclasses import dataclass
from pathlib import Path


EXPORT_COLUMNS = (
    "来源",
    "时间",
    "作者",
    "标题",
    "摘要",
    "关键词",
    "正文",
    "来源链接",
    "重复计数",
)


@dataclass(frozen=True)
class MaterialCandidate:
    source_url: str
    period: str
    source_category: str
    query_label: str
    platform_id: str | None = None


@dataclass(frozen=True)
class SourceEvidence:
    source_url: str
    fetched_at: str
    status_code: int
    content_sha256: str
    evidence_path: Path | None = None
    body_complete: bool = False
    metadata_verified: bool = False
    body_format: str = "source_text"
    original_page_verified: bool = False
    authorization_note: str = ""
    retrieval_method: str = "scrapy"
    retrieval_id: str = ""


@dataclass(frozen=True)
class VerifiedMaterial:
    source: str
    time: str
    author: str
    title: str
    abstract: str
    keywords: str
    body: str
    source_url: str
    duplicate_count: int = 0
