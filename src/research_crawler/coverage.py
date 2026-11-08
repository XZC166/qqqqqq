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


def yearly_coverage(store: ResearchStore) -> list[dict]:
    """Count formal records by publication year and discovered source category."""
    material_counts = {
        row["year"]: row["count"]
        for row in store.connection.execute(
            """SELECT CAST(substr(published_on,1,4) AS INTEGER) AS year, COUNT(*) AS count
               FROM materials
               WHERE published_on >= '1949-01-01' AND published_on < '2026-01-01'
               GROUP BY year"""
        )
    }
    category_counts: dict[int, dict[str, int]] = {}
    for row in store.connection.execute(
        """SELECT CAST(substr(m.published_on,1,4) AS INTEGER) AS year,
                  c.source_category, COUNT(DISTINCT m.id) AS count
           FROM materials m JOIN candidates c ON c.identity_key=m.identity_key
           WHERE m.published_on >= '1949-01-01' AND m.published_on < '2026-01-01'
             AND c.status != 'excluded'
           GROUP BY year, c.source_category"""
    ):
        category_counts.setdefault(row["year"], {})[row["source_category"]] = row["count"]

    rows = []
    for year in range(1949, 2026):
        if year <= 1972:
            period = "1949-1972"
        elif year <= 1991:
            period = "1972-1991"
        elif year <= 2016:
            period = "1992-2016"
        else:
            period = "2017-2025"
        rows.append({
            "year": year,
            "period": period,
            "formal_unique_full_texts": material_counts.get(year, 0),
            "by_source_category": category_counts.get(year, {}),
        })
    return rows


def discovery_batch_coverage(store: ResearchStore) -> list[dict]:
    """Report source/period/query labels without inferring an event taxonomy."""
    batches = store.connection.execute(
        """SELECT b.id, b.period, b.source_category, b.query_label,
                  COUNT(DISTINCT c.id) AS candidate_count,
                  COUNT(DISTINCT CASE WHEN c.status != 'excluded' THEN m.id END)
                    AS formal_unique_materials,
                  COUNT(DISTINCT d.id) AS duplicate_discoveries
           FROM batches b
           LEFT JOIN candidates c ON c.batch_id=b.id
           LEFT JOIN materials m ON m.identity_key=c.identity_key
           LEFT JOIN duplicate_discoveries d ON d.candidate_id=c.id
           GROUP BY b.id, b.period, b.source_category, b.query_label
           ORDER BY b.id"""
    ).fetchall()
    rows = []
    for batch in batches:
        statuses = store.connection.execute(
            """SELECT status, COUNT(*) AS count FROM candidates
               WHERE batch_id=? GROUP BY status""",
            (batch["id"],),
        ).fetchall()
        rows.append({
            "batch_id": batch["id"],
            "period": batch["period"],
            "source_category": batch["source_category"],
            "query_label": batch["query_label"],
            "candidate_count": batch["candidate_count"],
            "formal_unique_materials": batch["formal_unique_materials"],
            "duplicate_discoveries": batch["duplicate_discoveries"],
            "status_counts": {row["status"]: row["count"] for row in statuses},
        })
    return rows


def _applicability(period: str, source_category: str) -> tuple[bool, str]:
    if source_category == "new_media" and period in {"1949-1972", "1972-1991"}:
        return False, "Out of scope: the collection specification includes new-media content only from 2006 onward."
    if source_category == "new_media" and period == "1992-2016":
        return True, "Applicable only for 2006-2016, per the collection specification."
    return True, "Applicable within the stated period and source category."
