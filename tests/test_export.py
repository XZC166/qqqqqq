from openpyxl import load_workbook

from research_crawler.export import export_verified
from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.store import ResearchStore


def add_verified(store, body: str, duplicate_count: int = 0) -> None:
    batch_id = store.create_batch("2017-2025", "government", "sample")
    url = "https://example.org/story"
    candidate_id = store.add_candidate(
        batch_id,
        MaterialCandidate(url, "2017-2025", "government", "sample"),
    )
    for occurrence in range(duplicate_count):
        duplicate_batch = store.create_batch(
            "2017-2025", "government", f"sample-duplicate-{occurrence + 1}"
        )
        store.add_candidate(
            duplicate_batch,
            MaterialCandidate(
                url,
                "2017-2025",
                "government",
                f"sample-duplicate-{occurrence + 1}",
            ),
        )
    evidence_id = store.add_evidence(
        candidate_id,
        SourceEvidence(
            source_url=url,
            fetched_at="2026-11-06T00:00:00Z",
            status_code=200,
            content_sha256="verified-hash",
            body_complete=True,
            metadata_verified=True,
        ),
        access_status="allow",
    )
    store.add_verified_material(
        candidate_id,
        evidence_id,
        VerifiedMaterial(
            "Example Agency",
            "2020-01-02",
            "未注明",
            "Example title",
            "Publisher abstract",
            "China; policy",
            body,
            url,
            0,
        ),
        field_sources={
            name: url
            for name in ("source", "time", "author", "title", "abstract", "keywords")
        },
    )


def test_export_uses_exact_nine_columns_and_verbatim_body(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    add_verified(store, "First paragraph.\n\nSecond paragraph.", duplicate_count=2)
    workbook_path = tmp_path / "records.xlsx"

    export_verified(store, workbook_path)

    sheet = load_workbook(workbook_path, read_only=True).active
    rows = list(sheet.iter_rows(values_only=True))
    assert rows[0] == ("来源", "时间", "作者", "标题", "摘要", "关键词", "正文", "来源链接", "重复计数")
    assert rows[1][1:4] == ("2020-01-02", "未注明", "Example title")
    assert rows[1][6] == "First paragraph.\n\nSecond paragraph."
    assert rows[1][8] == 2
    store.close()


def test_long_body_is_saved_in_full_as_utf8_and_cell_has_relative_path(tmp_path):
    body = "原文段落。" * 11000
    store = ResearchStore(tmp_path / "research.sqlite3")
    add_verified(store, body)
    workbook_path = tmp_path / "records.xlsx"

    export_verified(store, workbook_path)

    sheet = load_workbook(workbook_path, read_only=True).active
    body_reference = sheet.cell(row=2, column=7).value
    body_file = tmp_path / body_reference
    assert body_reference.startswith("records_bodies/")
    assert body_file.read_text(encoding="utf-8") == body
    assert body_file.stat().st_size > 32767
    store.close()


def test_unverified_candidate_never_appears_in_export(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite3")
    batch_id = store.create_batch("2017-2025", "government", "sample")
    store.add_candidate(
        batch_id,
        MaterialCandidate("https://example.org/snippet", "2017-2025", "government", "sample"),
    )
    workbook_path = tmp_path / "records.xlsx"

    export_verified(store, workbook_path)

    sheet = load_workbook(workbook_path, read_only=True).active
    assert list(sheet.iter_rows(values_only=True)) == [
        ("来源", "时间", "作者", "标题", "摘要", "关键词", "正文", "来源链接", "重复计数")
    ]
    store.close()
