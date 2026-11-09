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
SUMMARIES = {'记者会讨论通过记者和人员互访改善中国与美国之间的相互了解，并解释公开外交讲话的目的。': [14019],
 '记者会说明对华关系正常化目标、军售限制，并回应中国国内变化与美国人权政策之间的关系。': [14020],
 '美国退伍军人协会演说援引林彪及相关媒体言辞，阐述对越南战争和中国亚洲政策的判断。': [14021],
 '讲话表达中国大陆未来与邻国及世界和平相处、参与合作的希望。': [14023],
 '公告介绍两党国会代表团访华安排，将交流与上海公报所载增进了解的目标相联系。': [14024],
 '记者会回应有关陈毅表示中美均不寻求军事对抗的报道。': [14025],
 '记者会说明扩大对华贸易、关系正常化与高技术出口安全限制之间的政策关系。': [14026],
 '东西方中心演说主张增加中美人员和思想交流，期待和解，同时重申美国及盟友的安全承诺。': [14027],
 '抵达泰国的讲话展望中国大陆参与太平洋地区合作，并表明美国不寻求永久敌对或地区支配。': [14029],
 '国情咨文介绍对华新关系与邓小平即将访美，并呼吁立法支持继续维持与台湾的关系。': [14030],
 '年度国情书面咨文讨论对华科技交流、经贸往来与新关系，并提出维持台湾非官方关系所需的立法支持。': [14032],
 '媒体问答说明对华军售和高技术出口立场，并介绍邓小平访美期间的交流、公众接触及预期议题。': [14034],
 '在马来西亚的讲话回应中国核试验，主张将资源用于经济发展，并阐明美国对和平与对抗两种情形的态度。': [14035],
 '记者会介绍外交访问期间关于中国内部局势、国际影响和越南和平问题的观察。': [14037],
 '记者会回应关于中国阻止苏联向越南运送物资的报道，并说明美方所掌握信息的限制。': [14039],
 '记者会面对中国第五次核试验的提问，说明对核不扩散谈判及国际协议的期望。': [14041],
 '欢迎泰国总理的宴会讲话讨论中美建交的地区意义，并表明维持与台湾关系和安全的立场。': [14042],
 '外交教育会议演说说明继续与北京保持对话，并将其与亚洲和平和地区发展相联系。': [14043],
 '美泰联合新闻声明评价中美关系正常化对地区稳定的意义，并说明双方对亚洲局势的看法。': [14044],
 '记者会回应对华态度是否变化的报道，表达希望各国进入国际社会并和平共处的立场。': [14045],
 '记者会回应媒体关于越南近中国边境轰炸的担忧，声明相关空袭不旨在威胁中国或扩大越南战争。': [14047],
 '媒体问答讨论邓小平访美、中国领导层变化与关系正常化的持续性，并解释台湾问题上的美国政策空间。': [14048],
 '记者会澄清关于台湾防卫的表态，并回应邓小平访美期间的涉苏言论及美国与中国看法的差异。': [14050],
 '美日联合声明讨论中国核能力及其对亚洲安全的影响，并表达对中国与国际社会和平相处的期待。': [14051],
 '佐治亚理工学院讲话回应中越冲突，说明反对跨境军事行动及保持中美正常关系的立场。': [14052],
 '面向编辑和广播界的外交问答说明中越战争不改变中美建交，并呼吁撤军和缓和地区冲突。': [14054],
 '面向企业界的外交演说以亚洲国家对中国的担忧解释地区发展、信心及美国承诺的关系。': [14055],
 '致国会的咨文介绍美国国际交流计划与预算，并列明对华人员交流的新项目和拟议经费。': [14058],
 '电视采访说明美国对中国的公开信息和交往意愿，讨论中国国内局势、国际活动及增进了解的可能。': [14059],
 '面向州长的讲话和问答讨论对华信贷、州级贸易访问、台湾经贸联系及通过往来增进相互了解。': [14060],
 '州长晚宴讲话和问答讨论对华友谊、台湾关系、最惠国待遇与人员交流，并介绍双方领导人对话。': [14062],
 '广播演说提出亚洲地区合作与长远对华对话，阐述不应使中国永久处于国际社会之外的主张。': [14063],
 '记者会解释在反对中国对越军事行动的同时继续发展双边关系、推动布卢门撒尔访华的理由。': [14064],
 '记者会解释保障反导系统决策，并以对中国及苏联核能力的判断论证政策。': [14067]}
DEFER = {14018: 'China is only one country in a generic comparison of domestic problems; substantive China-focused '
        'relevance not established.',
 14022: 'China appears only as an unaddressed agenda item before unrelated questions.',
 14028: 'Compilation of nominations includes Woodcock among many entries with different submission '
        'boundaries; not an individually verified nomination release.',
 14031: 'China refers to distant historical ancestry of Thai people, not relevant modern China policy.',
 14033: 'Ancient Chinese philosophical history is an introductory example; no substantive modern China '
        'discussion.',
 14036: 'Header attributes Carter but accord is explicitly signed by Schlesinger and Fang Yi; original '
        'authorship and first publication day need verification.',
 14038: 'Checklist of press releases is a directory, not the named original releases.',
 14040: 'Deng visit is a passing timing reference in a Thai welcome ceremony; direct China-focused relevance '
        'not established.',
 14046: 'Memo states it is to be published in the Federal Register; displayed signing/filing day not '
        'independently established as publication day.',
 14049: 'South China Sea is only a geographic location in a military unit citation.',
 14053: 'One-word confirmation of China discussion points to a separate communique; no substantive China '
        'content in this answer.',
 14056: 'White House announcement digest requires separate publication-day/byline/document-boundary '
        'verification.',
 14057: 'No substantive China-related text; keyword/source gate failed.',
 14061: 'Republic of China is only in a generic list of Asian economic progress; direct communication '
        'relationship unresolved.',
 14065: 'South China Sea is only a geographic location in a military unit citation.',
 14066: 'Executive-order header/signature dates are ambiguous (body says February 98); signing, filing and '
        'publication must not be conflated.'}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300b-first50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300b-first50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300b-first50-review-20261109.sqlite3"
    if not backup.exists():
        b = sqlite3.connect(backup);c.backup(b);b.close()
    prior = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    records, changes = [], []
    adapter = GovernmentArticleAdapter()
    for observed in selected:
        row = c.execute("SELECT * FROM materials WHERE id=?", (observed["id"],)).fetchone()
        for field, reading_key in [("published_on", "date"), ("author", "author"), ("title", "title"), ("source_url", "url")]:
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
    manifest = ROOT / "data/reviews/app-next300b-first50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Stored-original source/body checks plus individual topic and field decisions. This is a review subset of the ongoing 300-URL crawl, not another discovery batch."}, ensure_ascii=False, indent=2).encode()
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
