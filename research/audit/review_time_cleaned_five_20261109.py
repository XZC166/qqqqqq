"""Revalidate five exact TIME originals after source-backed ad removal."""
import hashlib
import json
import re
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.quality_audit import audit_material, material_fingerprint, _source_row
from research_crawler.revalidation import _extract_existing
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import ResearchStore

ROOT = Path(__file__).resolve().parents[2]
SUMMARIES = {
    2748: "报道安全公司对中国网络活动的追踪、美国政府指控与中方否认，并讨论公开报告在网络安全争论中的作用。",
    2749: "评论讨论中国经济与国际影响力的增长、信息控制和长期风险，以及美国面对中国崛起的政策选择。",
    2750: "报道与评论特朗普初期对华言辞、台湾及南海争议、贸易摩擦与全球领导权竞争，并呈现中美相关人士的看法。",
    2751: "评论将中美关税措施与国内政治、台湾及科技竞争相联系，讨论贸易争端进一步升级的风险。",
    2753: "报道台湾选举中的两岸关系、竞选传播和信息指控，并讨论美国对台关系及中方反应。",
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Trump", "Xi Jinping", "cyber", "CrowdStrike", "hacker", "propaganda", "trade", "tariffs", "information", "public opinion", "misinformation", "South China Sea")


def main():
    report_path = ROOT / "data/reviews/time-five-cleaned-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    observed = json.loads((ROOT / "data/reviews/time-five-raw-cleaning-review-20261109.json").read_text(encoding="utf-8"))
    assert {r["id"] for r in observed} == SUMMARIES.keys()
    store = ResearchStore(ROOT / "data/research.sqlite3")
    backup = sqlite3.connect(ROOT / "data/backups/pre-time-five-cleaned-review-20261109.sqlite3")
    store.connection.backup(backup);backup.close()
    records, corrections = [], []
    for item in observed:
        row = _source_row(store, item["id"])
        assert hashlib.sha256(row["body"].encode()).hexdigest() == item["old_body_sha256"]
        raw = Path(row["evidence_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["raw_sha256"] == row["content_sha256"]
        result, metadata_ids = _extract_existing(store, row, GovernmentArticleAdapter())
        parsed = result.get("material")
        assert parsed and parsed.body == "\n\n".join(item["clean_paragraphs"])
        assert hashlib.sha256(parsed.body.encode()).hexdigest() == item["body_sha256"]
        old_paragraphs = row["body"].split("\n\n")
        assert parsed.body == "\n\n".join(t for t in old_paragraphs if t != "Advertisement")
        assert len(old_paragraphs) == item["total"]
        for field in ("source", "author", "title", "source_url"):
            assert getattr(parsed, field) == row[field]
        assert parsed.time == row["published_on"] == item["date"]
        abstract = "据正文整理：" + SUMMARIES[item["id"]]
        keywords = "; ".join(dict.fromkeys(m.group() for term in TERMS if (m := re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", parsed.body, re.I))))
        fields = json.loads(store.connection.execute("SELECT field_sources FROM material_verifications WHERE material_id=?", (item["id"],)).fetchone()[0])
        fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
        mid, created = store.add_verified_material(row["candidate_id"], row["evidence_id"], replace(parsed, abstract=abstract, keywords=keywords), abstract_origin="derived", field_sources=fields, metadata_evidence_ids=metadata_ids)
        assert mid == item["id"] and not created
        corrections.append({"material_id": mid, "previous_fields": dict(row), "removed_ad_paragraph_positions": item["ads"], "old_body_sha256": item["old_body_sha256"], "new_body_sha256": item["body_sha256"]})
        current = store.connection.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        records.append({"material_id": mid, "fingerprint": material_fingerprint(current), "approved": True, "reason": "Individual complete-body topic review and raw-source ad-element verification: " + SUMMARIES[mid], "source_url": parsed.source_url, "body_sha256": item["body_sha256"]})
    manifest = ROOT / "data/reviews/time-five-cleaned-topic-decisions-20261109.json"
    assert not manifest.exists()
    raw = json.dumps({"records": records, "field_corrections": corrections, "note": "Original raw evidence unchanged. Only source-declared Advertisement paragraphs removed, preserving all article paragraph order and wording."}, ensure_ascii=False, indent=2).encode()
    manifest.write_bytes(raw)
    results = [audit_material(store, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    passed = sum(r["status"] == "pass" for r in results)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": 5, "new_candidates": 0, "formal_fulltexts": passed, "restored_formal": passed, "pending": 5-passed, "withdrawn_formal": 0, "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests": 0, "records": results}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="records"}, ensure_ascii=False));store.close()


if __name__ == "__main__":
    main()
