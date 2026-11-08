import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
TIME_CASES = (
    ("time_china_advice_nixon_1989.html", "https://time.com/archive/6703890/china-advice-from-a-former-president/", "1989-11-20", "TIME", "China Advice from a Former President", 29, 11729, "1c71b965dd57d55db7c7b491ceda882cdb9493a5ed08f635ee66cce8448396c1"),
    ("time_china_deng_big_lie_1989.html", "https://time.com/archive/6702848/china-dengs-big-lie/", "1989-06-26", "Jill Smolowe", "China Deng's Big Lie", 20, 10897, "960b003972614ca60d6d6f939d84c5b3233f0d0147230afd1719872ed8f7edaa"),
    ("time_china_come_out_1989.html", "https://time.com/archive/6702408/china-come-out-come-out/", "1989-05-01", "TIME", "China Come Out! Come Out!", 12, 8010, "8b866f96ff31f489d90a1fef97786590e02683edb2bb552e69bee3d6eed843eb"),
    ("time_waiting_deng_1979.html", "https://time.com/archive/6846036/nation-waiting-for-deng-xiaoping/", "1979-01-29", "TIME", "Nation: Waiting for Deng Xiaoping", 9, 4869, "58556fe109f5f9237f5a10ecbea655db58fa328e236675bb5f5069d4568532ce"),
    ("time_tying_sino_american_knot_1979.html", "https://time.com/archive/6853967/china-tying-the-sino-american-knot/", "1979-01-15", "TIME", "CHINA: Tying the Sino-American Knot", 13, 7734, "2f8802f24db9fb15fcff1755589725863e9de5f5cf23c093211dddea536284ec"),
    ("time_wrath_deng_1989.html", "https://time.com/archive/6702803/the-wrath-of-deng/", "1989-06-19", "Howard Chua-Eoan", "The Wrath of Deng", 31, 17464, "15ef392bb93d7d281a1593831ac6061f216104f8cb774d37f5f6d64d230834d3"),
)


@pytest.mark.parametrize("fixture,url,date,author,title,paragraphs,length,digest", TIME_CASES)
def test_reviewed_time_1979_1989_articles_match_full_body(fixture, url, date, author, title, paragraphs, length, digest):
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=(FIXTURES / fixture).read_bytes()),
        MaterialCandidate(url, "1972-1991", "media", "time-tiananmen-and-normalization-20261109"),
    )
    material = result["material"]
    assert material is not None
    assert (material.source, material.time, material.author, material.title) == (
        "TIME", date, author, title,
    )
    assert len(material.body.split("\n\n")) == paragraphs
    assert len(material.body) == length
    assert hashlib.sha256(material.body.encode()).hexdigest() == digest
    assert result["evidence"].body_complete and result["evidence"].metadata_verified


def test_reviewed_pbs_2001_china_transcript_matches_full_text_and_metadata():
    url = "https://www.pbs.org/newshour/show/reevaluating-china-u-s-relations"
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=(FIXTURES / "pbs_reevaluating_china_us_2001.html").read_bytes()),
        MaterialCandidate(url, "1992-2016", "media", "pbs-china-relations-2001"),
    )
    material = result["material"]
    assert material is not None
    assert (material.time, material.source, material.title, material.author) == (
        "2001-03-22", "PBS News", "Reevaluating China-U.S. Relations", "未注明",
    )
    assert len(material.body) == 14979
    assert hashlib.sha256(material.body.encode()).hexdigest() == "e84752e3b526878bd6ea0175f129230bbb99f83d43a1a1a907978518b8fcad32"
    assert material.abstract.startswith("President Bush said during his campaign")
    assert result["evidence"].body_complete and result["evidence"].metadata_verified
