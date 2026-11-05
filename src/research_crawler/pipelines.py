import hashlib
from dataclasses import replace
from pathlib import Path

from research_crawler.policy import AccessDecision
from research_crawler.store import ResearchStore
from research_crawler.validation import ValidationError, validate_material


class VerificationPipeline:
    def __init__(
        self,
        database_path: str | Path = "data/research.sqlite3",
        evidence_dir: str | Path = "data/evidence",
    ):
        self.database_path = Path(database_path)
        self.evidence_dir = Path(evidence_dir)
        self.store: ResearchStore | None = None
        self.batch_id: int | None = None
        self.batch_ids: dict[tuple[str, str, str], int] = {}
        self.crawler = None
        self.spider = None

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls(
            crawler.settings.get("DATABASE_PATH", "data/research.sqlite3"),
            crawler.settings.get("EVIDENCE_DIR", "data/evidence"),
        )
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self) -> None:
        self.store = ResearchStore(self.database_path)
        if self.crawler is not None:
            self.spider = self.crawler.spider

    def process_item(self, item: dict):
        if self.store is None:
            raise RuntimeError("verification pipeline is not open")

        candidate = item["candidate"]
        batch_key = (candidate.period, candidate.source_category, candidate.query_label)
        if batch_key not in self.batch_ids:
            self.batch_ids[batch_key] = self.store.create_batch(*batch_key)
        self.batch_id = self.batch_ids[batch_key]
        candidate_id = self.store.add_candidate(self.batch_id, candidate)
        raw_response = item.get("raw_response", b"")
        digest = hashlib.sha256(raw_response).hexdigest()
        evidence_path = self.evidence_dir / f"{digest}.html"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with evidence_path.open("wb") as handle:
            handle.write(raw_response)

        evidence = replace(
            item["evidence"],
            content_sha256=digest,
            evidence_path=evidence_path,
        )
        decision = item["decision"]
        evidence_id = self.store.add_evidence(
            candidate_id,
            evidence,
            access_status=decision.value,
        )

        if decision is AccessDecision.RESTRICTED:
            self.store.update_candidate_status(candidate_id, "restricted")
            return item
        if decision is not AccessDecision.ALLOW or item.get("material") is None:
            self.store.update_candidate_status(candidate_id, "pending", "full text or metadata not verified")
            return item

        try:
            material = validate_material(
                item["material"],
                evidence,
                item.get("field_sources", {}),
                abstract_origin=item.get("abstract_origin", "publisher"),
            )
            self.store.add_verified_material(
                candidate_id,
                evidence_id,
                material,
                abstract_origin=item.get("abstract_origin", "publisher"),
                field_sources=item.get("field_sources", {}),
            )
        except ValidationError as exc:
            self.store.update_candidate_status(candidate_id, "pending", str(exc))
            return item

        self.store.update_candidate_status(candidate_id, "verified")
        return item

    def close_spider(self) -> None:
        if self.store is not None:
            self.store.close()
            self.store = None
