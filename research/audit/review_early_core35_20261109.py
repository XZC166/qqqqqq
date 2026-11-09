"""Next APP batch first-50 review: individually judged topic and field evidence."""
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
 '接受哥伦比亚广播公司采访时，尼克松讨论在对华及对苏接触中提出越战战俘问题的安排。': [55],
 '记者会谴责中国军队对示威者使用武力，并解释军事交流限制、保持双边联系及推动改革的政策取舍。': [56],
 '周年声明回顾天安门事件，强调表达、新闻和结社自由，并说明美国对中国恢复改革与双边关系发展的期待。': [57],
 '朝鲜局势声明宣布军事支援、派第七舰队阻止攻击台湾，并说明台湾未来地位和两岸军事行动的政策。': [68],
 '全国讲话宣读中美建交公报，解释关系正常化的和平目标、对台非官方关系及邓小平访美安排。': [94],
 '美国声明宣布承认中华人民共和国、终止与台湾的外交及条约关系，并说明继续非政府往来的安排。': [95],
 '建交讲话后的白宫简报讨论对华谈判、对台关系、国会反应、贸易文化交流及对外公开说明。': [96],
 '记者会回应中国领导层、天安门事件、学生签证及制裁选择，说明继续接触与人权关切之间的政策考虑。': [98],
 '记者会讨论中美联系和中国推迟和平队英语教学项目，表达保持美国人与中国接触的立场。': [99],
 '美法联合记者会回应北京示威，表示支持言论、集会和新闻自由，并呼吁克制及和平解决。': [100],
 '共和党纲领的亚洲部分支持台湾安全和台湾关系法，同时主张对华经贸往来、市场改革及减少政治压制。': [170],
 '全国讲话宣布接受访华邀请，说明基辛格与周恩来会谈及通过关系正常化促进和平的目标。': [223],
 '联合声明公布尼克松访华于 1972 年 2 月 21 日开始。': [224],
 '上海公报记述双方会谈，分别表达两国立场，并提出关系正常化、人员往来与地区和平等原则。': [225],
 '访华启程讲话将此行称为和平之旅，强调双方存在分歧仍应寻找共同点并避免战争。': [226],
 '亚洲政策演说讨论中国对外行动、结束中国大陆人民孤立与鼓励和平合作之间的政策关系。': [234],
 '否决中国移民救济法案的备忘录说明对中国学生及其他在美人员提供行政保护，并主张保留教育和经济联系。': [246],
 '邓小平访美欢迎仪式讲话强调现代化、文化贸易交流、人民相互认识及友好合作的意义。': [247],
 '卡特与邓小平对记者介绍会谈成果，表示应通过定期磋商和各领域往来增进理解与友谊。': [248],
 '邓小平访美联合新闻公报列举科技、文化、教育和领事合作协议，并公布进一步谈判及互访安排。': [249],
 '复旦大学演说介绍教育交流和富布赖特项目，主张通过知识、思想及人员往来发展中美关系。': [251],
 '记者会说明美国对台湾海峡军事调动的判断，重申反对使用武力及有关台湾防卫的政策。': [271],
 '艾奇逊演说讨论中国国民党政府失败的原因、亚洲变革与美国政策，回应关于美国对华援助的争论。': [283],
 '记者会把中国对北越的支持纳入美国越战政策叙事，并回应中国可能作何反应的问题。': [284],
 '美方与陈诚会谈后的联合声明重申双边关系，讨论中国在联合国的代表权及反对北京入联的立场。': [285],
 '记者会介绍访华安排和对中国领导人的认识，并回应围绕中国的政策及信息交流问题。': [290],
 '记者会宣读美国关于中国领土完整与台湾地位的声明，并表示当时不寻求台湾军事基地或介入中国内战。': [2578],
}
DEFER = {
 54:'485,000-character annual report includes a contents list and multiple major sections; remaining whole-report boundaries and internal completeness review retained pending.',
 67:'Korean War conference has no explicit China/Taiwan reference in its body; direct dissertation linkage requires further review.',
 69:'Korean War address has no explicit China/Taiwan reference in its body; direct dissertation linkage requires further review.',
 97:'Taiwan memorandum dated December 30 but Federal Register filing January 2; publication day not verified.',
 101:'Title explicitly says statement by Press Secretary Fitzwater, while author field is uncredited; byline extraction requires source review before approval.',
 168:'Memorandum explicitly says determination is to be published in Federal Register; signing/filing day is not sufficient publication-day evidence.',
 250:'Cultural accord has explicit signatures, but header day may be signature day; verify publication day independently before promotion.',
 272:'Paired-toast title while source main text contains only Nixon toast; complete-document boundary needs clarification.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/early-core35-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/early-core35-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 35
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-early-core35-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/early-core35-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed existing early-government records individually reviewed. Whole original body re-extracted and byte-for-byte compared; topical sections and field evidence reviewed for each decision. No keyword rule authorizes later records. Entire annual report pending further boundary/completeness review; date/author ambiguities retained pending."}, ensure_ascii=False, indent=2).encode()
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
