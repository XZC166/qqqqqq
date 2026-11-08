import csv
import json
from argparse import Namespace

from openpyxl import load_workbook

from research_crawler.cli import main
from research_crawler.store import ResearchStore
from research_crawler import cli
from research_crawler.discovery import import_candidate_csv
from research_crawler.items import MaterialCandidate


def test_plan_command_writes_queries_as_csv(tmp_path):
    destination = tmp_path / "queries.csv"

    result = main(["plan", "--period", "1949-1972", "--category", "media", "--output", str(destination)])

    assert result == 0
    with destination.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert rows[0]["period"] == "1949-1972"
    assert rows[0]["source_category"] == "media"
    assert "query" in rows[0]


def test_import_candidates_creates_resumable_batch_state(tmp_path, capsys):
    candidate_file = tmp_path / "candidates.csv"
    candidate_file.write_text(
        "url,period,source_category,query_label\n"
        "https://example.org/a,2017-2025,government,taiwan-strait\n",
        encoding="utf-8",
    )
    database = tmp_path / "research.sqlite3"

    result = main(["import-candidates", "--csv", str(candidate_file), "--db", str(database)])

    assert result == 0
    assert "Imported 1 candidate" in capsys.readouterr().out
    store = ResearchStore(database)
    assert store.connection.execute("SELECT COUNT(*) FROM candidates").fetchone()[0] == 1
    assert store.connection.execute("SELECT COUNT(*) FROM batches").fetchone()[0] == 1
    store.close()


def test_coverage_audit_writes_complete_matrix(tmp_path, capsys):
    from research_crawler.cli import main

    database = tmp_path / "research.sqlite3"
    output = tmp_path / "coverage.json"

    assert main(["coverage-audit", "--db", str(database), "--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["matrix"]) == 20
    assert len(payload["gaps"]) == 18
    assert len(payload["verification_gaps"]) == 18
    assert "coverage cells" in capsys.readouterr().out


def test_export_command_creates_workbook_with_fixed_header(tmp_path):
    database = tmp_path / "research.sqlite3"
    ResearchStore(database).close()
    workbook_path = tmp_path / "output.xlsx"

    result = main(["export", "--db", str(database), "--output", str(workbook_path)])

    assert result == 0
    rows = list(load_workbook(workbook_path, read_only=True).active.iter_rows(values_only=True))
    assert rows[0] == ("来源", "时间", "作者", "标题", "摘要", "关键词", "正文", "来源链接", "重复计数")


def test_revalidate_command_can_include_pending_candidates_from_local_evidence(tmp_path):
    import hashlib
    from pathlib import Path
    from research_crawler.items import MaterialCandidate, SourceEvidence

    database = tmp_path / "research.sqlite3"
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    raw = (Path(__file__).parent / "fixtures" / "government_page.html").read_bytes()
    evidence_path = evidence_dir / "source.html"
    evidence_path.write_bytes(raw)
    store = ResearchStore(database)
    batch_id = store.create_batch("2017-2025", "government", "pending-review")
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/story", "2017-2025", "government", "pending-review"),
    )
    store.update_candidate_status(candidate_id, "pending", "prior parse incomplete")
    store.add_evidence(
        candidate_id,
        SourceEvidence(
            "https://example.org/story", "2026-11-07T00:00:00Z", 200,
            hashlib.sha256(raw).hexdigest(), evidence_path=evidence_path,
            body_complete=True, metadata_verified=True,
        ),
        access_status="allow",
    )
    store.close()

    output = tmp_path / "revalidation.json"
    assert main([
        "revalidate", "--db", str(database), "--output", str(output), "--include-pending"
    ]) == 0

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["pending_candidates"]["verified"] == [candidate_id]


def test_fast_profile_keeps_robots_and_per_domain_limit(monkeypatch):
    class Settings:
        def __init__(self):
            self.values = {}

        def set(self, name, value, priority=None):
            self.values[name] = value

    settings = Settings()
    args = Namespace(
        fast=True, concurrency=None, per_domain=None, delay=None, target_concurrency=None
    )

    cli._apply_throughput_options(settings, args)

    assert settings.values["CONCURRENT_REQUESTS"] == 8
    assert settings.values["CONCURRENT_REQUESTS_PER_DOMAIN"] == 2
    assert settings.values["DOWNLOAD_DELAY"] == 0.25
    assert "ROBOTSTXT_OBEY" not in settings.values


def test_candidate_filter_skips_verified_materials_unless_refresh_is_requested(tmp_path):
    from test_export import add_verified

    store = ResearchStore(tmp_path / "research.sqlite3")
    add_verified(store, "Complete source body.")
    batch_id = store.create_batch("2017-2025", "government", "repeat-filter")
    repeated_id = store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/story", "2017-2025", "government", "repeat-filter"),
    )
    candidates = [
        MaterialCandidate(
            "https://example.org/story", "2017-2025", "government", "repeat"
        ),
        MaterialCandidate(
            "https://example.org/new", "2017-2025", "government", "new"
        ),
    ]

    eligible = cli._unverified_candidates(candidates, store)
    refreshed = cli._unverified_candidates(candidates, store, refresh_verified=True)

    assert [candidate.source_url for candidate in eligible] == ["https://example.org/new"]
    assert [candidate.source_url for candidate in refreshed] == [
        "https://example.org/story", "https://example.org/new"
    ]
    assert store.connection.execute(
        "SELECT status FROM candidates WHERE id = ?", (repeated_id,)
    ).fetchone()[0] == "verified"
    store.close()


def test_candidate_directory_merges_files_and_deduplicates_urls(tmp_path, monkeypatch):
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    first.write_text(
        "url,period,source_category,query_label\n"
        "https://example.org/a,2017-2025,research_literature,first\n",
        encoding="utf-8",
    )
    second.write_text(
        "url,period,source_category,query_label\n"
        "https://example.org/a,2017-2025,research_literature,second\n"
        "https://example.org/b,2017-2025,research_literature,second\n",
        encoding="utf-8",
    )
    captured = {}

    def fake_crawl(args):
        captured["candidates"] = import_candidate_csv(args.csv)
        return 17

    monkeypatch.setattr(cli, "_crawl_candidates", fake_crawl)
    args = Namespace(
        directory=str(tmp_path), pattern="*.csv", db="db.sqlite3", evidence_dir="evidence",
        fast=True, concurrency=None, per_domain=None, delay=None, target_concurrency=None,
    )

    result = cli._crawl_candidate_dir(args)

    assert result == 17
    assert [item.source_url for item in captured["candidates"]] == [
        "https://example.org/a", "https://example.org/b"
    ]


def test_screen_pmc_candidates_writes_only_metadata_screened_rows(tmp_path, monkeypatch):
    import json

    source = tmp_path / "pmc.csv"
    source.write_text(
        "url,period,source_category,query_label,platform_id\n"
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC1/,2017-2025,research_literature,q,PMC1\n"
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC2/,2017-2025,research_literature,q,PMC2\n",
        encoding="utf-8",
    )
    output = tmp_path / "screened.csv"
    review_output = tmp_path / "review.csv"
    report = tmp_path / "screen-report.json"
    monkeypatch.setattr(
        cli,
        "fetch_pmc_esummaries",
        lambda ids: [
            {"pmcid": "PMC1", "title": "China media discourse and public diplomacy in the United States", "abstract": "", "abstract_available": True},
            {"pmcid": "PMC2", "title": "Clinical outcomes in China", "abstract": "", "abstract_available": True},
        ],
    )

    result = cli._screen_pmc_candidates(str(source), str(output), str(review_output), str(report))

    assert result == 0
    screened = import_candidate_csv(output)
    assert [item.platform_id for item in screened] == ["PMC1"]
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["input_count"] == 2
    assert payload["screened_count"] == 1
    assert payload["manual_review_count"] == 0
    assert payload["excluded_count"] == 1


def test_screen_pmc_candidates_retains_missing_public_metadata(tmp_path, monkeypatch):
    import json

    source = tmp_path / "pmc.csv"
    source.write_text(
        "url,period,source_category,query_label,platform_id\n"
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC404/,2017-2025,research_literature,q,PMC404\n",
        encoding="utf-8",
    )
    output = tmp_path / "screened.csv"
    review_output = tmp_path / "review.csv"
    report = tmp_path / "screen-report.json"
    monkeypatch.setattr(cli, "fetch_pmc_esummaries", lambda ids: [])

    cli._screen_pmc_candidates(str(source), str(output), str(review_output), str(report))

    assert len(import_candidate_csv(output)) == 0
    assert len(import_candidate_csv(review_output)) == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["screened_count"] == 0
    assert payload["manual_review_count"] == 1
    assert payload["metadata_missing_candidates_retained"] == ["PMC404"]


def test_screen_pmc_candidates_routes_all_to_review_when_metadata_service_fails(tmp_path, monkeypatch):
    import json
    from urllib.error import URLError

    source = tmp_path / "pmc.csv"
    source.write_text(
        "url,period,source_category,query_label,platform_id\n"
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC503/,2017-2025,research_literature,q,PMC503\n",
        encoding="utf-8",
    )
    output = tmp_path / "screened.csv"
    review_output = tmp_path / "review.csv"
    report = tmp_path / "screen-report.json"

    def unavailable(ids):
        raise URLError("NCBI is temporarily unavailable")

    monkeypatch.setattr(cli, "fetch_pmc_esummaries", unavailable)

    cli._screen_pmc_candidates(str(source), str(output), str(review_output), str(report))

    assert len(import_candidate_csv(output)) == 0
    assert len(import_candidate_csv(review_output)) == 1
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["metadata_fetch_error"] == "<urlopen error NCBI is temporarily unavailable>"
    assert payload["manual_review_count"] == 1
    assert payload["excluded_count"] == 0
