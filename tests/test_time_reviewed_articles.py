import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    (
        "time_china_what_can_li_do_19490131.html",
        "https://time.com/archive/6785414/china-what-can-li-do/",
        "1949-01-31", "CHINA: What Can Li Do?", 5, 1759,
        "e7f81783699e699e0e15151d711d83d0d912630db65538c2cecd892fb8b38dde",
    ),
    (
        "time_china_defeat_19490207.html",
        "https://time.com/archive/6602114/china-defeat/",
        "1949-02-07", "CHINA: Defeat", 9, 4265,
        "cd2f1848c007052167071fa01479884fa1a68bd0b48cfd3704757ed89934b5d4",
    ),
    (
        "time_window_dressing_19490627.html",
        "https://time.com/archive/6602803/foreign-news-window-dressing/",
        "1949-06-27", "Foreign News: Window-Dressing", 1, 559,
        "a34b305baa0edbf3ca185c143adc850b3812deac032152f21c040a9f8ba06377",
    ),
    (
        "time_mao_settles_dust_19490711.html",
        "https://time.com/archive/6791264/the-nations-mao-settles-the-dust/",
        "1949-07-11", "THE NATIONS: Mao Settles the Dust", 8, 3047,
        "7028b51a0817867652f0a81b651df994c87a74ab2f911dfea4680ff8c2469d03",
    ),
    (
        "time_democratic_dictatorship_19491003.html",
        "https://time.com/archive/6603186/china-democratic-dictatorship/",
        "1949-10-03", "CHINA: Democratic Dictatorship", 5, 1550,
        "58d2947261ac0c1840d1d93da76b8ec989163b403ea3d2c0390f7e07183a7338",
    ),
    (
        "time_nations_teamwork_19491010.html",
        "https://time.com/archive/6603251/the-nations-teamwork/",
        "1949-10-10", "THE NATIONS: Teamwork", 7, 2575,
        "9c36c85421ebbbf91c723d392f27d16707459831c7dade080ab6e047e2e81dec",
    ),
    (
        "time_formosa_heroes_welcome_19540201.html",
        "https://time.com/archive/6797748/formosa-heroes-welcome/",
        "1954-02-01", "FORMOSA: Heroes' Welcome", 11, 5665,
        "2e10dcc5968d366ee00d3f5469544b4814ff9d38ad53eb74e06b7a383c1890ee",
    ),
    (
        "time_formosa_uncle_chen_19540301.html",
        "https://time.com/archive/6621832/formosa-uncle-chen/",
        "1954-03-01", "FORMOSA: Uncle Chen", 6, 2663,
        "45ccb3656e672c7433b01b4e120f13352f5da1c36a929badc93eacc6c39d3761",
    ),
    (
        "time_quemoy_autumn_nightmare_19581006.html",
        "https://time.com/archive/6888300/foreign-news-quemoy-autumn-nightmare/",
        "1958-10-06", "Foreign News: QUEMOY: AUTUMN NIGHTMARE", 12, 5793,
        "90d585da7cce8f2d4894a6848b65bc16ba84fd3ed6599e02859b7f5eb0b16356",
    ),
    (
        "time_nixon_china_journey_19720221.html",
        "https://time.com/archive/6839619/special-section-a-guide-to-nixons-china-journey/",
        "1972-02-21", "SPECIAL SECTION: A Guide to Nixon's China Journey", 23, 10669,
        "ac50a31ee3edf18b0e288924fe82269224c17431c639e261d2f074dd8e76a885",
    ),
)


def _extract(case, raw=None, url=None):
    fixture, source_url, *_ = case
    response_url = url or source_url
    return GovernmentArticleAdapter().extract(
        HtmlResponse(
            response_url,
            body=raw if raw is not None else (FIXTURES / fixture).read_bytes(),
        ),
        MaterialCandidate(response_url, "1949-1972", "media", "reviewed-time-vault"),
    )


@pytest.mark.parametrize("case", CASES)
def test_reviewed_time_vault_article_has_matching_full_body_and_publication_date(case):
    result = _extract(case)
    material = result["material"]

    assert material is not None
    _, url, date, title, paragraphs, length, digest = case
    assert (material.source, material.time, material.author, material.title) == (
        "TIME", date, "TIME", title,
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


@pytest.mark.parametrize("mutation", ["body", "date", "title", "author"])
def test_reviewed_time_vault_rejects_changed_source_text_or_metadata(mutation):
    case = CASES[0]
    raw = (FIXTURES / case[0]).read_bytes()
    if mutation == "body":
        raw = raw.replace(b"Defeated and helpless", b"Changed and helpless")
    elif mutation == "date":
        raw = raw.replace(b"1949-01-31", b"1949-02-01")
    elif mutation == "title":
        raw = raw.replace(b"CHINA: What Can Li Do?", b"CHINA: What Can Li Do!?")
    else:
        raw = raw.replace(b"name=\"author\" content=\"TIME\"", b"name=\"author\" content=\"Unknown\"")

    assert _extract(case, raw=raw)["material"] is None
