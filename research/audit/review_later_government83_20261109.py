"""Individual later-period source/field decisions using preserved original bytes."""
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
    "报道美国提高对华关税、中方回应及双方贸易谈判。": [3],
    "报道美国官员对中美贸易谈判进展、关税安排与中国经济政策的表态。": [4],
    "报道美国推迟对部分中国商品加征关税的决定，并讨论消费者、农业和贸易谈判。": [6],
    "演讲说明美国对华政策与外交，并以气候合作等问题讨论双方关系。": [45],
    "记录中美战略与经济对话开幕发言，涉及战略沟通、合作与分歧。": [46, 59],
    "讲话介绍中美战略与经济对话战略轨道会议的气候、能源等合作议题。": [60],
    "材料支持给予中国永久正常贸易关系，并将中国加入世界贸易组织与经济、改革和开放相联系。": [77, 126, 127, 128, 203, 204, 205],
    "报道天安门事件周年期间的安保、信息限制及有关政治表态。": [84, 2451, 2454],
    "社论在天安门事件二十周年之际回顾抗议和镇压，并讨论公民自由。": [85],
    "材料讨论对华最惠国或正常贸易待遇，并说明接触政策与美国利益的联系。": [123, 190, 192, 193, 194, 195, 197],
    "讲话介绍中美领导人会谈议题与两国合作、分歧。": [124, 131, 133],
    "行政命令规定1994年延长中国最惠国待遇的条件。": [125],
    "声明欢迎接纳中国和台湾加入世界贸易组织的决定，并阐述预期经贸影响。": [129],
    "问答回应亚太安全政策、中国威胁说与中美关系的问题。": [130],
    "演讲及问答讨论中国的发展、改革与中美关系。": [132],
    "政策说明讨论美国与亚洲的关系，并阐述对华经贸、人权与对话政策。": [134],
    "文件就延续中国最惠国待遇及相关法定豁免作出说明。": [191, 196],
    "讲话讨论全球经济一体化，并提及中国的发展、贸易与环境问题。": [202],
    "新闻稿介绍VOA对鲍彤的采访、相关政治表态与播出安排；该稿不是完整采访文字稿。": [244],
    "报道天安门事件三十周年期间的媒体管制、网络讨论与纪念活动。": [245],
    "报道柬埔寨裔摄影师在纽约举办天安门事件影展，并转述其采访内容。": [253],
    "记者手记讨论天安门事件周年期间外国记者在北京采访所遇到的限制与压力。": [256],
    "报道美国要求中国释放周年纪念前被拘押批评者，并转述中国外交部回应。": [257],
    "报道VOA对Gemini中文答复的测试及美国议员、专家对其涉华回答的批评。": [2138],
    "报道皮尤有关美国公众对华看法的调查，并讨论受访者差异与政策关切。": [2139],
    "文章分析中国官方媒体对美国大选的叙述，包括新华社视频和《环球时报》报道。": [2140],
    "报道美国与日韩就应对信息失实问题达成的合作，并转述专家与中国驻美使馆的不同说法。": [2141],
    "报道台湾安全部门关于涉华网络信息活动的说法及其对台美关系的担忧。": [2142],
    "报道VOA与Doublethink Lab对X平台涉华账号的调查，并讨论美国大选前的信息叙述。": [2143],
    "文章整理VOA中文受众对1989年事件的回忆，其中包含一名天津学生的叙述。": [2452],
    "报道蓬佩奥在尼克松基金会的演说及其对美国长期对华接触政策的批评。": [2453],
    "报道缅甸放松媒体审查在中国引起的讨论，并比较中国媒体的反应。": [2455],
    "报道习近平访美前中美围绕网络安全与商业秘密的争议。": [2458],
    "报道美国驻华使馆知乎问答被删除后对社交媒体公共外交的回应。": [2459],
    "文章讨论中美网络安全协议的不同解释及专家对其效果的质疑。": [2460],
}
DEFER = {
    **{mid: "VOA archive migration-date conflict: page date in October/November 2009 is not established as original publication day; original dates in title/body need independent resolution." for mid in [7, 8, 9, 10, 11, 12, 13, 14, 2449, 2450]},
    **{mid: "Explicit speaker names/roles versus stored '未注明' need an individual author-provenance decision; do not guess missing authors." for mid in [76, 160, 161, 207, 208, 209, 210, 291, 2573, 2574, 2575, 2576]},
    **{mid: "Body includes WATCH, related-reading or documentary promotional text; clean and verify same-page boundaries before formal export." for mid in [252, 255, 2456, 2457]},
    58: "Transcript starts at the first question; resolve whether opening remarks are absent from the source or omitted by extraction.",
    163: "General WTO agenda with only a brief China example; direct topic relationship not approved.",
    199: "Joint statement refers to Attachments 1, 2 and 3 that are absent from the saved body; resolve appendix completeness.",
    298: "General VOA history contains no China-specific discussion; direct dissertation relationship remains unresolved.",
}
TERMS = ("China", "Chinese", "United States", "U.S.", "Taiwan", "Tiananmen", "Hong Kong", "Xinjiang", "WTO", "World Trade Organization", "MFN", "PNTR", "trade", "tariffs", "human rights", "censorship", "public opinion", "VOA", "Beijing", "disinformation", "cybersecurity", "Gemini", "strategic communication")


def main():
    report_path = ROOT / "data/reviews/later-government83-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/later-government83-reading-20261109.json").read_text(encoding="utf-8"))
    assert len(selected) == 83
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-later-government83-review-20261109.sqlite3"
    if not backup.exists():
        b = sqlite3.connect(backup);c.backup(b);b.close()
    prior_formal = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    records, changes = [], []
    adapter = GovernmentArticleAdapter()
    for observed in selected:
        row = c.execute("SELECT * FROM materials WHERE id=?", (observed["id"],)).fetchone()
        for key in ("source", "published_on", "author", "title", "source_url"):
            assert row[key] == observed[key]
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
                        "reason": "Individually reviewed topic/fields; " + (summaries[row["id"]] if approved else DEFER[row["id"]]),
                        "source_url": row["source_url"], "body_sha256": hashlib.sha256(row["body"].encode()).hexdigest()})
    manifest = ROOT / "data/reviews/later-government83-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "new_network_requests": 0}, ensure_ascii=False, indent=2).encode()
    assert not manifest.exists();manifest.write_bytes(raw)
    results = [audit_material(s, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    now = {r["material_id"] for r in results if r["status"] == "pass"}
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "reviewed_records": len(results), "new_candidates": 0,
              "formal_fulltexts": len(now), "new_formal_promotions": len(now - prior_formal), "pending": len(results) - len(now),
              "withdrawn_formal": len((prior_formal & {r["material_id"] for r in results}) - now),
              "duplicate_discoveries": 0, "restricted": 0, "http_failed": 0, "new_http_requests": 0,
              "field_corrections": len(changes), "backup": str(backup.relative_to(ROOT)), "records": results}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2));s.close()


if __name__ == "__main__":
    main()
