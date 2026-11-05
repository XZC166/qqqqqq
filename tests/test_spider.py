from pathlib import Path
import csv
import asyncio

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.adapters import SourceAdapter
from research_crawler.policy import AccessDecision
from research_crawler.spiders.government import (
    GovernmentArticleAdapter,
    GovernmentSpider,
    JsonLdArticleAdapter,
    StateDepartmentRemarksAdapter,
    WhiteHouseFactSheetAdapter,
)


FIXTURES = Path(__file__).parent / "fixtures"


def response_for(name: str, url: str = "https://agency.example/speech") -> HtmlResponse:
    request = Request(url=url)
    return HtmlResponse(
        url=url,
        request=request,
        body=(FIXTURES / name).read_bytes(),
        encoding="utf-8",
        status=200,
    )


def test_extracts_article_body_in_order_without_page_template():
    assert isinstance(GovernmentArticleAdapter(), SourceAdapter)
    candidate = MaterialCandidate(
        "https://agency.example/speech", "2017-2025", "government", "test-query"
    )

    extracted = GovernmentArticleAdapter().extract(response_for("government_page.html"), candidate)

    assert extracted["decision"] is AccessDecision.ALLOW
    assert extracted["material"].source == "Example U.S. Agency"
    assert extracted["material"].time == "2020-02-03"
    assert extracted["material"].author == "A. Author"
    assert extracted["material"].body == "First source paragraph.\n\nSecond source paragraph."
    assert "Navigation" not in extracted["material"].body
    assert "Footer" not in extracted["material"].body
    assert extracted["evidence"].body_complete is True


def test_missing_exact_publication_date_remains_unverified_candidate():
    url = "https://agency.example/speech"
    html = b"""<html><head><meta property='og:site_name' content='Example Agency'>
    <meta name='author' content='A. Author'></head><body>
    <article data-full-text='true'><h1>Source title</h1><div class='article-body'>
    <p>Full source paragraph.</p></div></article></body></html>"""
    response = HtmlResponse(
        url=url,
        request=Request(url),
        body=html,
        encoding="utf-8",
        status=200,
    )
    candidate = MaterialCandidate(url, "2017-2025", "government", "date-missing")

    extracted = GovernmentArticleAdapter().extract(response, candidate)

    assert extracted["material"] is None
    assert extracted["evidence"].metadata_verified is False


def test_restricted_response_is_never_extracted_as_full_text():
    candidate = MaterialCandidate(
        "https://agency.example/speech", "2017-2025", "government", "test-query"
    )

    extracted = GovernmentArticleAdapter().extract(response_for("restricted_page.html"), candidate)

    assert extracted["decision"] is AccessDecision.RESTRICTED
    assert extracted["material"] is None


def test_spider_reads_candidate_csv_and_preserves_each_batch_label(tmp_path):
    candidate_file = tmp_path / "candidates.csv"
    with candidate_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("url", "period", "source_category", "query_label"),
        )
        writer.writeheader()
        writer.writerow({
            "url": "https://agency.example/one",
            "period": "2017-2025",
            "source_category": "government",
            "query_label": "taiwan-strait",
        })
        writer.writerow({
            "url": "https://agency.example/two",
            "period": "2017-2025",
            "source_category": "government",
            "query_label": "trade-war",
        })

    spider = GovernmentSpider(candidates_csv=str(candidate_file))
    requests = asyncio.run(_collect_start_requests(spider))

    assert [request.url for request in requests] == [
        "https://agency.example/one", "https://agency.example/two"
    ]
    assert [request.meta["candidate"].query_label for request in requests] == [
        "taiwan-strait", "trade-war"
    ]


async def _collect_start_requests(spider):
    return [request async for request in spider.start()]


def test_white_house_adapter_uses_visible_publication_date_and_excludes_related_content():
    url = (
        "https://www.whitehouse.gov/fact-sheets/2025/02/fact-sheet-us-china-trade/"
    )
    candidate = MaterialCandidate(url, "2017-2025", "government", "trade-war")
    response = response_for("whitehouse_fact_sheet.html", url)

    extracted = WhiteHouseFactSheetAdapter().extract(response, candidate)

    assert extracted["material"].time == "2025-02-01"
    assert extracted["material"].author == "未注明"
    assert extracted["material"].body == (
        "First section heading and paragraph.\n\n"
        "• First source list item.\n• Second source list item.\n\n"
        "Final source paragraph."
    )
    assert "Related item" not in extracted["material"].body
    assert "Footer" not in extracted["material"].body


def test_state_department_adapter_extracts_remarks_metadata_and_body_only():
    url = "https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/"
    candidate = MaterialCandidate(url, "2017-2025", "government", "trade-war")

    extracted = StateDepartmentRemarksAdapter().extract(
        response_for("state_department_remarks.html", url), candidate
    )

    material = extracted["material"]
    assert material.source == "United States Department of State"
    assert material.time == "2024-09-05"
    assert material.author == (
        "Jose W. Fernandez, Under Secretary for Economic Growth, Energy, and the Environment"
    )
    assert material.title == "Remarks at the Asia Society on Countering Economic Coercion"
    assert material.abstract == ""
    assert material.keywords == ""
    assert material.body == (
        "As prepared.\n\nThank you very much Wendy for that great introduction."
        "\n\nU.S. ECONOMIC SECURITY\n\n"
        "Thank you again to the Asia Society for hosting me here today."
    )
    assert "Economic Prosperity" not in material.body
    assert extracted["evidence"].body_complete is True


def test_state_department_technical_difficulties_page_is_not_material():
    url = "https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/"
    html = b"<html><head><title>Technical Difficulties</title></head><body><p>We are experiencing technical difficulties.</p></body></html>"
    response = HtmlResponse(url=url, request=Request(url), body=html, encoding="utf-8", status=200)

    extracted = StateDepartmentRemarksAdapter().extract(
        response, MaterialCandidate(url, "2017-2025", "government", "trade-war")
    )

    assert extracted["material"] is None
    assert extracted["evidence"].body_complete is False


def test_jsonld_adapter_requires_full_body_to_match_visible_article():
    url = "https://news.example/article/123"
    candidate = MaterialCandidate(url, "2017-2025", "media", "china-framing")
    extracted = JsonLdArticleAdapter().extract(response_for("structured_article.html", url), candidate)

    assert extracted["material"].source == "Example Publisher"
    assert extracted["material"].time == "2020-02-03"
    assert extracted["material"].author == "A. Author"
    assert extracted["material"].body == "First structured paragraph.\n\nSecond structured paragraph."
    assert extracted["field_sources"]["abstract"] == url
    assert extracted["field_sources"]["keywords"] == url


def test_jsonld_excerpt_mismatch_is_not_accepted_as_full_text():
    url = "https://news.example/article/123"
    html = b"""<html><script type='application/ld+json'>
    {"@type":"NewsArticle","headline":"Title","datePublished":"2020-02-03",
    "publisher":{"name":"Example"},"articleBody":"Only a preview."}
    </script><article><h1>Title</h1><time datetime='2020-02-03'>February 3, 2020</time>
    <div itemprop='articleBody'><p>Only a preview.</p><p>Full article continues here.</p></div>
    </article></html>"""
    response = HtmlResponse(url=url, request=Request(url), body=html, encoding="utf-8", status=200)
    candidate = MaterialCandidate(url, "2017-2025", "media", "china-framing")

    extracted = JsonLdArticleAdapter().extract(response, candidate)

    assert extracted["material"] is None
    assert extracted["evidence"].body_complete is False
