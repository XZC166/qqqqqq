from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.adapters import SourceAdapter
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def _extract(fixture_name, url):
    response = HtmlResponse(
        url=url,
        request=Request(url),
        body=(FIXTURES / fixture_name).read_bytes(),
        encoding="utf-8",
    )
    candidate = MaterialCandidate(url, "1992-2016", "government", "clinton-legacy")
    return GovernmentArticleAdapter().extract(response, candidate)


def test_clinton_legacy_work_page_uses_visible_page_date_and_excludes_navigation():
    result = _extract(
        "clinton_whitehouse_work_1998_synthetic.html",
        "https://clintonwhitehouse4.archives.gov/WH/Work/061198.html",
    )

    material = result["material"]
    assert material is not None
    assert material.source == "The White House"
    assert material.time == "1998-06-11"
    assert material.title == "PRESIDENT CLINTON: U.S. - CHINA RELATIONS IN THE 21ST CENTURY"
    assert "The United States and China are working together." in material.body
    assert "Related archive pages" not in material.body
    assert "President and First Lady" not in material.body


def test_clinton_textonly_press_availability_extracts_complete_original_body():
    result = _extract(
        "clinton_textonly_press_availability_synthetic.html",
        "https://clintonwhitehouse4.archives.gov/textonly/WH/New/China/19980627-9474.html",
    )

    material = result["material"]
    assert material is not None
    assert material.source == "The White House, Office of the Press Secretary"
    assert material.time == "1998-06-27"
    assert material.title == "PRESS AVAILABILITY BY PRESIDENT CLINTON AND PRESIDENT JIANG"
    assert material.body == (
        "PRESIDENT JIANG: The talks were positive and productive.\n\n"
        "PRESIDENT CLINTON: Our relationship is important to both countries.\n\n"
        "THE PRESS: Thank you."
    )
    assert "Related remarks" not in material.body


def test_clinton_textonly_photo_op_uses_visible_title_instead_of_browser_title():
    result = _extract(
        "clinton_textonly_photo_op_synthetic.html",
        "https://clintonwhitehouse4.archives.gov/textonly/WH/New/China/19980627-13450.html",
    )

    material = result["material"]
    assert material is not None
    assert material.time == "1998-06-27"
    assert material.title == (
        "REMARKS BY PRESIDENT CLINTON AND PRESIDENT JIANG ZEMIN IN PHOTO OPPORTUNITY"
    )
    assert material.body == (
        "PRESIDENT JIANG: I welcome you, Mr. President.\n\n"
        "PRESIDENT CLINTON: Thank you, Mr. President."
    )
