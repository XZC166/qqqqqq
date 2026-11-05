from pathlib import Path

from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.pipelines import VerificationPipeline
from research_crawler.policy import AccessDecision
from research_crawler.store import ResearchStore


class FakeSpider:
    period = "2017-2025"
    source_category = "government"
    query_label = "fixture-source-test"


def test_pipeline_saves_original_evidence_and_verified_material(tmp_path):
    pipeline = VerificationPipeline(tmp_path / "state.sqlite3", tmp_path / "evidence")
    pipeline.spider = FakeSpider()
    pipeline.open_spider()
    url = "https://agency.example/speech"
    evidence = SourceEvidence(
        source_url=url,
        fetched_at="2026-11-06T00:00:00Z",
        status_code=200,
        content_sha256="fixture-hash",
        body_complete=True,
        metadata_verified=True,
    )
    material = VerifiedMaterial(
        "Example U.S. Agency", "2020-02-03", "A. Author", "Source title", "",
        "China", "Full source text.", url,
    )
    item = {
        "candidate": MaterialCandidate(url, FakeSpider.period, FakeSpider.source_category, FakeSpider.query_label),
        "decision": AccessDecision.ALLOW,
        "evidence": evidence,
        "material": material,
        "field_sources": {
            name: url for name in ("source", "time", "author", "title", "keywords")
        },
        "abstract_origin": "none",
        "raw_response": b"<article>Full source text.</article>",
    }

    pipeline.process_item(item)

    store = ResearchStore(tmp_path / "state.sqlite3")
    assert store.get_verified_materials() == [material]
    evidence_files = list((tmp_path / "evidence").glob("*.html"))
    assert len(evidence_files) == 1
    assert evidence_files[0].read_bytes() == item["raw_response"]
    store.close()
    pipeline.close_spider()


def test_pipeline_keeps_restricted_candidate_out_of_verified_table(tmp_path):
    pipeline = VerificationPipeline(tmp_path / "state.sqlite3", tmp_path / "evidence")
    pipeline.spider = FakeSpider()
    pipeline.open_spider()
    url = "https://agency.example/speech"
    item = {
        "candidate": MaterialCandidate(url, FakeSpider.period, FakeSpider.source_category, FakeSpider.query_label),
        "decision": AccessDecision.RESTRICTED,
        "evidence": SourceEvidence(url, "2026-11-06T00:00:00Z", 403, "restricted-hash"),
        "material": None,
        "raw_response": b"Access restricted",
    }

    pipeline.process_item(item)

    store = ResearchStore(tmp_path / "state.sqlite3")
    assert store.get_verified_materials() == []
    assert store.batch_summary(pipeline.batch_id)["restricted"] == 1
    store.close()
    pipeline.close_spider()
