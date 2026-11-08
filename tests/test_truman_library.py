from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import TrumanLibraryPublicPaperAdapter


def test_truman_library_extracts_date_and_body_from_official_document_node():
    fixture = Path(__file__).parent / "fixtures" / "truman_library_public_paper_synthetic.html"
    url = "https://www.trumanlibrary.gov/library/public-papers/3/presidents-news-conference"
    response = HtmlResponse(url=url, request=Request(url), body=fixture.read_bytes(), encoding="utf-8")
    candidate = MaterialCandidate(
        source_url=url,
        period="1949-1972",
        source_category="government",
        query_label="truman-library-test",
    )

    result = TrumanLibraryPublicPaperAdapter().extract(response, candidate)

    assert result["material"].source == "Harry S. Truman Library & Museum"
    assert result["material"].time == "1950-01-06"
    assert result["material"].author == "未注明"
    assert result["material"].title == "The President's News Conference"
    assert result["material"].body == (
        "January 5, 1950\n\n"
        "THE PRESIDENT. I have a statement about China.\n\n"
        "We will not provide military aid or advice to Chinese forces."
    )
