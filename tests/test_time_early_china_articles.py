import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    (
        "time_backs_to_the_wall_19500522.html",
        "https://time.com/archive/6614797/foreign-news-backs-to-the-wall/",
        "1950-05-22", "Foreign News: Backs to the Wall", 15, 6359,
        "f3b5033d2d3723c4d6029fdc9cd9cbc9dd87492c9ee2944849b997c43e2faf33",
    ),
    (
        "time_drawing_a_line_19500102.html",
        "https://time.com/archive/6776583/national-affairs-drawing-a-line/",
        "1950-01-02", "National Affairs: Drawing a Line", 6, 2321,
        "7a4360b41a85165b8189b97756eeed3c18cc534860bfe38c17525206e3cd6975",
    ),
    (
        "time_report_on_formosa_19491226.html",
        "https://time.com/archive/6603495/china-report-on-formosa/",
        "1949-12-26", "CHINA: Report on Formosa", 12, 5645,
        "679ec14925f86779b5a1477edc13aa2d695ffc6e7b28cc9362704bf951382f3a",
    ),
    (
        "time_return_of_the_gimo_19500313.html",
        "https://time.com/archive/6614462/china-return-of-the-gimo/",
        "1950-03-13", "CHINA: Return of the Gimo", 5, 2413,
        "e5302a691a0cf19bf951433505f1a84c1f071f3c7b5f8be10182f1957167de20",
    ),
    (
        "time_formosa_guns_silent_19581020.html",
        "https://time.com/archive/6801420/formosa-the-guns-are-silent/",
        "1958-10-20", "FORMOSA: The Guns Are Silent", 7, 3981,
        "c9aea88ecd8815ff05e785d57392058018cc373f183202a5be336b5f675d4866",
    ),
    (
        "time_progress_on_formosa_19520728.html",
        "https://time.com/archive/6618946/foreign-news-progress-on-formosa/",
        "1952-07-28", "Foreign News: PROGRESS ON FORMOSA", 16, 7319,
        "471a11d6001e1904d1e80fcb50128d084a030acf4a72a17442ad8117515d8076",
    ),
    (
        "time_formosa_turn_screw_19580915.html",
        "https://time.com/archive/6801244/formosa-the-turn-of-the-screw/",
        "1958-09-15", "FORMOSA: The Turn of the Screw", 7, 3946,
        "ac8108ad4da4689512b074339623cb282567d3e31dd62ee9525f3c2bee6a32de",
    ),
    (
        "time_danger_zones_chinese_revolution_19510326.html",
        "https://time.com/archive/6608261/danger-zones-another-chinese-revolution/",
        "1951-03-26", "DANGER ZONES: Another Chinese Revolution?", 22, 7788,
        "1bcf579e6dfcff8c2a87ddafef6dc503024ccaa39ba04a6b9fd272144439c099",
    ),
)


@pytest.mark.parametrize("case", CASES)
def test_reviewed_early_time_article_matches_original_metadata_and_body(case):
    fixture, url, published_on, title, paragraphs, length, digest = case
    if not (FIXTURES / fixture).exists():
        pytest.skip("Requires a locally retained original source capture; full copyrighted HTML is not published with this test.")
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=(FIXTURES / fixture).read_bytes()),
        MaterialCandidate(url, "1949-1972", "media", "reviewed-time-early-china"),
    )
    material = result["material"]

    assert material is not None
    assert (material.source, material.time, material.author, material.title) == (
        "TIME", published_on, "TIME", title,
    )
    assert material.source_url == url
    assert len(material.body.split("\n\n")) == paragraphs
    assert len(material.body) == length
    assert hashlib.sha256(material.body.encode()).hexdigest() == digest
    assert material.abstract.startswith("据正文整理：")
    assert material.keywords
    assert result["evidence"].body_complete
    assert result["evidence"].metadata_verified
    assert result["evidence"].original_page_verified
