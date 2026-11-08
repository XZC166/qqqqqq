import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    ("time_war_late_entry_19501106.html", "https://time.com/archive/6615999/war-late-entry/", "1950-11-06", "War: Late Entry", 5, 1445, "bb038e0c6a4e7669c6d3b8aa4fb23b697f7e6ce9cea0b01767a5f013047725fe"),
    ("time_battle_korea_breakthrough_19501211.html", "https://time.com/archive/6616371/battle-of-korea-after-the-breakthrough/", "1950-12-11", "BATTLE OF KOREA: After the Breakthrough", 13, 5684, "4c06f568792fefbdf1a82608d02aa20c7b596a7855f2b49af36b55cd87d5d946"),
    ("time_war_asia_not_too_late_19500703.html", "https://time.com/archive/6615045/war-in-asia-not-too-late/", "1950-07-03", "WAR IN ASIA: Not Too Late?", 22, 8079, "e0cef87e2537be205d111c0a70eb08060d54b07d52c6abea53ccb4b1f293a948"),
    ("time_war_korea_three_fronts_19520922.html", "https://time.com/archive/6887156/war-in-korea-three-fronts/", "1952-09-22", "WAR IN KOREA: Three Fronts", 3, 1554, "b0592f064181e12dfa584a01143910406d2c32b75cc907680a6da089c30c8f97"),
    ("time_korea_tug_of_war_19530810.html", "https://time.com/archive/6620963/korea-tug-of-war/", "1953-08-10", "KOREA: Tug of War", 6, 2700, "ab308ba72ea861e9df030b8c808c1370cd136ccc81984bc21d4507df5dda12eb"),
    ("time_china_uprisings_19510312.html", "https://time.com/archive/6608182/china-uprisings-against-the-reds/", "1951-03-12", "CHINA: Uprisings Against the Reds", 6, 2443, "99640e8333d8334fcda66220ed92d550b515db7ba825900538b07d4d9a6fd405"),
    ("time_un_seven_months_after_19510129.html", "https://time.com/archive/6886123/united-nations-seven-months-after/", "1951-01-29", "UNITED NATIONS: Seven Months After", 15, 4746, "383bb33d7c3c9f3c7534de90aad1a61d27d736362f561b601481f17fa1772a81"),
    ("time_china_comrades_competitors_19510108.html", "https://time.com/archive/6607993/the-nations-comrades-or-competitors/", "1951-01-08", "THE NATIONS: Comrades or Competitors?", 12, 4312, "5360a87ce7e04cc6ca55d72b5cb58f1a67b0c87949d306e0f9ded4c221dd1b5e"),
    ("time_china_rubber_communist_19510618.html", "https://time.com/archive/6617273/china-rubber-communist/", "1951-06-18", "CHINA: Rubber Communist", 45, 20360, "a7ef7f0276d3a19e03fb038d6bd8e2dfffe6a6b7c8cac763fe3ea9c2d9d6d14c"),
    ("time_enemy_human_sea_19510212.html", "https://time.com/archive/6885350/the-enemy-human-sea/", "1951-02-12", "THE ENEMY: Human Sea", 10, 4089, "770db66c5d6ce48d3e586e610a6dfed2d926668d4385ffe7f7f3ab2e67e731be"),
)


@pytest.mark.parametrize("case", CASES)
def test_reviewed_time_korean_war_article_matches_full_body(case):
    fixture, url, date, title, paragraph_count, length, digest = case
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=(FIXTURES / fixture).read_bytes()),
        MaterialCandidate(url, "1949-1972", "media", "reviewed-time-korean-war"),
    )
    material = result["material"]

    assert material is not None
    assert (material.source, material.time, material.author, material.title) == (
        "TIME", date, "TIME", title,
    )
    assert material.source_url == url
    assert len(material.body.split("\n\n")) == paragraph_count
    assert len(material.body) == length
    assert hashlib.sha256(material.body.encode()).hexdigest() == digest
    assert material.abstract.startswith("据正文整理：")
    assert material.keywords
    assert result["evidence"].body_complete
    assert result["evidence"].metadata_verified
    assert result["evidence"].original_page_verified
