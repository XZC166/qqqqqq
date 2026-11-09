"""Bounded APP full-text search discovery. Search excerpts never become bodies."""
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from lxml import html


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/candidates-app-fulltext-early-moreterms-20261109.csv"
EVIDENCE = ROOT / "data/candidate-evidence/app-fulltext-early-moreterms-20261109"
UA = "research-crawler/0.1 (academic historical document discovery)"
BASE = "https://www.presidency.ucsb.edu"


def main():
    assert not OUT.exists(), "Fixed discovery exists; preserve history."
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    robots_raw = urlopen(Request(BASE + "/robots.txt", headers={"User-Agent": UA}), timeout=15).read()
    (EVIDENCE / "robots.txt").write_bytes(robots_raw)
    robots_text = robots_raw.decode("utf-8")
    robots = RobotFileParser()
    robots.parse(robots_text.splitlines())
    declared = [float(v) for v in re.findall(r"(?im)^Crawl-delay:\s*(\d+(?:\.\d+)?)", robots_text)]
    interval = max([10.0, *declared])
    records, pages = {}, []
    fields = ["url", "period", "source_category", "query_label", "platform_id", "metadata_url"]
    last_request = time.monotonic()
    for request_index, (term, page) in enumerate((term, page) for term in ("Taiwan", "Quemoy", "Matsu", "Voice of America") for page in range(2)):
        params = {"field-keywords": term, "from[date]": "01-01-1949", "to[date]": "12-31-1991", "items_per_page": 100, "page": page}
        url = BASE + "/advanced-search?" + urlencode(params)
        if not robots.can_fetch(UA, url):
            pages.append({"term": term, "page": page, "url": url, "status": "restricted", "reason": "robots.txt"})
            continue
        time.sleep(max(0, interval - (time.monotonic() - last_request)))
        last_request = time.monotonic()
        try:
            with urlopen(Request(url, headers={"User-Agent": UA}), timeout=15) as response:
                raw, status = response.read(), response.status
            path = EVIDENCE / (term.lower().replace(" ", "-") + f"-page-{page:02d}.html")
            path.write_bytes(raw)
            document = html.fromstring(raw)
            count = 0
            for row in document.xpath('//div[contains(@class,"view-content")]//tr[td]'):
                dates = row.xpath('./td[contains(@class,"field-docs-start-date-time-value")]')
                links = row.xpath('./td[contains(@class,"views-field-title")]/a[contains(@href,"/documents/")]')
                if len(dates) != 1 or len(links) != 1:
                    continue
                date = datetime.strptime(" ".join(dates[0].text_content().split()), "%b %d, %Y").date()
                if not 1949 <= date.year <= 1991:
                    continue
                source_url = urljoin(BASE, links[0].get("href"))
                period = "1949-1972" if date.year <= 1972 else "1972-1991"
                records.setdefault(source_url, {
                    "url": source_url, "period": period, "source_category": "government",
                    "query_label": "app-fulltext-early-moreterms-20261109:" + term, "platform_id": "", "metadata_url": "",
                    "index_date": date.isoformat(), "index_title": " ".join(links[0].text_content().split()),
                    "index_evidence": str(path.relative_to(ROOT)),
                })
                count += 1
            pages.append({"term": term, "page": page, "url": url, "http_status": status, "rows": count, "raw_sha256": hashlib.sha256(raw).hexdigest(), "path": str(path.relative_to(ROOT))})
        except Exception as exc:
            pages.append({"term": term, "page": page, "url": url, "status": "pending", "reason": f"{type(exc).__name__}: {exc}"})
        with OUT.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows({k: record[k] for k in fields} for record in records.values())
        report = {"generated_at": datetime.now(timezone.utc).isoformat(), "notice": "Search hits only; no full-text or topic verification claimed. Two bounded pages per additional historical term, not exhaustive. Index dates are discovery cues until individual-page verification.", "candidate_count": len(records), "pages": pages, "records": list(records.values())}
        OUT.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"page": page, "candidates": len(records), "result": pages[-1]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
