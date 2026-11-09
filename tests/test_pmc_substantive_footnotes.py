"""Synthetic regression cases; no third-party article text in the fixture."""
from scrapy.http import HtmlResponse
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import PMCFulTextArticleAdapter

URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC12345/"

def extract(body):
    page = f"""<html><head>
    <meta name="citation_title" content="China public opinion and US media">
    <meta name="citation_journal_title" content="Synthetic Research Journal">
    <meta name="citation_author" content="Research Author">
    <meta name="citation_publication_date" content="2021 Sep 9">
    </head><body><nav>Website navigation</nav><main id="main-content"><article lang="en">
    <h1>China public opinion and US media</h1>
    <section class="pmc-layout__citation">2021 Sep 9;10:1</section>
    <section class="abstract"><h2>Abstract</h2><p>China and US media affect public opinion.</p></section>
    <section class="kwd-group"><p>Keywords: China; public opinion</p></section>
    {body}</article></main><footer>Website footer</footer></body></html>"""
    response = HtmlResponse(URL, body=page.encode(), encoding="utf-8")
    return PMCFulTextArticleAdapter().extract(response, MaterialCandidate(URL,"2017-2025","research_literature","regression"))


def test_back_footnotes_retain_source_text_labels_and_paragraphs():
    result = extract("""<section class="body main-article-body"><h2>Introduction</h2>
    <p>China and US media shape public opinion.<a href="#Fn1">1</a></p></section>
    <section class="fn-group"><h2>Footnotes</h2><div class="fn p" id="Fn1">
    <span class="label">1</span><p>The survey covered nine societies.</p><p>The sampling note is part of this article.</p></div>
    <div class="fn p" id="pub"><h3>Publisher's Note</h3><p>Administrative neutrality statement.</p></div></section>
    <section class="ref-list"><p>Bibliographic reference.</p></section>""")
    assert result["material"] is not None
    body = result["material"].body
    assert "1 The survey covered nine societies.\n\nThe sampling note is part of this article." in body
    assert body.index("China and US") < body.index("The survey")
    assert "neutrality" not in body and "Bibliographic" not in body
    assert "Website" not in body


def test_nested_notes_remain_in_document_order_without_duplication():
    result = extract("""<section class="body main-article-body"><p>China public opinion before the note.</p>
    <section class="fn-group"><div class="fn" id="n1"><sup>2</sup><p>A substantive explanatory note.</p></div></section>
    <p>US media after the note.</p></section>""")
    body = result["material"].body
    assert body.index("before the note") < body.index("explanatory note") < body.index("after the note")
    assert body.count("explanatory note") == 1


def test_notes_from_subarticles_and_abstracts_do_not_enter_main_body():
    result = extract("""<section class="body main-article-body"><p>China public opinion and US media.</p></section>
    <article class="sub-article"><section class="fn-group"><div class="fn"><p>Other article note.</p></div></section></article>
    <section class="abstract"><h2>Other preview</h2><div class="fn-group"><div class="fn"><p>Preview note.</p></div></div></section>
    <section class="fn-group"><div class="fn"><sup>3</sup><p>Main article note.</p></div></section>""")
    body = result["material"].body
    assert "Main article note." in body
    assert "Other article note." not in body and "Preview note." not in body


def test_mixed_note_content_preserves_lists_and_intervening_text():
    result = extract("""<section class="body main-article-body"><p>China public opinion and US media.</p></section>
    <section class="fn-group"><div class="fn"><sup>4</sup><p>First paragraph.</p>
    Intervening <em>source text.</em><ul><li>Second detail.</li></ul>
    <p>Last paragraph.</p>Final inline text.</div></section>""")
    body = result["material"].body
    phrases = ["4 First paragraph.", "Intervening source text.", "Second detail.", "Last paragraph.", "Final inline text."]
    assert all(body.count(phrase) == 1 for phrase in phrases)
    assert [body.index(phrase) for phrase in phrases] == sorted(body.index(phrase) for phrase in phrases)


def test_note_already_in_enclosing_quotation_is_not_emitted_twice():
    result = extract("""<section class="body main-article-body"><p>China public opinion and US media.</p>
    <blockquote>Main quotation.<section class="fn-group"><div class="fn"><sup>5</sup>
    <p>Note inside the quotation.</p></div></section></blockquote></section>""")
    body = result["material"].body
    assert "Main quotation." in body and body.count("Note inside the quotation.") == 1
