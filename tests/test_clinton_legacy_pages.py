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


def test_clinton_1997_textonly_address_uses_release_date_and_complete_blockquote():
    result = _extract(
        "clinton_textonly_china_address_1997_synthetic.html",
        "https://clintonwhitehouse4.archives.gov/textonly/WH/New/html/19971024-3863.html",
    )

    material = result["material"]
    assert material is not None
    assert material.time == "1997-10-24"
    assert material.title == "REMARKS BY THE PRESIDENT IN ADDRESS ON CHINA AND THE NATIONAL INTEREST"
    assert material.body.startswith("THE PRESIDENT: We will discuss the future of U.S.-China relations.")
    assert material.body.endswith("Thank you very much. (Applause.)")
    assert "Related White House pages" not in material.body


def test_clintonwhitehouse6_briefing_uses_header_date_and_transcript_end_marker():
    source_url = (
        "https://clintonwhitehouse6.archives.gov/1994/05/"
        "1994-05-26-briefing-by-lake-et-al-on-mfn-status-for-china.html"
    )
    metadata_url = (
        "https://clintonwhitehouse6.archives.gov/1994/05/header/"
        "1994-05-26-briefing-by-lake-et-al-on-mfn-status-for-china.header.html"
    )
    source = HtmlResponse(
        url=source_url,
        request=Request(source_url, meta={"metadata_response": HtmlResponse(
            url=metadata_url,
            request=Request(metadata_url),
            body=(FIXTURES / "clinton_whitehouse6_header_1994_synthetic.html").read_bytes(),
            encoding="utf-8",
        )}),
        body=(FIXTURES / "clinton_whitehouse6_briefing_1994_synthetic.html").read_bytes(),
        encoding="utf-8",
    )
    candidate = MaterialCandidate(
        source_url,
        "1992-2016",
        "government",
        "clinton-whitehouse-china-broadcasting-1994",
        metadata_url=metadata_url,
    )

    result = GovernmentArticleAdapter().extract(source, candidate)
    material = result["material"]
    assert material is not None
    assert material.source == "The White House, Office of the Press Secretary"
    assert material.time == "1994-05-26"
    assert material.title == "1994-05-26 Briefing by Lake et al on MFN Status for China"
    assert material.body == "MR. LAKE: China policy must serve our interests.\n\nQ What happens next?\n\nMR. LAKE: We will continue engagement."
    assert len(result["supporting_evidence"]) == 1
    assert result["supporting_evidence"][0]["evidence"].source_url == metadata_url
