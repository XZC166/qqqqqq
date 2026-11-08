import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    ("time_trump_cold_war_2017.html", "https://time.com/4644775/donald-trump-china-trade-cold-war/", "2017-01-24", "Charlie Campbell", "Donald Trump Could Be Starting a New Cold War With China. But He Has Little Chance of Winning", 65, 22931, "faab7ab7572223f24674ecedca81f949c4965912787139018140cb1172bb73ab"),
    ("time_trump_tariff_tussle_2018.html", "https://time.com/5228991/president-trumps-tariff-tussle-with-china-is-just-the-beginning/", "2018-04-05", "Ian Bremmer", "Why President Trump’s Tariff Tussle With China Is Just the Beginning", 14, 4227, "8095cab3a0c9fc0670025cb14fd0319653f9fb97f17caffb1d09742ff5909910"),
    ("time_trade_war_world_status_2019.html", "https://time.com/5590699/u-s-china-trade-war-reveals-world-status/", "2019-05-17", "Peter Frankopan", "The U.S.-China Trade War Reveals America's New World Status", 14, 6199, "7c016be8c8ea29c75eac000a3b27551d5efb2c60137eb1f91309a03e870e230d"),
    ("time_taiwan_election_2020.html", "https://time.com/5759394/taiwan-election-2020/", "2020-01-06", "Charlie Campbell", "Here's What's at Stake in Taiwan's Presidential Election", 39, 10070, "e33b39106122533eaa7741e0d6aeaeadaf34b3410342f1a7ca15837058629d70"),
    ("time_biden_xi_taiwan_2022.html", "https://time.com/6201447/joe-biden-xi-jinping-taiwan-china/", "2022-07-28", "Charlie Campbell", "China’s Xi Jinping Warns President Joe Biden Against ‘Playing With Fire’ Over Taiwan", 23, 7386, "1cda1f6597e2d84e08a3cf2e8612dd3d130ae519211aa7e366a5c54ac5645c69"),
    ("time_us_china_ai_2023.html", "https://time.com/6272400/us-china-ai-competition/", "2023-04-18", "Paul Scharre", "To Stay Ahead of China in AI, the U.S. Needs to Work with China", 11, 5332, "89107d00319bd576cee8f264d770e2e6ae81eeb578a68f7b720fcc83edfacbc6"),
    ("time_china_ai_chips_2025.html", "https://time.com/7204164/china-ai-advances-chips/", "2025-01-08", "Harry Booth", "How China Is Advancing in AI Despite U.S. Chip Restrictions", 31, 10937, "85341107fab53a66350fa2c4a7d2f7e086588304782be3c683771c33d299cb5e"),
)


@pytest.mark.parametrize("fixture,url,date,author,title,paragraphs,length,digest", CASES)
def test_reviewed_time_2017_2025_articles_match_full_body(fixture, url, date, author, title, paragraphs, length, digest):
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url, body=(FIXTURES / fixture).read_bytes()),
        MaterialCandidate(url, "2017-2025", "media", "time-trade-taiwan-ai-20261109"),
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


def test_time_2025_ai_article_uses_published_date_and_rejects_changed_publication_day():
    case = CASES[-1]
    raw = (FIXTURES / case[0]).read_bytes()
    changed = raw.replace(b"2025-01-08T17:46:13.000Z", b"2025-01-09T17:46:13.000Z")
    assert changed != raw
    fixture_result = GovernmentArticleAdapter().extract(
        HtmlResponse(case[1], body=raw),
        MaterialCandidate(case[1], "2017-2025", "media", "time-ai-date-mutation"),
    )
    mutated_result = GovernmentArticleAdapter().extract(
        HtmlResponse(case[1], body=changed),
        MaterialCandidate(case[1], "2017-2025", "media", "time-ai-date-mutation"),
    )
    assert fixture_result["material"] is not None
    assert fixture_result["material"].time == "2025-01-08"
    assert mutated_result["material"] is None
