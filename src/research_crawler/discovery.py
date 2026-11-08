import csv
import json
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from research_crawler.items import MaterialCandidate


PERIODS = ("1949-1972", "1972-1991", "1992-2016", "2017-2025")

PMC_DATE_RANGES = {
    "1949-1972": ("1949/01/01", "1972/12/31"),
    # The two user-defined periods share 1972. Assign 1972 to the earlier
    # period so one API result cannot be emitted into both files.
    "1972-1991": ("1973/01/01", "1991/12/31"),
    "1992-2016": ("1992/01/01", "2016/12/31"),
    "2017-2025": ("2017/01/01", "2025/12/31"),
}

PMC_DEFAULT_TERM = (
    '("China"[Title/Abstract] OR "Chinese"[Title/Abstract]) AND '
    '("news media"[Title/Abstract] OR "media coverage"[Title/Abstract] OR '
    '"media framing"[Title/Abstract] OR "media discourse"[Title/Abstract] OR '
    '"public opinion"[Title/Abstract] OR propaganda[Title/Abstract] OR '
    '"public diplomacy"[Title/Abstract] OR "international broadcasting"[Title/Abstract] OR '
    '"strategic communication"[Title/Abstract] OR "political communication"[Title/Abstract] OR '
    '"information operations"[Title/Abstract] OR "China image"[Title/Abstract] OR '
    '"image of China"[Title/Abstract] OR "China threat"[Title/Abstract]) AND '
    'open access[filter]'
)

SOURCE_TERMS = {
    "media": (
        "New York Times", "Associated Press", "CNN", "Reuters",
        "纽约时报", "美联社", "路透社",
    ),
    "government": (
        "U.S. Department of State",
        "White House",
        "U.S. Congress",
        "Voice of America",
        "美国国务院",
        "白宫",
        "美国国会",
        "美国之音",
    ),
    "think_tank": (
        "Brookings Institution",
        "Council on Foreign Relations",
        "RAND Corporation",
        "CSIS",
        "布鲁金斯学会",
        "外交关系协会",
        "兰德公司",
        "战略与国际问题研究中心",
    ),
    "new_media": (
        "official U.S. government account",
        "official media account",
        "official think tank account",
        "美国政府官方账号",
        "美国媒体官方账号",
        "智库官方账号",
    ),
    "research_literature": (
        "academic journal",
        "scholarly research",
        "dissertation",
        "中文学术期刊",
        "中国学术论文",
        "学位论文",
    ),
}

EVENT_TERMS = {
    "1949-1972": (
        "founding of the People's Republic of China",
        "Korean War",
        "First Taiwan Strait Crisis",
        "Second Taiwan Strait Crisis",
        "Voice of America broadcasts to China",
        "Nixon visit to China",
        "中华人民共和国成立",
        "朝鲜战争",
        "第一次台湾海峡危机",
        "第二次台湾海峡危机",
        "美国之音对华广播",
        "尼克松访华",
    ),
    "1972-1991": (
        "Nixon visit to China",
        "U.S.-China normalization",
        "U.S. international broadcasting China",
        "1989 Tiananmen events",
        "尼克松访华",
        "中美关系正常化",
        "美国对华国际广播",
        "1989年天安门事件",
    ),
    "1992-2016": (
        "China joins the WTO",
        "South China Sea dispute",
        "China cybersecurity",
        "Asia-Pacific rebalance",
        "中国加入世界贸易组织",
        "南海争端",
        "中国网络安全",
        "亚太再平衡",
    ),
    "2017-2025": (
        "U.S.-China trade war",
        "Huawei sanctions",
        "COVID-19 pandemic",
        "Xinjiang and Hong Kong policy",
        "Taiwan Strait",
        "semiconductor and artificial intelligence competition",
        "中美贸易战",
        "华为制裁",
        "新冠疫情",
        "涉疆与涉港政策",
        "台海局势",
        "芯片与人工智能竞争",
    ),
}

TOPIC_TERMS = (
    "propaganda",
    "psychological warfare",
    "political warfare",
    "public diplomacy",
    "strategic communication",
    "international broadcasting",
    "influence operations",
    "information operations",
    "disinformation",
    "media framing",
    "China image",
    "China threat",
    "宣传",
    "心理战",
    "政治战",
    "公共外交",
    "战略传播",
    "国际广播",
    "影响行动",
    "信息行动",
    "虚假信息",
    "媒体框架",
    "中国形象",
    "中国威胁论",
    "舆论竞争",
)

TOPIC_GROUPS = (
    ("en", TOPIC_TERMS[:12]),
    ("zh", TOPIC_TERMS[12:]),
)

PMC_SCREEN_CHINA_TERMS = (
    "china",
    "chinese",
    "sino-american",
    "people's republic",
    "prc",
    "beijing",
    "taiwan",
    "hong kong",
)

PMC_SCREEN_TOPIC_TERMS = (
    "news media",
    "media coverage",
    "media framing",
    "media discourse",
    "news discourse",
    "news framing",
    "media reports",
    "foreign media",
    "mainstream media",
    "political discourse",
    "political narrative",
    "political communication",
    "communication strategy",
    "narrative",
    "discourse",
    "propaganda",
    "public diplomacy",
    "strategic communication",
    "information operation",
    "public opinion",
    "china image",
    "image of china",
    "china threat",
    "soft power",
    "national image",
    "framing",
    "public discussion",
    "public debate",
    "weaponization",
    "chinese virus",
    "china virus",
    "political warfare",
    "influence operation",
    "international broadcasting",
)

PMC_SCREEN_US_TERMS = (
    "united states",
    "u.s.",
    "us-china",
    "u.s.-china",
    "sino-american",
    "american",
    "western media",
    "u.s. government",
    "china policy",
    "foreign policy",
)


@dataclass(frozen=True)
class SearchQuery:
    period: str
    source_category: str
    event_term: str
    topic_term: str
    query_label: str
    query: str


def parse_pmc_esummary(payload: dict) -> list[dict]:
    """Convert one public NCBI ESummary JSON response to screen records."""
    result = payload.get("result") or {}
    records: list[dict] = []
    for uid in result.get("uids") or []:
        entry = result.get(str(uid)) or {}
        pmcid = ""
        pmid = ""
        for article_id in entry.get("articleids") or []:
            if article_id.get("idtype") == "pmcid":
                pmcid = str(article_id.get("value") or "").strip()
            elif article_id.get("idtype") == "pmid":
                pmid = str(article_id.get("value") or "").strip()
        if not pmcid:
            pmcid = f"PMC{uid}"
        records.append(
            {
                "pmcid": pmcid,
                "pmid": pmid,
                "title": str(entry.get("title") or "").strip(),
                "abstract": "",
                "abstract_available": False,
            }
        )
    return records


def parse_pubmed_abstracts(xml_text: str) -> dict[str, str]:
    """Parse only citation abstracts from a public PubMed EFetch response."""
    root = ET.fromstring(xml_text)
    abstracts: dict[str, str] = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = (article.findtext(".//PMID") or "").strip()
        segments = []
        for segment in article.findall(".//Abstract/AbstractText"):
            text = " ".join("".join(segment.itertext()).split())
            if text:
                segments.append(text)
        if pmid:
            abstracts[pmid] = " ".join(segments)
    return abstracts


def fetch_pubmed_abstracts(pmids: list[str], *, chunk_size: int = 200) -> dict[str, str]:
    """Fetch citation abstracts only; this endpoint does not retrieve article bodies."""
    if chunk_size < 1 or chunk_size > 200:
        raise ValueError("chunk_size must be between 1 and 200")
    abstracts: dict[str, str] = {}
    unique_pmids = list(dict.fromkeys(value.strip() for value in pmids if value.strip()))
    for index, start in enumerate(range(0, len(unique_pmids), chunk_size)):
        if index:
            time.sleep(0.34)
        chunk = unique_pmids[start : start + chunk_size]
        params = urlencode(
            {
                "db": "pubmed",
                "id": ",".join(chunk),
                "retmode": "xml",
                "tool": "research-crawler",
            }
        )
        request = Request(
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}",
            headers={"User-Agent": "research-crawler/0.1 (public citation abstract screening)"},
        )
        with urlopen(request, timeout=30) as response:
            abstracts.update(parse_pubmed_abstracts(response.read().decode("utf-8")))
    return abstracts


def fetch_pmc_esummaries(platform_ids: list[str], *, chunk_size: int = 200) -> list[dict]:
    """Fetch public PMC title metadata in bounded ESummary requests."""
    if chunk_size < 1 or chunk_size > 200:
        raise ValueError("chunk_size must be between 1 and 200")
    records: list[dict] = []
    for start in range(0, len(platform_ids), chunk_size):
        chunk = [str(value).strip().removeprefix("PMC") for value in platform_ids[start : start + chunk_size]]
        chunk = [value for value in chunk if value]
        if not chunk:
            continue
        params = urlencode(
            {
                "db": "pmc",
                "id": ",".join(chunk),
                "retmode": "json",
                "tool": "research-crawler",
            }
        )
        request = Request(
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{params}",
            headers={"User-Agent": "research-crawler/0.1 (public metadata screening)"},
        )
        with urlopen(request, timeout=30) as response:
            records.extend(parse_pmc_esummary(json.load(response)))
    abstracts = fetch_pubmed_abstracts(
        [record["pmid"] for record in records if record.get("pmid")]
    )
    for record in records:
        if record.get("pmid") in abstracts:
            record["abstract"] = abstracts[record["pmid"]]
            record["abstract_available"] = bool(record["abstract"])
    return records


def screen_pmc_records(records: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Screen public PMC metadata before any full-text request.

    This is a recall-preserving discovery filter: records with no usable
    metadata are retained for manual review. Clear China/topic/U.S.-context
    matches enter the full-text queue; other topic matches are held for review.
    It never creates a formal material or substitutes metadata for full text.
    """
    kept: list[dict] = []
    review: list[dict] = []
    excluded: list[dict] = []
    for record in records:
        pmcid = str(record.get("pmcid") or "").strip()
        text = " ".join(
            str(record.get(field) or "").strip()
            for field in ("title", "abstract")
        ).strip().casefold()
        has_china = any(term in text for term in PMC_SCREEN_CHINA_TERMS)
        has_topic = any(term in text for term in PMC_SCREEN_TOPIC_TERMS)
        has_us_context = any(term in text for term in PMC_SCREEN_US_TERMS)
        abstract_available = record.get("abstract_available", bool(record.get("abstract")))
        if not text or not abstract_available:
            review.append(
                {
                    "pmcid": pmcid,
                    "reason": "citation abstract unavailable; retain for manual review",
                }
            )
        elif has_china and has_topic and has_us_context:
            kept.append(record)
        elif has_china and has_topic:
            review.append(
                {
                    "pmcid": pmcid,
                    "reason": "China and communication topic present; U.S. connection unclear",
                }
            )
        else:
            excluded.append(
                {
                    "pmcid": pmcid,
                    "reason": "no thesis-topic term in title/abstract",
                }
            )
    return kept, review, excluded


def build_query_plan(period: str, source_category: str) -> list[SearchQuery]:
    if period not in PERIODS:
        raise ValueError(f"unknown period: {period}")
    if source_category not in SOURCE_TERMS:
        raise ValueError(f"unknown source category: {source_category}")

    queries = []
    for source in SOURCE_TERMS[source_category]:
        for event in EVENT_TERMS[period]:
            for language, topics in TOPIC_GROUPS:
                topic = " OR ".join(f'"{term}"' for term in topics)
                label = "-".join(
                    (period, source_category, _slug(source), _slug(event), language)
                )
                queries.append(
                    SearchQuery(
                        period=period,
                        source_category=source_category,
                        event_term=event,
                        topic_term=topic,
                        query_label=label,
                        query=f'"{source}" "{event}" ({topic}) {period}',
                    )
                )
    return queries


def import_candidate_csv(path: str | Path) -> list[MaterialCandidate]:
    candidates = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"url", "period", "source_category", "query_label"}
        if not required.issubset(reader.fieldnames or ()):
            raise ValueError(f"candidate CSV must include columns: {', '.join(sorted(required))}")
        for line_number, row in enumerate(reader, start=2):
            url = (row.get("url") or "").strip()
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"invalid HTTP(S) URL on line {line_number}")
            period = (row.get("period") or "").strip()
            if period not in PERIODS:
                raise ValueError(f"unknown period on line {line_number}: {period}")
            category = (row.get("source_category") or "").strip()
            if category not in SOURCE_TERMS:
                raise ValueError(f"unknown source category on line {line_number}: {category}")
            query_label = (row.get("query_label") or "").strip()
            if not query_label:
                raise ValueError(f"missing query label on line {line_number}")
            platform_id = (row.get("platform_id") or "").strip() or None
            metadata_url = (row.get("metadata_url") or "").strip() or None
            if metadata_url:
                metadata_parsed = urlsplit(metadata_url)
                if metadata_parsed.scheme not in {"http", "https"} or not metadata_parsed.netloc:
                    raise ValueError(f"invalid metadata URL on line {line_number}")
            candidates.append(
                MaterialCandidate(
                    source_url=url,
                    period=period,
                    source_category=category,
                    query_label=query_label,
                    platform_id=platform_id,
                    metadata_url=metadata_url,
                )
            )
    return candidates


def discover_pmc_candidates(
    period: str,
    output: str | Path,
    *,
    retmax: int = 500,
    retstart: int = 0,
    term: str = PMC_DEFAULT_TERM,
) -> int:
    """Write PMC IDs returned by the public E-utilities index as candidates.

    The endpoint is used only for discovery. Every emitted URL must still be
    fetched and verified by the Scrapy source adapter before formal export.
    """
    if period not in PMC_DATE_RANGES:
        raise ValueError(f"unknown period: {period}")
    if retmax < 1 or retmax > 5000:
        raise ValueError("retmax must be between 1 and 5000")
    if retstart < 0:
        raise ValueError("retstart must be non-negative")
    start, end = PMC_DATE_RANGES[period]
    query = f"({term}) AND (\"{start}\"[PDAT] : \"{end}\"[PDAT])"
    params = urlencode(
        {
            "db": "pmc",
            "term": query,
            "retmode": "json",
            "retmax": retmax,
            "retstart": retstart,
            "tool": "research-crawler",
        }
    )
    request = Request(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}",
        headers={"User-Agent": "research-crawler/0.1 (public discovery; no body capture)"},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    ids = list(dict.fromkeys(payload.get("esearchresult", {}).get("idlist", [])))

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("url", "period", "source_category", "query_label", "platform_id"),
        )
        writer.writeheader()
        for pmc_id in ids:
            platform_id = f"PMC{pmc_id}"
            writer.writerow(
                {
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{platform_id}/",
                    "period": period,
                    "source_category": "research_literature",
                    "query_label": f"pmc-bulk-{period}-start{retstart}",
                    "platform_id": platform_id,
                }
            )
    return len(ids)


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")
