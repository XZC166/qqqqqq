import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from research_crawler.items import MaterialCandidate


PERIODS = ("1949-1972", "1972-1991", "1992-2016", "2017-2025")

SOURCE_TERMS = {
    "media": ("New York Times", "Associated Press", "CNN", "Reuters"),
    "government": (
        "U.S. Department of State",
        "White House",
        "U.S. Congress",
        "Voice of America",
    ),
    "think_tank": (
        "Brookings Institution",
        "Council on Foreign Relations",
        "RAND Corporation",
        "CSIS",
    ),
    "new_media": (
        "official U.S. government account",
        "official media account",
        "official think tank account",
    ),
    "research_literature": (
        "academic journal",
        "scholarly research",
        "dissertation",
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
    ),
    "1972-1991": (
        "Nixon visit to China",
        "U.S.-China normalization",
        "U.S. international broadcasting China",
        "1989 Tiananmen events",
    ),
    "1992-2016": (
        "China joins the WTO",
        "South China Sea dispute",
        "China cybersecurity",
        "Asia-Pacific rebalance",
    ),
    "2017-2025": (
        "U.S.-China trade war",
        "Huawei sanctions",
        "COVID-19 pandemic",
        "Xinjiang and Hong Kong policy",
        "Taiwan Strait",
        "semiconductor and artificial intelligence competition",
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
)


@dataclass(frozen=True)
class SearchQuery:
    period: str
    source_category: str
    event_term: str
    topic_term: str
    query_label: str
    query: str


def build_query_plan(period: str, source_category: str) -> list[SearchQuery]:
    if period not in PERIODS:
        raise ValueError(f"unknown period: {period}")
    if source_category not in SOURCE_TERMS:
        raise ValueError(f"unknown source category: {source_category}")

    queries = []
    for source in SOURCE_TERMS[source_category]:
        for event in EVENT_TERMS[period]:
            for topic in TOPIC_TERMS:
                label = "-".join((period, source_category, _slug(event), _slug(topic)))
                queries.append(
                    SearchQuery(
                        period=period,
                        source_category=source_category,
                        event_term=event,
                        topic_term=topic,
                        query_label=label,
                        query=f'"{source}" "{event}" "{topic}" {period}',
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
            candidates.append(
                MaterialCandidate(
                    source_url=url,
                    period=period,
                    source_category=category,
                    query_label=query_label,
                    platform_id=platform_id,
                )
            )
    return candidates


def _slug(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")
