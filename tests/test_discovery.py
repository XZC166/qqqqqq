import csv

from research_crawler.discovery import PERIODS, build_query_plan, import_candidate_csv


def test_query_plan_covers_all_periods_and_topic_vocabulary():
    assert PERIODS == ("1949-1972", "1972-1991", "1992-2016", "2017-2025")
    plan = build_query_plan("1949-1972", "media")

    queries = [entry.query for entry in plan]
    assert queries
    assert any("New York Times" in query for query in queries)
    assert any("Korean War" in query for query in queries)
    assert any("international broadcasting" in query for query in queries)


def test_query_plan_rejects_unknown_period_or_category():
    try:
        build_query_plan("1930-1948", "media")
    except ValueError as exc:
        assert "period" in str(exc)
    else:
        raise AssertionError("unknown period should be rejected")

    try:
        build_query_plan("1949-1972", "unknown")
    except ValueError as exc:
        assert "category" in str(exc)
    else:
        raise AssertionError("unknown source category should be rejected")


def test_candidate_csv_import_does_not_promote_metadata_to_article_fields(tmp_path):
    path = tmp_path / "candidates.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("url", "period", "source_category", "query_label", "platform_id"),
        )
        writer.writeheader()
        writer.writerow({
            "url": "https://example.org/article",
            "period": "2017-2025",
            "source_category": "government",
            "query_label": "taiwan-strategic-communication",
            "platform_id": "post-123",
        })

    candidates = import_candidate_csv(path)

    assert len(candidates) == 1
    assert candidates[0].source_url == "https://example.org/article"
    assert candidates[0].period == "2017-2025"
    assert candidates[0].query_label == "taiwan-strategic-communication"
    assert candidates[0].platform_id == "post-123"
    assert not hasattr(candidates[0], "title")
    assert not hasattr(candidates[0], "body")
