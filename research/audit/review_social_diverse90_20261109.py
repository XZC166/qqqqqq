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
 '纽约时报意见账号引述 Jacob Dreyer，主张增加获得中国制造药物的机会可为美国患者提供更便宜的治疗选择。': [3815],
 '纽约时报意见账号引述 Phillip Saunders 与 Joel Wuthnow，讨论中国军官缺乏实战经验及军队控制问题。': [3822],
 '纽约时报意见账号引述自由亚洲电台负责人 Bay Fang，认为停止该台运作会使美国把信息空间让给中国。': [3823],
 'Pew 帖文比较南非受访者对与中国及美国保持经济联系的重要性判断，并列出同二〇一九年的差异。': [4283],
 'Pew 帖文称更多南非受访者把中国视为世界领先经济体，并比较二〇二三年以来的比例变化。': [4284],
 'Pew 帖文比较南非受访者对中美的好感度，称对中国的评价首次高于对美国的评价。': [4285],
 'Pew 帖文比较美国两党受访者对中国监管人工智能能力的信任程度，指出共和党人的不信任程度更高。': [4286],
 'Foreign Affairs 帖文引述 Jonathan Czin，批评特朗普政府对华策略未给美国带来实际收益。': [4330],
 'Foreign Affairs 帖文引述刘宗媛，认为缺少道德领导力会影响中国在全球被追随而非仅被管理或畏惧的地位。': [4332],
 'Foreign Affairs 帖文介绍刘宗媛对中国短期与长期目标及中美竞争成败因素的分析主题。': [4333],
 'Foreign Affairs 帖文介绍 Elizabeth Economy 对美国如何在深海、北极及网络空间等领域同中国竞争的讨论。': [4334],
 'Chatham House 帖文认为美国新安全战略对移民和有组织犯罪的关注多于中国及乌克兰相关挑战。': [4688],
 'Chatham House 帖文认为对欧盟及全球南方等非美国市场的贸易增长帮助中国应对特朗普关税的影响。': [4689,4691],
 'Chatham House 帖文认为中菲紧张关系使南海行为准则难以达成，并提出菲律宾利用东盟主席国角色的其他可能性。': [4690],
 'Foreign Policy 帖文比较中国新的拉美政策蓝图与特朗普政府在该地区宣布的战略和优先事项。': [4832],
 'Foreign Policy 帖文称中国军队虽有国家媒体宣传、报酬及福利等因素支持，仍难吸引部分年轻人。': [4835],
 'Lawfare 帖文认为美国无法独自胜过中国，主张把盟友重新视为共同创造实力的伙伴。': [5157],
 'Lawfare 帖文比较俄罗斯对北约盟友的灰色地带行动与北京对台湾的压力，并讨论对美国及盟友的影响。': [5158],
 'Lawfare 帖文称美国在技术标准参与和影响力方面落后于中国，强调在国际标准机构发挥作用的重要性。': [5165],
 'Lawfare 帖文介绍美国对盐台风网络行动应如何作出攻防应对的讨论，并引述克里斯托弗·雷对行动规模的评价。': [5166],
 'Axios 帖文发布特朗普将允许部分英伟达芯片向中国销售、美国取得百分之二十五份额的消息。': [5300],
 'Axios 帖文把关键矿产同特朗普第二任期的对华贸易战及其他外交议题相联系。': [5319],
 'Axios 帖文转述特朗普与习近平会谈后降低对华关税的表态，以及中方关于大豆、能源、稀土和芬太尼的承诺。': [5325],
 'Axios 帖文讨论特朗普对华语调趋缓后，金融市场仍对中国商品关税是否升高感到不确定。': [5332],
 'Axios 帖文将市场关于特朗普会收回关税威胁的判断，与中美贸易紧张期间的股市表现联系起来。': [5336],
 'Human Rights Watch 帖文称土耳其正限制寻求安全的维吾尔人的合法居留，并把担忧同中土关系变化联系起来。': [5361],
 'Human Rights Watch 帖文介绍特朗普与习近平将于亚太经合组织峰会期间会面，并批评中美对国际人权制度的影响。': [5362],
 'Human Rights Watch 帖文批评中国一项拟议法律对少数群体及思想表达的影响。': [5363],
 'Human Rights Watch 帖文介绍重庆一栋建筑投射呼吁反对法西斯及争取权利标语的事件。': [5364],
 'Human Rights Watch 帖文介绍黎智英庭审因健康原因推迟，并呼吁撤销其所批评的指控。': [5365],
 'Just Security 帖文把特朗普推动南高加索与中亚贸易通道，同对抗中国及俄罗斯影响的目标联系起来。': [5390],
 'CNN 帖文称美国海军试图从南海海底回收两架飞机，以防敏感信息先被中国取得。': [5547],
 'CNN 帖文把中国新航母服役描述为北京追赶美国海上优势的重要进展。': [5562],
 'CNN 帖文转述特朗普在会见习近平前要求立即开始核武器试验的表态，并列出其提及的中俄背景。': [5575],
 'CNN 帖文认为习近平与特朗普的会晤为中国展示与美国在全球舞台平等地位提供机会。': [5578],
 'The Diplomat 帖文将中国在萨摩亚的影响力行动描述为长期持续，并评价其选举效果。': [6277],
 'The Diplomat 帖文回顾二〇一五年底中国军队开始的大规模组织改革及其历史背景。': [6278],
 'The Diplomat 帖文把日本加强防务同中朝俄军事压力及美国提高防务支出的要求联系起来。': [6280],
 'The Diplomat 帖文回顾二〇一五年中国军队改革，并提出十年后改革进展的问题。': [6281],
 'The Diplomat 帖文认为西方在讨论避免新冷战时，未认识到冷战已经发生且中国正在获胜。': [6286],
 'Politico 帖文介绍共和党参议员对进口阿根廷牛肉的批评，并联系美国大豆农民面临的对华贸易问题。': [6774],
 'Politico 帖文发布白宫披露对华贸易休战细节的消息标题。': [6779],
 'Politico 帖文发布赫格塞思寻求重启中美军事热线的消息标题。': [6780],
 'Politico 帖文发布日本首相涉台言论后中日相互批评的消息标题。': [6788],
 'Politico 帖文发布中国在气候谈判中填补美国留下空缺的消息标题。': [6794],
 'NPR 帖文介绍一本编辑文集中的十二篇人物特写，称其突出中美在建交后交往的积极方面。': [6842,6844],
 'NPR 帖文发布美国官员宣布让 TikTok 继续在美国运营的框架安排，同时说明细节尚在商谈。': [6845],
 'CFR 帖文引述 Jonathan Hillman，认为美国军人与公务员的退休储蓄间接支持中国技术工业发展。': [7947],
 'CFR 帖文列出美国对中国稀土的依赖比例，并介绍供应链与技术竞争问题。': [7951],
 'CFR 帖文引述 Benn Steil，认为经济相互依赖既可能提高战争成本，也可能滋生猜疑与竞争。': [7952],
 'CFR 帖文引述 Rush Doshi，把近期特朗普与习近平峰会描述为大国政治的重要转折点。': [7953],
 'CFR 帖文介绍 Chris McGuire 向美国众议院作证时，将先进半导体及制造设备出口管制视为对华技术竞争的重要工具。': [7954],
 'RAND 帖文引述 Raymond Kuo 与 Catherine Kish，将台湾面临的问题界定为政治极化，而不仅是抵抗意愿不足。': [8072],
 'RAND 帖文称台湾正在准备政府、社会和军队，以应对中国的多维挑战。': [8073],
 'RAND 帖文比较当代美国盟友对华经济联系与冷战时期的差异，并提出其对盟友取向选择的影响。': [8078],
 'ECFR 帖文认为中国海上灰色地带活动影响台湾及欧洲安全，主张欧洲同印太伙伴合作揭示与应对相关行动。': [9719],
 'ECFR 帖文讨论中日围绕台湾的外交紧张及中国施压，主张欧盟同印太伙伴协调应对。': [9721],
 'DGAP 帖文转述 Susanne Riegraf 对北约核共享及同中俄开展军控接触的看法，强调威慑和军控可以并行。': [9946],
}
DEFER = {
 3313:'Podcast episode promotional description; no full transcript verified.',
 3314:'Podcast episode promotional description; no full transcript verified.',
 3315:'YouTube short promotional description; no full transcript verified.',
 3317:'Chinese auto manufacturers and emerging markets are mentioned, but direct US-China research relevance requires further context.',
 3318:'YouTube video promotional description; no full transcript verified.',
 3812:'China-shop is an English idiom about White House demolition; no China-topic substance.',
 3821:'Researcher nationality appears with generic courage advice; the specific China-policy/discourse context is not established by this post.',
 4282:'China favorability occurs in a generic South African country-opinion list without a US comparison; fuller direct-scope review pending.',
 4331:'Magazine issue contents promotional listing, not any of the listed analyses fulltext.',
 4692:'Podcast promotional description, not a full written transcript.',
 4834:'Regional Bangladesh-China-Pakistan/India balance claim requires further direct US-China thematic linkage.',
 4836:'Documentary promotional synopsis; no video or transcript obtained.',
 4837:'Multi-topic news roundup preview; underlying reports are not verified fulltext.',
 5162:'Newsletter contents preview mixes unrelated headlines; underlying report texts are not supplied.',
 5392:'China appears chiefly as a hashtag accompanying a general nuclear-testing teaser; direct specific context needs further review.',
 5393:'Multi-topic news roundup directory preview, not the listed underlying full reports.',
 5394:'Multi-topic news roundup directory preview, not the listed underlying full reports.',
 5395:'Multi-topic news roundup directory preview, not the listed underlying full reports.',
 5569:'Question/teaser about China economic data supplies no findings; full report or transcript remains unverified.',
 6841:'Radio-interview description; no full transcript verified.',
 6843:'Radio-interview description; no full transcript verified.',
 8071:'Research preview poses a demographic-security question without substantive findings; underlying report not verified.',
 8077:'Report preview poses a Taiwan-resilience question without supplying findings; underlying report not verified.',
 9720:'EU-Mercosur/China competition argument requires further direct US-China thematic scope review.',
 9722:'West African coup/disinformation discussion has no China-specific body evidence.',
 9723:'EU electric-vehicle policy argument requires further direct US-China thematic scope review.',
 9947:'Event invitation; no substantive event proceedings or China-topic passage verified.',
 9948:'Germany-China book-review promotion requires further direct US-China thematic linkage.',
 9949:'Russia/Ukraine disinformation and Trump discussion; no China-topic passage.',
 9950:'Explicit thread fragment /2 discusses propaganda generally; no China-specific context or complete thread verified.',
}
TERMS = ("China", "Chinese", "United States", "U.S.", "Taiwan", "AI", "Radio Free Asia", "information space", "Hong Kong", "Jimmy Lai", "Uyghurs", "semiconductor", "Nvidia", "nuclear", "trade", "tariffs", "TikTok", "Taiwan", "Taiwan Strait", "Beijing", "TikTok", "technology", "global leadership", "critical materials", "minerals", "trade", "South China Sea", "Yellow Sea", "Golden Dome", "public opinion", "international system", "Global South", "CRINK", "Russia", "military", "climate", "diplomatic")


def main():
    report_path = ROOT / "data/reviews/social-diverse90-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/social-diverse90-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 90
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-social-diverse90-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/social-diverse90-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "All 90 complete posted texts individually read across 18 institutional domain handles. Per-post HTML/API correspondence, raw hashes, createdAt publication day and canonical domain identity rechecked. Derived summaries/keywords repaired; original posted text unchanged. Linked articles/reports and audiovisual descriptions are not promoted as fulltext."}, ensure_ascii=False, indent=2).encode()
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
