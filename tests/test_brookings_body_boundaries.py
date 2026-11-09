import pytest
from scrapy.http import HtmlResponse
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter

URL = "https://www.brookings.edu/articles/us-china-example/"
RAW = b'''<html><head><meta property="og:site_name" content="Brookings">
<script type="application/ld+json">{"@type":"Article","headline":"US-China Example","datePublished":"2011-06-13","author":{"@type":"Person","name":"Example Author"}}</script>
</head><body><h1>US-China Example</h1><div class="byo-blocks article-content">
<div class="byo-block archived wysiwyg-block"><p>This content is archived.</p></div>
<div class="byo-block wysiwyg-block"><p>China and the United States discussed relations.</p><p>Public communication was discussed.</p></div>
<div class="byo-block wysiwyg-block medium border-t"><p>Brookings website disclaimer.</p></div>
</div></body></html>'''


def extract(raw=RAW):
    return GovernmentArticleAdapter().extract(HtmlResponse(URL,body=raw,encoding="utf-8"),MaterialCandidate(URL,"1992-2016","think_tank","sitemap"))


def test_archival_banner_is_template_text_and_not_article_body():
    material=extract()["material"]
    assert material is not None
    assert material.body == "China and the United States discussed relations.\n\nPublic communication was discussed."


@pytest.mark.parametrize("extra", [
    b"Unparsed narrative", b"<div>Unparsed narrative</div>",
    b"<table><tr><td>Important data</td></tr></table>",
    b'<iframe src="video"></iframe>', b'<img src="important-data.png">',
])
def test_unparsed_body_content_cannot_pass_completeness(extra):
    raw=RAW.replace(b'<p>China',extra+b'<p>China')
    assert extract(raw)["material"] is None


@pytest.mark.parametrize("extra", [
    b'<div class="byo-block narrative-block"><p>Unparsed narrative.</p></div>',
    b'<div class="byo-block table-block"><table><tr><td>Unparsed data.</td></tr></table></div>',
])
def test_unparsed_sibling_blocks_cannot_pass_completeness(extra):
    raw=RAW.replace(b'<div class="byo-block wysiwyg-block">',extra+b'<div class="byo-block wysiwyg-block">')
    assert extract(raw)["material"] is None


def test_substantive_footnotes_are_kept_once_without_tooltip_duplicate():
    note=b'''<div class="byo-block footnotes acknowledgements"><ul class="accordion">
<li class="accordion-item"><a><span class="h3">Footnotes</span></a>
<div class="accordion-content"><ol><li>Survey methodology describes the original sample.</li></ol></div></li></ul>
<div role="tooltip" class="tooltip">Survey methodology describes the original sample.</div></div>'''
    raw=RAW.replace(b'<div class="byo-block wysiwyg-block medium border-t">',note+b'<div class="byo-block wysiwyg-block medium border-t">')
    material=extract(raw)["material"]
    assert material is not None
    assert material.body.endswith("Footnotes\n\nSurvey methodology describes the original sample.")
    assert material.body.count("Survey methodology") == 1
