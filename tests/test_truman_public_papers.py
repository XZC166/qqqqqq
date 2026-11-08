from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import (
    TRUMAN_LIBRARY_REVIEWED_HASHED_METADATA,
    TRUMAN_LIBRARY_VISIBLE_PUBLICATION_DATE_URLS,
)
from research_crawler.spiders.government import (
    GovernmentArticleAdapter,
    _reviewed_truman_library_metadata,
)


FIXTURES = Path(__file__).parent / "fixtures"


def test_truman_legacy_page_uses_leading_visible_date_and_excludes_page_chrome():
    url = "https://www.trumanlibrary.gov/library/public-papers/173/statement-president-situation-korea"
    response = HtmlResponse(
        url=url,
        request=Request(url),
        body=(FIXTURES / "truman_public_paper_legacy_synthetic.html").read_bytes(),
        encoding="utf-8",
    )
    candidate = MaterialCandidate(
        url,
        "1949-1972",
        "government",
        "truman-korean-war-formosa-statement-1950",
    )

    result = GovernmentArticleAdapter().extract(response, candidate)
    material = result["material"]

    assert material is not None
    assert material.time == "1950-06-27"
    assert material.title == "Statement by the President on the Situation in Korea"
    assert material.source == "Harry S. Truman Library & Museum"
    assert material.body == (
        "IN KOREA the Government forces were attacked by invading forces.\n\n"
        "Accordingly I have ordered the 7th Fleet to prevent any attack on Formosa."
    )
    assert material.abstract.startswith("据正文整理：")
    assert "Korean War" in material.keywords
    assert "Navigation" not in material.body
    assert "Footer text" not in material.body


def test_1951_truman_library_metadata_is_bound_to_the_reviewed_body():
    cases = {
        "https://www.trumanlibrary.gov/library/public-papers/295/presidents-news-conference-key-west": (
            "cbcac82d26148c678a5143275a26d2baf685853408ea54a4d84f1056e71b442a",
        ),
        "https://www.trumanlibrary.gov/library/public-papers/77/statement-and-order-president-relieving-general-macarthur-his-commands": (
            "4645787196c3f7952a73b49067b8ae7b25b8fe18d08665009f94da494d6295f0",
        ),
    }

    for url, (body_hash,) in cases.items():
        reviewed_hash, abstract, keywords = TRUMAN_LIBRARY_REVIEWED_HASHED_METADATA[url]
        assert reviewed_hash == body_hash
        assert abstract.startswith("据正文整理：")
        assert keywords
        assert url in TRUMAN_LIBRARY_VISIBLE_PUBLICATION_DATE_URLS
        assert _reviewed_truman_library_metadata(url, "changed or incomplete body") == ("", "")
