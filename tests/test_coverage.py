from research_crawler.coverage import coverage_gaps, coverage_matrix, verification_gaps
from research_crawler.discovery import PERIODS, SOURCE_TERMS
from research_crawler.items import MaterialCandidate
from research_crawler.store import ResearchStore
from test_export import add_verified


def test_coverage_matrix_includes_empty_period_category_cells(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")

    rows = coverage_matrix(store)

    assert len(rows) == len(PERIODS) * len(SOURCE_TERMS)
    assert all(row["candidate_count"] == 0 for row in rows)
    assert all(row["verified_unique_materials"] == 0 for row in rows)
    assert all(row["has_candidates"] is False for row in rows)
    assert all(row["has_verified_materials"] is False for row in rows)
    assert all(row["source_terms"] for row in rows)
    assert len([row for row in rows if not row["applicable"]]) == 2
    assert len(coverage_gaps(store)) == 18
    store.close()


def test_coverage_matrix_counts_statuses_and_unique_materials(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    add_verified(store, "Complete body")

    rows = coverage_matrix(store)
    target = next(
        row for row in rows
        if row["period"] == "2017-2025" and row["source_category"] == "government"
    )

    assert target["candidate_count"] == 1
    assert target["verified_unique_materials"] == 1
    assert target["status_counts"] == {
        "candidate": 1,
        "pending": 0,
        "restricted": 0,
        "verified": 0,
        "excluded": 0,
    }
    assert target["has_candidates"] is True
    assert target["has_verified_materials"] is True
    assert target not in verification_gaps(store)
    store.close()


def test_pending_or_restricted_candidates_remain_verification_gaps(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "government", "pending-only")
    store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/pending", "2017-2025", "government", "pending-only"),
    )

    rows = coverage_matrix(store)
    target = next(
        row for row in rows
        if row["period"] == "2017-2025" and row["source_category"] == "government"
    )

    assert target["has_candidates"] is True
    assert target["has_verified_materials"] is False
    assert target in verification_gaps(store)
    store.close()


def test_excluded_irrelevant_candidate_does_not_count_as_a_coverage_candidate(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("1949-1972", "research_literature", "false-positive")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC2106437/",
            "1949-1972", "research_literature", "false-positive",
        ),
    )
    store.update_candidate_status(candidate_id, "excluded", "outside thesis scope")

    target = next(
        row for row in coverage_matrix(store)
        if row["period"] == "1949-1972" and row["source_category"] == "research_literature"
    )

    assert target["candidate_count"] == 1
    assert target["status_counts"]["excluded"] == 1
    assert target["has_candidates"] is False
    assert target in coverage_gaps(store)
    store.close()


def test_new_media_is_not_a_gap_before_the_requested_2006_start(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")

    rows = coverage_matrix(store)
    old_cells = [
        row for row in rows
        if row["source_category"] == "new_media"
        and row["period"] in {"1949-1972", "1972-1991"}
    ]

    assert all(row["applicable"] is False for row in old_cells)
    assert all("2006" in row["applicability_note"] for row in old_cells)
    assert all(row not in coverage_gaps(store) for row in old_cells)
    store.close()
