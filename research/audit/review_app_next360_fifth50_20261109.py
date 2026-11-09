"""Next 360-URL APP queue, fifth fifty: individual field and topic decisions."""
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
SUMMARIES = {'东京记者会说明布什访华目标、人权立场及中美文化、贸易和战略关系，并回应中苏关系缓和问题。': [14513], '北京教堂讲话回顾个人在华经历，以宗教、家庭和社区纽带说明中美友谊，并介绍学生、文化和科技交流。': [14514], '在首尔会见卢泰愚后的讲话回顾访华和朝鲜半岛议题，说明美国对韩国接触中国等国家的外交政策的支持。': [14515], '亚洲行程结束后的公开讲话介绍与中国领导人讨论中苏关系、柬埔寨及地区合作的情况，并阐述美国在亚洲的角色。': [14516], '面向小企业组织的讲话以中国变化说明经济相互依存，并援引香港、台湾等经济体讨论竞争力和税收政策。': [14519], '面向威尔逊中心的讲话将中国市场化变化、国际思想和技术交流同美国外交与经济竞争的机会联系起来。': [14521], '记者会回应访华期间人权和异议人士问题，说明布什对私下交涉、公开表态及外交效果的看法。': [14522], '公布提名詹姆斯·罗德里克·李洁明为美国驻华大使，并介绍其中国事务、情报和东亚外交任职经历。': [14523], '休斯敦讲话将中国变化及中苏关系与美国对苏政策、国际缓和和维护和平的政策判断联系起来。': [14524], '与宗教团体座谈时，布什比较其两次在华经历，讨论中国的家庭、宗教活动与政治制度。': [14526], '面向高中生的问答说明国际学生交流对美国外交及相互理解的作用，并联系在华经历讨论教育交流。': [14528], '总统决定确认沙特从中国购买的中程弹道导弹未装备生物、化学或核弹头，并授权在联邦公报公布该认定。': [14529], '致国会领导人的信解释有关中国制导弹的军售限制，并通报沙特相关弹头状况的总统认定。': [14530], '商会讲话支持中国经济改革，将市场激励和私人所有制的国际扩展同美国自由企业政策联系起来。': [14533], '会见加拿大总理后的记者问答回应中国学生示威、新闻自由和民主诉求，并说明布什的公开立场。': [14534], '古巴独立日讲话引用电视呈现的中国示威等事态，阐述美国关于民主和政治变革的公开论述。': [14540], '州长晚宴讲话以天安门广场学生示威及其他地区变化，说明其对民主发展和美国制度示范作用的判断。': [14541], '商业圆桌会议讲话回应北京事件和坦克前个人的电视影像，说明对军事供应采取措施及保留商业联系的理由。': [14547], '诺曼底登陆纪念声明将中国近期事件、波兰选举与盟国合作联系起来，阐述美国推进民主与自由的立场。': [14549], '驻沙特大使提名公告介绍弗里曼在尼克松访华翻译、国务院中国事务及美国新闻署等岗位的任职经历。': [14551], '高中毕业典礼讲话讨论中国学生示威，并以坦克前个人的新闻影像阐释勇气和自由等公共价值。': [14552], '华尔街日报周年晚宴讲话评价该报对中国的历史报道及近期北京事件报道，并讨论新闻职业责任。': [14554], '欢迎澳大利亚总理的讲话提出就中国近期事件开展盟国磋商，并介绍美澳地区合作议题。': [14560]}
DEFER = {14512: 'Digest lists travel and meetings but not the actual China meetings or presidential statements; release-level author attribution remains unresolved.', 14517: 'Title explicitly attributes statement to Press Secretary Fitzwater whereas stored author is George Bush; resolve source-level author mismatch before formal acceptance.', 14518: 'China occurs in a trip itinerary and generic description of meetings; no specific China-policy or communication position established in the China passages.', 14520: 'China mainly illustrates a recent trip and educational change; direct topic substance beyond generic educational comparison requires further assessment.', 14525: 'China is only a students recent travel background in an unrelated answer about schools.', 14527: 'China appears only in a historical opium-war analogy in domestic drug-policy questions; no substantive post-1949 China communication content.', 14531: 'White House institutional statement is stored under George Bush collection authorship; verify explicit institutional author attribution before acceptance.', 14532: 'Digest only lists meeting with ambassador Lilley without proceedings; individual-release authorship unresolved.', 14535: 'China is mainly a personal church/family reminiscence and proverb in a heritage ceremony; direct international communication-theme relevance needs further assessment.', 14536: 'China appears only as birthplace and Chinese-American organization name in a Nepal nominees biography.', 14537: 'Chinas integrity appears in one broad Soviet-policy vision clause; insufficient specific China discussion for this batch.', 14538: 'China only occurs in a retrospective list of conflicts around the presidents graduation in 1948, outside the selected post-1949 theme.', 14539: 'Explicit Fitzwater press-secretary statement has George Bush stored as author; author mismatch unresolved despite direct topic relevance.', 14542: 'Explicit Fitzwater statement has George Bush stored as author; must resolve author attribution before accepting this relevant VOA/journalist-access account.', 14543: 'China is a past-posting anecdote about the burdens of presidential visits, not substantive China-policy content.', 14544: 'China is one prior posting in general praise of the Foreign Service; the USIA reference does not establish China-specific program content.', 14545: 'China is only a previous posting mentioned in an anecdote about hosting visits.', 14546: 'China is listed among meeting topics without actual policy content or discussion transcript for that topic.', 14548: 'Digest lists a meeting with Chinese students without actual discussion; release-level author unresolved.', 14550: 'China is a prior law-teaching experience in one fellows biography, without substantive China policy or communication account.', 14553: 'China occurs only in a generic opening expression of concern; substantive speech is domestic national service.', 14555: 'China appears in past academic and advisory jobs in a nominees biography; no direct communication-policy account established.', 14556: 'Digest lists a congressional meeting on China without actual proceedings; individual-release author unresolved.', 14557: 'Explicit Fitzwater statement has George Bush stored as author; China also merely appears in a list of discussed issues.', 14558: 'Explicit Fitzwater statement has George Bush stored as author; relevant bilateral coordination content retained pending correct attribution.', 14559: 'China is only an old delegation visit in an unrelated nominees biography.', 14561: 'China is mentioned only as generic difficulties in a closing global contrast; main speech concerns Eastern Europe without substantive China discussion.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next360-fifth50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next360-fifth50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next360-fifth50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next360-fifth50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed fifth fifty working records of next 360-URL APP queue reviewed individually. Complete body re-extracted exactly from original raw evidence and field attribution checked. Explicit China-policy, trade, press framing, student exchange and communication-institution career records approved individually. Incidental mentions, diaries, and title-versus-collection author conflicts remain pending. No source body was shortened or rewritten."}, ensure_ascii=False, indent=2).encode()
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
