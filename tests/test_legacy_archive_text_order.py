from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


def extract(raw, url):
    return GovernmentArticleAdapter().extract(
        HtmlResponse(url=url, body=raw.encode(), encoding="utf-8"),
        MaterialCandidate(url, "1992-2016", "government", "synthetic-regression"),
    )


def test_archived_state_preserves_script_tail_opening_and_nested_quote_once():
    raw = '''<html><head><title>China remarks</title>
    <meta property="og:site_name" content="U.S. Department of State"></head><body>
    <div id="page-title">China remarks</div><div id="top-meta">
    <span class="officials-name">Named Speaker</span><div id="date_long">May 3, 2012</div></div>
    <div id="centerblock"><p></p><div class="flex-video"><p>Player labels</p>
    <style>Player styles</style></div><script>Player commands</script>
    Opening text <em>outside paragraphs</em> continues here.<p></p>
    <p>First full China paragraph.</p><blockquote>Quoted introduction.
    <p>Quote paragraph.</p></blockquote><p>Final paragraph.</p></div></body></html>'''
    result = extract(raw, "https://2009-2017.state.gov/remarks/synthetic.htm")
    assert result["material"].body == (
        "Opening text outside paragraphs continues here.\n\nFirst full China paragraph.\n\n"
        "Quoted introduction.\n\nQuote paragraph.\n\nFinal paragraph."
    )
    assert result["evidence"].body_complete


def test_archived_state_preserves_unwrapped_text_between_and_after_paragraphs():
    raw = '''<html><head><title>China remarks</title>
    <meta property="og:site_name" content="U.S. Department of State"></head><body>
    <div id="page-title">China remarks</div><div id="top-meta"><div id="date_long">May 3, 2012</div></div>
    <div id="centerblock">Opening.<p>First.</p>Between.<p>Second.</p>Closing.</div></body></html>'''
    assert extract(raw, "https://2009-2017.state.gov/remarks/synthetic.htm")["material"].body == (
        "Opening.\n\nFirst.\n\nBetween.\n\nSecond.\n\nClosing."
    )


def test_clinton_work_page_preserves_mixed_blockquote_before_its_attribution():
    from pathlib import Path
    raw = (Path(__file__).parent / "fixtures/clinton_whitehouse_work_1998_synthetic.html").read_text(encoding="utf-8")
    raw = raw.replace("<blockquote>", "<blockquote><i>Original China engagement quotation.</i><br>", 1)
    result = extract(raw, "https://clintonwhitehouse4.archives.gov/WH/Work/061198.html")
    body = result["material"].body
    assert "Original China engagement quotation." in body
    assert body.index("Original China engagement quotation.") < body.index("President Bill Clinton")
    assert body.count("President Bill Clinton") == 1
    assert "President and First Lady" not in body


def test_inline_emphasis_does_not_insert_letters_spaces_or_duplicate_list_items():
    from lxml import html
    from research_crawler.spiders.government import _legacy_ordered_text_blocks
    source = html.fromstring('<div><p>Chi<em>na</em>’s policy.</p><ul><li>One <b>item</b>.</li></ul></div>')
    assert _legacy_ordered_text_blocks(source) == ["China’s policy.", "One item."]


def test_archived_state_translation_switcher_is_not_speech_text():
    raw = '''<html><head><title>China remarks</title>
    <meta property="og:site_name" content="U.S. Department of State"></head><body>
    <div id="page-title">China remarks</div><div id="top-meta"><div id="date_long">May 3, 2012</div></div>
    <div id="centerblock">Also available in <a href="/chinese/texttrans/speech.html">Chinese</a>
    <p></p><p>SECRETARY: Original China remarks.</p></div></body></html>'''
    assert extract(raw, "https://2009-2017.state.gov/remarks/synthetic.htm")["material"].body == "SECRETARY: Original China remarks."
