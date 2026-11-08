import argparse
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from lxml import html


BASE_URL = "https://www.presidency.ucsb.edu/documents/app-categories/presidential"
USER_AGENT = "research-crawler/0.1 (academic historical document discovery)"
TOPIC_PATTERN = re.compile(
    r"\b(?:china|chinese|taiwan|taiwanese|formosa|peking|quemoy|matsu|"
    r"sino[- ]american|people['’]s republic of china|republic of china)\b|"
    r"\b(?:korean war|north korea(?:n)?|korean peninsula)\b",
    re.I,
)
DATE_PATTERN = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})")


def discover(start_page: int, end_page: int, output: Path, *, concurrency: int, delay: float) -> dict:
    if start_page < 0 or end_page < start_page or end_page > 1512:
        raise ValueError("page range must be between 0 and 1512")
    if concurrency not in {1, 2}:
        raise ValueError("concurrency must be 1 or 2")

    robots = RobotFileParser("https://www.presidency.ucsb.edu/robots.txt")
    robots.read()
    pages = range(start_page, end_page + 1)
    errors = []
    records = {}

    def fetch(page: int):
        url = f"{BASE_URL}?{urlencode({'items_per_page': 60, 'page': page})}"
        if not robots.can_fetch(USER_AGENT, url):
            return page, [], "blocked by robots.txt"
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                status = response.status
            if status != 200:
                return page, [], f"HTTP {status}"
            document = html.fromstring(raw)
            rows = []
            for anchor in document.xpath(
                '//div[contains(@class,"view-content")]//a[contains(@href,"/documents/")]'
            ):
                href = anchor.get("href", "")
                if not href.startswith("/documents/"):
                    continue
                parent = anchor
                for _ in range(3):
                    if parent.getparent() is not None:
                        parent = parent.getparent()
                row_text = " ".join(parent.text_content().split())
                match = DATE_PATTERN.search(row_text)
                if not match:
                    continue
                published = datetime.strptime(match.group(1), "%B %d, %Y").date()
                title = " ".join(anchor.text_content().split())
                if not title or not TOPIC_PATTERN.search(title):
                    continue
                if published.year <= 1972:
                    period = "1949-1972"
                elif published.year <= 1991:
                    period = "1972-1991"
                else:
                    continue
                rows.append({
                    "url": urljoin(BASE_URL, href),
                    "period": period,
                    "source_category": "government",
                    "query_label": f"app-index-{period}-page-{page}",
                    "platform_id": "",
                    "metadata_url": "",
                    "index_page": url,
                    "index_title": title,
                    "index_date": published.isoformat(),
                    "index_row": row_text,
                })
            time.sleep(delay)
            return page, rows, ""
        except Exception as exc:
            time.sleep(delay)
            return page, [], f"{type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(fetch, page) for page in pages]
        for future in as_completed(futures):
            page, rows, error = future.result()
            if error:
                errors.append({"page": page, "error": error})
            for row in rows:
                records.setdefault(row["url"], row)

    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ("url", "period", "source_category", "query_label", "platform_id", "metadata_url")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in records.values())

    report = {
        "source": "The American Presidency Project presidential document index",
        "page_range": [start_page, end_page],
        "items_per_page": 60,
        "listing_pages_requested": len(pages),
        "candidate_urls": len(records),
        "candidates_by_period": {
            period: sum(row["period"] == period for row in records.values())
            for period in ("1949-1972", "1972-1991")
        },
        "error_pages": errors,
        "candidate_csv": str(output),
        "notice": "Index titles and dates are discovery evidence only. No candidate is a formal full-text record until its original page is fetched and verified.",
    }
    output.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-page", type=int, required=True)
    parser.add_argument("--end-page", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()
    print(json.dumps(discover(
        args.start_page, args.end_page, args.output,
        concurrency=args.concurrency, delay=args.delay,
    ), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
