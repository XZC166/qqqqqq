import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    ("time_red_china_home_mao_19640306.html", "https://time.com/archive/6871528/red-china-at-home-with-mao/", "1949-1972", "TIME", "TIME", "1964-03-06", "Red China: At Home with Mao", "time", 11, 3514, "0f6b02a8192da7b20ecf4b77ae5540c28c7750887e0a09b4673aea16bdcc666c"),
    ("time_asia_test_tigers_19650226.html", "https://time.com/archive/6627307/asia-a-test-for-tigers/", "1949-1972", "TIME", "TIME", "1965-02-26", "Asia: A Test for Tigers", "time", 52, 27358, "d1b6ab301765471ca2cced3473151a97bacd0dc0d2385215078540f8a8be5689"),
    ("time_red_china_chain_19641030.html", "https://time.com/archive/6814031/red-china-start-of-the-chain/", "1949-1972", "TIME", "TIME", "1964-10-30", "Red China: Start of the Chain", "time", 8, 4272, "6c68a7cea316ae2bacf42f1dfa5c0fdf0f77e641c924ac58d90c6081d68c026f"),
    ("time_red_china_cave_19660909.html", "https://time.com/archive/6630140/red-china-back-to-the-cave/", "1949-1972", "TIME", "TIME", "1966-09-09", "Red China: Back to the Cave!", "time", 46, 25354, "0ced6f6b47775074f5fab490b19a430544f404da01a4cc93ac1c8e07c9548716"),
    ("time_red_china_appalling_alone_19660930.html", "https://time.com/archive/6630281/red-china-appalling-alone/", "1949-1972", "TIME", "TIME", "1966-09-30", "Red China: Appalling & Alone", "time", 10, 4332, "91fbce4b137a9e56540e9e8e9f01088ffb78c6571826a56057de7537ccc9aa48"),
    ("time_china_stability_19690411.html", "https://time.com/archive/6636820/world-chinas-search-for-stability/", "1949-1972", "TIME", "TIME", "1969-04-11", "World: CHINA'S SEARCH FOR STABILITY", "time", 11, 6493, "da529dc4b057348ed1a1966ff34680e727bada6fec4c9a026c80db51c253bc58"),
    ("time_china_un_debate_19711025.html", "https://time.com/archive/6815015/the-world-the-china-debate-finally-begins/", "1949-1972", "TIME", "TIME", "1971-10-25", "The World: The China Debate Finally Begins", "time", 11, 5883, "9bd984c41d487133e3f274a600b84d1e12f4e2bb4e69567847ff6741bf9fbd06"),
    ("time_nixon_peking_announcement_19710726.html", "https://time.com/archive/6814714/the-nation-nixons-coup-to-peking-for-peace/", "1949-1972", "TIME", "TIME", "1971-07-26", "The Nation: Nixon's Coup: To Peking for Peace", "time", 47, 27149, "69a13b0464acfbe19666e673f7087272f8735ab9cfe7bb3b1b70606f290cf3bd"),
    ("time_china_un_seat_19710920.html", "https://time.com/archive/6843822/diplomacy-a-new-stripe-at-the-u-n/", "1949-1972", "TIME", "TIME", "1971-09-20", "DIPLOMACY: A New Stripe at the U.N.", "time", 9, 5720, "667837214253daed3b01d0dd892eeff0a5b77bf29c580d0069817666bfe3bc8f"),
    ("time_nixon_china_departure_19720228.html", "https://time.com/archive/6839664/the-presidency-now-in-living-color-from-china/", "1949-1972", "TIME", "TIME", "1972-02-28", "THE PRESIDENCY: Now, in Living Color from China", "time", 14, 9337, "0634a6cbaec47a2e4fd23c7b3717abcab235d16b821fbc4565712baaf2934fed"),
    ("abc_us_china_coronavirus_envoy_20200314.html", "https://www.abc.net.au/news/2020-03-14/us-summons-chinese-envoy-over-beijing-coronavirus-comments/12056396", "2017-2025", "ABC News", "Reuters", "2020-03-14", "US-China tensions intensify over comments American military might have brought coronavirus to Wuhan", "abc_news_nested", 19, 3176, "d4def3070679c80e4e9a3418f0e8aa061cb8c74e2288d114ed71c21dbbad8687"),
    ("abc_huawei_5g_us_china_20190130.html", "https://www.abc.net.au/news/2019-01-30/huawei-china-us-fight-technology-dominance-australia/10762746", "2017-2025", "ABC News", "Adam Ni", "2019-01-30", "Australia a potential target in US-China fight over Huawei", "abc_news_nested", 25, 3916, "c2ade4b5fb15310b5cdfa08304dda641294370163f4cb51630392f5a9f458db4"),
    ("abc_trade_tariffs_china_20180404.html", "https://www.abc.net.au/news/2018-04-04/us-hits-china-with-increased-tariffs-on-huge-list-of-imports/9617474", "2017-2025", "ABC News", "AP/Reuters", "2018-04-04", "US hits back at China with plans to increase tariffs on 1,300 imports", "abc_news_nested", 33, 5504, "9f4b664b3a1bd51cda86efd8d55af40080b587604951c7b7ffdeb11644c9093e"),
    ("abc_us_taiwan_trade_china_20230602.html", "https://www.abc.net.au/news/2023-06-02/us-and-taiwan-sign-trade-deal-as-china-issues-warning/102425100", "2017-2025", "ABC News", "AFP/AP", "2023-06-02", "US and Taiwan sign trade deal as China issues warning on 'wrong signals' to independence forces", "abc_news_nested", 23, 4127, "82c2baed35f0bbb1852e72b30d064ca4a533da5c73bc2ea3fd0b89f6bc5440e6"),
)


def _extract(case, raw=None, url=None):
    fixture, source_url, period, *_ = case
    response_url = url or source_url
    return GovernmentArticleAdapter().extract(
        HtmlResponse(
            response_url,
            body=raw if raw is not None else (FIXTURES / fixture).read_bytes(),
        ),
        MaterialCandidate(response_url, period, "media", "reviewed-time-abc-20261109"),
    )


@pytest.mark.parametrize("case", CASES)
def test_reviewed_time_and_abc_articles_match_complete_source_body(case):
    result = _extract(case)
    material = result["material"]

    assert material is not None
    _, url, _, source, author, date, title, _, paragraphs, length, digest = case
    assert (material.source, material.time, material.author, material.title) == (
        source, date, author, title,
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
def test_reviewed_abc_news_rejects_changed_text_or_metadata(mutation):
    case = CASES[11]
    raw = (FIXTURES / case[0]).read_bytes()
    replacements = {
        "body": (b"have already banned Huawei from building", b"have already embraced Huawei in building"),
        "date": (b"2019-01-30T02:29:05+00:00", b"2019-01-31T02:29:05+00:00"),
        "title": (b"Australia a potential target in US-China fight over Huawei", b"Australia's Huawei target"),
        "author": (b"By Adam Ni", b"By Unknown"),
    }
    before, after = replacements[mutation]
    assert before in raw
    assert _extract(case, raw=raw.replace(before, after, 1))["material"] is None
