"""Fixed APP third50 review: individually judged topic and field evidence."""
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
 '全国公共广播电台电话问答回应中美文化及商业往来问题，并把对华关系正常化置于争取国际友谊与和平竞争的叙事中。': [14119],
 '抵达坎顿讲话解释访华是为结束中国与外部世界的隔绝，增进各国人民相互了解并促进和平。': [14120],
 '水坝落成讲话说明访华将为与中国人民建立新沟通迈出第一步，并把此举与后代的和平联系起来。': [14122],
 '记者会介绍访华时间、代表团及准备工作，强调对话不会立即消除中美分歧，并回应越南问题。': [14124],
 '面向乳品生产者的讲话把访华列为建立一代和平的外交举措，并讨论中国未来的经济竞争潜力。': [14126],
 '电视采访在介绍人权与外交政策时强调同中国建立关系，同时维持与台湾人民的关系。': [14127],
 '记者会说明中国在联合国的代表权政策、反对驱逐中华民国的立场，并回应访华及周恩来公开言论问题。': [14128],
 '面向明尼苏达州编辑和广播工作者的问答回顾对华开放、对台关系及贸易外交，称相关平衡取得进展。': [14129],
 '底特律问答说明访华不会消除中美深刻分歧，主张通过对话和关系正常化降低长期隔绝与冲突风险。': [14130],
 '抵达蒙大拿州讲话解释访华不能解决所有分歧，但应以沟通和谈判降低中国长期孤立带来的风险。': [14132],
 '抵达波特兰讲话强调中美分歧仍会存在，把访华解释为促进各国人民开放沟通的和平举措。': [14134],
 '面向西北地区媒体负责人的问答回应中国内部局势及访华安排，并介绍与中国政府和共产党领导人会面的考虑。': [14136],
 '瓦拉瓦拉讲话说明访华旨在开启对话，以讨论分歧代替冲突，并把对华交流与太平洋地区的未来联系起来。': [14138],
 '宗教广播工作者大会讲话回顾与邓小平讨论圣经及传教问题，并表达希望中国重新允许传教士进入的立场。': [14139],
 '汉福德讲话介绍基辛格访京与访华计划，强调通过对话讨论中美分歧，使后代免于冲突。': [14140],
 '森林节讲话介绍基辛格赴北京筹备访华，说明此行旨在使美国与其他国家保持沟通并促进后代和平。': [14142],
 '国会肖像揭幕讲话把中美高层会晤置于谈判政策中，提醒不能以举行会议或谈判代替实际协议。': [14144],
 '记者会说明访华与访苏各有双边目标，否认以一方牵制另一方，并介绍峰会准备及时间安排。': [14146],
 '美国退伍军人协会讲话把中美建交称为具有战略意义的政策，强调继续对台贸易友谊及亚洲和平稳定。': [14147],
 '纪念葛培理讲话把访华、访苏与结束越战联系起来，表达建设长时期和平的希望。': [14148],
 '德特里克堡设施转用于癌症研究的讲话欢迎各国科学家交流，并提及未来来自中国的人员及共享研究信息。': [14150],
 '共和党妇女大会讲话说明同对手交谈是建设一代和平的办法，并讨论中国在人口、经济及军事方面的竞争潜力。': [14152],
 '提交国会的科技合作报告介绍与中国签署的科技合作协议及十三项议定书，说明合作与两国利益的关系。': [14153],
 '退伍军人节讲话说明赴北京和莫斯科旨在减少冲突，强调政府分歧与人民共同利益可以并存。': [14154],
 '芝加哥晚宴讲话承认中美差异深刻，认为持续对抗可能引发战争，而谈判为和平提供机会。': [14157],
 '纽约晚宴讲话解释访华不能消除哲学分歧，但应以谈判降低战争风险，并讨论中国潜在经济实力。': [14159],
 '记者会回应访华是否讨论印度支那问题，表示不宜公开推测北京作用，并说明访华日期尚未公布。': [14161],
 '劳联产联大会讲话回应访华是政治活动的批评，以中国未来核力量及战争风险说明对话的必要性。': [14163],
 '全国四健会讲话回顾结束中国隔绝的政策，主张在存在制度和外交分歧时保持领导人沟通，以降低冲突风险。': [14165],
 '广播讲话介绍年度外交报告，回顾打开对华沟通渠道的准备，并把即将访华称为通向和平的重要突破。': [14167],
}
DEFER = {
 14118:'China appears only in global population/economic-competition comparisons at a football banquet; direct policy/discourse relevance insufficiently established.',
 14121:'China is merely listed among topics discussed with the Pope; no substantive China passage follows.',
 14123:'China appears in a brief missionary aside and a question comparing Cuba recognition; assess direct China-policy substance before approval.',
 14125:'Only a brief list of new diplomatic friends includes China; full interview is predominantly other subjects.',
 14131:'China occurs in an appointee biography naming a trade council, not in the US-Japan announcement subject.',
 14133:'China occurs briefly in a general achievements paragraph; direct thematic contribution of the full conference needs further scope review.',
 14135:'Christmas greeting has a brief China friendship line only; direct research scope not yet established.',
 14137:'China appears in a list of US immigrant ancestries; no substantive China policy is established.',
 14141:'State of Union includes a single brief China-normalization sentence; preserve pending a fuller relevance/context determination.',
 14143:'China/Taiwan occurs briefly among general diplomatic achievements; remaining interview is not clearly China focused.',
 14145:'China/Taiwan friendship is briefly listed in general achievements; direct study relevance remains to be assessed.',
 14149:'China is a passing example of a potential grain market in a discussion about the Soviet embargo.',
 14151:'Single brief China/Taiwan friendship line in a general governors dinner toast; direct thematic relevance remains uncertain.',
 14155:'Paired-toast title while extracted body appears to contain only presidential toast; no explicit China/Taiwan passage found.',
 14156:'China is the name of the company Rosenthal China in an attendee biography; this is not China policy.',
 14158:'China Sea is merely a geographical reference in budget-reduction discussion; no substantive China-policy evidence established.',
 14160:'China normalization and Taiwan friendship are briefly listed among general accomplishments; further direct-scope review pending.',
 14162:'Digest combines several White House announcements; publication/author and single-item body boundaries need clarification.',
 14164:'China appears only in an immigrant-ancestry list, not a China policy discussion.',
 14166:'Paired resignation letters are attributed only to Carter although Vance authors the second letter; separate authorship/date evidence before approval.',
}
TERMS = ("China", "Chinese", "United States", "Taiwan", "Formosa", "Quemoy", "Matsu", "Peking", "Peiping", "Shanghai", "Voice of America", "United Nations", "propaganda", "public diplomacy", "foreign policy", "public opinion", "normalization", "trade", "Korean War", "Hong Kong", "Soviet Union", "Woodcock", "Peace Corps")


def main():
    report_path = ROOT / "data/reviews/app-next300b-third50-quality-review-20261109.json"
    if report_path.exists():
        raise SystemExit("Fixed batch already reviewed; preserve later decisions.")
    selected = json.loads((ROOT / "data/reviews/app-next300b-third50-reading-20261109.json").read_text(encoding="utf-8"))
    summaries = {mid: text for text, ids in SUMMARIES.items() for mid in ids}
    assert len(selected) == 50
    assert summaries.keys().isdisjoint(DEFER)
    assert summaries.keys() | DEFER.keys() == {r["id"] for r in selected}
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    backup = ROOT / "data/backups/pre-app-next300b-third50-review-20261109.sqlite3"
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
    manifest = ROOT / "data/reviews/app-next300b-third50-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "field_corrections": changes, "note": "Fixed next fifty acquired APP records individually reviewed. Entire original body re-extracted and byte-for-byte compared; article metadata and boundaries plus topical passages and surrounding answers reviewed for each decision. Exact matches or a China mention alone do not grant thematic approval; ambiguous authorship, multiple-item boundaries and incidental mentions retained pending."}, ensure_ascii=False, indent=2).encode()
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
