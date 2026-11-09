import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


URL = "https://api.parliament.uk/historic-hansard/commons/1972/mar/06/china"
RAW = b'''<html><head><title>China (Hansard, 6 March 1972)</title>
<meta author="UK Parliament"></head><body><h1>China</h1>
<div id="content" class="house-of-commons-sitting">
<cite class="section">HC Deb 06 March 1972 vol 832 cc1012-3</cite>
<div class="hentry member_contribution" id="first"><blockquote class="contribution_text entry-content">
<a class="speech-permalink permalink">section link</a><span class="question_no">11.</span>
<cite class="member author entry-title">Mr. Dalyell</cite>
<p>What is the policy toward China?</p></blockquote></div>
<div class="hentry member_contribution" id="second"><blockquote class="contribution_text entry-content">
<cite class="member author entry-title">Sir Alec Douglas-Home</cite>
<p>Following President Nixon's visit, the United States and <a class="column-permalink permalink">1013</a> China are discussing Taiwan.</p>
<p>We will continue these contacts.</p></blockquote></div>
<ol class="xoxo"></ol><div id="section-navigation">Other article</div></div>
<div id="footer">UK Parliament</div></body></html>'''


def extract(raw=RAW, url=URL):
    return GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=raw, encoding="utf-8"),
        MaterialCandidate(url, "1949-1972", "government", "hansard-china"),
    )


def test_hansard_full_debate_preserves_speakers_and_text_but_removes_navigation():
    result = extract()
    assert result["material"] is None
    assert not result["evidence"].metadata_verified
    assert "sitting date" in result["pending_reason"]
    assert result["extracted_body"] == (
        "11. Mr. Dalyell\n\nWhat is the policy toward China?\n\n"
        "Sir Alec Douglas-Home\n\nFollowing President Nixon's visit, the United States and China are discussing Taiwan.\n\n"
        "We will continue these contacts."
    )
    assert result["evidence"].body_complete
    assert result["evidence"].original_page_verified


def test_hansard_keeps_procedural_and_constituency_text_in_original_order():
    raw = RAW.replace(
        b'<div class="hentry member_contribution" id="second">',
        b'<p class="procedural"><a class="permalink">section link</a>4.13 p.m.</p>'
        b'<div class="hentry member_contribution" id="second">',
    ).replace(
        b"Sir Alec Douglas-Home</cite>",
        b'Sir Alec Douglas-Home</cite><span class="member_constituency">(Kinross)</span>',
    )
    body = extract(raw)["extracted_body"]
    assert "What is the policy toward China?\n\n4.13 p.m.\n\nSir Alec Douglas-Home (Kinross)" in body


@pytest.mark.parametrize("extra", [b"Missing narrative", b"<p>Missing narrative</p>"])
def test_hansard_rejects_unhandled_content_outside_contribution_quote(extra):
    raw = RAW.replace(b'<blockquote class="contribution_text entry-content">', extra + b'<blockquote class="contribution_text entry-content">', 1)
    assert not extract(raw)["evidence"].body_complete


@pytest.mark.parametrize("raw,url", [
    (RAW.replace(b"HC Deb 06 March", b"HC Deb 07 March"), URL),
    (RAW.replace(b"6 March 1972)</title>", b"7 March 1972)</title>"), URL),
    (RAW, URL.replace("/06/", "/07/")),
    (RAW.replace(b"<p>We will continue", b"<table><tr><td>Unparsed data</td></tr></table><p>We will continue"), URL),
    (RAW.replace(b'<ol class="xoxo"></ol>', b'<ol class="xoxo"><li>Child section not included</li></ol>'), URL),
    (RAW.replace(b'UK Parliament"', b'Unknown"'), URL),
])
def test_hansard_rejects_date_conflicts_unparsed_content_and_composite_sections(raw, url):
    assert not extract(raw, url)["evidence"].body_complete


@pytest.mark.parametrize("raw", [
    RAW.replace(b"<p>We will continue these contacts.</p>", b"").replace(b"<p>Following President Nixon's visit, the United States and <a class=\"column-permalink permalink\">1013</a> China are discussing Taiwan.</p>", b""),
    RAW.replace(b'<ol class="xoxo"></ol>', b'<ol class="xoxo"><li><a><img src="subsection.png"></a></li></ol>'),
])
def test_hansard_rejects_empty_speech_and_nonempty_child_section(raw):
    assert not extract(raw)["evidence"].body_complete
