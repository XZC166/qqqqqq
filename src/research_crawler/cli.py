import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from research_crawler.discovery import build_query_plan, import_candidate_csv
from research_crawler.export import export_verified
from research_crawler.import_authorized import import_authorized_full_text
from research_crawler.items import VerifiedMaterial
from research_crawler.report import render_batch_report
from research_crawler.store import ResearchStore


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "plan":
        return _write_query_plan(args.period, args.category, args.output)
    if args.command == "import-candidates":
        return _import_candidates(args.csv, args.db)
    if args.command == "crawl":
        return _crawl(args)
    if args.command == "crawl-candidates":
        return _crawl_candidates(args)
    if args.command == "report":
        store = ResearchStore(args.db)
        try:
            print(render_batch_report(store, args.batch_id))
        finally:
            store.close()
        return 0
    if args.command == "export":
        store = ResearchStore(args.db)
        try:
            export_verified(store, args.output)
        finally:
            store.close()
        return 0
    if args.command == "import-authorized":
        return _import_authorized(args.manifest, args.file, args.db)
    parser.error("unknown command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="research-crawler")
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="write period/source search queries")
    plan.add_argument("--period", required=True)
    plan.add_argument("--category", required=True)
    plan.add_argument("--output", required=True)

    candidates = commands.add_parser("import-candidates", help="import candidate URLs from CSV")
    candidates.add_argument("--csv", required=True)
    candidates.add_argument("--db", default="data/research.sqlite3")

    crawl = commands.add_parser("crawl", help="crawl one explicitly supplied public source page")
    crawl.add_argument("--url", required=True)
    crawl.add_argument("--period", required=True, choices=("1949-1972", "1972-1991", "1992-2016", "2017-2025"))
    crawl.add_argument("--category", required=True)
    crawl.add_argument("--query-label", required=True)
    crawl.add_argument("--db", default="data/research.sqlite3")
    crawl.add_argument("--evidence-dir", default="data/evidence")

    crawl_candidates = commands.add_parser(
        "crawl-candidates", help="crawl candidate URLs from a CSV file"
    )
    crawl_candidates.add_argument("--csv", required=True)
    crawl_candidates.add_argument("--db", default="data/research.sqlite3")
    crawl_candidates.add_argument("--evidence-dir", default="data/evidence")

    report = commands.add_parser("report", help="print one batch coverage report")
    report.add_argument("--db", default="data/research.sqlite3")
    report.add_argument("--batch-id", required=True, type=int)

    export = commands.add_parser("export", help="export verified materials to nine-column XLSX")
    export.add_argument("--db", default="data/research.sqlite3")
    export.add_argument("--output", required=True)

    authorized = commands.add_parser("import-authorized", help="import user-provided authorized full text")
    authorized.add_argument("--manifest", required=True)
    authorized.add_argument("--file", required=True)
    authorized.add_argument("--db", default="data/research.sqlite3")
    return parser


def _write_query_plan(period: str, category: str, output: str) -> int:
    queries = build_query_plan(period, category)
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("period", "source_category", "event_term", "topic_term", "query_label", "query"),
        )
        writer.writeheader()
        writer.writerows(query.__dict__ for query in queries)
    print(f"Wrote {len(queries)} queries to {destination}")
    return 0


def _import_candidates(csv_path: str, database_path: str) -> int:
    candidates = import_candidate_csv(csv_path)
    groups = defaultdict(list)
    for candidate in candidates:
        groups[(candidate.period, candidate.source_category, candidate.query_label)].append(candidate)
    store = ResearchStore(database_path)
    try:
        for (period, category, label), grouped in groups.items():
            batch_id = store.create_batch(period, category, label)
            for candidate in grouped:
                store.add_candidate(batch_id, candidate)
    finally:
        store.close()
    print(f"Imported {len(candidates)} candidate URL(s) in {len(groups)} batch(es)")
    return 0


def _crawl(args) -> int:
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    from research_crawler.spiders.government import GovernmentSpider
    from research_crawler.items import MaterialCandidate

    store = ResearchStore(args.db)
    try:
        batch_id = store.create_batch(args.period, args.category, args.query_label)
        store.add_candidate(
            batch_id,
            MaterialCandidate(args.url, args.period, args.category, args.query_label),
        )
    finally:
        store.close()

    settings = get_project_settings()
    settings.set("DATABASE_PATH", args.db, priority="cmdline")
    settings.set("EVIDENCE_DIR", args.evidence_dir, priority="cmdline")
    process = CrawlerProcess(settings)
    process.crawl(
        GovernmentSpider,
        url=args.url,
        period=args.period,
        source_category=args.category,
        query_label=args.query_label,
    )
    process.start()
    return 0


def _crawl_candidates(args) -> int:
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings

    from research_crawler.spiders.government import GovernmentSpider

    _import_candidates(args.csv, args.db)

    settings = get_project_settings()
    settings.set("DATABASE_PATH", args.db, priority="cmdline")
    settings.set("EVIDENCE_DIR", args.evidence_dir, priority="cmdline")
    process = CrawlerProcess(settings)
    process.crawl(GovernmentSpider, candidates_csv=args.csv)
    process.start()
    return 0


def _import_authorized(manifest_path: str, file_path: str, database_path: str) -> int:
    with Path(manifest_path).open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    material = VerifiedMaterial(
        source=manifest["source"],
        time=manifest["time"],
        author=manifest.get("author", "未注明"),
        title=manifest["title"],
        abstract=manifest.get("abstract", ""),
        keywords=manifest.get("keywords", ""),
        body="",
        source_url=manifest["source_url"],
    )
    store = ResearchStore(database_path)
    try:
        import_authorized_full_text(
            store=store,
            candidate_id=int(manifest["candidate_id"]),
            file_path=file_path,
            material=material,
            authorization_note=manifest["authorization_note"],
            completeness_confirmed=bool(manifest["completeness_confirmed"]),
            field_sources=manifest["field_sources"],
            abstract_origin=manifest.get("abstract_origin", "publisher"),
        )
    finally:
        store.close()
    print("Authorized full text imported and verified")
    return 0
