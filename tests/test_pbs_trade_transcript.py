import hashlib
from pathlib import Path

from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


URL = "https://www.pbs.org/newshour/show/what-are-the-ripple-effects-of-a-u-s-china-trade-war"
TITLE = "What are the ripple effects of a U.S.-China trade war?"
DATE = "2018-07-06"
FIXTURE = Path(__file__).parent / "fixtures" / "pbs_trade_war_transcript.html"


def test_pbs_trade_transcript_is_promoted_only_for_reviewed_complete_body():
    candidate = MaterialCandidate(URL, "2017-2025", "media", "pbs-trade-war-transcript")
    raw = FIXTURE.read_bytes()
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url=URL, body=raw, encoding="utf-8"), candidate
    )

    assert result["material"] is not None
    assert result["material"].time == DATE
    assert result["material"].title == TITLE
    assert result["material"].author == "未注明"
    assert result["material"].body.endswith("Thank you.")
    assert hashlib.sha256(result["material"].body.encode()).hexdigest() == (
        "42968a0566a3d750c1d75ca58585ed4e368832412c9725cd37af6a4519afe90a"
    )


def test_pbs_trade_transcript_rejects_changed_transcript_body():
    candidate = MaterialCandidate(URL, "2017-2025", "media", "pbs-trade-war-transcript")
    raw = FIXTURE.read_bytes().replace(b"Thank you.</p>", b"Edited transcript.</p>", 1)
    result = GovernmentArticleAdapter().extract(
        HtmlResponse(url=URL, body=raw, encoding="utf-8"), candidate
    )

    assert result["material"] is None
