from scrapy.http import HtmlResponse
import pytest

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter

URL = "https://www.csis.org/analysis/us-china-example"
RAW = b'''<html><head><title>U.S.-China Relations</title></head><body>
<h1>U.S.-China Relations</h1><div id="block-ts-csis-content">
<div class="layout--columns-article"><div class="column--first">
<div class="byline-block">Commentary by Example Author Published February 5, 2013</div>
<div class="text-block"><div></div></div>
<div class="block--migrated-content"><div><div class="wysiwyg-wrapper">
<p>U.S. media reports have discussed China.</p><p>Both governments discussed their relations.</p>
</div></div></div><div class="content-footer-block">Other articles</div>
</div></div></div></body></html>'''


def extract(raw=RAW):
    return GovernmentArticleAdapter().extract(
        HtmlResponse(URL,body=raw,encoding="utf-8"),
        MaterialCandidate(URL,"1992-2016","think_tank","sitemap"),
    )


def test_migrated_article_keeps_complete_body_and_original_metadata():
    result = extract()
    assert result["material"] is not None
    assert result["material"].time == "2013-02-05"
    assert result["material"].author == "Example Author"
    assert result["material"].body == "U.S. media reports have discussed China.\n\nBoth governments discussed their relations."


@pytest.mark.parametrize("insert", [
    b"Unparsed source narrative", b"<div>Unparsed source narrative</div>",
    b"<table><tr><td>Important data</td></tr></table>",
    b'<img src="important-chart.png">',
])
def test_migrated_article_rejects_unhandled_body_content(insert):
    raw=RAW.replace(b'<p>U.S. media',insert+b'<p>U.S. media')
    assert extract(raw)["material"] is None


def test_migrated_download_overview_does_not_stand_for_full_report():
    raw=RAW.replace(b'<div class="text-block">',b'<div class="downloads-block"><a href="full.pdf">Download Full Report</a></div><div class="text-block">')
    assert extract(raw)["material"] is None


@pytest.mark.parametrize("raw", [
    RAW.replace(b'<div class="block--migrated-content">', b'<div class="block--migrated-content"><p>Omitted narrative</p>'),
    RAW.replace(b'<p>Both governments', b'<p>For additional China studies see:</p><p>Both governments'),
    RAW.replace(b'</div></div></div><div class="content-footer-block">', b'<p>Example Author is a senior fellow at CSIS.</p></div></div></div><div class="text-block"><div class="wysiwyg-wrapper"><p>Later source narrative.</p></div></div><div class="content-footer-block">'),
    RAW.replace(b'<p>Both governments', b'<video src="full-body.mp4"></video><p>Both governments'),
])
def test_migrated_checks_outer_wrapper_and_all_text_after_termination(raw):
    assert extract(raw)["material"] is None


@pytest.mark.parametrize("raw", [
    RAW.replace(b'<div class="block--migrated-content">',b'<div class="block--migrated-content"><img src="essential-chart.png">'),
    RAW.replace(b'<div class="text-block"><div></div></div>',b'<div class="text-block"><div class="wysiwyg-wrapper"><p>First paragraph.</p><div>Important omitted narrative.</div></div></div>'),
])
def test_migrated_page_checks_every_block_and_outer_media(raw):
    assert extract(raw)["material"] is None
