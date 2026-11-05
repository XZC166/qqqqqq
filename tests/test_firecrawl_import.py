import hashlib
import json
from pathlib import Path

import pytest

from research_crawler.cli import main
from research_crawler.store import ResearchStore
from research_crawler.validation import ValidationError


URL = "https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/"


def _capture(html: str) -> dict:
    return {
        "structuredContent": {
            "success": True,
            "rawHtml": html,
            "metadata": {
                "sourceURL": URL,
                "url": URL,
                "statusCode": 200,
                "scrapeId": "firecrawl-test-123",
            },
        },
    }


def test_import_firecrawl_raw_html_uses_same_verification_pipeline(tmp_path):
    source_html = Path(__file__).parent / "fixtures" / "state_department_remarks.html"
    html = source_html.read_text(encoding="utf-8")
    capture_file = tmp_path / "firecrawl-result.json"
    capture_file.write_text(json.dumps(_capture(html)), encoding="utf-8")
    database = tmp_path / "research.sqlite3"
    evidence_dir = tmp_path / "evidence"

    result = main([
        "import-firecrawl",
        "--capture", str(capture_file),
        "--url", URL,
        "--period", "2017-2025",
        "--category", "government",
        "--query-label", "state-dept-remarks-economic-coercion",
        "--db", str(database),
        "--evidence-dir", str(evidence_dir),
    ])

    assert result == 0
    store = ResearchStore(database)
    assert len(store.get_verified_materials()) == 1
    row = store.connection.execute(
        "SELECT e.content_sha256, e.evidence_path, e.body_complete, e.metadata_verified, "
        "e.retrieval_method, e.retrieval_id "
        "FROM evidence e JOIN materials m ON m.evidence_id = e.id"
    ).fetchone()
    evidence_path = Path(row["evidence_path"])
    assert evidence_path.read_bytes() == html.encode("utf-8")
    assert row["content_sha256"] == hashlib.sha256(html.encode("utf-8")).hexdigest()
    assert row["body_complete"] == 1
    assert row["metadata_verified"] == 1
    assert row["retrieval_method"] == "firecrawl"
    assert row["retrieval_id"] == "firecrawl-test-123"
    store.close()


@pytest.mark.parametrize(
    "capture, message",
    [
        ({"success": True, "markdown": "a summary", "metadata": {"sourceURL": URL, "statusCode": 200, "scrapeId": "x"}}, "rawHtml"),
        ({"success": True, "rawHtml": "<html></html>", "metadata": {"sourceURL": "https://other.example/page", "statusCode": 200, "scrapeId": "x"}}, "sourceURL"),
        ({"success": True, "rawHtml": "<html></html>", "metadata": {"sourceURL": URL, "url": "https://other.example/page", "statusCode": 200, "scrapeId": "x"}}, "metadata url"),
        ({"success": False, "rawHtml": "<html></html>", "metadata": {"sourceURL": URL, "statusCode": 200, "scrapeId": "x"}}, "success"),
        ({"success": True, "rawHtml": "<html></html>", "metadata": {"sourceURL": URL, "url": URL, "statusCode": 200}}, "scrapeId"),
    ],
)
def test_import_firecrawl_rejects_unusable_or_unproven_capture(tmp_path, capture, message):
    from research_crawler.firecrawl_import import import_firecrawl_capture

    capture_file = tmp_path / "capture.json"
    capture_file.write_text(json.dumps(capture), encoding="utf-8")

    with pytest.raises(ValidationError, match=message):
        import_firecrawl_capture(
            capture_path=capture_file,
            source_url=URL,
            period="2017-2025",
            source_category="government",
            query_label="fixture",
            database_path=tmp_path / "state.sqlite3",
            evidence_dir=tmp_path / "evidence",
        )

    assert not (tmp_path / "state.sqlite3").exists()
