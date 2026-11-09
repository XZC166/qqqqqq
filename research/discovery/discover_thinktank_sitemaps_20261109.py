"""Bounded official sitemap discovery; sitemap lastmod is never a publication date."""
import csv
import hashlib
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / "data/candidate-evidence/thinktank-20261109"
TOPIC = re.compile(r"(?:china|chinese|taiwan|beijing|peking|hong-kong|xinjiang|tibet|sino-|trade-war|huawei)",re.I)


def collect(host):
    rules = RobotFileParser()
    rules.parse((DIRECTORY/(host+".robots.txt")).read_text(encoding="utf-8").splitlines())
    index = etree.fromstring((DIRECTORY/(host+".sitemap.xml")).read_bytes())
    urls = index.xpath('//*[local-name()="loc"]/text()')
    if host == "www.brookings.edu":
        urls = [u for u in urls if "/article-sitemap" in u][:55]
    else:
        urls = urls[:22]
    candidates, pages = {}, []
    for i,url in enumerate(urls):
        if not rules.can_fetch("research-crawler",url):
            pages.append({"url":url,"status":"restricted","reason":"robots.txt"})
            continue
        # CSIS explicitly allows /*?page= ahead of its broader query disallow.
        time.sleep(1)
        try:
            with urlopen(Request(url,headers={"User-Agent":"research-crawler/0.1"}),timeout=25) as response:
                raw,status = response.read(),response.status
            path = DIRECTORY / (host+f".sitemap-{i:02d}.xml")
            path.write_bytes(raw)
            document = etree.fromstring(raw)
            locations = document.xpath('//*[local-name()="url"]/*[local-name()="loc"]/text()')
            matches = 0
            for location in locations:
                parsed = urlsplit(location)
                if parsed.hostname != host or not TOPIC.search(parsed.path) or not rules.can_fetch("research-crawler",location):
                    continue
                if host == "www.csis.org" and not parsed.path.startswith("/analysis/"):
                    continue
                if host == "www.brookings.edu" and not parsed.path.startswith(("/articles/","/research/")):
                    continue
                candidates.setdefault(location,{"url":location,"period":"2017-2025","source_category":"think_tank","query_label":"thinktank-sitemap-china-20261109","platform_id":"","metadata_url":""})
                matches += 1
            pages.append({"url":url,"http_status":status,"fetched_at":datetime.now(timezone.utc).isoformat(),"sha256":hashlib.sha256(raw).hexdigest(),"evidence_path":str(path.relative_to(ROOT)),"locations":len(locations),"topic_candidates":matches})
        except Exception as exc:
            pages.append({"url":url,"status":"pending","reason":f"{type(exc).__name__}: {exc}"})
        print(json.dumps({"host":host,"page":i,"candidates":len(candidates),"status":pages[-1].get("http_status",pages[-1].get("status"))}),flush=True)
    return {"host":host,"pages":pages,"records":list(candidates.values())}


def main():
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(collect,["www.csis.org","www.brookings.edu"]))
    records = {r["url"]:r for result in results for r in result["records"]}
    output = ROOT / "data/candidates-thinktank-sitemap-china-20261109.csv"
    with output.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=["url","period","source_category","query_label","platform_id","metadata_url"])
        writer.writeheader();writer.writerows(records.values())
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"notice":"Discovery only. Queue period is provisional scope, not an asserted publication date. Verify each source page; reassign its period from actual publication metadata before promotion. Never use sitemap lastmod.","candidate_count":len(records),"results":results}
    output.with_suffix(".json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_count":len(records),"csv":str(output)}),flush=True)


if __name__ == "__main__":main()
