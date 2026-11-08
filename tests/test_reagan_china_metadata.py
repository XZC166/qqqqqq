from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_reagan_china_materials_have_hash_bound_summaries_and_keywords():
    cases = (
        (
            "https://www.presidency.ucsb.edu/documents/remarks-the-welcoming-ceremony-for-president-li-xiannian-china",
            "presidency_reagan_welcoming_li_1985.html",
            "1985-07-23",
            "据正文整理：里根在欢迎中国国家主席李先念访美的仪式上谈及两国贸易、科技合作、教育和文化交流，并表示双方将以相互尊重、互利原则处理共同利益与分歧。",
            "Ronald Reagan; Li Xiannian; U.S.-China relations; trade; scientific cooperation; cultural exchange",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/toast-the-state-dinner-for-president-li-xiannian-china",
            "presidency_reagan_toast_li_1985.html",
            "1985-07-23",
            "据正文整理：里根在李先念访美国宴祝酒词中回顾此前访华和双方交往，表达对中美友好关系、合作及中国人民发展的期望。",
            "Ronald Reagan; Li Xiannian; U.S.-China friendship; public diplomacy; bilateral cooperation",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/written-responses-questions-submitted-the-far-eastern-economic-review",
            "presidency_reagan_china_interview_1984.html",
            "1984-05-09",
            "据正文整理：里根在书面答复中总结近期访华及与中国领导人的会谈，谈及两国制度差异、共同利益、中国的不结盟立场与太平洋地区合作。",
            "Ronald Reagan; China visit; U.S.-China relations; nonalignment; Pacific Basin; Far Eastern Economic Review",
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
            MaterialCandidate(url, "1972-1991", "government", "reagan-china-public-texts"),
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
