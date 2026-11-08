from collections import Counter

from research_crawler.discovery import PERIODS, SOURCE_TERMS
from research_crawler.store import ResearchStore


_STATUSES = ("candidate", "pending", "restricted", "verified", "excluded")


def coverage_matrix(store: ResearchStore) -> list[dict]:
    """Return a complete period/source matrix, including cells with no candidates."""
    rows = []
    for period in PERIODS:
        for source_category, source_terms in SOURCE_TERMS.items():
            status_rows = store.connection.execute(
                """SELECT status, COUNT(*) AS count
                   FROM candidates
                   WHERE period=? AND source_category=?
                   GROUP BY status""",
                (period, source_category),
            ).fetchall()
            counts = Counter({row["status"]: row["count"] for row in status_rows})
            verified = store.connection.execute(
                """SELECT COUNT(DISTINCT m.id) AS count
                   FROM candidates c JOIN materials m
                     ON m.identity_key=c.identity_key
                   WHERE c.period=? AND c.source_category=?""",
                (period, source_category),
            ).fetchone()["count"]
            candidate_count = sum(counts.values())
            applicable, applicability_note = _applicability(period, source_category)
            rows.append({
                "period": period,
                "source_category": source_category,
                "source_terms": list(source_terms),
                "applicable": applicable,
                "applicability_note": applicability_note,
                "candidate_count": candidate_count,
                "verified_unique_materials": verified,
                "has_verified_materials": verified > 0,
                "status_counts": {status: counts.get(status, 0) for status in _STATUSES},
                "has_candidates": candidate_count > counts.get("excluded", 0),
            })
    return rows


def coverage_gaps(store: ResearchStore) -> list[dict]:
    """Return cells without any candidate URL for follow-up discovery."""
    return [
        row for row in coverage_matrix(store)
        if row["applicable"] and not row["has_candidates"]
    ]


def verification_gaps(store: ResearchStore) -> list[dict]:
    """Return applicable cells without any linked verified full-text material."""
    return [
        row for row in coverage_matrix(store)
        if row["applicable"] and not row["has_verified_materials"]
    ]


def _applicability(period: str, source_category: str) -> tuple[bool, str]:
    if source_category == "new_media" and period in {"1949-1972", "1972-1991"}:
        return False, "Out of scope: the collection specification includes new-media content only from 2006 onward."
    if source_category == "new_media" and period == "1992-2016":
        return True, "Applicable only for 2006-2016, per the collection specification."
    return True, "Applicable within the stated period and source category."
