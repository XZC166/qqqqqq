from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_bush_china_documents_have_hash_bound_derived_metadata():
    cases = (
        (
            "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-26",
            "presidency_bush_mfn_conference_1990.html",
            "1990-05-24",
            "据正文整理：布什宣布延长中国最惠国贸易待遇一年，解释其对中美贸易和美国利益的考虑，并回顾天安门事件后的制裁措施。",
            "George H. W. Bush; China; most-favored-nation status; Tiananmen sanctions; U.S.-China trade",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-press-secretary-fitzwater-the-renewal-most-favored-nation-trade-status-for-china",
            "presidency_bush_mfn_fitzwater_1990.html",
            "1990-05-24",
            "据正文整理：新闻秘书声明说明布什延长中国最惠国待遇的决定，列举其对中国人权状况的关切及维持贸易待遇的理由。",
            "China; most-favored-nation status; human rights; U.S.-China trade; White House statement",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-administration-policy-sj-res-153-resolution-disapproval-the-presidents-decision",
            "presidency_bush_mfn_policy_1991.html",
            "1991-07-11",
            "据正文整理：布什政府反对要求撤销对华最惠国待遇延期决定或附加续期条件的参议院议案，并说明继续贸易关系的政策理由。",
            "China; most-favored-nation status; U.S. Congress; trade policy; U.S.-China relations",
        ),
    )

    for url, fixture, published_on, abstract, keywords in cases:
        response = HtmlResponse(
            url=url,
            request=Request(url),
            body=(FIXTURES / fixture).read_bytes(),
            encoding="utf-8",
        )
        result = GovernmentArticleAdapter().extract(
            response,
            MaterialCandidate(url, "1972-1991", "government", "bush-china-public-texts"),
        )
        material = result["material"]

        assert material is not None
        assert material.time == published_on
        assert material.abstract == abstract
        assert material.keywords == keywords
        assert PRESIDENCY_REVIEWED_HASHED_METADATA[url][0] == sha256(
            material.body.encode("utf-8")
        ).hexdigest()
        assert result["abstract_origin"] == "derived"
        assert result["field_sources"]["abstract"] == url
        assert result["field_sources"]["keywords"] == url
