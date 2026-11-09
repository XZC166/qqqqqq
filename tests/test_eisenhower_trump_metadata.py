from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_public_china_records_have_hash_bound_derived_metadata():
    cases = (
        (
            "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-329",
            "presidency_eisenhower_china_press_1955.html",
            "1949-1972",
            "1955-02-02",
            "据正文整理：艾森豪威尔在记者会上回应有关台湾海峡、金门和马祖防务、与中国共产党政权谈判及美国公开政策的问题。",
            "Dwight D. Eisenhower; China; Taiwan Strait; Quemoy; Matsu; U.S. foreign policy",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-president-united-nations-negotiations-with-communist-china-for-release",
            "presidency_eisenhower_airmen_china_1955.html",
            "1949-1972",
            "1955-01-14",
            "据正文整理：艾森豪威尔就联合国秘书长访问北京及被拘留美国飞行员问题发表声明，呼吁克制，并支持继续通过联合国争取释放人员。",
            "Dwight D. Eisenhower; China; United Nations; detained U.S. airmen; public opinion",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/remarks-welcome-the-white-house-vice-president-yen-the-republic-china",
            "presidency_johnson_yen_china_1967.html",
            "1949-1972",
            "1967-05-09",
            "据正文整理：约翰逊欢迎严家淦访美，谈及台湾经济发展与合作；同页注释区保存严家淦有关双边友谊、自由与亚洲事务的完整回应。",
            "Republic of China; Free China; economic assistance; freedom and democracy",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/remarks-signing-ceremony-for-four-united-states-china-agreements",
            "presidency_reagan_china_agreements_1984.html",
            "1972-1991",
            "1984-04-30",
            "据正文整理：里根在北京出席四项美中协议签署仪式，介绍协议涉及贸易投资、人员与思想交流、核能合作及管理培训。",
            "Ronald Reagan; U.S.-China agreements; trade; investment; exchanges; nuclear energy",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-chinese-governments-suppression-student-demonstrations",
            "presidency_bush_tiananmen_statement_1989.html",
            "1972-1991",
            "1989-06-03",
            "据正文整理：布什谴责中国政府对和平示威者使用武力并造成伤亡，呼吁克制、对话及恢复政治和经济改革。",
            "George H. W. Bush; China; student demonstrations; public statement; political reform; human rights",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-press-secretary-chinas-political-correctness",
            "presidency_trump_china_correctness_2018.html",
            "2017-2025",
            "2018-05-05",
            "据正文整理：白宫新闻秘书回应中国民航局要求外国航空公司调整台湾、香港和澳门标示的事件，称美国反对中国将相关政治要求施加于美国企业和公民。",
            "Donald Trump; China; Taiwan; Hong Kong; Macau; airlines; political language",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-press-secretary-regarding-the-presidents-working-dinner-with-china",
            "presidency_trump_xi_dinner_2018.html",
            "2017-2025",
            "2018-12-01",
            "据正文整理：白宫新闻秘书介绍特朗普与习近平在布宜诺斯艾利斯工作晚餐后的公开表述，涉及芬太尼管制、关税安排和中国采购美国农产品、能源及工业产品。",
            "Donald Trump; Xi Jinping; trade negotiations; tariffs; fentanyl; U.S.-China relations",
        ),
    )

    for url, fixture, period, published_on, abstract, keywords in cases:
        response = HtmlResponse(
            url=url,
            request=Request(url),
            body=(FIXTURES / fixture).read_bytes(),
            encoding="utf-8",
        )
        result = GovernmentArticleAdapter().extract(
            response,
            MaterialCandidate(url, period, "government", "reviewed-china-public-texts"),
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
        if fixture == "presidency_johnson_yen_china_1967.html":
            assert "Vice President Yen responded as follows:" in material.body
            assert material.body.endswith("Thank you, Mr. President. Thank you very much.")
