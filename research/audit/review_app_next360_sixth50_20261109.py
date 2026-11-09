"""Next 360-URL APP queue, sixth fifty: individual field and topic decisions."""
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
SUMMARIES = {'被奴役国家周讲话向中国等国人民表达支持，将其置于美国关于自由和国际民主变革的公开论述中。': [14567], '战俘与失踪人员纪念日讲话将中国等地近期事件作为其评价共产主义制度变化的依据，并讨论越战及失踪人员问题。': [14569], '记者会否认委托陈香梅向中国领导人传递有关示威或方励之问题的信息，并说明政府使用自身外交渠道的立场。': [14571], '与日本首相会谈后的讲话说明美国既希望保留对华关系，又支持中国人民政治表达诉求的政策立场。': [14572], '蒙大拿记者会回应北京事件后美国企业对华活动问题，区分保留关系、商业联系与全面恢复正常往来的政策。': [14575], '国际教育协会讲话以个人在华经历讨论跨国理解，并介绍学生、学者和专业人士交流对友谊及美国形象的作用。': [14580], '记者会讨论尼克松访华和私下沟通、人权争议、天安门事件及美国对华关系的政策选择。': [14585], '面向报纸编辑的问答解释斯考克罗夫特访华、对华制裁、导弹问题及保持接触的理由，并回应相关公众批评。': [14588], '美法联合记者会回应美国特使访华及祝酒表述争议，并说明布什对中国关系和制裁政策的立场。': [14589], '记者会讨论秘密外交与新闻公开之间的关系，并以对华接触及尼克松时期的秘密访华解释总统外交权限。': [14593], '记者会回应中国学生保护立法、国会表决、秘密使团及电视祝酒影像争议，并讨论交流项目与对华政策效果。': [14594], '记者会回应中国学生出国学习条件的报道，说明其对学生交流的支持及对有关限制表态的评价。': [14596], '商业委员会问答解释保持对华联系的政策，讨论富布赖特计划、和平队、美国之音及公开施压的效果。': [14597], '记者会回应中国改革进展、特使访华和人权问题，说明布什不愿改变接触政策的理由，并讨论民调与政策判断。': [14598], '奥委会晚宴讲话回顾一九七一年乒乓交流，说明体育往来与中美关系突破之间的联系。': [14600], '全国广播协会讲话讨论电视、美国新闻署世界网和美国之音对国际政治的影响，并回顾天安门影像及驻华记者问题。': [14601], '面向报纸编辑的问答回应中国学生安全和移民保护，说明行政命令、延期离境及护照问题的拟议处理。': [14602], '地球日登山队电话讲话向美国、中国和苏联队员致意，将联合登山及清理珠峰活动与和平理解、环境合作联系起来。': [14603], '记者会回应北京事件后美国对华政策及改革进展，讨论交流项目、西藏解除戒严和保留中美关系的理由。': [14606], '记者会讨论中国最惠国待遇决策，回应社论意见、人权信号、香港贸易和维持经济接触之间的权衡。': [14608]}
DEFER = {14562: 'China occurs only in a broad contrast between changes in Poland and anguish in China; specific China policy/communication substance insufficient in this item.', 14563: 'China is a humorous past-posting example about handling Kissinger visits; no substantive China-policy account.', 14564: 'The China reform analogy is attributed to Walesa, while stored author is only George Bush; joint-participant attribution needs review.', 14565: 'Administration policy statement is stored under presidential collection author; release-level institutional authorship requires verification before acceptance.', 14566: 'China and Hong Kong are mentioned among topics, but the president defers the substantive China position to a separate communique; do not substitute that absent text.', 14568: 'Administration policy statement is stored under presidential collection author; release-level institutional authorship requires verification.', 14570: 'China is only one business-council job in an unrelated Brunei nominees career; direct communication-theme relevance unresolved.', 14573: 'Administration policy statement has collection-level author; explicit note Not sent to Hill also requires provenance context before use as public policy statement.', 14574: 'Administration policy statement has presidential collection authorship; verify actual institutional authorship before acceptance.', 14576: 'China is a passing reference to prior joint work with Richard Solomon, without actual China policy content.', 14577: 'Digest only lists a scientific/educational meeting with T.D. Lee; proceedings and release-level author unconfirmed.', 14578: 'Administration policy statement has collection-level presidential author; institutional author attribution unresolved.', 14579: 'Administration policy statement has collection-level presidential author; institutional author attribution unresolved.', 14581: 'Administration policy statement has collection-level presidential author; institutional author attribution unresolved.', 14582: 'China is only a previous posting in a joke about hosting presidential/Kissinger visits.', 14583: 'China only appears in a reporters analogy about a possible Soviet crackdown; answer concerns Soviet policy, not substantive China content.', 14584: 'Digest records only a dinner to discuss Nixons China trip; it does not contain the discussion and authorship is collection-level.', 14586: 'Administration policy statement has presidential collection authorship; verify institutional release author before acceptance.', 14587: 'Explicit Fitzwater statement is stored as George Bush; China only occurs in a meeting-topic list.', 14590: 'Digest lists receipt of diplomatic credentials, including Chinas envoy, without actual remarks; release-level author unresolved.', 14591: 'Explicit Fitzwater statement stored as George Bush; relevant communications-satellite policy retained pending author correction.', 14592: 'Explicit Fitzwater statement stored as George Bush; relevant trade-waiver statement retained pending author correction.', 14595: 'Explicit Fitzwater statement stored as George Bush; retain full divestiture statement pending author-attribution correction.', 14599: 'White House fact sheet is stored as George Bush. Verify institutional attribution; this fact sheet must not be represented as the separate 32-page strategy report.', 14604: 'China is only a nominees birthplace; no substantive China-policy or communication passage.', 14605: 'Source audit fails for missing abstract or keywords. Body lacks a direct China reference and title attributes Fitzwater rather than stored presidential author; no formal promotion.', 14607: 'China/Taiwan are old postings and training entries in an unrelated Mongolia nominees biography.', 14609: 'China only occurs in the name China Institute in America in an appointment reference; speech is domestic civil rights.', 14610: 'Digest mentions China Institute in America only as an appointees current employer; author is collection-level.', 14611: 'China-related military/dialogue passages are Gorbachevs, while author is solely George Bush; verify multi-speaker authorship before inclusion.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-sixth50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-sixth50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-sixth50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next360-sixth50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed sixth fifty working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, press framing, student exchange and communication-institution career records approved individually. Incidental mentions, diaries, and title-versus-collection author conflicts remain pending. No source body was shortened or rewritten."}, ensure_ascii=False, indent=2).encode()
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
