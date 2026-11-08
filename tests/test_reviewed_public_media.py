import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    (
        "guardian_may17_1989.html",
        "https://www.theguardian.com/world/1989/may/17/china.fromthearchive",
        "1972-1991",
        "The Guardian",
        "Leader",
        "1989-05-17",
        "As the old order suddenly crumbles",
        5729,
        "da12ba887e7649e862e1ae4438af024b6e5d6adeb43dc895d0aa42fad1c8c6c5",
    ),
    (
        "guardian_jun05_1989.html",
        "https://www.theguardian.com/world/1989/jun/05/china.fromthearchive",
        "1972-1991",
        "The Guardian",
        "Guardian Staff",
        "1989-06-05",
        "They must not get away with it",
        4384,
        "bcdc02f7a3bd3831f1fe8cd58f7ef0a6478438cda2a96b8805d491a97f9f9d55",
    ),
    (
        "abc_worldtoday_20140604.html",
        "https://www.abc.net.au/worldtoday/archive/articles/2014/06/04/s4018514.htm",
        "1992-2016",
        "ABC Radio (The World Today)",
        "Lindy Kerin",
        "2014-06-04",
        "25 years since Tiananmen Square massacre, China not ready to confront its past",
        5061,
        "db6049990fcb54327e08a6838359fda3cc42443e81c9f3dc8ec028d700486793",
    ),
    (
        "abc_fourcorners_tremble_obey_20190604.html",
        "https://www.abc.net.au/news/2019-06-04/tremble-and-obey/11174758",
        "2017-2025",
        "ABC News (Four Corners)",
        "Lesley Robinson",
        "2019-06-04",
        "Tremble and Obey",
        34798,
        "57d36a8e8f542dbc010739ccd38b1e9d9d6e7e4a5737165f5cd8188be6d1a4bc",
    ),
)


def _extract(case, raw=None, url=None):
    fixture, source_url, period, *_ = case
    response_url = url or source_url
    return GovernmentArticleAdapter().extract(
        HtmlResponse(
            response_url,
            body=raw if raw is not None else (FIXTURES / fixture).read_bytes(),
            encoding="utf-8",
        ),
        MaterialCandidate(response_url, period, "media", "reviewed-public-media"),
    )


@pytest.mark.parametrize("case", CASES)
def test_reviewed_public_media_requires_exact_page_metadata_and_complete_body(case):
    result = _extract(case)

    material = result["material"]
    assert material is not None
    _, url, _, source, author, date, title, size, digest = case
    assert (material.source, material.time, material.author, material.title) == (
        source,
        date,
        author,
        title,
    )
    assert len(material.body) == size
    assert hashlib.sha256(material.body.encode()).hexdigest() == digest
    if case == CASES[3]:
        assert material.abstract.startswith("据正文整理：")
    else:
        assert material.abstract and not material.abstract.startswith("据正文整理：")
    assert material.keywords
    assert material.source_url == url
    assert result["evidence"].body_complete
    assert result["evidence"].metadata_verified
    assert result["evidence"].original_page_verified


@pytest.mark.parametrize("mutation", ["body", "date", "title", "url"])
def test_reviewed_public_media_rejects_unreviewed_changes(mutation):
    case = CASES[0]
    raw = (FIXTURES / case[0]).read_bytes()
    url = None
    if mutation == "body":
        raw = raw.replace(b"glasnost", b"changed", 1)
    elif mutation == "date":
        raw = raw.replace(b"1989-05-17", b"1989-05-18")
    elif mutation == "title":
        raw = raw.replace(b"As the old order suddenly crumbles", b"Changed title")
    else:
        url = "https://www.theguardian.com/world/1989/may/18/china.fromthearchive"

    assert _extract(case, raw=raw, url=url)["material"] is None
