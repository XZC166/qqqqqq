from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PEW_REVIEWED_ARTICLES
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURE = Path(__file__).parent / "fixtures" / "pew_global_views_china_2025.html"
URL = "https://www.pewresearch.org/global/2025/07/15/international-views-of-china-turn-slightly-more-positive/"


def test_2025_pew_global_views_article_includes_supported_callout_and_complete_text():
    response = HtmlResponse(
        url=URL,
        request=Request(URL),
        body=FIXTURE.read_bytes(),
        encoding="utf-8",
    )
    result = GovernmentArticleAdapter().extract(
        response,
        MaterialCandidate(URL, "2017-2025", "think_tank", "pew-global-views-china-2025"),
    )

    material = result["material"]
    assert material is not None
    assert material.time == "2025-07-15"
    assert material.title == "International Views of China Turn Slightly More Positive"
    assert material.author == "Laura Silver, Laura Clancy, Jonathan Schulman, William Miner, Christine Huang"
    assert "What is a median?" in material.body
    assert "the middle number in a list of all percentages" in material.body
    assert "A median of 36% of adults across the 25 countries" in material.body
    assert "International Views of China Turn Slightly More Positive" == material.title
    assert result["evidence"].body_complete
    assert result["evidence"].metadata_verified
    assert sha256(material.body.encode("utf-8")).hexdigest() == PEW_REVIEWED_ARTICLES[URL][3]
    assert "Chart title:" not in material.body
