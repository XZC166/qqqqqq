from typing import Protocol, runtime_checkable

from scrapy.http import Response

from research_crawler.items import MaterialCandidate


@runtime_checkable
class SourceAdapter(Protocol):
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        """Return page evidence and a material draft when the source is verifiable."""
