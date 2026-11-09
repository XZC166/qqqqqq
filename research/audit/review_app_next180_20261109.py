"""Bounded individual APP review; repairs summaries without new discoveries."""
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from research_crawler.quality_audit import audit_material, material_fingerprint, _source_row
from research_crawler.revalidation import _extract_existing
from research_crawler.spiders.government import GovernmentArticleAdapter
from research_crawler.store import ResearchStore

ROOT = Path(__file__).resolve().parents[2]
# Individually inspected same-document passages and metadata. These concise
# summaries report document contents without adopting the speakers' claims.
SUMMARIES = {
    "材料就台湾海峡局势、美国的相关政策与对华立场作出公开说明。": [52, 231, 232, 233, 2943, 2945, 2949, 3130, 3132, 13668, 13674, 13678, 13680],
    "记者会回应是否承认中华人民共和国政府的提问。": [188],
    "讲话说明朝鲜战争背景下美国的远东政策，并讨论中国参战及扩大冲突的风险。": [235, 3161],
    "声明就中华民国总统蒋介石逝世表示哀悼。": [3078],
    "材料讨论中美人员往来、文化交流与两国人民之间的关系。": [3087, 3089, 13639],
    "文件规定中华人民共和国驻华盛顿联络处及其成员的外交特权与豁免。": [3088],
    "声明回应被中国扣押的美国飞行员获释的消息。": [3131],
    "记者会介绍美国驻北京联络处的人事安排及中美关系。": [13605],
    "材料说明美国与中华人民共和国开展对话、改善关系与维护和平之间的联系。": [13606, 13607, 13610, 13611, 13612, 13613, 13616, 13619, 13620, 13625, 13628, 13629, 13635, 13646, 13648, 13649, 13651, 13660, 13665, 13669, 13670, 13671, 13675, 13677, 13679, 13685, 13690, 13695, 13711, 13713, 13715, 13719, 13723],
    "咨文讨论贸易改革，并提及发展对华互利贸易的机会。": [13609],
    "美英联合声明讨论中国军队介入朝鲜战争后的远东形势与两国政策。": [13615],
    "讲话说明美国发展对华关系时仍重视利比里亚等传统伙伴。": [13617],
    "声明讨论对外援助法案附加条款，并说明美国对华出口管制和禁运措施。": [13621],
    "美日联合公报讨论国际形势、中日关系正常化与中美关系改善。": [13623],
    "咨文讨论中华人民共和国参加联合国工作与国际政治、安全问题。": [13631],
    "讲话批评共和党与包括“China lobby”在内的利益集团之间的联系。": [13632],
    "讲话讨论朝鲜战争中的中国军队，并批评利益集团对美国政治的影响。": [13634],
    "讲话讨论出口与经济竞争，并说明美国与中华人民共和国开展交往的政策考虑。": [13637],
    "讲话讨论朝鲜战争及避免将冲突扩大到中国和苏联的政策。": [13638],
    "咨文说明贸易协定与立法进展，并讨论改善对华商业关系。": [13642, 13697],
    "问答中回顾访华等外交活动，并将其作为回应政治批评的内容。": [13647],
    "讲话在美罗签署原则声明时讨论大国关系，并将对华原则声明作为参照。": [13652],
    "讲话在夫人赴拉美访问前强调美国发展对华关系的同时仍重视西半球伙伴。": [13656],
    "材料讨论中国扣押人员问题以及联合国与公众舆论在争取释放人员中的作用。": [13658],
    "声明说明美国海军陆战队在贝鲁特登陆的理由，并将中国等地的共产党活动用作论证。": [13661],
    "讲话讨论在政治制度存在差异时开展国际合作，并提到与中华人民共和国的关系。": [13662],
    "记者会讨论中国与停止核试验协议、苏联政策之间的关系。": [13663],
    "讲话讨论美国农业出口，并将对华关系改善与农产品市场联系起来。": [13664],
    "讲话说明美国发展对华关系时仍重视拉丁美洲与加勒比地区的传统伙伴。": [13667],
    "讲话讨论农业、健康与国际合作，并提及中美科技、环境和医疗交流。": [13673],
    "电报讨论如何回应对美国外交政策的政治批评，其中涉及对台关系与金门、马祖防务。": [13676],
    "讲话就访问远东作出说明，并肯定美国与中华民国的合作。": [13682],
    "联合声明将共产主义中国描述为远东和平的威胁，并讨论区域合作。": [13684],
    "讲话以开启中美关系为例说明外交冒险与争取和平的政策考虑。": [13686],
    "祝酒辞回顾蒋介石的经历及其在美中关系中的作用。": [13687],
    "讲话将对华关系的开启与世界和平相联系，并强调不忘约旦等老朋友。": [13688],
    "广播电视讲话回顾远东之行，并讨论台湾、中国形象与共产主义宣传。": [13691],
    "记者会讨论中国与苏联的政策及对外姿态。": [13693],
    "记者会讨论美国对中华人民共和国的承认政策与其加入联合国的问题。": [13698],
    "辞职讲话回顾中美关系的开启，并主张两国人民继续保持友好。": [13699],
    "讲话以与中国师生交流的经历说明人民友好与美国外交目标。": [13700],
    "讲话在冷战竞争背景下讨论中国、美国的国际地位及对外政策。": [13702, 13704, 13706, 13708, 13710, 13714, 13722],
    "讲话承诺延续《上海公报》原则，并维持与中华人民共和国的新关系。": [13703],
    "讲话谈到改善中美关系，并评价中国的技术进步、生产与青年。": [13707],
    "讲话介绍乔治·布什担任美国驻中华人民共和国代表的安排，并评价其履历。": [13709],
    "记者会回应古巴承认中华人民共和国的提问。": [13712],
    "致辞表达对中国人民的友谊，反对中华人民共和国加入联合国，并肯定华裔美国人的贡献。": [13716],
    "讲话将美国农民的处境与苏联、中国农民作比较，以说明其对不同制度的评价。": [13724],
    "讲话讨论美日关系，并提及双方改善与中华人民共和国关系的努力。": [13725],
    "问答讨论中华人民共和国的内部状况、中苏关系及其加入联合国的问题。": [13727],
    "美法联合公报回顾东西方关系，并提及基辛格与中国领导人的会谈。": [13728],
    "讲话将苏联和中华人民共和国描述为国际共产主义力量中心及和平的威胁。": [13729],
    "讲话回顾美国对外政策，并说明对华关系与《上海公报》原则。": [13730],
    "讲话回顾早期对华贸易，并以美国形象与自由选举说明对外传播目标。": [13731],
    "报纸编辑协会问答讨论中国、台湾问题与中美关系正常化。": [13732],
    "讲话讨论对华缓和政策、盟友关系及公开而持续的外交对话。": [13733],
    "讲话将美国农业与开启对华关系、改善国际关系相联系。": [13734],
}


def main():
    out = ROOT / "data/reviews/app-next180-quality-review-20261109.json"
    if out.exists():
        raise SystemExit("Fixed batch already reviewed; preserve its report.")
    s = ResearchStore(ROOT / "data/research.sqlite3")
    c = s.connection
    urls = {r["url"] for r in csv.DictReader((ROOT / "data/candidates-app-fulltext-early-next180-20261109.csv").open(encoding="utf-8-sig"))}
    reading = json.loads((ROOT / "data/reviews/app-next180-topic-reading-20261109.json").read_text(encoding="utf-8"))
    inspected = {r["id"]: r for r in reading}
    summaries = {mid: summary for summary, mids in SUMMARIES.items() for mid in mids}
    assert summaries.keys() <= inspected.keys()
    backup = ROOT / "data/backups/pre-app-next180-field-review-20261109.sqlite3"
    if not backup.exists():
        target = sqlite3.connect(backup)
        c.backup(target)
        target.close()
    rows = [r for r in c.execute("SELECT * FROM materials ORDER BY id") if r["source_url"] in urls]
    prior_formal = {r[0] for r in c.execute("SELECT material_id FROM quality_reviews WHERE status='pass'")}
    changes = []
    adapter = GovernmentArticleAdapter()
    for row in rows:
        if row["id"] not in summaries:
            continue
        observed = inspected[row["id"]]
        assert row["source_url"] == observed["url"]
        assert (row["published_on"], row["author"], row["title"]) == (observed["date"], observed["author"], observed["title"])
        source = _source_row(s, row["id"])
        result, metadata_ids = _extract_existing(s, source, adapter)
        parsed = result.get("material")
        assert parsed and parsed.body == row["body"]
        assert hashlib.sha256(Path(source["evidence_path"]).read_bytes()).hexdigest() == source["content_sha256"]
        abstract = "据正文整理：" + summaries[row["id"]]
        material = replace(parsed, abstract=abstract, keywords=row["keywords"], duplicate_count=row["duplicate_count"])
        fields = json.loads(c.execute("SELECT field_sources FROM material_verifications WHERE material_id=?", (row["id"],)).fetchone()[0])
        fields.update({"abstract": row["source_url"], "keywords": row["source_url"]})
        # No add_candidate: an offline correction is not another discovery.
        mid, created = s.add_verified_material(source["candidate_id"], row["evidence_id"], material,
                                             abstract_origin="derived", field_sources=fields, metadata_evidence_ids=metadata_ids)
        assert mid == row["id"] and not created
        changes.append({"material_id": mid, "previous_fields": dict(row), "new_abstract": abstract,
                        "raw_evidence_path": source["evidence_path"], "raw_sha256": source["content_sha256"]})
    records = []
    for old in rows:
        row = c.execute("SELECT * FROM materials WHERE id=?", (old["id"],)).fetchone()
        previous = c.execute("SELECT checks_json FROM quality_reviews WHERE material_id=?", (row["id"],)).fetchone()
        prior_decision = json.loads(previous[0]).get("topic_decision") if previous else None
        if row["id"] not in inspected and prior_decision:
            # Keep previously reviewed records and their immutable decisions.
            continue
        approved = row["id"] in summaries
        reason = ("Individually checked direct topic passages and metadata; corrected same-body summary. " + summaries[row["id"]]
                  if approved else "Pending: no positive individual decision, incidental/Indochina-only reference, excerpt rather than complete speech, or unresolved relevance/fields. Evidence preserved.")
        records.append({"material_id": row["id"], "fingerprint": material_fingerprint(row), "approved": approved,
                        "reason": reason, "source_url": row["source_url"], "body_sha256": hashlib.sha256(row["body"].encode()).hexdigest()})
    manifest = ROOT / "data/reviews/app-next180-topic-decisions-20261109.json"
    raw = json.dumps({"records": records, "summary_field_corrections": changes,
                      "note": "Source completeness checked against full saved original; topic passages inspected individually. Full bodies were not replaced by these summaries."}, ensure_ascii=False, indent=2).encode()
    assert not manifest.exists()
    manifest.write_bytes(raw)
    results = [audit_material(s, r["material_id"], {**r, "evidence_path": str(manifest), "evidence_sha256": hashlib.sha256(raw).hexdigest()}) for r in records]
    # Refresh prior decisions after the crawl, too, without resetting them.
    covered = {r["material_id"] for r in records}
    for row in rows:
        if row["id"] in covered:
            continue
        previous = c.execute("SELECT checks_json FROM quality_reviews WHERE material_id=?", (row["id"],)).fetchone()
        decision = json.loads(previous[0]).get("topic_decision") if previous else None
        results.append(audit_material(s, row["id"], decision))
    candidates = [r for r in c.execute("SELECT * FROM candidates WHERE query_label='app-fulltext-early-20261109'") if r["source_url"] in urls]
    now_formal = {r["material_id"] for r in results if r["status"] == "pass"}
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "batch_candidate_urls": len(urls), "working_materials": len(rows),
              "candidate_statuses": dict(Counter(r["status"] for r in candidates)), "formally_verified_in_batch": len(now_formal),
              "new_formal_promotions": len(now_formal - prior_formal), "withdrawn_formal": len((prior_formal & {r["id"] for r in rows}) - now_formal),
              "pending": len(urls) - len(now_formal), "restricted": sum(r["status"] == "restricted" for r in candidates),
              "failed": sum(r["status"] == "failed" for r in candidates), "summary_fields_corrected": len(changes),
              "offline_correction_duplicate_discoveries": 0, "backup": str(backup.relative_to(ROOT)), "records": results}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False, indent=2))
    s.close()


if __name__ == "__main__":
    main()
