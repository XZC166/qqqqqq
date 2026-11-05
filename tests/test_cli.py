import csv

from openpyxl import load_workbook

from research_crawler.cli import main
from research_crawler.store import ResearchStore


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


def test_export_command_creates_workbook_with_fixed_header(tmp_path):
    database = tmp_path / "research.sqlite3"
    ResearchStore(database).close()
    workbook_path = tmp_path / "output.xlsx"

    result = main(["export", "--db", str(database), "--output", str(workbook_path)])

    assert result == 0
    rows = list(load_workbook(workbook_path, read_only=True).active.iter_rows(values_only=True))
    assert rows[0] == ("来源", "时间", "作者", "标题", "摘要", "关键词", "正文", "来源链接", "重复计数")
