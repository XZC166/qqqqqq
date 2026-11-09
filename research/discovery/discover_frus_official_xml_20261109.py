"""Bounded official FRUS data acquisition; document inventory is never formal text."""
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/candidate-evidence/frus-official-xml-20261109"
UA = "research-crawler/0.1 (academic historical source inventory)"
NS = {"t": "http://www.tei-c.org/ns/1.0"}
XMLID = "{http://www.w3.org/XML/1998/namespace}id"
VOLUMES = ("frus1949v08.xml", "frus1949v09.xml", "frus1950v06.xml", "frus1951v07p1.xml", "frus1951v07p2.xml", "frus1969-76v17.xml")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "manifest.json"
    assert not manifest.exists(), "Fixed acquisition batch exists; do not replace historical evidence."
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "records": [], "documents": [], "formal_records_added": 0,
              "notice": "Officially released TEI files and candidate document inventory only. No final topic, publication-day, author or completeness acceptance; do not count XML documents as formal Excel records."}

    def save_report():
        manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    def fetch(url, name):
        started = datetime.now(timezone.utc).isoformat()
        try:
            with urlopen(Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json" if "api.github.com" in url else "*/*"}), timeout=20) as response:
                raw, code, final = response.read(), response.status, response.url
                headers = {k: response.headers[k] for k in ("Content-Type", "ETag", "Last-Modified", "X-RateLimit-Remaining", "X-RateLimit-Reset") if k in response.headers}
        except HTTPError as exc:
            raw, code, final, headers = exc.read(), exc.code, exc.url, {}
        except Exception as exc:
            record = {"url": url, "fetched_at": started, "status": "pending", "reason": f"{type(exc).__name__}: {exc}"}
            report["records"].append(record); save_report(); return None, record
        path = OUT / name
        assert not path.exists()
        path.write_bytes(raw)
        record = {"url": url, "final_url": final, "fetched_at": started, "http_status": code, "path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest(), "headers": headers, "status": "captured" if code == 200 else ("restricted" if code in (401, 403, 429) else "pending")}
        report["records"].append(record); save_report()
        return raw if code == 200 else None, record

    # Official API discovery uses only public endpoints; no credentials or retries.
    raw, _ = fetch("https://api.github.com/repos/HistoryAtState/frus/commits/master", "commit.json")
    if raw is None: return
    commit = json.loads(raw)["sha"]
    assert re.fullmatch(r"[0-9a-f]{40}", commit)
    report["official_repository"] = "https://github.com/HistoryAtState/frus"
    report["pinned_commit"] = commit
    time.sleep(1)
    raw, _ = fetch("https://api.github.com/repos/HistoryAtState/frus/contents/volumes?ref=" + commit, "volume-index.json")
    if raw is None: return
    files = {r["name"]: r for r in json.loads(raw)}
    raw, robot_record = fetch("https://raw.githubusercontent.com/robots.txt", "raw-host-robots.txt")
    robots = RobotFileParser()
    if raw is not None: robots.parse(raw.decode("utf-8").splitlines())
    elif robot_record.get("http_status") in (404, 410): robots.parse([])
    else:
        report["raw_file_access"] = "pending: raw-host robots could not be established"; save_report(); return
    for filename in ("README.md", *VOLUMES):
        relative = filename if filename == "README.md" else "volumes/" + filename
        if filename != "README.md" and filename not in files:
            report["records"].append({"repository_path": relative, "status": "pending", "reason": "Not present in pinned official volume index; no guessed substitute."}); save_report(); continue
        url = f"https://raw.githubusercontent.com/HistoryAtState/frus/{commit}/{relative}"
        if not robots.can_fetch(UA, url):
            report["records"].append({"url": url, "status": "restricted", "reason": "robots.txt"}); save_report(); continue
        time.sleep(max(1, robots.crawl_delay(UA) or 0))
        raw, capture = fetch(url, filename)
        if raw is None: continue
        if filename == "README.md":
            report["license_notice_preserved"] = "public domain" in raw.decode("utf-8").lower(); save_report(); continue
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        assert blob == files[filename]["sha"], "Downloaded file differs from official pinned Git blob"
        capture["official_git_blob_sha1"] = blob
        tree = etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))
        volume_title = " ".join(tree.xpath("string(t:teiHeader/t:fileDesc/t:titleStmt/t:title[1])", namespaces=NS).split())
        for doc in tree.xpath(".//t:div[@type='document']", namespaces=NS):
            doc_id = doc.get(XMLID)
            if not doc_id: continue
            title = " ".join(doc.xpath("string(t:head[1])", namespaces=NS).split())
            dates = doc.xpath(".//t:dateline//t:date/@when", namespaces=NS)
            report["documents"].append({"volume": filename[:-4], "volume_title": volume_title, "document_id": doc_id, "title_cue": title, "encoded_date_cues": dates,
                "source_url": f"https://history.state.gov/historicaldocuments/{filename[:-4]}/{doc_id}", "official_xml_url": url, "evidence_path": capture["path"], "source_sha256": capture["sha256"], "status": "candidate", "not_formal": True})
        save_report()
        print(json.dumps({"volume": filename, "http_status": capture["http_status"], "candidate_documents": len(report["documents"]), "formal": 0}, ensure_ascii=False), flush=True)
    report["candidate_document_count"] = len(report["documents"])
    report["completed_at"] = datetime.now(timezone.utc).isoformat(); save_report()


if __name__ == "__main__":
    main()
