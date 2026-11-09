"""Next 360-URL APP queue, second fifty: individual field and topic decisions."""
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
SUMMARIES = {'里根接受富士电视台采访，向日本受众解释对华友好关系、赵紫阳访美与本人访华计划，并比较对华和对苏政策。': [14366], '里根在日本接受 NHK 采访，说明改善对华关系与保持对台友谊的立场，并回应有关强硬政策和东西方关系的问题。': [14368], '签署拨款法案的声明澄清亚洲开发银行涉台条款，重申承认中华人民共和国政府的政策及与台湾保持非官方关系的立场。': [14369], '面对高中生问答，里根解释访华目的，强调直接沟通、贸易和文化交流，同时说明两岸问题应和平解决及对台友谊。': [14370], '接受美国新闻与世界报道采访时，里根说明对华关系、高技术合作、文化交流和台湾问题，称不能为结交新朋友而抛弃旧朋友。': [14371], '战略与国际研究论坛讲话把访华纳入太平洋关系政策，并介绍民主推广、国家民主基金会和美国之音等国际广播建设。': [14373], '在塔科马与雇员交流时，里根说明访华行程，介绍贸易、投资、避免双重征税及参访合资企业与大学的计划。': [14377], '赴华途中在夏威夷讲话，里根回顾建交、经贸和文化协议，说明对华访问的和平友好目标及美国太平洋利益。': [14379], '离开夏威夷赴华时，里根说明行程和两国关系历程，表示将直接向中国人民传达美国的尊重友谊并讨论共同利益。': [14380], '访华后在费尔班克斯讲话，里根回顾同中国领导人及学生接触，解释制度差异、经贸合作与和平共处的看法。': [14387], '在太平洋杂志书面问答中，里根回应太平洋岛国同中国等国的关系及文化交流，表示独立国家有选择朋友的权利。': [14390], '小企业颁奖讲话借访华见闻描述中国私人经营与激励措施，并把这些观察同其国内经济政策论述联系起来。': [14395], '国会共和党筹款晚宴讲话把访华后的经贸、技术和科学交流协议作为外交成果，强调虽有制度差异仍能合作。': [14397], '记者问答回应访华言论遭删减的报道，里根解释其在中国比较美国与苏联政策的说法，并为相关措辞辩护。': [14400], '出口颁奖讲话说明访华等出访的贸易推广目的，自称在海外扮演推销员，并重申开放市场和反保护主义立场。': [14402], '全国广播讲话回顾亚洲与欧洲出访，称访华达成的协议有助于美国出口及中国经济现代化。': [14403], '国际青年年委员会讲话回顾在复旦大学与中国学生交流，强调青年相互了解、美国形象和跨国青年接触的意义。': [14407], '独立日活动讲话回顾向复旦学生介绍美国争论自由、平等与民主的经历，并陈述其对学生反应的观察。': [14409]}
DEFER = {14362: 'China Sea is an old bank-management territory in a nominee biography, without substantive China communication policy.', 14363: 'Multi-item White House digest includes a visit announcement; single-release authorship and publication boundaries remain unresolved.', 14364: 'China/Taiwan office and Hong Kong posts are past career entries for a Malaysia ambassador nomination; direct thematic context unresolved.', 14365: 'Diary names a Chinese foreign minister meeting without its full discussion or verified single-release authorship.', 14367: 'Body contains complete Nakasone and Reagan addresses while author field names only Reagan; multi-speaker authorship needs correction and evidence.', 14372: 'White House digest summarizes a Zhao visit invitation among unrelated entries; authorship/release boundaries need clarification.', 14374: 'Digest lists Scowcroft visit discussion without the actual China-policy discussion; release authorship unresolved.', 14375: 'China is only a country in a list of foreign visitors inspecting automobile production.', 14376: 'Roundtable includes substantive statements by multiple named industry speakers while author field is only Reagan; full authorship and source scope need correction.', 14378: 'Short White House digest lists departure and an unrelated funeral designation; authorship/release boundaries unresolved.', 14381: 'Visit itinerary digest has unverified individual-release authorship and is not the full meeting proceedings.', 14382: 'Diary summarizes multiple China meetings but does not supply full meeting texts; authorship and release boundaries unresolved.', 14383: 'Digest gives visit itinerary rather than actual meeting content; authorship and release boundaries unresolved.', 14384: 'Travel diary gives archaeological-tour itinerary; full release authorship and direct communication-theme scope require review.', 14385: 'China is merely the Presidents location while writing a letter about the Ku Klux Klan.', 14386: 'Digest lists agreements and itinerary without full agreement texts; single-release authorship needs verification.', 14388: 'Body explicitly attributed to press secretary Speakes while material author is Reagan; author-source mismatch requires correction.', 14389: 'Pope and Reagan both speak, but author field names Reagan only; China references mostly visit transitions, direct scope uncertain.', 14391: 'Brief opening mentions previous China trip, then the substantive radio address concerns domestic waste/fraud; direct scope requires more review.', 14392: 'Digest lists a Chinese trade-minister meeting without its content; release authorship unresolved.', 14393: 'Digest names Kirkpatrick travel plan without actual China-policy discussion; release authorship unresolved.', 14394: 'Only brief introduction recalls China trip, while substantive address concerns Central America; direct thematic scope requires further review.', 14396: 'China is a jet-lag joke and a travel transition before a papal meeting; no substantive China communication discussion.', 14398: 'Digest only lists a cabinet discussion of China trip, not the discussion itself; release authorship unresolved.', 14399: 'China trip is a passing remark about applauding the audience, without substantive China-policy content.', 14401: 'China is only a comparison about crowd size in a Michael Jackson drunk-driving ceremony.', 14404: 'Digest merely lists a Chinese defense-minister meeting; actual discussion and release authorship not supplied.', 14405: 'China is only a geographical boundary; lower-case voice of America is a general metaphor, not evidence of VOA broadcasting or China policy.', 14406: 'China references concern ancient Sri Lankan relations and pilgrims rather than post-1949 US-China communication.', 14408: 'Only a brief generic claim that Asian trips improved relations, within domestic party-policy remarks; more direct thematic context required.', 14410: 'China appears only in an election-campaign joke about meeting a billion people.', 14411: 'Diary only lists a trade-mission meeting without substantive text; single-release authorship unresolved.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-second50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-second50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-second50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next360-second50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed second fifty working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, media explanation and communication-institution career records approved individually. Birthplaces, incidental jobs, title-only bibliographies, report-directory items and ambiguous multi-speaker attribution remain pending."}, ensure_ascii=False, indent=2).encode()
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
