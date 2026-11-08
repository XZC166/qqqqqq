from hashlib import sha256
from pathlib import Path

from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA
from research_crawler.spiders.government import GovernmentArticleAdapter


FIXTURES = Path(__file__).parent / "fixtures"


def test_china_trade_records_have_hash_bound_abstracts_and_keywords():
    cases = (
        (
            "https://www.presidency.ucsb.edu/documents/statement-the-president-the-first-chinese-nuclear-device",
            "presidency_china_nuclear_1964.html",
            "1949-1972",
            "1964-10-16",
            "据正文整理：约翰逊就中国首次核试验发表声明，称美国已确认试验发生，并讨论其军事意义、美国在亚洲的防务承诺及核扩散影响。",
            "Chinese nuclear test; U.S. public statement; Lyndon B. Johnson; Asian security; nuclear proliferation",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/remarks-permanent-normal-trade-relations-with-china-and-exchange-with-reporters",
            "presidency_china_pntr_2000.html",
            "1992-2016",
            "2000-01-10",
            "据正文整理：克林顿阐述给予中国永久正常贸易关系待遇的理由，说明其对美国市场准入、WTO规则及美中人权和安全分歧的看法。",
            "Permanent normal trade relations; China; World Trade Organization; U.S.-China trade; Bill Clinton",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/message-the-congress-transmitting-report-chinas-accession-the-world-trade-organization",
            "presidency_china_wto_message_2001.html",
            "1992-2016",
            "2001-11-09",
            "据正文整理：布什向国会提交报告，说明中国加入世界贸易组织的条款和条件符合美国与中国此前达成的协议要求。",
            "China; World Trade Organization accession; U.S. Congress; George W. Bush; trade agreement",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/memorandum-chinas-accession-the-world-trade-organization",
            "presidency_china_wto_memo_2001.html",
            "1992-2016",
            "2001-11-09",
            "据正文整理：布什就中国加入 WTO 所涉国有及国有投资企业贸易行为作出法定认定，并指示将备忘录刊载于《联邦公报》。",
            "China; World Trade Organization; state trading enterprises; U.S. trade law; presidential memorandum",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/statement-china-united-states-trade",
            "presidency_china_trade_2018.html",
            "2017-2025",
            "2018-06-15",
            "据正文整理：特朗普宣布对部分中国商品加征关税，并将措施与知识产权和技术获取问题、贸易失衡及美国就业联系起来。",
            "China-U.S. trade; tariffs; intellectual property; technology transfer; Donald Trump",
        ),
        (
            "https://www.presidency.ucsb.edu/documents/remarks-signing-memorandum-actions-the-united-states-related-the-section-301-investigation",
            "presidency_section301_2018.html",
            "2017-2025",
            "2018-03-22",
            "据正文整理：特朗普在签署针对中国技术转让、知识产权和创新相关 Section 301 调查行动的备忘录时发表讲话并回答记者提问。",
            "Section 301; China; technology transfer; intellectual property; trade policy; Donald Trump",
        ),
    )

    for url, fixture, period, published_on, abstract, keywords in cases:
        response = HtmlResponse(
            url=url,
            request=Request(url),
            body=(FIXTURES / fixture).read_bytes(),
            encoding="utf-8",
        )
        candidate = MaterialCandidate(url, period, "government", "presidency-china-trade")
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
