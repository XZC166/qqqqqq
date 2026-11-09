"""Individually read complete original social posts; never linked article or video fulltexts."""
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
 '纽约时报意见账号引述 Eric Schmidt 与 Selina Xu，主张美国在科技与全球领导地位竞争中重新审视自身领先的假定。': [2881],
 'CSIS 帖文称隔离、封锁或入侵等台湾危机可能扰乱台湾海峡贸易。': [2882],
 '美联社账号发布 TikTok 签署协议、向美国投资者出售美国业务的消息。': [2918],
 'CSIS 帖文认为日本仍需加强国家安全韧性，以应对中国或其他对手可能利用的薄弱环节。': [3249],
 'CSIS 帖文称特朗普政府撤销东南亚能源转型支持计划后，中国可能填补扩大的资金缺口。': [3251],
 'CSIS 帖文将中国在黄海的设施与针对韩国船只的行动描述为渐进主权策略，并提出美国和韩国应如何应对的问题。': [3257,3266],
 'CSIS 帖文引述 Clayton Seigle，讨论美国扣押油轮与中国从受制裁供应国进口石油之间的政策关联。': [3258],
 'CSIS 帖文称中国掌握无人机战争所需关键材料，并主张美国国防工业加强供应链韧性。': [3262,3267],
 'CSIS 帖文将北京对日本的反应描述为政府信号与全球外交行动，并认为仍有升级空间。': [3264],
 'CSIS 帖文将中国官员和专家对日本防务政策的担忧，与中日军机雷达事件及紧张局势相联系。': [3268,3271],
 'CSIS 帖文讨论美国缺席 COP30 与中国等经济体在化石燃料转型议程中争取影响力之间的关系。': [3273],
 'CSIS 帖文引述南非将中国视为制衡美国主导的西方秩序的力量这一判断。': [3275],
 'CSIS 帖文介绍其亚洲海事透明倡议关于中国南沙据点电子战及情报监视侦察系统的卫星图像研究。': [3276],
 'CSIS 帖文介绍邀请专家提出印太地区对华升级风险管理策略的报告。': [3277],
 'CSIS 帖文认为国际体系竞争将取决于美国盟友网络和中俄朝伊之外的国家。': [3279],
 'CSIS 帖文将国际体系竞争描述为美国及伙伴建立的规则秩序与更有利于中俄的规范之间的竞争。': [3282],
 'CSIS 帖文称中俄正在劝说全球南方国家抵制美国及其建立的国际秩序，并介绍相关政策建议。': [3283],
 'CSIS 帖文以中俄贸易规模说明中国、俄罗斯、伊朗和朝鲜之间的经济实力差异。': [3286,3299],
 'CSIS 帖文讨论全球多数国家对国际规则和机构的支持，以及其遵循美国或中俄规范的问题。': [3287],
 'CSIS 帖文引述 Jane Nakano，认为中国由接受气候融资转向提供融资可显示气候合作领导作用。': [3288],
 'CSIS 帖文介绍全球阵营取向指数，称其按年比较 2008 至 2024 年各国相对美国、中国和俄罗斯的取向。': [3292,3295],
 'CSIS 帖文引述中俄对金穹系统战略稳定影响的担忧、对可行性的怀疑及俄罗斯关于反制的判断。': [3293],
 'CSIS 帖文称中俄领导人与外交官自 2022 年起近五十次接触，并据此比较中俄朝伊合作强度。': [3296],
 'CSIS 帖文比较朝鲜、伊朗和中国对俄罗斯战争的支持形式，并评价中国军民两用出口及经济支持的作用。': [3297],
 'CSIS 帖文将中国增加从俄罗斯和伊朗采购石油，描述为在西方制裁背景下提供经济支持。': [3298],
 'CSIS 帖文称中俄伊朝有意挑战美国及西方影响力，并介绍其合计经济和军事力量。': [3300],
 'CSIS 帖文将美沙矿产合作描述为减少中国供应链影响力的矿山至磁体路径。': [3302,3311],
 'CSIS 帖文讨论全球多数国家对规则和机构的重要性，并介绍关于美国和中国领导作用取向的数据分析。': [3303],
 'CSIS 帖文引述 Lauryn Williams，主张美国专家借鉴中国经验参与美国军事演变的讨论。': [3304,3306],
 'CSIS 帖文转述中俄分析者对美国金穹系统战略优势与二次打击生存能力影响的判断。': [3308],
 'CSIS 帖文引述对马尼拉安全判断的分析，称东盟谈判缓慢可能不足以应对南海安全风险。': [3310],
}
MEDIA_DESCRIPTIONS = {2890,2897,3177,3215,3242,3245,3247,3250,3253,3254,3260,3261,3265,3274,3278,3285,3289,3290,3291,3294,3305,3307,3309,3312}
EVENT_PREVIEWS = {3252,3255,3263,3281}
DEFER = {mid: 'Audiovisual or podcast promotional description; not a full transcript. Retained outside formal fulltext.' for mid in MEDIA_DESCRIPTIONS}
DEFER.update({mid: 'Event invitation or preview; no substantive proceedings or full transcript verified.' for mid in EVENT_PREVIEWS})
DEFER.update({
 2883: 'Journal abstract-like promotional post; institutional ownership of bsky.social handle lacks independent evidence.',
 2884: 'Institutional ownership of bsky.social handle lacks independent evidence.',
 2932: 'South China Sea is only crash geography; no substantive China-US discourse relationship established.',
 3220: 'Ancient Sun Tzu quotation; a direct modern China-related argument is absent from this post.',
 3237: 'Turkey geopolitical balancing; direct US-China dissertation relevance insufficiently established.',
 3272: 'Turkey geopolitical balancing; direct US-China dissertation relevance insufficiently established.',
 3280: 'UAE geopolitical balancing; direct US-China dissertation relevance insufficiently established.',
 3284: 'Turkey geopolitical balancing; direct US-China dissertation relevance insufficiently established.',
 3301: 'Explicit thread introduction; broader thread boundaries require review. Retained without presenting a complete thread.',
})
TERMS = ("China", "Chinese", "United States", "U.S.", "Taiwan", "Taiwan Strait", "Beijing", "TikTok", "technology", "global leadership", "critical materials", "minerals", "trade", "South China Sea", "Yellow Sea", "Golden Dome", "public opinion", "international system", "Global South", "CRINK", "Russia", "military", "climate", "diplomatic")


def main():
    report_path = ROOT / "data/reviews/social-next75-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/social-next75-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 75
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-social-next75-review-20261109.sqlite3"
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
            assert ".bsky.social/" not in row["source_url"]
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
                        "reason": "Individual complete-post review: " + (summaries[row["id"]] + " Complete original post only, never the linked article, research report, whole thread, or audiovisual content." if approved else DEFER[row["id"]]),
                        "source_url": row["source_url"], "body_sha256": observed["body_sha256"]})
    manifest = ROOT / "data/reviews/social-next75-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "All 75 complete posted texts individually read. Per-post HTML/API correspondence, raw hashes, createdAt publication day and canonical domain identity rechecked. Derived summaries/keywords repaired; original posted text unchanged. Linked articles/reports and audiovisual descriptions are not promoted as fulltext."}, ensure_ascii=False, indent=2).encode()
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
