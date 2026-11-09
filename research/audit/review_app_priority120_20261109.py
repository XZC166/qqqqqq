"""Source re-extraction and recorded scope decisions for one fixed early batch."""
import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from scrapy.http import HtmlResponse
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data/reviews/app-priority120-source-topic-review-20261109.json"
BACKUP = ROOT / "data/backups/pre-app-priority120-topic-review-20261109.sqlite3"
WEAK = {
    13042: "Prayer proposal only; no substantive China policy or communications discussion.",
    13043: "Only asks whether a China statement is planned; response contains no substantive statement.",
    13045: "Unconfirmed visit report; no substantive China policy response.",
    13046: "Unconfirmed appointment report only.",
    13056: "UN admission question receives no comment; retained pending for contextual sampling.",
    13070: "Only a planned fur-restriction proclamation query, with no substantive policy response.",
    13080: "China hit is Indo-China, without direct PRC or Taiwan discussion.",
    13089: "Only a list of nineteenth-century party achievements including the Open Door Policy.",
    13090: "Ceremonial gift/visit report with explicit absence of a specific China discussion.",
    13011: "Republic of China appears only in an alliance enumeration.",
    13015: "Chinese bases mentioned only incidentally in a disarmament discussion.",
    13127: "Free China appears only in an alliance enumeration.",
    13025: "China appears only in a list of foreign student origins.",
    13027: "China is only a passing comparison in a Cuba answer.",
    13031: "China appears only as a speculative explanation of Soviet motives.",
    13039: "No direct China/Chinese/Taiwan/Formosa discussion found in the extracted document.",
}


def main():
    if REPORT.exists():
        raise SystemExit("Saved review exists; do not repeat or recount.")
    c = sqlite3.connect(ROOT / "data/research.sqlite3")
    c.row_factory = sqlite3.Row
    urls = {r["url"] for r in csv.DictReader((ROOT / "data/candidates-app-fulltext-early-priority120-20261109.csv").open(encoding="utf-8-sig"))}
    rows = [r for r in c.execute("SELECT m.*,e.evidence_path,e.content_sha256,c.period,c.source_category,c.query_label FROM materials m JOIN evidence e ON e.id=m.evidence_id JOIN candidates c ON c.id=e.candidate_id ORDER BY m.published_on,m.id") if r["source_url"] in urls]
    assert len(urls) == len(rows) == 120
    assert set(WEAK) <= {r["id"] for r in rows}
    if not BACKUP.exists():
        b = sqlite3.connect(BACKUP); c.backup(b); b.close()
    records = []
    for row in rows:
        path = Path(row["evidence_path"])
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["content_sha256"]
        candidate = MaterialCandidate(row["source_url"],row["period"],row["source_category"],row["query_label"])
        result = GovernmentArticleAdapter().extract(HtmlResponse(row["source_url"],body=raw,encoding="utf-8"),candidate)
        material = result["material"]
        assert material is not None and result["evidence"].body_complete and result["evidence"].metadata_verified
        for name, field in (("source","source"),("time","published_on"),("author","author"),("title","title"),("body","body")):
            assert getattr(material,name) == row[field], (row["id"],name)
        assert c.execute("SELECT 1 FROM material_verifications WHERE material_id=?",(row["id"],)).fetchone()
        reason = WEAK.get(row["id"])
        records.append({"material_id":row["id"],"source_url":row["source_url"],"title":row["title"],"published_on":row["published_on"],"raw_sha256":row["content_sha256"],"body_sha256":hashlib.sha256(row["body"].encode()).hexdigest(),"evidence_path":str(path),"source_reextraction_match":True,"scope_decision":"pending" if reason else "retain","reason":reason or "Reviewed China-related paragraphs and adjacent Q&A: direct public China policy, image, media access, recognition, Taiwan, Korea or foreign-policy framing; whole document retained without excerpting.","identity_key":row["identity_key"]})
    with c:
        for record in records:
            if record["scope_decision"] != "pending":
                continue
            c.execute("UPDATE candidates SET status='pending',status_detail=? WHERE identity_key=?",("Scope review pending: "+record["reason"],record["identity_key"]))
            c.execute("DELETE FROM material_verifications WHERE material_id=?",(record["material_id"],))
            c.execute("DELETE FROM materials WHERE id=?",(record["material_id"],))
    report = {"generated_at":datetime.now(timezone.utc).isoformat(),"batch_candidates":120,"source_fulltext_pass":120,"retained_source_and_topic_review":104,"pending_topic_review":16,"restricted":0,"http_failed":0,"retained_records_are_whole_documents":True,"backup":str(BACKUP.relative_to(ROOT)),"records":records}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
