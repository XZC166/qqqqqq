import argparse
import csv
import json
import tempfile
from collections import defaultdict
from pathlib import Path

from research_crawler.discovery import (
    PERIODS,
    PMC_DEFAULT_TERM,
    build_query_plan,
    discover_pmc_candidates,
    fetch_pmc_esummaries,
    import_candidate_csv,
    screen_pmc_records,
)
from research_crawler.export import export_verified
from research_crawler.coverage import (
    coverage_gaps,
    coverage_matrix,
    discovery_batch_coverage,
    verification_gaps,
    yearly_coverage,
)
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
    if args.command == "crawl-candidate-dir":
        return _crawl_candidate_dir(args)
    if args.command == "discover-pmc":
        count = discover_pmc_candidates(
            args.period,
            args.output,
            retmax=args.retmax,
            retstart=args.retstart,
            term=args.term,
        )
        print(f"Wrote {count} PMC candidate URL(s) to {args.output}")
        return 0
    if args.command == "screen-pmc-candidates":
        return _screen_pmc_candidates(args.csv, args.output, args.review_output, args.report)
    if args.command == "report":
        store = ResearchStore(args.db)
        try:
            print(render_batch_report(store, args.batch_id))
        finally:
            store.close()
        return 0
    if args.command == "export":
        from research_crawler.quality_audit import ReviewedExportStore

        store = ResearchStore(args.db)
        try:
            export_verified(ReviewedExportStore(store), args.output)
        finally:
            store.close()
        return 0
    if args.command == "deliver":
        from research_crawler.quality_audit import build_reviewed_delivery

        store = ResearchStore(args.db)
        try:
            print(build_reviewed_delivery(store, args.output))
        finally:
            store.close()
        return 0
    if args.command == "revalidate":
        return _revalidate(args)
    if args.command == "repair-pmc-metadata":
        from research_crawler.revalidation import repair_pmc_derived_metadata

        store = ResearchStore(args.db)
        try:
            report = repair_pmc_derived_metadata(store)
        finally:
            store.close()
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Repaired {len(report['repaired'])} PMC record(s); unresolved: {len(report['no_material']) + len(report['mismatch']) + len(report['error'])}")
        return 0
    if args.command == "coverage-audit":
        return _coverage_audit(args)
    if args.command == "import-authorized":
        return _import_authorized(args.manifest, args.file, args.db)
    if args.command == "import-firecrawl":
        return _import_firecrawl(args)
    if args.command == "import-firecrawl-pdf":
        return _import_firecrawl_pdf(args)
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
    crawl_candidates.add_argument(
        "--refresh-verified",
        action="store_true",
        help="re-fetch candidates that already have verified full text",
    )
    _add_throughput_options(crawl_candidates)

    crawl_candidate_dir = commands.add_parser(
        "crawl-candidate-dir", help="merge and crawl all candidate CSV files in a directory"
    )
    crawl_candidate_dir.add_argument("--directory", required=True)
    crawl_candidate_dir.add_argument("--db", default="data/research.sqlite3")
    crawl_candidate_dir.add_argument("--evidence-dir", default="data/evidence")
    crawl_candidate_dir.add_argument("--pattern", default="*.csv")
    crawl_candidate_dir.add_argument(
        "--refresh-verified",
        action="store_true",
        help="re-fetch candidates that already have verified full text",
    )
    _add_throughput_options(crawl_candidate_dir)

    discover_pmc = commands.add_parser(
        "discover-pmc", help="discover open-access PMC candidates through NCBI E-utilities"
    )
    discover_pmc.add_argument("--period", required=True, choices=PERIODS)
    discover_pmc.add_argument("--output", required=True)
    discover_pmc.add_argument("--retmax", type=int, default=500)
    discover_pmc.add_argument("--retstart", type=int, default=0)
    discover_pmc.add_argument("--term", default=PMC_DEFAULT_TERM)

    screen_pmc = commands.add_parser(
        "screen-pmc-candidates",
        help="screen PMC candidates by public title metadata before full-text crawling",
    )
    screen_pmc.add_argument("--csv", required=True)
    screen_pmc.add_argument("--output", required=True)
    screen_pmc.add_argument("--review-output", required=True)
    screen_pmc.add_argument("--report", required=True)

    report = commands.add_parser("report", help="print one batch coverage report")
    report.add_argument("--db", default="data/research.sqlite3")
    report.add_argument("--batch-id", required=True, type=int)

    export = commands.add_parser("export", help="export individually quality-reviewed full texts to nine-column XLSX")
    export.add_argument("--db", default="data/research.sqlite3")
    export.add_argument("--output", required=True)

    deliver = commands.add_parser("deliver", help="verify and package workbook, bodies, evidence and reports")
    deliver.add_argument("--db", default="data/research.sqlite3")
    deliver.add_argument("--output", default="data/materials-delivery.zip")

    revalidate = commands.add_parser(
        "revalidate", help="reparse stored raw evidence without making network requests"
    )
    revalidate.add_argument("--db", default="data/research.sqlite3")
    revalidate.add_argument("--output", required=True)
    revalidate.add_argument(
        "--include-pending",
        action="store_true",
        help="also retry pending candidates whose complete source evidence is already stored",
    )

    repair_pmc = commands.add_parser(
        "repair-pmc-metadata", help="derive missing PMC abstract/keywords from stored verified bodies"
    )
    repair_pmc.add_argument("--db", default="data/research.sqlite3")
    repair_pmc.add_argument("--output", required=True)

    coverage = commands.add_parser(
        "coverage-audit", help="write the complete period/source coverage matrix"
    )
    coverage.add_argument("--db", default="data/research.sqlite3")
    coverage.add_argument("--output", required=True)

    authorized = commands.add_parser("import-authorized", help="import user-provided authorized full text")
    authorized.add_argument("--manifest", required=True)
    authorized.add_argument("--file", required=True)
    authorized.add_argument("--db", default="data/research.sqlite3")

    firecrawl = commands.add_parser(
        "import-firecrawl", help="verify and import raw HTML from a Firecrawl capture"
    )
    firecrawl.add_argument("--capture", required=True)
    firecrawl.add_argument("--url", required=True)
    firecrawl.add_argument("--period", required=True, choices=("1949-1972", "1972-1991", "1992-2016", "2017-2025"))
    firecrawl.add_argument("--category", required=True)
    firecrawl.add_argument("--query-label", required=True)
    firecrawl.add_argument("--db", default="data/research.sqlite3")
    firecrawl.add_argument("--evidence-dir", default="data/evidence")

    firecrawl_pdf = commands.add_parser(
        "import-firecrawl-pdf",
        help="verify a Scrapy PDF against a Firecrawl source-page capture",
    )
    firecrawl_pdf.add_argument("--capture", required=True)
    firecrawl_pdf.add_argument("--url", required=True)
    firecrawl_pdf.add_argument("--metadata-url", required=True)
    firecrawl_pdf.add_argument("--period", required=True, choices=("1949-1972", "1972-1991", "1992-2016", "2017-2025"))
    firecrawl_pdf.add_argument("--category", required=True)
    firecrawl_pdf.add_argument("--query-label", required=True)
    firecrawl_pdf.add_argument("--db", default="data/research.sqlite3")
    firecrawl_pdf.add_argument("--evidence-dir", default="data/evidence")
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


def _screen_pmc_candidates(
    csv_path: str, output: str, review_output: str, report_path: str
) -> int:
    candidates = import_candidate_csv(csv_path)
    ids = list(
        dict.fromkeys(
            candidate.platform_id
            for candidate in candidates
            if candidate.platform_id
        )
    )
    metadata_fetch_error = ""
    try:
        metadata = fetch_pmc_esummaries(ids)
    except OSError as exc:
        metadata = []
        metadata_fetch_error = str(exc)
    metadata_by_id = {record["pmcid"]: record for record in metadata}
    records = []
    missing_ids = []
    for candidate in candidates:
        record = metadata_by_id.get(candidate.platform_id or "")
        if record is None:
            missing_ids.append(candidate.platform_id or candidate.source_url)
            records.append(
                {
                    "pmcid": candidate.platform_id or "",
                    "title": "",
                    "abstract": "",
                    "candidate": candidate,
                }
            )
        else:
            records.append({**record, "candidate": candidate})

    screened_records, review_records, excluded = screen_pmc_records(records)
    screened_rows = {
        (
            record["candidate"].source_url,
            record["candidate"].platform_id or "",
        )
        for record in screened_records
    }
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        fields = ("url", "period", "source_category", "query_label", "platform_id", "metadata_url")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in candidates:
            if (candidate.source_url, candidate.platform_id or "") not in screened_rows:
                continue
            writer.writerow(
                {
                    "url": candidate.source_url,
                    "period": candidate.period,
                    "source_category": candidate.source_category,
                    "query_label": candidate.query_label,
                    "platform_id": candidate.platform_id or "",
                    "metadata_url": candidate.metadata_url or "",
                }
            )

    review_ids = {record["pmcid"] for record in review_records}
    review_destination = Path(review_output)
    review_destination.parent.mkdir(parents=True, exist_ok=True)
    with review_destination.open("w", encoding="utf-8", newline="") as handle:
        fields = ("url", "period", "source_category", "query_label", "platform_id", "metadata_url")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for candidate in candidates:
            if (candidate.platform_id or "") not in review_ids:
                continue
            writer.writerow(
                {
                    "url": candidate.source_url,
                    "period": candidate.period,
                    "source_category": candidate.source_category,
                    "query_label": candidate.query_label,
                    "platform_id": candidate.platform_id or "",
                    "metadata_url": candidate.metadata_url or "",
                }
            )

    report = {
        "input_count": len(candidates),
        "metadata_records": len(metadata),
        "screened_count": len(screened_rows),
        "manual_review_count": len(review_records),
        "excluded_count": len(excluded),
        "manual_review": review_records,
        "excluded": excluded,
        "metadata_missing_candidates_retained": missing_ids,
        "abstract_records": sum(bool(record.get("abstract_available")) for record in metadata),
        "metadata_fetch_error": metadata_fetch_error,
        "policy": "Discovery-only title and PubMed citation abstracts; no article body was fetched or added to formal materials. Missing abstracts are retained for manual review.",
    }
    report_destination = Path(report_path)
    report_destination.parent.mkdir(parents=True, exist_ok=True)
    report_destination.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Screened {len(candidates)} candidate(s): "
        f"{len(screened_rows)} queued for full-text verification, "
        f"{len(review_records)} held for manual review, {len(excluded)} excluded by metadata"
    )
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
            store.add_candidates(batch_id, grouped)
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
    _apply_throughput_options(settings, args)
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

    from research_crawler.discovery import import_candidate_csv
    from research_crawler.spiders.government import GovernmentSpider

    _import_candidates(args.csv, args.db)
    candidates = import_candidate_csv(args.csv)
    store = ResearchStore(args.db)
    try:
        eligible = _unverified_candidates(
            candidates, store, refresh_verified=getattr(args, "refresh_verified", False)
        )
    finally:
        store.close()
    skipped = len(candidates) - len(eligible)
    if skipped:
        print(f"Skipped {skipped} already-verified candidate URL(s)")
    if not eligible:
        return 0

    fieldnames = ("url", "period", "source_category", "query_label", "platform_id", "metadata_url")
    temporary_path = None
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False
    ) as handle:
        temporary_path = Path(handle.name)
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in eligible:
            writer.writerow(
                {
                    "url": candidate.source_url,
                    "period": candidate.period,
                    "source_category": candidate.source_category,
                    "query_label": candidate.query_label,
                    "platform_id": candidate.platform_id or "",
                    "metadata_url": candidate.metadata_url or "",
                }
            )

    try:
        settings = get_project_settings()
        settings.set("DATABASE_PATH", args.db, priority="cmdline")
        settings.set("EVIDENCE_DIR", args.evidence_dir, priority="cmdline")
        _apply_throughput_options(settings, args)
        process = CrawlerProcess(settings)
        process.crawl(GovernmentSpider, candidates_csv=str(temporary_path))
        process.start()
    finally:
        temporary_path.unlink(missing_ok=True)
    return 0


def _unverified_candidates(candidates, store, *, refresh_verified: bool = False):
    eligible = []
    candidates = list(candidates)
    identities = store.resolve_candidate_identities(candidates)
    excluded = {row[0] for row in store.connection.execute(
        "SELECT identity_key FROM candidates WHERE status = 'excluded'"
    )}
    existing = {row[0] for row in store.connection.execute(
        "SELECT identity_key FROM materials"
    )}
    for candidate, identity in zip(candidates, identities):
        if identity in excluded:
            continue
        if refresh_verified:
            eligible.append(candidate)
            continue
        if identity not in existing:
            eligible.append(candidate)
        else:
            with store.connection:
                store.connection.execute(
                    """UPDATE candidates SET status = 'verified',
                              status_detail = 'matched existing verified material; request skipped'
                       WHERE identity_key = ? AND status != 'excluded'""",
                    (identity,),
                )
    return eligible


def _crawl_candidate_dir(args) -> int:
    """Run one Scrapy process for a directory of validated candidate CSVs."""
    from research_crawler.discovery import import_candidate_csv

    directory = Path(args.directory)
    files = sorted(directory.glob(args.pattern))
    if not files:
        raise SystemExit(f"no candidate CSV files found in {directory}")

    # Keep one request per normalized source URL/platform id in this run. The
    # database still owns cross-run deduplication and duplicate_count updates.
    unique = {}
    for path in files:
        for candidate in import_candidate_csv(path):
            key = (candidate.source_url, candidate.platform_id or "")
            unique.setdefault(key, candidate)

    fieldnames = ("url", "period", "source_category", "query_label", "platform_id", "metadata_url")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", suffix=".csv", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for candidate in unique.values():
                writer.writerow(
                    {
                        "url": candidate.source_url,
                        "period": candidate.period,
                        "source_category": candidate.source_category,
                        "query_label": candidate.query_label,
                        "platform_id": candidate.platform_id or "",
                        "metadata_url": candidate.metadata_url or "",
                    }
                )
        args.csv = str(temporary_path)
        return _crawl_candidates(args)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _add_throughput_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--fast",
        action="store_true",
        help="use a polite higher-throughput profile (robots and per-domain cap remain enabled)",
    )
    parser.add_argument("--concurrency", type=int, help="global concurrent requests")
    parser.add_argument("--per-domain", type=int, help="concurrent requests per domain")
    parser.add_argument("--delay", type=float, help="download delay in seconds")
    parser.add_argument(
        "--target-concurrency", type=float, help="AutoThrottle target concurrency per domain"
    )


def _apply_throughput_options(settings, args) -> None:
    values = {}
    if getattr(args, "fast", False):
        values.update(
            CONCURRENT_REQUESTS=8,
            CONCURRENT_REQUESTS_PER_DOMAIN=2,
            DOWNLOAD_DELAY=0.25,
            DOWNLOAD_DELAY_JITTER=0.0,
            AUTOTHROTTLE_START_DELAY=0.25,
            AUTOTHROTTLE_TARGET_CONCURRENCY=1.0,
            AUTOTHROTTLE_MAX_DELAY=10.0,
        )
    if getattr(args, "concurrency", None) is not None:
        values["CONCURRENT_REQUESTS"] = max(1, args.concurrency)
    if getattr(args, "per_domain", None) is not None:
        values["CONCURRENT_REQUESTS_PER_DOMAIN"] = max(1, args.per_domain)
    if getattr(args, "delay", None) is not None:
        values["DOWNLOAD_DELAY"] = max(0.0, args.delay)
    if getattr(args, "target_concurrency", None) is not None:
        values["AUTOTHROTTLE_TARGET_CONCURRENCY"] = max(0.1, args.target_concurrency)
    for name, value in values.items():
        settings.set(name, value, priority="cmdline")


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


def _revalidate(args) -> int:
    from research_crawler.revalidation import (
        revalidate_legacy_materials,
        revalidate_pending_candidates,
    )

    store = ResearchStore(args.db)
    try:
        report = revalidate_legacy_materials(store)
        if args.include_pending:
            report["pending_candidates"] = revalidate_pending_candidates(store)
    finally:
        store.close()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unresolved_legacy = sum(
        len(report[key])
        for key in ("mismatch", "no_material", "missing_supporting_evidence", "error")
    )
    print(
        f"Revalidated {len(report['exact'])} exact legacy material(s); "
        f"left {unresolved_legacy} unresolved"
    )
    if "pending_candidates" in report:
        print(
            f"Revalidated {len(report['pending_candidates']['verified'])} pending candidate(s) "
            f"from local evidence; left {len(report['pending_candidates']['pending'])} pending"
        )
    return 0


def _coverage_audit(args) -> int:
    store = ResearchStore(args.db)
    try:
        matrix = coverage_matrix(store)
        gaps = coverage_gaps(store)
        full_text_gaps = verification_gaps(store)
        yearly = yearly_coverage(store)
        batches = discovery_batch_coverage(store)
    finally:
        store.close()
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "matrix": matrix,
                "yearly": yearly,
                "discovery_batches": batches,
                "gaps": gaps,
                "verification_gaps": full_text_gaps,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(matrix)} coverage cells; {len(gaps)} have no candidate URL(s), "
        f"{len(full_text_gaps)} have no verified full text(s)"
    )
    return 0


def _import_firecrawl(args) -> int:
    from research_crawler.firecrawl_import import import_firecrawl_capture

    status = import_firecrawl_capture(
        capture_path=args.capture,
        source_url=args.url,
        period=args.period,
        source_category=args.category,
        query_label=args.query_label,
        database_path=args.db,
        evidence_dir=args.evidence_dir,
    )
    print(f"Firecrawl capture processed; candidate status: {status}")
    return 0


def _import_firecrawl_pdf(args) -> int:
    from research_crawler.firecrawl_import import import_firecrawl_pdf_capture

    status = import_firecrawl_pdf_capture(
        capture_path=args.capture,
        source_url=args.url,
        metadata_url=args.metadata_url,
        period=args.period,
        source_category=args.category,
        query_label=args.query_label,
        database_path=args.db,
        evidence_dir=args.evidence_dir,
    )
    print(f"Paired PDF capture processed; candidate status: {status}")
    return 0
