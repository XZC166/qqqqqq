"""Inventory six publicly released official FRUS files; never auto-promote documents."""
import hashlib
import json
import re
import sqlite3
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from lxml import etree
from research_crawler.items import MaterialCandidate
from research_crawler.store import ResearchStore

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "data/vendor/frus-official-20261109"
OUT = ROOT / "data/candidate-evidence/frus-official-git6-20261109"
FILES = ("frus1949v08.xml", "frus1949v09.xml", "frus1950v06.xml", "frus1951v07p1.xml", "frus1951v07p2.xml", "frus1969-76v17.xml")
NS = {"t": "http://www.tei-c.org/ns/1.0"}
XMLID = "{http://www.w3.org/XML/1998/namespace}id"


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True).stdout


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = OUT / "manifest.json"
    assert not manifest.exists(), "Fixed inventory exists; retain history."
    commit = git("rev-parse", "HEAD").decode().strip()
    assert commit == "216cdb7649a8e29504377d4f2858351dc46331a8"
    origin = git("remote", "get-url", "origin").decode().strip()
    assert origin == "https://github.com/HistoryAtState/frus.git"
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "repository": origin, "commit": commit,
              "retrieval_method": "Official public Git clone and sparse checkout; Git command exit status 0. HTTP response status is not available from Git and is not fabricated.",
              "http_status": None, "formal_added": 0, "volumes": [], "documents": [],
              "notice": "Complete original volume files retained. Individual document text/author/topic are NOT accepted. Historical document datelines are creation-date cues, not independently verified publication dates. These candidates are excluded from formal Excel until every required check passes."}
    readme = git("show", f"{commit}:README.md")
    assert b"public domain" in readme
    (OUT / "README.md").write_bytes(readme)
    report["license_evidence"] = {"path": str((OUT / "README.md").relative_to(ROOT)), "sha256": hashlib.sha256(readme).hexdigest(), "publisher_notice": "Official repository states its files are in the public domain."}
    grouped = defaultdict(list)
    for filename in FILES:
        path = "volumes/" + filename
        expected = git("rev-parse", f"{commit}:{path}").decode().strip()
        raw = git("cat-file", "blob", expected)
        assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == expected
        dest = OUT / filename; assert not dest.exists(); dest.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        tree = etree.fromstring(raw, parser=etree.XMLParser(resolve_entities=False, no_network=True))
        title = " ".join(tree.xpath("string(t:teiHeader/t:fileDesc/t:titleStmt/t:title[1])", namespaces=NS).split())
        pub_dates = tree.xpath("t:teiHeader/t:fileDesc/t:publicationStmt/t:date/@when", namespaces=NS)
        volume = {"file": filename, "title": title, "path": str(dest.relative_to(ROOT)), "sha256": digest, "git_blob_sha1": expected, "bytes": len(raw), "publication_date_cues": pub_dates, "document_count": 0}
        for doc in tree.xpath(".//t:div[@type='document']", namespaces=NS):
            doc_id = doc.get(XMLID)
            assert doc_id
            dates = doc.xpath("t:opener//t:dateline//t:date/@when", namespaces=NS)
            valid = [d for d in dates if re.match(r"\d{4}-\d{2}-\d{2}", d) and 1949 <= int(d[:4]) <= 1991]
            source_url = f"https://history.state.gov/historicaldocuments/{filename[:-4]}/{doc_id}"
            github_url = f"https://github.com/HistoryAtState/frus/blob/{commit}/{path}"
            period = ("1949-1972" if int(valid[0][:4]) <= 1972 else "1972-1991") if valid else None
            record = {"volume": filename[:-4], "document_id": doc_id, "title_cue": " ".join(doc.xpath("string(t:head[1])", namespaces=NS).split()),
                      "historical_dateline_cues": dates, "publication_date_verified": False, "source_url": source_url,
                      "official_xml_source_url": github_url, "source_sha256": digest, "evidence_path": volume["path"], "period_discovery_cue": period,
                      "status": "pending", "reason": "Exact publication date, author, thematic relevance and individual full-body fidelity remain unverified; historical dateline is not publication evidence."}
            report["documents"].append(record); volume["document_count"] += 1
            if period:
                grouped[period].append(MaterialCandidate(source_url, period, "government", "frus-official-git6-20261109", metadata_url=github_url))
        report["volumes"].append(volume)
    report["document_inventory_count"] = len(report["documents"])
    report["within_scope_dateline_candidates"] = sum(map(len, grouped.values()))
    # Preserve the full inventory before modifying progress; files are primary XML,
    # but no synthetic success response or formally accepted body is inserted.
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    known = {r[0] for r in c.execute("SELECT DISTINCT source_url FROM candidates").fetchall()}
    old_duplicates = c.execute("SELECT count(*) FROM duplicate_discoveries").fetchone()[0]
    backup = ROOT / "data/backups/pre-frus-official-git6-registration-20261109.sqlite3"
    assert not backup.exists(); b = sqlite3.connect(backup); c.backup(b); b.close()
    candidate_ids = []
    for period, records in grouped.items():
        batch = store.create_batch(period, "government", "frus-official-git6-20261109")
        ids = store.add_candidates(batch, records); candidate_ids.extend(ids)
        with c:
            c.executemany("UPDATE candidates SET status='pending',status_detail=? WHERE id=?", [("Official XML retained at " + str(manifest.relative_to(ROOT)) + "; exact publication day, authorship, individual topic/body review pending. Git capture has no observed HTTP status. Not a formal record.", cid) for cid in ids])
    report.update({"registered_candidate_rows": len(candidate_ids), "new_unique_urls": sum(r.source_url not in known for records in grouped.values() for r in records),
                   "known_url_rediscoveries": sum(r.source_url in known for records in grouped.values() for r in records), "duplicate_discoveries_added": c.execute("SELECT count(*) FROM duplicate_discoveries").fetchone()[0] - old_duplicates,
                   "discovery_period_counts": dict(Counter(r["period_discovery_cue"] for r in report["documents"] if r["period_discovery_cue"])),
                   "backup": str(backup.relative_to(ROOT)), "candidate_ids": candidate_ids, "completed_at": datetime.now(timezone.utc).isoformat()})
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("documents", "candidate_ids", "volumes")}, ensure_ascii=False, indent=2))
    store.close()


if __name__ == "__main__":
    main()
