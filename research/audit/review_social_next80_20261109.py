"""Fixed, individually read original posts, never their linked article full texts."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.quality_audit import audit_material, material_fingerprint
from research_crawler.store import ResearchStore

ROOT = Path(__file__).resolve().parents[2]
# Decisions followed reading each complete saved post and all exported fields.
# No keyword rule grants approval to subsequent posts.
GROUPS = {
    "Public attitudes to China, perceived threats, influence and comparative US image": [4279, 4280, 4281, 5501, 5504, 6836],
    "US-China diplomatic, economic, intelligence or technological competition": [4325, 4326, 4828, 4830, 5150, 5155, 5297, 5298, 5350, 5351, 5385, 5386, 6271, 6757, 6758, 6771, 7937, 7945, 8068, 9942],
    "China policy and political-system representations in institutional public discourse": [4328, 4329, 4829, 4831, 5151, 9945],
    "Taiwan security and public framing of regional competition": [5294, 5295, 6274, 6276, 8065, 9715, 9717],
    "Hong Kong, Xinjiang, dissent and human-rights public communication": [5357, 5359, 5360, 5380, 5381, 5382, 5383, 5532, 6819, 6820, 7941],
    "US media representations of Chinese military policy and international alignment": [6268, 6829],
}
DEFERRED_FIELDS = {5151, 5294, 6268}
# Their full bodies were read, but current generated summaries end mid-sentence
# or contain an unmatched quotation. Repair with new provenance before approval.
REASONS = {
    4278: "Religious population geography; no direct dissertation relationship established.",
    4684: "China-India missile-test item; direct dissertation relationship remains unapproved.",
    4685: "Broad year-end institutional promotion; individual China-discourse relationship unresolved.",
    4686: "China-India missile-test item; direct dissertation relationship remains unapproved.",
    4687: "UK embassy controversy; needs closer relevance review within US-centred dissertation scope.",
    5154: "Newsletter roundup and incomplete generated summary; repair and reassess.",
    5358: "Local fire/investigation item; direct dissertation relationship remains unapproved.",
    5387: "Mixed news roundup and incomplete generated summary; no blanket approval.",
    5389: "Mixed news roundup; separate Taiwan and AI topics must not be conflated.",
    5535: "Direct chip-competition post, but generated summary ends mid-sentence; repair with provenance.",
    5542: "Local fire casualty bulletin; direct dissertation relationship remains unapproved.",
    5543: "Local fire casualty bulletin; direct dissertation relationship remains unapproved.",
    6765: "Direct tariffs post, but generated summary is only 'Michigan Gov.'; repair with provenance.",
    7943: "Direct US-China investment post, but generated summary ends mid-sentence; repair with provenance.",
    8060: "Broad institutional year-end list; generated summary also ends mid-sentence.",
    8066: "Direct AI-competition post, but generated summary ends mid-sentence; repair with provenance.",
    9715: "Taiwan competition post has a complete original body, not a linked article.",
    9716: "Podcast promotional description; not a transcript or original substantive full article.",
    9718: "EU enlargement item; direct dissertation relationship remains unapproved.",
    9943: "Event invitation only; no substantive event transcript.",
    9944: "Event invitation only; no substantive event transcript.",
}


def main():
    report_path = ROOT / "data/reviews/social-next80-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later approvals and its report.")
    store = ResearchStore(ROOT / "data/research.sqlite3")
    c = store.connection
    selected = json.loads((ROOT / "data/reviews/social-next-selected-20261109.json").read_text(encoding="utf-8"))
    assert len(selected) == 80
    prior_formal = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    reasons = {mid: reason for reason, mids in GROUPS.items() for mid in mids if mid not in DEFERRED_FIELDS}
    rows = []
    records = []
    for item in selected:
        row = c.execute("SELECT * FROM materials WHERE id=?", (item["id"],)).fetchone()
        assert row is not None
        for key in ("source", "published_on", "author", "title", "abstract", "keywords", "body", "source_url"):
            assert row[key] == item[key], (row["id"], key)
        approved = row["id"] in reasons
        if approved:
            assert ".bsky.social/" not in row["source_url"]
        reason = reasons.get(row["id"], REASONS.get(row["id"]))
        if row["id"] in DEFERRED_FIELDS:
            reason = "Direct topic but generated summary is incomplete or has an unmatched quotation; repair with provenance."
        if reason is None:
            reason = "Institutional ownership of bsky.social handle is not independently established, and/or direct China-US topic is absent."
        records.append({"material_id": row["id"], "fingerprint": material_fingerprint(row), "approved": approved,
                        "reason": reason + (" Complete original post only; not the linked article or audiovisual content." if approved else " Pending; original evidence retained."),
                        "source_url": row["source_url"], "body_sha256": hashlib.sha256(row["body"].encode()).hexdigest()})
        rows.append(row)
    manifest = ROOT / "data/reviews/social-next80-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "content_type": "original_social_post", "reviewed_full_post_count": 80}, ensure_ascii=False, indent=2).encode()
    if manifest.exists():
        assert manifest.read_bytes() == raw
    else:
        manifest.write_bytes(raw)
    results = [audit_material(store, row["id"], {**decision, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for row, decision in zip(rows, records)]
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0,
              "formal_full_posts": sum(r["status"] == "pass" for r in results), "pending": sum(r["status"] != "pass" for r in results),
              "duplicates": 0, "restricted": 0, "failed": 0,
              "withdrawn_formal": len((prior_formal & {r['material_id'] for r in results}) - {r['material_id'] for r in results if r['status'] == 'pass'}),
              "new_formal_promotions": len({r['material_id'] for r in results if r['status'] == 'pass'} - prior_formal), "new_http_requests": 0,
              "removed_acquisition_rows": 0, "records": results}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False))
    store.close()


if __name__ == "__main__":
    main()
