"""Next 360-URL APP queue, final forty-eight: individual field and topic decisions."""
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
SUMMARIES = {'伦敦北约峰会后记者会回应方励之获准离境和人权双重标准指责，说明美国对华公开表态与制裁政策。': [14613], '尼克松图书馆落成讲话回顾一九七二年访华，评价这一外交突破在结束隔绝及中美关系中的意义。': [14618], '面向农业广播机构的问答讨论最惠国待遇、人权与对华接触，并解释中国在海湾战争联合国决议中的作用。': [14632], '宣布提名芮效俭为美国驻华大使，并介绍其中美外交、中国事务及亚洲岗位经历。': [14634], '记者问答说明布什支持继续给予中国最惠国待遇，强调保持接触、推动变化与中国在海湾战争中的合作。': [14635], '耶鲁毕业典礼讲话系统解释对华接触与最惠国待遇政策，讨论贸易、学生交流、人权及美国思想和示范的影响。': [14639], '记者会回应最惠国待遇争论，说明保持对华接触及支持改革群体的理由，并讨论与国会和盟国沟通。': [14640], '面向亚太裔群体的讲话阐述贸易、学生交流和美国理念对中国的影响，并说明最惠国待遇与人权政策。': [14646], '致参议院咨文介绍北太平洋海洋科学组织公约，说明中国等五国参与及科学数据、研究和学术交流机制。': [14651], '与加拿大总理联合记者会回应美国对苏联与中国采取不同做法的质疑，说明经济接触和人权鼓励的对华政策。': [14654], '亚洲协会讲话阐述美国亚太政策，讨论中国在朝核问题中的作用、接触政策、政治制度与经济合作。': [14658], '珍珠港纪念讲话将中国等亚洲国家置于民主与自由发展的预期中，说明美国对地区政治变化的公开判断。': [14659]}
DEFER = {14612: 'Explicit Fitzwater statement is stored as George Bush; retain Fang Lizhi release account pending author-attribution correction.', 14614: 'Explicit Fitzwater statement is stored as George Bush; release-level author attribution unresolved.', 14615: 'Joint seven-country/European Community declaration is stored under George Bush alone; verify institutional/coauthor attribution before acceptance.', 14616: 'Joint summit declaration has only presidential collection author; China is chiefly a Montreal Protocol example, not a specific China communication-policy account.', 14617: 'China-policy response is directly relevant but stored/source-extracted passage contains repeated unusual sequences such as ÿ7E; resolve transcription/encoding fidelity before claiming complete clean original text.', 14619: 'China only occurs in a reporters list of conservative complaints in a Supreme Court nomination discussion.', 14620: 'China only occurs in a brief arms-sales fact in an Iraq deployment address; specific US-China communication-theme scope requires further assessment.', 14621: 'China is a humorous past-posting anecdote about hosting visits, not substantive China policy.', 14622: 'China dialog passages are spoken by Gorbachev, while author is solely George Bush; multi-speaker attribution requires review.', 14623: 'Administration policy statement is stored under presidential collection author; verify actual institutional release attribution.', 14624: 'China appears in Columbus and ancient-ideogram analogies, not substantive post-1949 China communication content.', 14625: 'Administration policy statement has presidential collection author; verify institutional release authorship before acceptance.', 14626: 'China occurs in a short coalition-unity claim in a Gulf troop address; China-specific communication-theme scope requires fuller assessment.', 14627: 'China is briefly named in a coalition-unity answer; China-specific policy substance is too limited for this formal decision.', 14628: 'China occurs in a short coalition-unity reference during a campaign speech; more direct China communication relevance unestablished.', 14629: 'Explicit Fitzwater export-control statement is stored as George Bush; author conflict unresolved.', 14630: 'China is the origin of a winners parents in a domestic academic-awards story; direct international communication-theme relevance unestablished.', 14631: 'China-related offices occur as previous positions in a Pakistan nominees career; no current China policy or communication program described.', 14633: 'Explicit Fitzwater satellite-export statement is stored as George Bush; actual release author needs correction.', 14636: 'China occurs only in an unanswered final reporters question about MFN; do not infer a missing answer.', 14637: 'China is a generic example in a students question session about the burdens and aims of being president; no specific China policy content.', 14638: 'Explicit Fitzwater export-control statement is stored as George Bush; verify actual release author.', 14641: 'White House fact sheet has presidential collection author; institutional release attribution needs verification.', 14642: 'Letter explicitly states the China determination and reasons are transmitted separately; this letter cannot substitute for that absent determination.', 14643: 'Digest merely lists a Senate discussion of China-US relations without its proceedings; release-level authorship unresolved.', 14644: 'Digest only lists a House discussion on China without actual content; release-level author unresolved.', 14645: 'China is a language-learning comparator in domestic education remarks; no substantive China-directed broadcasting content established.', 14647: 'Explicit Fitzwater trade-constraint statement is stored as George Bush; retain pending actual author verification.', 14648: 'Digest lists China-trade meeting and a public diplomacy appointment without the China proceedings or evidence that that appointment addresses China.', 14649: 'China passages are regional-background comments by Roh, whereas stored author is George Bush; multi-speaker attribution unresolved.', 14650: 'Administration policy statement has presidential collection author; verify institutional release authorship.', 14652: 'MFN appears in one brief question and reply deferring substantive Cabinet discussion; actual discussion absent.', 14653: 'Title explicitly says Excerpt of a Statement and identifies Fitzwater; incomplete statement and stored author conflict preclude full-text acceptance.', 14655: 'China only appears in a question and Majors list of unfinished discussion topics; no substantive China answer.', 14656: 'China is only Bushs former post in the visiting monarchs compliments; author attribution and thematic relevance require review.', 14657: 'China and intelligence posts are previous career entries in a Defense appointment; direct communication-theme substance unestablished.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-tail-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-tail-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 48
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-tail-review-20261109.sqlite3"
    if not backup.exists():
        b = sqlite3.connect(backup);c.backup(b);b.close()
    prior = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    records, changes = [], []
    adapter = GovernmentArticleAdapter()
    for observed in selected:
        row = c.execute("SELECT * FROM materials WHERE id=?", (observed["id"],)).fetchone()
        for field, reading_key in [(key, key) for key in ("source", "published_on", "author", "title", "source_url", "abstract", "keywords", "body")]:
            assert row[field] == observed[reading_key]
        assert hashlib.sha256(row["body"].encode()).hexdigest() == observed["body_sha256"]
        approved = row["id"] in summaries
        if approved:
            source = _source_row(s, row["id"])
            result, metadata_ids = _extract_existing(s, source, adapter)
            parsed = result.get("material")
            assert parsed and parsed.body == row["body"]
            assert hashlib.sha256(Path(source["evidence_path"]).read_bytes()).hexdigest() == source["content_sha256"]
            keywords = "; ".join(dict.fromkeys(m.group() for t in TERMS if (m := re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", row["body"], re.I))))
            assert keywords
            abstract = "据正文整理：" + summaries[row["id"]]
            fields = json.loads(c.execute("SELECT field_sources FROM material_verifications WHERE material_id=?", (row["id"],)).fetchone()[0])
            fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
            mid, created = s.add_verified_material(source["candidate_id"], row["evidence_id"], replace(parsed, abstract=abstract, keywords=keywords),
                                                 abstract_origin="derived", field_sources=fields, metadata_evidence_ids=metadata_ids)
            assert not created and mid == row["id"]
            changes.append({"material_id": mid, "previous_fields": dict(row), "new_abstract": abstract, "new_keywords": keywords})
            row = c.execute("SELECT * FROM materials WHERE id=?", (mid,)).fetchone()
        records.append({"material_id": row["id"], "fingerprint": material_fingerprint(row), "approved": approved,
                        "reason": "Individual topic/field review: " + (summaries[row["id"]] if approved else DEFER[row["id"]]),
                        "source_url": row["source_url"], "body_sha256": observed["body_sha256"]})
    manifest = ROOT / "data/reviews/app-next360-tail-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed final forty-eight working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, press framing, student exchange and communication-institution career records approved individually. Incidental mentions, diaries, and title-versus-collection author conflicts remain pending. No source body was shortened or rewritten."}, ensure_ascii=False, indent=2).encode()
    assert not manifest.exists();manifest.write_bytes(raw)
    results = [audit_material(s, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    now = {r["material_id"] for r in results if r["status"] == "pass"}
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0,
              "formal_fulltexts": len(now), "new_formal_promotions": len(now - prior), "pending": len(results) - len(now),
              "withdrawn_formal": len((prior & {r["material_id"] for r in results}) - now),
              "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests_for_offline_review": 0,
              "field_corrections": len(changes), "backup": str(backup.relative_to(ROOT)), "records": results}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2));s.close()


if __name__ == "__main__":
    main()
