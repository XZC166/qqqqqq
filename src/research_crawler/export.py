import hashlib
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

from research_crawler.items import EXPORT_COLUMNS
from research_crawler.store import ResearchStore


EXCEL_CELL_LIMIT = 32767


def export_verified(store: ResearchStore, workbook_path: str | Path) -> Path:
    destination = Path(workbook_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    body_directory = destination.parent / f"{destination.stem}_bodies"

    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet("资料")
    sheet.append(list(EXPORT_COLUMNS))

    for material in store.get_verified_materials():
        body_value = material.body
        if _excel_character_count(body_value) > EXCEL_CELL_LIMIT:
            body_directory.mkdir(parents=True, exist_ok=True)
            record_hash = hashlib.sha256(
                f"{material.source_url}\0{material.body}".encode("utf-8")
            ).hexdigest()
            body_path = body_directory / f"body-{record_hash}.txt"
            with body_path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(material.body)
            body_value = body_path.relative_to(destination.parent).as_posix()

        values = (
            material.source,
            material.time,
            material.author,
            material.title,
            material.abstract,
            material.keywords,
            body_value,
            material.source_url,
            material.duplicate_count,
        )
        cells = []
        for value in values:
            cell = WriteOnlyCell(sheet, value=value)
            if isinstance(value, str):
                cell.data_type = "s"
            cells.append(cell)
        sheet.append(cells)

    workbook.save(destination)
    return destination


def _excel_character_count(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2
