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
        (
            "https://www.presidency.ucsb.edu/documents/white-house-statement-trade-with-romania-hungary-and-china",
            "presidency_reagan_mfn_china_1987.html",
            "1987-06-02",
            "据正文整理：白宫说明里根决定继续给予中国、罗马尼亚和匈牙利最惠国关税待遇，称该待遇对双边贸易及美国政治和经济利益具有作用。",
            "China; most-favored-nation status; U.S.-China trade; Jackson-Vanik amendment; Ronald Reagan",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/letter-the-speaker-the-house-representatives-and-the-president-the-senate-trade-with-0",
            "presidency_reagan_china_waiver_1988.html",
            "1988-06-03",
            "据正文整理：里根向国会提交继续对中国和匈牙利贸易法豁免的文件，说明延长豁免的理由，并介绍中国移民政策、对外开放和对美人员往来。",
            "China; trade waiver; Jackson-Vanik amendment; emigration; human rights; U.S.-China relations",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-assistant-the-president-for-press-relations-fitzwater-the-presidents-meeting-2",
            "presidency_reagan_han_xu_1988.html",
            "1988-12-14",
            "据正文整理：白宫新闻声明介绍里根会见中国驻美大使韩叙并向中国人民致意，纪念两国宣布建立外交关系十周年，回顾两国关系及联合公报。",
            "U.S.-China normalization; tenth anniversary; Han Xu; White House statement; Ronald Reagan",
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
