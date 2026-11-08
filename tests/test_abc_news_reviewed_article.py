import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURE = Path(__file__).parent / "fixtures" / "abc_7478136.html"
URL = "https://www.abc.net.au/news/2016-06-04/us-flexes-muscles-as-asia-worries-about-south-china-sea-row/7478136"


def _extract(raw=None):
    return GovernmentArticleAdapter().extract(
        HtmlResponse(URL, body=raw if raw is not None else FIXTURE.read_bytes()),
        MaterialCandidate(URL, "1992-2016", "media", "reviewed-abc-south-china-sea"),
    )


def test_reviewed_abc_news_article_excludes_sidebar_and_page_template():
    result = _extract()
    material = result["material"]

    assert material is not None
    assert (material.source, material.time, material.author, material.title) == (
        "ABC News", "2016-06-04", "Reuters",
        "US flexes muscles as Asia worries about South China Sea row",
    )
    assert material.source_url == URL
    assert len(material.body.split("\n\n")) == 18
    assert len(material.body) == 3390
    assert hashlib.sha256(material.body.encode()).hexdigest() == (
        "dcb1c7da1ed138abb4ec24eaf231b6fe54ce7c730fac4683483bf70ba9d74031"
    )
    assert "Reuters" not in material.body
    assert "See more ABC coverage" not in material.body
    assert material.abstract.startswith("据正文整理：")
    assert material.keywords
    assert result["evidence"].body_complete
    assert result["evidence"].metadata_verified
    assert result["evidence"].original_page_verified


@pytest.mark.parametrize("mutation", ["body", "date", "title", "author"])
def test_reviewed_abc_news_rejects_changed_source_text_or_metadata(mutation):
    raw = FIXTURE.read_bytes()
    replacements = {
        "body": (b"The United States has stepped up pressure", b"The United States has lifted pressure"),
        "date": (b"2016-06-04T09:20:00+00:00", b"2016-06-05T09:20:00+00:00"),
        "title": (b"US flexes muscles as Asia worries about South China Sea row", b"US flexes muscles about the South China Sea row"),
        "author": (b"<strong>Reuters</strong></p>", b"<strong>Unknown</strong></p>"),
    }
    before, after = replacements[mutation]
    assert before in raw
    raw = raw.replace(before, after, 1)

    assert _extract(raw)["material"] is None
