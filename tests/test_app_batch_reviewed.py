from research_crawler.reviewed_sources import PRESIDENCY_REVIEWED_HASHED_METADATA


REVIEWED = {
    "https://www.presidency.ucsb.edu/documents/remarks-chinese-community-leaders-beijing-china": (
        "fa0972d2dc5d1676c886f78ebc81c06fe266e874905a455cf31ef204470524ad",
        "据正文整理：里根在访华讲话中回顾中美接触重启，承认双方制度差异，并主张在差异之外拓展和平、进步与交流。",
        "Ronald Reagan; China visit; U.S.-China relations; ideological differences; exchange",
    ),
    "https://www.presidency.ucsb.edu/documents/readout-president-joe-bidens-meeting-with-president-xi-jinping-the-peoples-republic-1": (
        "5b14f34ab13a28955df9b35dfe6626c42f56d7c9b2c8e84cea38f9ed1845fbfa",
        "据正文整理：白宫通报拜登与习近平在利马会晤，涉及维持沟通、管理竞争、禁毒、军事沟通、人工智能风险、气候变化及人员交流。",
        "Joe Biden; Xi Jinping; U.S.-China relations; Lima meeting; communication; counternarcotics; artificial intelligence",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-exchange-with-reporters-prior-departure-for-ramstein-miesenbach-germany": (
        "97f2d33c259ec80e46fc4843b25284fd9f79090f202114246325292909010a31",
        "据正文整理：特朗普在与习近平会晤前回应记者提问，提及将讨论台湾、双边议题及美国农民。",
        "Donald Trump; Xi Jinping; Taiwan; U.S.-China meeting; agriculture",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-and-exchange-with-reporters-joint-base-andrews-maryland-10": (
        "fd83563df869be41d59388625dd2aff7d166723780184980359fec5380284771",
        "据正文整理：特朗普在与习近平会晤后谈及对华经贸安排、美国农产品采购及芬太尼问题，并回应记者提问。",
        "Donald Trump; Xi Jinping; U.S.-China trade; agricultural purchases; fentanyl",
    ),
}


def test_reviewed_presidency_metadata_is_bound_to_each_captured_body_hash():
    for url, (expected_hash, abstract, keywords) in REVIEWED.items():
        assert PRESIDENCY_REVIEWED_HASHED_METADATA[url] == (
            expected_hash,
            abstract,
            keywords,
        )
        assert len(expected_hash) == 64
        assert all(character in "0123456789abcdef" for character in expected_hash)
        assert abstract.startswith("据正文整理：")
        assert keywords
