"""Fourteen further individually read early archive items."""
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
    14722: "肯尼迪杰克逊问答说明在金门、马祖遭袭构成对台湾及澎湖进攻一部分时的防卫立场，并讨论防卫界线。",
    14725: "肯尼迪声明比较其本人、尼克松及艾森豪威尔政府关于金门、马祖的公开立场，讨论承诺、条约和竞选言辞引发战争的风险。",
    14726: "尼克松声明批评肯尼迪的金门、马祖言论，主张以美国团结和坚定立场防止中国方面误判并降低战争风险。",
    14756: "肯尼迪祝酒辞强调包括美国、中国、苏联和英国在内各方对老挝中立与独立的共同承诺，并表示美国将履约且希望其他签署国同样履约。",
    14788: "约翰逊宣布恢复对北越空袭，说明停炸期间的和平交涉、河内和北京的反应，并要求通过联合国和媒体说明美国立场。",
    14789: "约翰逊在追授勋章仪式讲话中解释越战目的并指责河内、北京，强调国内团结；同篇页面还刊载明确标示的授勋引文。",
    14793: "约翰逊在接受和平奖时向河内和北京重申美国对越南战争的立场，并表示若停止战争行为，美国愿协助和平发展。",
}
DEFER = {
    14712: "Complete rally remarks read; the public-image argument concerns mainly Soviet competition, and Formosa is only named in a crisis list. Direct China communication linkage requires closer assessment.",
    14749: "Full available source text read, but title explicitly identifies excerpts and an advance release. Do not represent the available excerpts as the complete speech, despite directly relevant VOA passages.",
    14752: "Complete address read; Peking is mentioned only as the location of a pre-1949 emperor in a historical comparison, not contemporary China communication.",
    14754: "Complete stored toast read; discussion concerns Laos and US-Soviet relations without identifying China in its body. Search/index references do not establish body relevance.",
    14755: "Complete stored toast read; Latin American policy and Castro are discussed, but no substantive China reference in body. Do not import China context from index/template.",
    14758: "Complete message read; Formosa Resolution appears only as a legislative analogy for the Southeast Asia resolution. Specific China-directed communication relevance not accepted in this decision.",
    14764: "Complete remarks read; Formosa Strait is one example in a list of bipartisan crisis responses. More direct China communication-policy content remains unestablished.",
}
TERMS = ("China", "Chinese", "United States", "U.S.", "Taiwan", "Formosa", "Peking", "Peiping", "Moscow", "Gallup", "United Nations", "propaganda", "ideological", "public opinion", "prestige", "influence", "educational exchanges", "university research", "peer competitor", "soybeans", "trade", "Communists", "Central Intelligence Agency")


def main():
    output = ROOT / "data/reviews/early-short-next14-quality-review-20261109.json"
    assert not output.exists(), "Fixed batch already reviewed; preserve subsequent decisions."
    early = json.loads((ROOT / "data/reviews/app-historical188-short-next15-reading-20261109.json").read_text(encoding="utf-8"))
    later = json.loads((ROOT / "data/reviews/later-social-next20-reading-20261109.json").read_text(encoding="utf-8"))
    ids = SUMMARIES.keys() | DEFER.keys()
    selected = [r for r in early + later if r["id"] in ids]
    assert len(selected) == len(ids) == 14 and SUMMARIES.keys().isdisjoint(DEFER)
    store = ResearchStore(ROOT / "data/research.sqlite3"); c = store.connection
    backup = ROOT / "data/backups/pre-early-short-next14-review-20261109.sqlite3"
    assert not backup.exists()
    b = sqlite3.connect(backup); c.backup(b); b.close()
    prior = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'").fetchall()}
    records, changes = [], []
    for observed in selected:
        mid = observed["id"]
        row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        for k in ("source", "published_on", "author", "title", "source_url", "abstract", "keywords", "body"):
            assert row[k] == observed[k], (mid, k)
        assert hashlib.sha256(row["body"].encode()).hexdigest() == observed["body_sha256"]
        approved = mid in SUMMARIES
        if approved:
            source = _source_row(store, mid)
            result, metadata_ids = _extract_existing(store, source, GovernmentArticleAdapter())
            parsed = result.get("material")
            assert parsed and parsed.body == row["body"]
            assert hashlib.sha256(Path(source["evidence_path"]).read_bytes()).hexdigest() == source["content_sha256"]
            for attribute, field in (("source", "source"), ("time", "published_on"), ("author", "author"), ("title", "title"), ("source_url", "source_url")):
                assert getattr(parsed, attribute) == row[field], (mid, field)
            abstract = "据正文整理：" + SUMMARIES[mid]
            keywords = "; ".join(dict.fromkeys(m.group() for t in TERMS if (m := re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", row["body"], re.I))))
            assert keywords
            snapshot = c.execute("SELECT * FROM material_verifications WHERE material_id=?", (mid,)).fetchone()
            assert snapshot and snapshot["abstract_origin"] == "derived"
            fields = json.loads(snapshot["field_sources"])
            fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
            saved, created = store.add_verified_material(source["candidate_id"], row["evidence_id"], replace(parsed, abstract=abstract, keywords=keywords), abstract_origin="derived", field_sources=fields, metadata_evidence_ids=metadata_ids)
            assert saved == mid and not created
            changes.append({"material_id": mid, "previous_fields": dict(row), "new_abstract": abstract, "new_keywords": keywords})
            row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        reason = ("Individually read same-source document: " + SUMMARIES[mid]) if approved else DEFER[mid]
        if approved and mid < 10000:
            reason += " Complete original institutional post only; not its linked article or audiovisual work. Same-text posts with different platform IDs remain distinct."
        records.append({"material_id": mid, "fingerprint": material_fingerprint(row), "approved": approved, "reason": reason, "source_url": row["source_url"], "body_sha256": observed["body_sha256"]})
    manifest = ROOT / "data/reviews/early-short-next14-topic-decisions-20261109.json"
    assert not manifest.exists()
    raw = json.dumps({"records": records, "field_corrections": changes, "scope": "Fourteen available source items individually read; seven accepted, explicit excerpts and incidental matches withheld. No decision implied for any other record. No source body changed."}, ensure_ascii=False, indent=2).encode()
    manifest.write_bytes(raw)
    results = [audit_material(store, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    passed = {r["material_id"] for r in results if r["status"] == "pass"}
    assert passed == set(SUMMARIES), [(r["material_id"], r["reason"]) for r in results if r["material_id"] in SUMMARIES and r["status"] != "pass"]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0, "formal_fulltexts": len(passed), "early_formal_full_documents": 7, "later_original_full_posts": 0, "new_formal_promotions": len(passed - prior), "pending": len(results) - len(passed), "withdrawn_formal": len((prior & ids) - passed), "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests_for_review": 0, "backup": str(backup.relative_to(ROOT)), "records": results}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2))
    store.close()


if __name__ == "__main__":
    main()
