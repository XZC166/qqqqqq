import csv

from research_crawler.discovery import (
    PERIODS,
    PMC_DEFAULT_TERM,
    build_query_plan,
    import_candidate_csv,
    parse_pmc_esummary,
    parse_pubmed_abstracts,
    screen_pmc_records,
)


def test_pmc_default_query_avoids_ambiguous_single_word_media_matches():
    assert 'media[Title/Abstract]' not in PMC_DEFAULT_TERM
    assert '"United States"[Title/Abstract]' not in PMC_DEFAULT_TERM
    assert '"news media"[Title/Abstract]' in PMC_DEFAULT_TERM
    assert '"media coverage"[Title/Abstract]' in PMC_DEFAULT_TERM
    assert '"public diplomacy"[Title/Abstract]' in PMC_DEFAULT_TERM


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


def test_query_plan_includes_chinese_sources_events_and_topics():
    queries = [
        query.query
        for query in build_query_plan("2017-2025", "research_literature")
    ]

    assert any("中文学术期刊" in query for query in queries)
    assert any("人工智能竞争" in query for query in queries)
    assert any("中国形象" in query for query in queries)
    assert len(queries) < 500
    assert any('"propaganda" OR "psychological warfare"' in query for query in queries)
    labels = [
        query.query_label
        for query in build_query_plan("2017-2025", "research_literature")
    ]
    assert len(labels) == len(set(labels))


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


def test_candidate_csv_import_preserves_an_explicit_metadata_url(tmp_path):
    path = tmp_path / "paired-source.csv"
    path.write_text(
        "url,period,source_category,query_label,metadata_url\n"
        "https://example.org/report.pdf,1992-2016,think_tank,paper,"
        "https://example.org/report-record\n",
        encoding="utf-8",
    )

    candidate = import_candidate_csv(path)[0]

    assert candidate.source_url == "https://example.org/report.pdf"
    assert candidate.metadata_url == "https://example.org/report-record"


def test_screen_pmc_records_keeps_topic_relevant_records_and_reports_exclusions():
    records = [
        {
            "pmcid": "PMC1",
            "title": "Media framing of China threat narratives in the United States",
            "abstract": "We analyze news discourse and public opinion.",
        },
        {
            "pmcid": "PMC2",
            "title": "Comparison of COVID-19 and influenza characteristics",
            "abstract": "We compare clinical symptoms and treatment outcomes in China.",
        },
        {
            "pmcid": "PMC3",
            "title": "China and public diplomacy in international media",
            "abstract": "",
        },
        {
            "pmcid": "PMC4",
            "title": "Quality of health information on Chinese short-video platforms",
            "abstract": "We analyzed medical information shared on social media.",
            "abstract_available": True,
        },
    ]

    kept, review, excluded = screen_pmc_records(records)

    assert [item["pmcid"] for item in kept] == ["PMC1"]
    assert [item["pmcid"] for item in review] == ["PMC3"]
    assert excluded == [
        {
            "pmcid": "PMC2",
            "reason": "no thesis-topic term in title/abstract",
        },
        {
            "pmcid": "PMC4",
            "reason": "no thesis-topic term in title/abstract",
        },
    ]


def test_parse_pmc_esummary_maps_uid_to_pmcid_and_title():
    payload = {
        "result": {
            "uids": ["123"],
            "123": {
                "title": "China media discourse and public diplomacy",
                "articleids": [
                    {"idtype": "pmcid", "value": "PMC123"},
                    {"idtype": "pmid", "value": "456"},
                ],
            },
        }
    }

    assert parse_pmc_esummary(payload) == [
        {
            "pmcid": "PMC123",
            "pmid": "456",
            "title": "China media discourse and public diplomacy",
            "abstract": "",
            "abstract_available": False,
        }
    ]


def test_parse_pubmed_abstracts_joins_labeled_segments_by_pmid():
    xml = """
    <PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>456</PMID>
      <Article><Abstract>
        <AbstractText Label="BACKGROUND">First segment.</AbstractText>
        <AbstractText Label="METHODS">Second segment.</AbstractText>
      </Abstract></Article>
    </MedlineCitation></PubmedArticle></PubmedArticleSet>
    """

    assert parse_pubmed_abstracts(xml) == {"456": "First segment. Second segment."}
