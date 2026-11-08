from hashlib import sha256

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PEW_REVIEWED_ARTICLES
from research_crawler.spiders.government import PewResearchArticleAdapter
import research_crawler.spiders.government as government_spider


def _page(body: str) -> HtmlResponse:
    url = "https://www.pewresearch.org/global/2024/05/01/china-us-opinion-test/"
    page = f"""<html><head>
      <meta property="og:site_name" content="Pew Research Center">
      <meta property="og:title" content="U.S. public attitudes toward China">
      <meta property="article:published_time" content="2024-05-01T11:55:11-04:00">
      <meta name="description" content="Publisher summary about public attitudes toward China.">
      <script type="application/ld+json">{{
        "@type":"Article","headline":"U.S. public attitudes toward China",
        "datePublished":"2024-05-01T11:55:11-04:00",
        "author":[{{"@type":"Person","name":"A. Researcher"}}],
        "publisher":{{"@type":"Organization","name":"Pew Research Center"}}
      }}</script></head><body>
      <article class="wp-block-group"><h1>U.S. public attitudes toward China</h1>
        <div class="wp-block-prc-block-bylines-display"><a>A. Researcher</a></div>
        <time datetime="2024-05-01T11:55:11-04:00">May 1, 2024</time>
      </article>
      <div class="entry-content wp-block-post-content">
        <p>{body}</p><h3>Views by party</h3>
        <ul><li>Republicans report one view.</li><li>Democrats report another view.</li></ul>
      </div></body></html>"""
    return HtmlResponse(url=url, request=Request(url), body=page.encode(), encoding="utf-8")


def test_pew_article_is_verified_only_against_the_exact_reviewed_body(monkeypatch):
    url = "https://www.pewresearch.org/global/2024/05/01/china-us-opinion-test/"
    opening = "Americans discuss China's role in public policy."
    extracted_body = (
        opening
        + "\n\nViews by party\n\n"
        + "Republicans report one view.\nDemocrats report another view."
    )
    monkeypatch.setitem(
        government_spider.PEW_REVIEWED_ARTICLES,
        url,
        (
            "2024-05-01",
            "U.S. public attitudes toward China",
            "A. Researcher",
            sha256(extracted_body.encode()).hexdigest(),
            "China; public opinion",
        ),
    )
    candidate = MaterialCandidate(url, "2017-2025", "research_literature", "pew-test")
    adapter = PewResearchArticleAdapter()

    result = adapter.extract(_page(opening), candidate)

    assert result["material"] is not None
    assert result["material"].time == "2024-05-01"
    assert result["material"].author == "A. Researcher"
    assert result["material"].keywords == "China; public opinion"
    assert result["material"].body == extracted_body
    assert result["field_sources"]["keywords"] == "body"
    assert result["evidence"].body_complete is True

    changed = adapter.extract(_page("A changed article body."), candidate)
    assert changed["material"] is None
    assert changed["evidence"].body_complete is False


def test_reviewed_pew_pages_bind_exact_metadata_and_body_hashes():
    assert PEW_REVIEWED_ARTICLES[
        "https://www.pewresearch.org/global/2024/05/01/chinas-relationship-with-the-u-s/"
    ] == (
        "2024-05-01",
        "2. China’s relationship with the U.S.",
        "Christine Huang, Laura Silver, Laura Clancy",
        "f8f857cc6403f1f838775f8bf722911f4455683b83fb08f186c09c4324c9389b",
        "U.S.-China relations; China threat perceptions; China as an enemy; economic influence; U.S. public opinion",
    )
    assert len(PEW_REVIEWED_ARTICLES) == 3
