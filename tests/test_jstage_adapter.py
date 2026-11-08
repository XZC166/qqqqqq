from io import BytesIO

from reportlab.pdfgen import canvas
from scrapy.http import HtmlResponse, Request, Response

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


METADATA_URL = (
    "https://www.jstage.jst.go.jp/article/kokusaiseiji1957/1998/118/"
    "1998_118_103/_article/-char/en"
)
PDF_URL = (
    "https://www.jstage.jst.go.jp/article/kokusaiseiji1957/1998/118/"
    "1998_118_103/_pdf/-char/en"
)
TITLE = (
    "The Changing Pattern of U. S. -China Relations since 1972 "
    "The History of Sino-U.S. Relations"
)
ABSTRACT = "The article reviews periods in U.S.-China relations since 1972."


def _metadata_response(publication_date="1998/05/08"):
    html = f"""<!doctype html><html><head>
      <meta name="citation_journal_title" content="International Relations">
      <meta name="citation_publisher" content="JAPAN ASSOCIATION OF INTERNATIONAL RELATIONS">
      <meta name="citation_author" content="Kenji TAKITA">
      <meta name="citation_title" content="{TITLE}">
      <meta name="citation_publication_date" content="{publication_date}">
      <meta name="publication_date" content="1998/05/08">
      <meta name="citation_online_date" content="2010/09/01">
      <meta name="citation_doi" content="10.11375/kokusaiseiji1957.118_103">
      <meta name="citation_pdf_url" content="{PDF_URL.removesuffix('/-char/en')}">
      </head><body>
      <div class="global-article-title">The Changing Pattern of U. S. -China Relations since 1972</div>
      <div class="global-article-inner-title">The History of Sino-U.S. Relations</div>
      <div class="global-authors-name-tags"><a><span>Kenji TAKITA</span></a></div>
      <div id="article-overiew-abstract-wrap"><div class="global-para-14">{ABSTRACT}</div></div>
      <a class="thirdlevel-pdf-btn" href="{PDF_URL}">Download PDF</a>
      </body></html>"""
    return HtmlResponse(
        url=METADATA_URL,
        request=Request(url=METADATA_URL),
        body=html.encode(),
        encoding="utf-8",
        status=200,
    )


def _pdf_response(metadata_response):
    output = BytesIO()
    pdf = canvas.Canvas(output)
    pdf.setTitle(TITLE)
    pdf.setAuthor("Kenji TAKITA")
    pdf.drawString(40, 800, TITLE)
    pdf.drawString(40, 780, "Kenji TAKITA")
    pdf.drawString(40, 760, "International Relations")
    pdf.drawString(40, 740, "U.S.-China relations and U.S. foreign policy")
    pdf.showPage()
    pdf.drawString(40, 800, "This is the final page of the article body.")
    pdf.save()
    return Response(
        url=PDF_URL,
        request=Request(url=PDF_URL, meta={"metadata_response": metadata_response}),
        body=output.getvalue(),
        status=200,
        headers={b"Content-Type": b"application/pdf"},
    )


def test_jstage_pdf_is_verified_against_its_free_article_page():
    metadata_response = _metadata_response()
    pdf_response = _pdf_response(metadata_response)
    candidate = MaterialCandidate(
        PDF_URL,
        "1992-2016",
        "research_literature",
        "jstage-sino-us-relations-history-1998",
        platform_id="10.11375/kokusaiseiji1957.118_103",
        metadata_url=METADATA_URL,
    )

    result = GovernmentArticleAdapter().extract(pdf_response, candidate)

    material = result["material"]
    assert material is not None
    assert material.source == "International Relations (JAPAN ASSOCIATION OF INTERNATIONAL RELATIONS)"
    assert material.time == "1998-05-08"
    assert material.author == "Kenji TAKITA"
    assert material.title == TITLE
    assert material.abstract == ABSTRACT
    assert "U.S.-China relations" in material.keywords
    assert "foreign policy" in material.keywords
    assert material.source_url == METADATA_URL
    assert "final page" in material.body
    assert result["evidence"].source_url == PDF_URL
    assert result["evidence"].body_complete is True
    assert result["evidence"].original_page_verified is True
    assert result["supporting_evidence"][0]["evidence"].metadata_verified is True
    assert result["keywords_origin"] == "derived"


def test_jstage_pdf_is_not_verified_when_page_date_conflicts():
    metadata_response = _metadata_response(publication_date="1998/05/09")
    candidate = MaterialCandidate(
        PDF_URL,
        "1992-2016",
        "research_literature",
        "jstage-sino-us-relations-history-1998",
        platform_id="10.11375/kokusaiseiji1957.118_103",
        metadata_url=METADATA_URL,
    )

    result = GovernmentArticleAdapter().extract(_pdf_response(metadata_response), candidate)

    assert result["material"] is None
