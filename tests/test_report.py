from research_crawler.items import MaterialCandidate, SourceEvidence
from research_crawler.report import render_batch_report
from research_crawler.store import ResearchStore


def test_report_shows_actual_counts_and_uncertain_items(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "government", "taiwan-strait")
    restricted_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/restricted", "2017-2025", "government", "q1"),
    )
    store.add_evidence(
        restricted_id,
        SourceEvidence("https://example.org/restricted", "2026-11-06T00:00:00Z", 403, "hash"),
        access_status="restricted",
    )
    pending_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/pending", "2017-2025", "government", "q1"),
    )
    store.update_candidate_status(pending_id, "pending", "publication date not found")

    report = render_batch_report(store, batch_id)

    assert "2017-2025 / government / taiwan-strait" in report
    assert "candidate: 2" in report
    assert "restricted: 1" in report
    assert "pending: 1" in report
    assert "https://example.org/restricted" in report
    assert "publication date not found" in report
    assert "not exhaustive" in report.casefold()
    store.close()
