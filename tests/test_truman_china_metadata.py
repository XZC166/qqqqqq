from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_truman_china_documents_have_hash_bound_derived_metadata():
    cases = (
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-president-upon-signing-the-foreign-economic-assistance-act",
            "presidency_truman_assistance_china_1950.html",
            "1950-06-05",
            "据正文整理：杜鲁门签署《1950年对外经济援助法》，说明该法授权延续欧洲复兴计划、援助韩国、东南亚及非共产主义中国，并开展技术援助。",
            "Harry S. Truman; Foreign Economic Assistance Act; China aid; Korea; Southeast Asia; Point Four Program",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-583",
            "presidency_truman_china_korea_1950.html",
            "1950-11-30",
            "据正文整理：杜鲁门在记者会上就中国军队进入朝鲜半岛及联合国部队撤退发表声明，讨论美国对中国的意图、联合国应对和后续行动。",
            "Harry S. Truman; Korean War; Chinese intervention; United Nations; U.S.-China relations",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-592",
            "presidency_truman_press_conference_1951.html",
            "1951-05-17",
            "据正文整理：杜鲁门在记者会上回应有关麦克阿瑟、朝鲜战争及远东政策的问题，其中谈及台湾和中国议题不应成为处理朝鲜问题的附带条件。",
            "Harry S. Truman; Korean War; Douglas MacArthur; Formosa; China policy; press conference",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-with-president-xi-jinping-china",
            "presidency_obama_xi_press_conference_2015.html",
            "2015-09-25",
            "据正文整理：奥巴马与习近平在白宫记者会上介绍双边会谈成果，涉及贸易、网络安全、气候变化、核安全及人权等议题。",
            "Barack Obama; Xi Jinping; U.S.-China relations; cybersecurity; trade; human rights; White House",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-press-secretary-the-visit-president-xi-jinping-the-peoples-republic-china",
            "presidency_obama_xi_visit_statement_2015.html",
            "2015-09-15",
            "据正文整理：白宫新闻秘书声明预告习近平对美国进行国事访问，并说明访问将为拓展美中合作和建设性处理分歧提供机会。",
            "Xi Jinping; Barack Obama; state visit; U.S.-China cooperation; White House statement",
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
            MaterialCandidate(url, "1949-1972", "government", "truman-china-public-texts"),
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
