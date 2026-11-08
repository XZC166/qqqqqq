from research_crawler.store import ResearchStore


def render_batch_report(store: ResearchStore, batch_id: int) -> str:
    batch = store.batch_metadata(batch_id)
    counts = store.batch_summary(batch_id)
    lines = [
        f"Batch {batch_id}: {batch['period']} / {batch['source_category']} / {batch['query_label']}",
        f"candidate: {counts['candidate']}",
        f"verified full text: {counts['verified']}",
        f"restricted: {counts['restricted']}",
        f"duplicate: {counts['duplicate']}",
        f"pending: {counts['pending']}",
        f"unprocessed: {counts['unprocessed']}",
        f"excluded: {counts['excluded']}",
        "Uncovered or restricted candidates:",
    ]
    uncovered = store.batch_uncovered(batch_id)
    if uncovered:
        lines.extend(
            f"- [{row['status']}] {row['source_url']} {row['status_detail']}".rstrip()
            for row in uncovered
        )
    else:
        lines.append("- none recorded")
    lines.append("Coverage is limited to the sources checked; this report is not exhaustive.")
    return "\n".join(lines)
