import sqlite3
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.validation import validate_material


class ResearchStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def create_batch(self, period: str, source_category: str, query_label: str) -> int:
        self.connection.execute(
            "INSERT OR IGNORE INTO batches(period, source_category, query_label) VALUES (?, ?, ?)",
            (period, source_category, query_label),
        )
        batch_id = self.connection.execute(
            "SELECT id FROM batches WHERE period = ? AND source_category = ? AND query_label = ?",
            (period, source_category, query_label),
        ).fetchone()[0]
        self.connection.commit()
        return int(batch_id)

    def add_candidate(self, batch_id: int, candidate: MaterialCandidate) -> int:
        identity = self._resolve_identity_key(candidate.source_url, candidate.platform_id)
        existing_in_batch = self.connection.execute(
            "SELECT id FROM candidates WHERE batch_id = ? AND identity_key = ? LIMIT 1",
            (batch_id, identity),
        ).fetchone()
        if existing_in_batch:
            if candidate.metadata_url:
                self.connection.execute(
                    "UPDATE candidates SET metadata_url = ? WHERE id = ? AND (metadata_url IS NULL OR metadata_url = '')",
                    (candidate.metadata_url, existing_in_batch["id"]),
                )
                self.connection.commit()
            return int(existing_in_batch["id"])
        previously_seen = self.connection.execute(
            "SELECT 1 FROM candidates WHERE identity_key = ? LIMIT 1", (identity,)
        ).fetchone()
        cursor = self.connection.execute(
            """INSERT INTO candidates(
                   batch_id, source_url, period, source_category, query_label,
                   platform_id, identity_key, metadata_url
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                batch_id,
                candidate.source_url,
                candidate.period,
                candidate.source_category,
                candidate.query_label,
                candidate.platform_id,
                identity,
                candidate.metadata_url,
            ),
        )
        candidate_id = int(cursor.lastrowid)
        if previously_seen:
            self.connection.execute(
                "INSERT INTO duplicate_discoveries(batch_id, candidate_id, identity_key) VALUES (?, ?, ?)",
                (batch_id, candidate_id, identity),
            )
            self.connection.execute(
                "UPDATE materials SET duplicate_count = duplicate_count + 1 WHERE identity_key = ?",
                (identity,),
            )
        self.connection.commit()
        return candidate_id

    def update_candidate_status(
        self, candidate_id: int, status: str, detail: str = ""
    ) -> None:
        if status not in {"candidate", "restricted", "pending", "verified", "excluded"}:
            raise ValueError(f"invalid candidate status: {status}")
        self.connection.execute(
            "UPDATE candidates SET status = ?, status_detail = ? WHERE id = ?",
            (status, detail, candidate_id),
        )
        self.connection.commit()

    def add_evidence(
        self,
        candidate_id: int,
        evidence: SourceEvidence,
        access_status: str,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO evidence(
                   candidate_id, source_url, fetched_at, status_code, content_sha256,
                   evidence_path, body_complete, metadata_verified, body_format,
                   original_page_verified, access_status, authorization_note,
                   retrieval_method, retrieval_id
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                candidate_id,
                evidence.source_url,
                evidence.fetched_at,
                evidence.status_code,
                evidence.content_sha256,
                str(evidence.evidence_path) if evidence.evidence_path else None,
                int(evidence.body_complete),
                int(evidence.metadata_verified),
                evidence.body_format,
                int(evidence.original_page_verified),
                access_status,
                evidence.authorization_note,
                evidence.retrieval_method,
                evidence.retrieval_id,
            ),
        )
        if access_status == "restricted":
            self.connection.execute(
                "UPDATE candidates SET status = 'restricted' WHERE id = ?",
                (candidate_id,),
            )
        self.connection.commit()
        return int(cursor.lastrowid)

    def add_verified_material(
        self,
        candidate_id: int,
        evidence_id: int,
        material: VerifiedMaterial,
        *,
        abstract_origin: str = "publisher",
        field_sources: dict[str, str] | None = None,
        metadata_evidence_ids: set[int] | None = None,
    ) -> tuple[int, bool]:
        evidence = self.connection.execute(
            "SELECT * FROM evidence WHERE id = ? AND candidate_id = ?",
            (evidence_id, candidate_id),
        ).fetchone()
        if evidence is None:
            raise ValueError("evidence does not belong to candidate")
        if evidence["access_status"] != "allow":
            raise ValueError("only allowed source evidence can be promoted")
        if not evidence["body_complete"]:
            raise ValueError("evidence body must be complete")
        if canonicalize_url(evidence["source_url"]) != canonicalize_url(material.source_url):
            raise ValueError("material URL must match evidence source URL")

        metadata_evidence_ids = metadata_evidence_ids or set()
        metadata_rows = []
        if metadata_evidence_ids:
            placeholders = ",".join("?" for _ in metadata_evidence_ids)
            metadata_rows = self.connection.execute(
                f"""SELECT source_url FROM evidence
                    WHERE candidate_id = ? AND id IN ({placeholders})
                      AND access_status = 'allow' AND status_code >= 200 AND status_code < 300
                      AND metadata_verified = 1""",
                (candidate_id, *metadata_evidence_ids),
            ).fetchall()
            if len(metadata_rows) != len(metadata_evidence_ids):
                raise ValueError("metadata evidence must be allowed, successful, and verified")
            candidate_metadata = self.connection.execute(
                "SELECT metadata_url FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()["metadata_url"]
            if not candidate_metadata or canonicalize_url(candidate_metadata) not in {
                canonicalize_url(row["source_url"]) for row in metadata_rows
            }:
                raise ValueError("metadata evidence does not match the candidate's declared metadata URL")
        if not evidence["metadata_verified"] and not metadata_rows:
            raise ValueError("evidence metadata must be verified")
        metadata_urls = {row["source_url"] for row in metadata_rows}
        if evidence["metadata_verified"]:
            metadata_urls.add(evidence["source_url"])

        material = validate_material(
            material,
            SourceEvidence(
                source_url=evidence["source_url"],
                fetched_at=evidence["fetched_at"],
                status_code=evidence["status_code"],
                content_sha256=evidence["content_sha256"],
                evidence_path=Path(evidence["evidence_path"]) if evidence["evidence_path"] else None,
                body_complete=bool(evidence["body_complete"]),
                metadata_verified=bool(evidence["metadata_verified"]),
                body_format=evidence["body_format"],
                original_page_verified=bool(evidence["original_page_verified"]),
            ),
            field_sources or {
                name: material.source_url for name in ("source", "time", "author", "title")
            },
            abstract_origin=abstract_origin,
            metadata_evidence_urls=metadata_urls,
            period=self.connection.execute(
                "SELECT period FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()["period"],
        )

        candidate = self.connection.execute(
            "SELECT identity_key FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        identity = candidate["identity_key"]
        existing = self.connection.execute(
            "SELECT id FROM materials WHERE identity_key = ?", (identity,)
        ).fetchone()
        if existing:
            with self.connection:
                self.connection.execute(
                    """UPDATE materials
                       SET source = ?, published_on = ?, author = ?, title = ?, abstract = ?,
                           keywords = ?, body = ?, source_url = ?, evidence_id = ?
                       WHERE id = ?""",
                    (
                        material.source,
                        material.time,
                        material.author,
                        material.title,
                        material.abstract,
                        material.keywords,
                        material.body,
                        material.source_url,
                        evidence_id,
                        existing["id"],
                    ),
                )
                self._save_verification_snapshot(
                    int(existing["id"]), evidence_id, material, abstract_origin,
                    field_sources, metadata_evidence_ids,
                )
            return int(existing["id"]), False

        duplicate_count = self.connection.execute(
            "SELECT COUNT(*) FROM duplicate_discoveries WHERE identity_key = ?",
            (identity,),
        ).fetchone()[0]

        with self.connection:
            cursor = self.connection.execute(
                """INSERT INTO materials(
                       identity_key, source, published_on, author, title, abstract,
                       keywords, body, source_url, duplicate_count, evidence_id
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    identity,
                    material.source,
                    material.time,
                    material.author,
                    material.title,
                    material.abstract,
                    material.keywords,
                    material.body,
                    material.source_url,
                    duplicate_count,
                    evidence_id,
                ),
            )
            self._save_verification_snapshot(
                int(cursor.lastrowid), evidence_id, material, abstract_origin,
                field_sources, metadata_evidence_ids,
            )
        return int(cursor.lastrowid), True

    def _save_verification_snapshot(
        self, material_id: int, evidence_id: int, material: VerifiedMaterial,
        abstract_origin: str, field_sources: dict[str, str] | None,
        metadata_evidence_ids: set[int],
    ) -> None:
        sources = field_sources or {
            name: material.source_url for name in ("source", "time", "author", "title")
        }
        self.connection.execute(
            """INSERT INTO material_verifications(
                   material_id,primary_evidence_id,abstract_origin,field_sources
               ) VALUES (?,?,?,?) ON CONFLICT(material_id) DO UPDATE SET
                   primary_evidence_id=excluded.primary_evidence_id,
                   abstract_origin=excluded.abstract_origin,
                   field_sources=excluded.field_sources,verified_at=CURRENT_TIMESTAMP""",
            (material_id, evidence_id, abstract_origin, json.dumps(sources, ensure_ascii=False)),
        )
        self.connection.execute(
            "DELETE FROM material_metadata_evidence WHERE material_id=?", (material_id,)
        )
        self.connection.executemany(
            "INSERT INTO material_metadata_evidence(material_id,evidence_id) VALUES (?,?)",
            [(material_id, value) for value in sorted(metadata_evidence_ids)],
        )

    def get_verified_materials(self) -> list[VerifiedMaterial]:
        rows = self.connection.execute(
            """SELECT source, published_on, author, title, abstract, keywords, body,
                      source_url, duplicate_count
               FROM materials ORDER BY id"""
        ).fetchall()
        return [
            VerifiedMaterial(
                source=row["source"],
                time=row["published_on"],
                author=row["author"],
                title=row["title"],
                abstract=row["abstract"],
                keywords=row["keywords"],
                body=row["body"],
                source_url=row["source_url"],
                duplicate_count=row["duplicate_count"],
            )
            for row in rows
        ]

    def batch_summary(self, batch_id: int) -> dict[str, int]:
        candidate_count = self.connection.execute(
            "SELECT COUNT(*) FROM candidates WHERE batch_id = ?", (batch_id,)
        ).fetchone()[0]
        restricted_count = self.connection.execute(
            "SELECT COUNT(*) FROM candidates WHERE batch_id = ? AND status = 'restricted'",
            (batch_id,),
        ).fetchone()[0]
        verified_count = self.connection.execute(
            "SELECT COUNT(*) FROM candidates WHERE batch_id = ? AND status = 'verified'",
            (batch_id,),
        ).fetchone()[0]
        duplicate_count = self.connection.execute(
            "SELECT COUNT(*) FROM duplicate_discoveries WHERE batch_id = ?",
            (batch_id,),
        ).fetchone()[0]
        pending_count = self.connection.execute(
            "SELECT COUNT(*) FROM candidates WHERE batch_id = ? AND status = 'pending'",
            (batch_id,),
        ).fetchone()[0]
        unprocessed_count = self.connection.execute(
            "SELECT COUNT(*) FROM candidates WHERE batch_id = ? AND status = 'candidate'",
            (batch_id,),
        ).fetchone()[0]
        excluded_count = self.connection.execute(
            "SELECT COUNT(*) FROM candidates WHERE batch_id = ? AND status = 'excluded'",
            (batch_id,),
        ).fetchone()[0]
        return {
            "candidate": candidate_count,
            "verified": verified_count,
            "restricted": restricted_count,
            "duplicate": duplicate_count,
            "pending": pending_count,
            "unprocessed": unprocessed_count,
            "excluded": excluded_count,
        }

    def batch_metadata(self, batch_id: int) -> sqlite3.Row:
        row = self.connection.execute(
            "SELECT period, source_category, query_label FROM batches WHERE id = ?",
            (batch_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown batch id: {batch_id}")
        return row

    def batch_uncovered(self, batch_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            """SELECT source_url, status, status_detail FROM candidates
               WHERE batch_id = ? AND status != 'verified' ORDER BY id""",
            (batch_id,),
        ).fetchall()

    def _resolve_identity_key(self, source_url: str, platform_id: str | None) -> str:
        canonical_url = canonicalize_url(source_url)
        platform_key = _platform_identity_key(source_url, platform_id)
        for row in self.connection.execute(
            "SELECT identity_key, source_url FROM materials ORDER BY id"
        ):
            if canonicalize_url(row["source_url"]) == canonical_url or (
                platform_key and _normalized_platform_key(row["identity_key"]) == platform_key
            ):
                return row["identity_key"]
        for row in self.connection.execute(
            "SELECT identity_key, source_url FROM candidates ORDER BY id"
        ):
            if canonicalize_url(row["source_url"]) == canonical_url or (
                platform_key and _normalized_platform_key(row["identity_key"]) == platform_key
            ):
                return row["identity_key"]
        return _identity_key(source_url, platform_id)

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY,
                period TEXT NOT NULL,
                source_category TEXT NOT NULL,
                query_label TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS ux_batches_period_category_query
                ON batches(period, source_category, query_label);
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY,
                batch_id INTEGER NOT NULL REFERENCES batches(id),
                source_url TEXT NOT NULL,
                period TEXT NOT NULL,
                source_category TEXT NOT NULL,
                query_label TEXT NOT NULL,
                platform_id TEXT,
                metadata_url TEXT,
                identity_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'candidate',
                status_detail TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY,
                candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                source_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                content_sha256 TEXT NOT NULL,
                evidence_path TEXT,
                body_complete INTEGER NOT NULL,
                metadata_verified INTEGER NOT NULL,
                body_format TEXT NOT NULL DEFAULT 'source_text',
                original_page_verified INTEGER NOT NULL DEFAULT 0,
                access_status TEXT NOT NULL,
                authorization_note TEXT NOT NULL DEFAULT '',
                retrieval_method TEXT NOT NULL DEFAULT 'scrapy',
                retrieval_id TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS duplicate_discoveries (
                id INTEGER PRIMARY KEY,
                batch_id INTEGER NOT NULL REFERENCES batches(id),
                candidate_id INTEGER NOT NULL REFERENCES candidates(id),
                identity_key TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY,
                identity_key TEXT NOT NULL UNIQUE,
                source TEXT NOT NULL,
                published_on TEXT NOT NULL,
                author TEXT NOT NULL,
                title TEXT NOT NULL,
                abstract TEXT NOT NULL,
                keywords TEXT NOT NULL,
                body TEXT NOT NULL,
                source_url TEXT NOT NULL,
                duplicate_count INTEGER NOT NULL DEFAULT 0,
                evidence_id INTEGER NOT NULL REFERENCES evidence(id)
            );
            CREATE TABLE IF NOT EXISTS material_verifications (
                material_id INTEGER PRIMARY KEY REFERENCES materials(id) ON DELETE CASCADE,
                primary_evidence_id INTEGER NOT NULL REFERENCES evidence(id),
                abstract_origin TEXT NOT NULL,
                field_sources TEXT NOT NULL,
                verified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS material_metadata_evidence (
                material_id INTEGER NOT NULL REFERENCES material_verifications(material_id) ON DELETE CASCADE,
                evidence_id INTEGER NOT NULL REFERENCES evidence(id),
                PRIMARY KEY(material_id,evidence_id)
            );
            """
        )
        candidate_columns = {
            row["name"] for row in self.connection.execute("PRAGMA table_info(candidates)")
        }
        if "metadata_url" not in candidate_columns:
            self.connection.execute("ALTER TABLE candidates ADD COLUMN metadata_url TEXT")
        evidence_columns = {
            row["name"] for row in self.connection.execute("PRAGMA table_info(evidence)")
        }
        if "retrieval_method" not in evidence_columns:
            self.connection.execute(
                "ALTER TABLE evidence ADD COLUMN retrieval_method TEXT NOT NULL DEFAULT 'scrapy'"
            )
        if "retrieval_id" not in evidence_columns:
            self.connection.execute(
                "ALTER TABLE evidence ADD COLUMN retrieval_id TEXT NOT NULL DEFAULT ''"
            )
        self.connection.commit()


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    port = parsed.port
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    path = parsed.path or "/"
    tracking_keys = {"fbclid", "gclid", "mc_cid", "mc_eid", "trk"}
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in tracking_keys
    ]
    query = urlencode(sorted(query_items))
    return urlunsplit((scheme, hostname, path, query, ""))


def _identity_key(source_url: str, platform_id: str | None) -> str:
    platform_key = _platform_identity_key(source_url, platform_id)
    if platform_key:
        return platform_key
    return f"url:{canonicalize_url(source_url)}"


def _platform_identity_key(source_url: str, platform_id: str | None) -> str:
    if not platform_id:
        return ""
    hostname = (urlsplit(source_url).hostname or "").lower()
    return _normalized_platform_key(f"platform:{hostname}:{platform_id.strip()}")


def _normalized_platform_key(identity: str) -> str:
    parts = identity.split(":", 2)
    if len(parts) == 3 and parts[0] == "platform" and parts[1] in {
        "x.com", "www.x.com", "mobile.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"
    }:
        return f"platform:x.com:{parts[2]}"
    return identity
