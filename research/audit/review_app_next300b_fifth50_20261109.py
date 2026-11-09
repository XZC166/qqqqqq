"""Fixed APP fifth50 review: individually judged topic and field evidence."""
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
 '接受共和党总统提名讲话称对华对话降低战争危险并增加和平合作机会，主张把各国人民的创造力用于和平。': [14219],
 '高中落成讲话把访华解释为结束中国隔绝、保持沟通的和平举措，并讨论共享癌症研究成果的国际合作。': [14221],
 '返回圣克利门蒂讲话回顾访华及交流合作，区分对中国人民和领导人的尊重与政府分歧，并讨论美国实力与青年赴华。': [14223],
 '抵达圣地亚哥讲话承认中美制度差异，强调结束隔绝、发展人员交往及通过谈判处理分歧的意义。': [14225],
 '美国退伍军人大会讲话把对华开放列为争取一代和平的步骤，并强调国家实力与国际尊重的关系。': [14227],
 '面向新泽西新闻编辑的问答说明对华贸易与友谊、亚洲稳定及维持对台贸易之间的政策关系。': [14228],
 '钢铁厂落成讲话介绍向中国销售钢材，并以运输距离与日本竞争作为说明美国生产力的例子。': [14230],
 '记者会回应与田中角荣将讨论中国及经济问题的提问，并以访华说明政府政策变革的考虑。': [14231],
 '珀斯安博伊社区讲话以钢厂向中国出口为例，说明建立外交关系带来的贸易机会及保持友好联系的主张。': [14232],
 '抵达檀香山讲话回顾赴华前在夏威夷准备行程，强调与中国保持对话对于和平的必要性。': [14233],
 '休斯敦筹款午宴讲话说明对华友谊和对台关系，引用向中国出口钢材的事例讨论美国竞争力。': [14234],
 '美日夏威夷会谈联合声明回顾尼克松访华，并期待日本首相即将访华有助于缓和亚洲紧张局势。': [14235],
 '佐治亚州筹款讲话把中国从以往的敌人转为出口客户作为政策成果，并以钢材销售为例说明贸易机会。': [14236],
 '向国会提交联合国年度报告的咨文说明中华人民共和国获得代表席位，同时重申美国反对剥夺中华民国代表权的立场。': [14237],
 '康纳利牧场晚宴讲话强调对华新关系只是开始，提出应使后续发展同时有利于中美人民及太平洋和平。': [14239],
 '面向支持尼克松的青年劳工讲话把与中国沟通及人员互访联系于和平，寻求继续推进相关政策的支持。': [14243],
 '克利夫兰筹款讲话介绍对华钢材出口及将签纺织协议，说明中美经贸友谊和地区稳定的预期。': [14244],
 '纽约竞选晚宴讲话提出继续对华对话，并把年轻人能访问中国等国的开放世界作为政策愿景。': [14245],
 '面向南方黑人领袖的讲话讨论对华钢材出口及新关系的价值，同时批评对手就中国等议题的公开表达。': [14246],
 '洛杉矶竞选晚宴讲话讨论结束中国隔绝、保持对话与美国实力，并介绍与中国合作研究癌症的设想。': [14247],
 '面向纺织厂员工讲话介绍即将同中国签署的有序销售协议，说明扩大出口、限制进口及竞争政策。': [14248],
 '旧金山竞选午宴讲话回顾中美长期缺乏沟通，主张在分歧持续时继续对话，并讨论人员及医疗研究交流。': [14249],
 '全国癌症会议讲话主张动员各国研究人才，强调中美存在制度差异仍可共享知识及开展医学合作。': [14251],
 '记者会介绍同中国签署的贸易、领事、民航和纺织四项协议，宣布两国正常关系进入新阶段。': [14252],
 'KOMO 电视采访把中国及其他亚洲贸易机会同西海岸港口繁荣和太平洋和平联系起来。': [14256],
 '纽约尤宁代尔讲话回顾对华开放，并介绍中国医生访美及联合研究疾病的意义，强调在制度分歧中寻求合作。': [14257],
 '波特兰筹款讲话把对华新关系说明为扩大客户与友谊、分享东亚及西太平洋战略责任的机会。': [14258],
 '艾斯利普讲话把赴北京及莫斯科之行与和平目标联系起来，主张政府存在分歧时人民仍可保持友谊。': [14259],
 '面向粮食码头员工讲话说明中美正常化的和平、就业及市场意义，并强调对台关系和贸易没有受损。': [14262],
 '亨廷顿讲话把访华与人民友谊及一代和平的目标联系起来，强调政府制度差异不应导致中美人民敌对。': [14263],
 '阿什兰讲话回顾开启中美对话及其核冲突风险背景，说明制度分歧仍在，并讨论对华农产品贸易的前景。': [14265],
 '面向美国农民的广播讲话介绍新中美关系及粮食贸易，并宣布近期签订向中国销售三十万吨玉米的合同。': [14267],
}
DEFER = {
 14218:'China relations occur briefly in a general Pacific security paragraph; direct thematic context of full speech needs further assessment.',
 14220:'China appears mainly in a joke about election candidates debating policy, without describing their positions.',
 14222:'China recognition is briefly listed among general efforts for peace; direct full-record relevance needs further review.',
 14224:'China recognition is briefly identified as an achievement in a wide-ranging townhall; more direct context review pending.',
 14226:'China exports are an anecdote about production competence in a public-service awards speech; direct dissertation relevance uncertain.',
 14229:'China is briefly listed among many accomplishments in a French ambassadors resignation acknowledgment; further scope assessment needed.',
 14238:'China/Taiwan is briefly named among general foreign-policy achievements at a campaign rally; further direct-scope review pending.',
 14240:'China is a passing alternative grain market in discussion of the Soviet embargo, rather than a substantive China-policy section.',
 14241:'China appears only in a list of countries visited; no substantive China policy established.',
 14242:'Reporters exchange mentions Reagan ceasing to talk about China but supplies no China-policy substance; direct scope uncertain.',
 14250:'China positions and language training appear in a Singapore nominees biography; no substantive China communication-policy discussion.',
 14253:'China appears in scattered campaign comparisons and grain-deal examples; full-record direct thematic contribution requires more review.',
 14254:'Checklist is a directory of releases including a China fact sheet, not those underlying fulltexts.',
 14255:'China is briefly listed among foreign-policy successes in an address about veterans; direct scope uncertain.',
 14260:'China is briefly listed among export markets in general campaign remarks; direct thematic contribution uncertain.',
 14261:'China trip is used chiefly as a personal teacher/geography anecdote in an education address.',
 14264:'China aquaculture is a comparative food-production example in domestic fisheries legislation; no direct China communication-policy relevance established.',
 14266:'China occurs in a generic list of countries and Indochina refugee references; no substantive China-policy passage established.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300b-fifth50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300b-fifth50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300b-fifth50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300b-fifth50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed next fifty acquired APP records individually reviewed. Full original body and metadata re-extracted and checked against saved raw evidence. Topic decisions consider explicit China communication, public diplomatic claims, trade-policy arguments or exchange substance; name lists, directories and incidental examples retained pending. Separate dates/URLs remain separate records even where speakers repeat arguments."}, ensure_ascii=False, indent=2).encode()
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
