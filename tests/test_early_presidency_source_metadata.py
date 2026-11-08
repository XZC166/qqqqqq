from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_1951_truman_and_1955_eisenhower_records_have_hash_bound_metadata():
    cases = (
        (
            "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-542",
            "presidency_truman_conference_1951.html",
            "1951-01-18",
            "据正文整理：杜鲁门在记者会上回应中国共产党拒绝朝鲜停火提议后的美国行动，并表示将推动联合国认定中国为侵略者。",
            "Chinese Communist rejection of ceasefire; Korean War; United Nations; aggressor designation; presidential press conference",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-president-upon-signing-the-joint-resolution-the-defense-formosa",
            "presidency_formosa_resolution_1955.html",
            "1955-01-29",
            "据正文整理：艾森豪威尔在签署保卫福尔摩沙联合决议时感谢国会支持，并表示美国将抵抗共产主义武装侵略、支持联合国推动结束台湾海峡敌对行动，同时维护台湾地区防卫。",
            "Formosa Resolution; Taiwan Strait; U.S. public statement; Communist armed aggression; Congress; United Nations",
        ),
    )

    for url, fixture, published_on, abstract, keywords in cases:
        response = HtmlResponse(
            url=url,
            request=Request(url),
            body=(FIXTURES / fixture).read_bytes(),
            encoding="utf-8",
        )
        candidate = MaterialCandidate(url, "1949-1972", "government", "early-presidency")

        result = GovernmentArticleAdapter().extract(response, candidate)

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
