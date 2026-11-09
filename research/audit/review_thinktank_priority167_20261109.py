"""Offline recheck of a fixed, manually scoped discovery batch. No network."""
import hashlib
import json
import re
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from scrapy.http import HtmlResponse
from research_crawler.items import MaterialCandidate
from research_crawler.pipelines import VerificationPipeline
from research_crawler.spiders.government import GovernmentArticleAdapter

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "data/reviews/thinktank-priority167-source-topic-review-20261109.json"
BACKUP = ROOT / "data/backups/pre-thinktank-priority167-review-20261109.sqlite3"
# Reviewed titles and same-document topic passages. This is a fixed review
# manifest, not an automatic keyword-based assertion about every discovered URL.
APPROVED = {
16348,16350,16354,16371,16374,16376,16377,16380,16381,16386,16387,16388,16390,16391,16394,16397,16401,16404,16407,16408,16409,16413,16419,16422,16423,16425,16431,16433,16434,16437,16440,
16442,16445,16448,16447,16450,16451,16452,16454,16455,16456,16457,16458,16459,16460,16461,16464,16465,16466,16469,16472,16476,16477,16478,16479,16480,16481,16486,16487,16488,16489,16490,16492,16493,16501,16506,
}
TERMS = ("United States", "U.S.", "US", "China", "Chinese", "Taiwan", "Taiwan Strait", "South China Sea", "Beijing", "Washington", "public opinion", "soft power", "media", "propaganda", "disinformation", "influence operations", "cybersecurity", "trade war", "trade", "tariffs", "security", "diplomacy", "climate", "energy", "Hong Kong", "Xinjiang", "human rights", "Nixon", "Trump", "Obama")


def main():
    if REPORT.exists():
        raise SystemExit("Review already recorded; do not repeat or recount.")
    pipeline = VerificationPipeline(ROOT / "data/research.sqlite3", ROOT / "data/evidence")
    pipeline.open_spider()
    store = pipeline.store
    c = store.connection
    rows = c.execute("SELECT c.*,e.id AS eid,e.evidence_path,e.content_sha256,e.status_code,e.fetched_at FROM candidates c JOIN evidence e ON e.id=(SELECT max(id) FROM evidence WHERE candidate_id=c.id AND source_url=c.source_url) WHERE c.query_label='thinktank-sitemap-priority-20261109' ORDER BY c.id").fetchall()
    assert len(rows) == 167 and APPROVED <= {r["id"] for r in rows}
    if not BACKUP.exists():
        b=sqlite3.connect(BACKUP);c.backup(b);b.close()
    records=[]
    for r in rows:
        raw=Path(r["evidence_path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == r["content_sha256"]
        candidate=MaterialCandidate(r["source_url"],r["period"],r["source_category"],r["query_label"])
        result=GovernmentArticleAdapter().extract(HtmlResponse(r["source_url"],body=raw,encoding="utf-8"),candidate)
        m=result.get("material")
        reason=None
        if m is None:
            reason="Source adapter cannot confirm complete body and same-article metadata."
        elif len(m.body)<1500:
            reason="Short page needs individual check for a report introduction or video/podcast description; length is a review flag, not proof of truncation."
        elif r["id"] not in APPROVED:
            reason="Direct topic relationship has not been approved for this record."
        if reason is None:
            y=int(m.time[:4])
            period="1949-1972" if 1949<=y<=1972 else "1972-1991" if 1973<=y<=1991 else "1992-2016" if 1992<=y<=2016 else "2017-2025" if 2017<=y<=2025 else None
            if period is None:
                reason="Publication date outside the research window."
        if reason is None:
            keywords=m.keywords or "; ".join(dict.fromkeys(match.group() for term in TERMS if (match:=re.search(r"(?<!\w)"+re.escape(term)+r"(?!\w)",m.body,re.I))))
            abstract=m.abstract
            if not abstract:
                passage=" ".join(m.body.split("\n\n")[:2])
                if len(passage)>650:passage=passage[:650].rsplit(" ",1)[0]
                abstract="据正文整理："+passage
                result["abstract_origin"]="derived"
            assert keywords and abstract
            m=replace(m,keywords=keywords,abstract=abstract)
            result["material"]=m
            result.setdefault("field_sources",{}).update({"abstract":r["source_url"],"keywords":r["source_url"]})
            result["keywords_origin"]="derived"
            batch_id=store.create_batch(period,r["source_category"],r["query_label"])
            c.execute("UPDATE candidates SET period=?,batch_id=? WHERE id=?",(period,batch_id,r["id"]));c.commit()
            result["candidate"]=replace(candidate,period=period)
            result["evidence"]=replace(result["evidence"],fetched_at=r["fetched_at"],retrieval_method="offline_revalidation",retrieval_id=f"candidate-{r['id']}-evidence-{r['eid']}")
            result["raw_response"]=raw
            pipeline.process_item(result)
            state=c.execute("SELECT status,status_detail FROM candidates WHERE id=?",(r["id"],)).fetchone()
            if state["status"] != "verified":reason=state["status_detail"]
        if reason:
            with c:
                for old in c.execute("SELECT id FROM materials WHERE identity_key=?",(r["identity_key"],)).fetchall():
                    c.execute("DELETE FROM material_verifications WHERE material_id=?",(old["id"],))
                    c.execute("DELETE FROM materials WHERE id=?",(old["id"],))
                c.execute("UPDATE candidates SET status='pending',status_detail=? WHERE id=?",(reason,r["id"]))
        records.append({"candidate_id":r["id"],"url":r["source_url"],"status":"pending" if reason else "verified","reason":reason or "Whole source body, exact source publication date and direct US-China policy/discourse relationship reviewed.","title":m.title if m else None,"published_on":m.time if m else None,"source_complete":bool(m),"body_sha256":hashlib.sha256(m.body.encode()).hexdigest() if m else None,"raw_sha256":r["content_sha256"],"evidence_path":r["evidence_path"]})
    report={"generated_at":datetime.now(timezone.utc).isoformat(),"candidates":len(rows),"source_fulltext_pass":sum(x["source_complete"] for x in records),"formal_source_and_scope_pass":sum(x["status"]=="verified" for x in records),"pending":sum(x["status"]=="pending" for x in records),"restricted":0,"http_failed":0,"backup":str(BACKUP.relative_to(ROOT)),"records":records}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!='records'},ensure_ascii=False,indent=2))
    pipeline.close_spider()


if __name__ == "__main__":main()
