import hashlib
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"
CASES = (
    (
        "guardian_liberty_goddess_2014.html",
        "https://www.theguardian.com/theguardian/2014/may/31/tiananmen-square-liberty-goddess-archive",
        "1992-2016", "John Gittings", "2014-05-31",
        "From the archive, 31 May 1989: Liberty goddess riles leadership",
        2477, "f1be662e208d8d67ad6fc7e2305664f46efd2c0850fce31803ffac8ea7354164",
    ),
    (
        "guardian_gittings_19990601_1.html",
        "https://www.theguardian.com/world/1999/jun/01/china.johngittings",
        "1992-2016", "John Gittings", "1999-06-01",
        "How the Guardian covered the brutal crackdown on the Tiananmen Square protests in 1989",
        7914, "9edbe89328c2f72a0d34f364720ac12723271c3fb1151b9d9b4b96bead91ce59",
    ),
    (
        "guardian_gittings_19990601_2.html",
        "https://www.theguardian.com/world/1999/jun/01/china.johngittings1",
        "1992-2016", "John Gittings", "1999-06-01",
        "Beijing under occupation, June 5-8",
        11285, "294113460905627e0c6ceb7596d4f8f9a2e8a97baba80c5098029acb35fb1bbe",
    ),
    (
        "guardian_gittings_19990601_3.html",
        "https://www.theguardian.com/world/1999/jun/01/china.johngittings2",
        "1992-2016", "John Gittings", "1999-06-01",
        "Postmortem on the crushing of the students",
        9722, "66f45634a0caa2bdd2d5a8552ae0a10e39dfc0c7e68fdcbd8f4c7750bc6a00fa",
    ),
    (
        "guardian_tiananmen_papers_2001.html",
        "https://www.theguardian.com/world/2001/jan/09/worlddispatch.china",
        "1992-2016", "Guardian Staff", "2001-01-09",
        "Tiananmen revelations raise new questions about massacre",
        6353, "dd04547deca343ba950ccb3bce7ecf525770eeeab9fdbe76c84eae9c73059a86",
    ),
    (
        "guardian_isabel_hilton_2005.html",
        "https://www.theguardian.com/world/2005/jun/04/china.comment",
        "1992-2016", "Isabel Hilton", "2005-06-03",
        "Reaching beyond the myth of Mao",
        6702, "2b0cf6e541fe4b3f8be3e894c36babe80ec8a669c4d6ac2d56746289d68a35de",
    ),
    (
        "guardian_other_tiananmens_2019.html",
        "https://www.theguardian.com/world/2019/jun/02/chinas-other-tiananmens-30th-anniversary-1989-protests",
        "2017-2025", "Lily Kuo", "2019-06-02",
        "China’s other Tiananmens: 30 years on",
        13764, "9e714208fe914c51b33776c102c58617cbd4a173a782ef811eccd31d7ee10d9d",
    ),
    (
        "guardian_mirsky_observer_2019.html",
        "https://www.theguardian.com/world/2019/jun/02/tiananmen-square-30-years-on-china-brutal-events-jonathan-mirsky",
        "2017-2025", "Jonathan Mirsky", "2019-06-02",
        "Tiananmen Square 30 years on: ‘At 3am, I feared I might be killed’",
        4263, "c4f81fa2932173efd86d7bdf81d69afd11754fb3b217e3a6317552dacbc63881",
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
        MaterialCandidate(response_url, period, "media", "reviewed-guardian"),
    )


@pytest.mark.parametrize("case", CASES)
def test_reviewed_guardian_article_preserves_only_complete_article_body(case):
    result = _extract(case)
    material = result["material"]

    assert material is not None
    _, url, _, author, date, title, length, digest = case
    expected_source = "The Guardian (The Observer)" if case[1].endswith("jonathan-mirsky") else "The Guardian"
    assert (material.source, material.author, material.time, material.title) == (
        expected_source, author, date, title,
    )
    assert material.source_url == url
    assert len(material.body) == length
    assert hashlib.sha256(material.body.encode()).hexdigest() == digest
    assert material.keywords
    assert result["evidence"].body_complete
    assert result["evidence"].metadata_verified
    assert result["evidence"].original_page_verified
    if "gittings_19990601_2" in case[0] or "gittings_19990601_3" in case[0]:
        assert "This report and other material" not in material.body
    if "tiananmen_papers" in case[0]:
        assert "Useful links" not in material.body
        assert "Email john.gittings" not in material.body


@pytest.mark.parametrize("mutation", ["body", "date", "author", "url"])
def test_reviewed_guardian_article_rejects_metadata_or_body_changes(mutation):
    case = CASES[1]
    raw = (FIXTURES / case[0]).read_bytes()
    url = None
    if mutation == "body":
        raw = raw.replace(b"A two-pronged attack from east", b"A changed attack from east")
    elif mutation == "date":
        raw = raw.replace(b"1999-06-01", b"1999-06-02")
    elif mutation == "author":
        raw = raw.replace(b">John Gittings<", b">Unknown Author<", 1)
    else:
        url = "https://www.theguardian.com/world/1999/jun/02/china.johngittings"

    assert _extract(case, raw=raw, url=url)["material"] is None
