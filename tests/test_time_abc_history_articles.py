import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    (
        "time_china_last_phase_19491212.html",
        "https://time.com/archive/6791512/china-last-phase/",
        "1949-1972", "TIME", "TIME", "1949-12-12", "CHINA: Last Phase",
        "time", 4, 2103,
        "d49f0211124f9eeadc984d40d9ac63bb0058cdaf95598b62e878151ffccc8d9d",
    ),
    (
        "time_china_last_stand_19491219.html",
        "https://time.com/archive/6792534/china-last-stand/",
        "1949-1972", "TIME", "TIME", "1949-12-19", "CHINA: Last Stand",
        "time", 6, 3173,
        "6a64e4eb8291800268faf7f5f0dcc2af7bdd7ad1038e7eec92b55b4085824210",
    ),
    (
        "time_china_communists_have_come_19490606.html",
        "https://time.com/archive/6604246/china-the-communists-have-come/",
        "1949-1972", "TIME", "TIME", "1949-06-06", "CHINA: The Communists Have Come",
        "time", 18, 8026,
        "65959a1d0775e49618a7461ec9bcf757d311cdfc437a2115f374deb0f346261c",
    ),
    (
        "time_china_next_chungking_19491024.html",
        "https://time.com/archive/6607475/china-next-chungking/",
        "1949-1972", "TIME", "TIME", "1949-10-24", "CHINA: Next: Chungking",
        "time", 6, 2082,
        "9afcfa2f9bc5cac5a4aebe4a6ec178456868db21b448ea9955897cadeabe45e8",
    ),
    (
        "time_china_coup_19491121.html",
        "https://time.com/archive/6793782/china-coup/",
        "1949-1972", "TIME", "TIME", "1949-11-21", "CHINA: Coup",
        "time", 5, 2962,
        "832aad57256ce77f6641f3441d72287182ee346276a27c134b2ef5ba0376c0ec",
    ),
    (
        "time_china_ultimatum_19490425.html",
        "https://time.com/archive/6793693/china-ultimatum/",
        "1949-1972", "TIME", "TIME", "1949-04-25", "CHINA: Ultimatum",
        "time", 4, 1385,
        "07ecabebb3dd58f1af656e2a57b3050d41d863658152610109a861a7a0141c40",
    ),
    (
        "abc_worldtoday_trade_relations_20000920.html",
        "https://www.abc.net.au/worldtoday/archive/articles/2000/09/20/s181924.htm",
        "1992-2016", "ABC Radio (The World Today)", "Tom O'Byrne", "2000-09-20",
        "US to restore trading relations with China", "abc_archive", 14, 4143,
        "ef0821832148baaf832f83923dc73f2677e499df076df7535449b76fd209ef82",
    ),
    (
        "abc_worldtoday_relations_apec_20011019.html",
        "https://www.abc.net.au/worldtoday/archive/articles/2001/10/19/s395557.htm",
        "1992-2016", "ABC Radio (The World Today)", "Michael Vincent", "2001-10-19",
        "Question mark hangs over warming of US-Chinese relations", "abc_archive", 16, 3708,
        "443f5a70a177f59be88085709f4884d236ba796cf11322b0fb20f51e4e49c196",
    ),
    (
        "abc_worldtoday_mixed_messages_20010409.html",
        "https://www.abc.net.au/worldtoday/archive/articles/2001/04/09/s274512.htm",
        "1992-2016", "ABC Radio (The World Today)", "Michael Carey", "2001-04-09",
        "US and China send mixed messages", "abc_archive", 17, 3653,
        "f46433b43f6ee08a53e22a389554353881ce309fc971ff7a4dcc7d2c55dde216",
    ),
    (
        "abc_pm_spy_plane_eases_20010406.html",
        "https://www.abc.net.au/pm/archive/articles/2001/04/06/s273403.htm",
        "1992-2016", "ABC Radio (PM)", "Tom O'Byrne", "2001-04-06",
        "China eases stance over US spy plane", "abc_archive", 24, 6351,
        "1b8a8493da9accf4bdbaae4c78a961c6cc7cccb1838dbfd6b0f357e96f529d52",
    ),
    (
        "abc_pm_spy_plane_patience_20010403.html",
        "https://www.abc.net.au/pm/archive/articles/2001/04/03/s271358.htm",
        "1992-2016", "ABC Radio (PM)", "Tom O'Byrne", "2001-04-03",
        "US patience wears as China withholds plane", "abc_archive", 31, 8023,
        "f26ce1fbdc3fdbf7e85708d53079ce86024127f2a8868288d4cc5623a185f1b0",
    ),
)


def _extract(case, raw=None, url=None):
    fixture, source_url, period, *_ = case
    response_url = url or source_url
    return GovernmentArticleAdapter().extract(
        HtmlResponse(
            response_url,
            body=raw if raw is not None else (FIXTURES / fixture).read_bytes(),
        ),
        MaterialCandidate(response_url, period, "media", "reviewed-time-abc-history"),
    )


@pytest.mark.parametrize("case", CASES)
def test_reviewed_time_and_abc_archive_articles_match_full_source(case):
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
def test_reviewed_abc_archive_rejects_changed_text_or_metadata(mutation):
    case = CASES[6]
    raw = (FIXTURES / case[0]).read_bytes()
    if mutation == "body":
        raw = raw.replace(b"President Clinton", b"President Example", 1)
    elif mutation == "date":
        raw = raw.replace(b"2000-09-20T00:00:00+10:00", b"2000-09-21T00:00:00+10:00", 1)
    elif mutation == "title":
        raw = raw.replace(b"US to restore trading relations with China", b"US to restore trade", 1)
    else:
        raw = raw.replace(b"Reporter: Tom O&#x27;Byrne", b"Reporter: Unknown", 1)

    assert _extract(case, raw=raw)["material"] is None
