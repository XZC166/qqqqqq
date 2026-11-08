from research_crawler.reviewed_sources import (
    BROOKINGS_REVIEWED_ABSTRACTS,
    BROOKINGS_REVIEWED_KEYWORDS,
    PRESIDENCY_REVIEWED_HASHED_METADATA,
    TRUMP_WHITEHOUSE_REVIEWED_HASHED_METADATA,
)
from research_crawler.spiders.government import (
    _reviewed_brookings_abstract,
    _reviewed_brookings_keywords,
    _reviewed_presidency_metadata,
    _reviewed_trump_whitehouse_metadata,
)


def test_2021_public_opinion_keywords_are_bound_to_reviewed_article_body():
    url = "https://www.brookings.edu/articles/a-momentous-shift-in-us-public-attitudes-toward-china/"
    body_hash, keywords = BROOKINGS_REVIEWED_KEYWORDS[url]

    assert body_hash == "6694e21594c93f0efa6d5d4b7602c4cec0de6586db3543b0ede5523f4c58d554"
    assert keywords == (
        "U.S. public opinion; China threat perceptions; U.S. public attitudes; COVID-19; Taiwan"
    )
    assert _reviewed_brookings_keywords(url, "changed or incomplete article body") == ""


def test_2024_global_views_keywords_are_bound_to_reviewed_article_body():
    url = "https://www.brookings.edu/articles/comparing-global-views-of-the-united-states-and-china-during-the-trump-and-biden-administrations/"
    body_hash, keywords = BROOKINGS_REVIEWED_KEYWORDS[url]

    assert body_hash == "98db8a8d9bde1a983d36ad89257b49fa4d3d808a67f3ee3355ef3f61834790d7"
    assert keywords == (
        "global public opinion; U.S. leadership; China favorability; soft power; U.S.-China competition"
    )
    assert _reviewed_brookings_keywords(url, "changed or incomplete article body") == ""


def test_1997_brookings_abstract_is_derived_only_for_the_reviewed_body():
    url = "https://www.brookings.edu/articles/the-united-states-and-china-a-new-framework/"
    body_hash, abstract = BROOKINGS_REVIEWED_ABSTRACTS[url]

    assert body_hash == "45b334cd9c71b9c49b1041eb1fc86568906da40089be05781a3b308a544a37ac"
    assert abstract.startswith("据正文整理：")
    assert BROOKINGS_REVIEWED_KEYWORDS[url][0] == body_hash
    assert _reviewed_brookings_abstract(url, "changed or incomplete article body") == ""


def test_recently_revalidated_presidency_records_have_hash_bound_metadata():
    urls = {
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-586",
        "https://www.presidency.ucsb.edu/documents/special-message-the-congress-reporting-the-situation-korea",
        "https://www.presidency.ucsb.edu/documents/letter-ambassador-warren-austin-restating-the-us-position-formosa",
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-598",
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-579",
        "https://www.presidency.ucsb.edu/documents/address-mass-rally-taipei",
        "https://www.presidency.ucsb.edu/documents/joint-statement-following-discussions-with-president-chiang-kai-shek",
        "https://www.presidency.ucsb.edu/documents/remarks-the-sungshan-airport-taipei-upon-leaving-for-okinawa",
        "https://www.presidency.ucsb.edu/documents/toasts-the-president-and-vice-premier-teng-hsiao-ping-the-peoples-republic-china-state",
        "https://www.presidency.ucsb.edu/documents/new-years-message-from-the-president-premier-hua-guofeng-the-peoples-republic-china",
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-974",
        "https://www.presidency.ucsb.edu/documents/cultural-agreement-between-the-united-states-and-china",
        "https://www.presidency.ucsb.edu/documents/united-states-peoples-republic-china-agreements-remarks-the-signing-ceremony",
        "https://www.presidency.ucsb.edu/documents/interview-with-chinese-television-journalists-beijing",
        "https://www.presidency.ucsb.edu/documents/statement-press-secretary-fitzwater-united-states-sanctions-against-the-chinese-government",
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-before-foreign-correspondents",
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-with-president-jiang-zemin-china-beijing",
        "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-with-premier-zhu-rongji-china",
    }

    assert urls.issubset(PRESIDENCY_REVIEWED_HASHED_METADATA)
    assert all(
        abstract.startswith("据正文整理：") and keywords
        for url in urls
        for _, abstract, keywords in [PRESIDENCY_REVIEWED_HASHED_METADATA[url]]
    )
    assert _reviewed_presidency_metadata(
        next(iter(urls)), "changed or incomplete article body"
    ) is None
    assert "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-582" not in urls


def test_2025_white_house_trade_fact_sheet_metadata_is_hash_bound():
    url = "https://www.whitehouse.gov/fact-sheets/2025/11/fact-sheet-president-donald-j-trump-strikes-deal-on-economic-and-trade-relations-with-china/"
    body_hash, abstract, keywords = TRUMP_WHITEHOUSE_REVIEWED_HASHED_METADATA[url]

    assert body_hash == "25474631cf77d53474e36f26003470f537854b14728a2ac35010afe67dad6e8f"
    assert abstract.startswith("据正文整理：")
    assert keywords
    assert _reviewed_trump_whitehouse_metadata(url, "changed or incomplete article body") == ("", "")
