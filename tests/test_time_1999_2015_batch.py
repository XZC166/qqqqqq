import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    ("time_collateral_damage_1999.html", "https://time.com/archive/6955373/collateral-damage-8/", "1999-05-24", "TIME Staff", "Collateral Damage (24 May 1999)", 20, 9542, "25f65f1a4b25545e8cf7e1b425a06d7bc9b3f0f3d11b1d412276c89d60a3df38"),
    ("time_embassy_bombing_1999.html", "https://time.com/archive/6955258/the-embassy-bombing-small-steps-to-a-big-disaster-2/", "1999-05-24", "Mark Thompson", "The Embassy Bombing: Small Steps to a Big Disaster (24 May 1999)", 11, 4723, "4912a39cc19e5af9edca0d0b749adf380b9e4cfe62c8e7f3a2681ea2e5f04278"),
    ("time_crouching_tiger_2001.html", "https://time.com/archive/6670779/crouching-tiger-hidden-message/", "2001-03-12", "TIME", "Crouching Tiger, Hidden Message", 8, 4154, "3c20cfe0307b49642529894f7df20d6200f6c9c3a0c14392b2a17dc1f2cf8da4"),
    ("time_saving_face_2001.html", "https://time.com/archive/6672669/saving-face/", "2001-04-02", "TIME Staff", "Saving Face", 32, 23106, "9f1bc5363dcced36baeef7a80972532b7095b7f5503524926ae5d6ab7aa218d8"),
    ("time_hu_visit_2010.html", "https://time.com/archive/6691358/hus-visit-finding-a-way-forward-on-u-s-china-relations/", "2010-04-08", "TIME", "Hu's Visit: Finding a Way Forward on U.S.-China Relations", 36, 25473, "f11a22e04b66d5d953d51e610ec69c85413de6b43fd37e2f5291ac81b71b1b80"),
    ("time_chinese_hacker_2014.html", "https://time.com/2918689/how-to-hunt-a-chinese-hacker/", "2014-07-03", "Sam Frizell", "How to Hunt a Chinese Hacker", 32, 11266, "0d811fe185f45cfb95851cd99b6e6296207413120cae37a63a3aa22bee8d4823"),
    ("time_china_decade_2015.html", "https://time.com/4004397/the-china-decade/", "2015-08-20", "Ian Bremmer", "The China Decade", 28, 12036, "6f869c5cebd8b5931bf2358ccd801d1e521af39a3bd28a42284267e222f81169"),
)


@pytest.mark.parametrize("fixture,url,date,author,title,paragraphs,length,digest", CASES)
def test_reviewed_time_1999_2015_articles_match_full_body(fixture, url, date, author, title, paragraphs, length, digest):
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=(FIXTURES / fixture).read_bytes()),
        MaterialCandidate(url, "1992-2016", "media", "time-us-china-1999-2015-20261109"),
    )
    material = result["material"]
    assert material is not None
    assert (material.source, material.time, material.author, material.title) == (
        "TIME", date, author, title,
    )
    assert len(material.body.split("\n\n")) == paragraphs
    assert len(material.body) == length
    assert hashlib.sha256(material.body.encode()).hexdigest() == digest
    assert material.abstract.startswith("据正文整理：")
    assert material.keywords
    assert result["evidence"].body_complete and result["evidence"].metadata_verified
