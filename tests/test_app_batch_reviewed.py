from research_crawler.reviewed_sources import (
    BLUESKY_REVIEWED_HASHED_METADATA,
    PRESIDENCY_REVIEWED_HASHED_METADATA,
)
from research_crawler.spiders.government import (
    BlueskyPostAdapter,
    _bluesky_post_text_matches,
    _derive_bluesky_metadata,
    _reviewed_bluesky_metadata,
)


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
    "https://www.presidency.ucsb.edu/documents/interview-with-representatives-chinese-central-television-beijing-china": (
        "1bb4b0d8875c49509e7beb449f2e19612a3d5bbe60444124c2864409089eb91a",
        "据正文整理：里根接受中国中央电视台采访，谈及中美关系、两国人民共同价值、和平、经济与文化交流及双边分歧。",
        "Ronald Reagan; China Central Television; U.S.-China relations; public diplomacy; cultural exchange",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-reception-for-members-the-american-community-beijing-china": (
        "39d5f486060598f0fb95a0ac3b46313c84a44ac1227bb7fb06ea2b3d6802db4b",
        "据正文整理：里根在北京向美国侨民讲话，回顾中美关系正常化后的交流、教育和经济联系，并谈到双方共同利益与合作。",
        "Ronald Reagan; American community in Beijing; U.S.-China relations; educational exchange; economic ties",
    ),
    "https://www.presidency.ucsb.edu/documents/toast-dinner-hosted-president-li-xiannian-china-beijing": (
        "46b4b705aad3199725b74fcc552494d02ea662ae0d403af209d21fd88984f6fd",
        "据正文整理：里根在李先念主持的晚宴上致祝酒词，强调中美人民的友好愿望、和平与繁荣，并回顾双方关系正常化和交流合作。",
        "Ronald Reagan; Li Xiannian; U.S.-China relations; normalization; cultural exchange; peace",
    ),
    "https://www.presidency.ucsb.edu/documents/toast-banquet-hosted-mayor-wang-daohan-shanghai": (
        "98e92ab4671063f99a026c4fc4c23845f38696e44d7d6a23df2fc71507c6620e",
        "据正文整理：里根在上海市长王道涵主持的宴会上回顾《上海公报》及中美关系发展，谈及政治、经济、文化联系、和平与合作。",
        "Ronald Reagan; Wang Daohan; Shanghai Communique; U.S.-China relations; political and cultural exchange",
    ),
    "https://www.presidency.ucsb.edu/documents/question-and-answer-session-with-reporters-the-trip-china": (
        "37abfc2b5af281bb796f15c08c38871b8194f33b32605b7461ff1510b2a9738e",
        "据正文整理：里根在访华期间回答记者提问，谈及其对中国现代化的印象、中美制度差异、对华关系的延续、公开表达美国价值及双方在和平与地区事务上的共识。",
        "Ronald Reagan; China visit; press interview; U.S.-China relations; modernization; public diplomacy",
    ),
    "https://www.presidency.ucsb.edu/documents/radio-and-television-address-opening-the-presidents-campaign-for-re-election": (
        "b3df3caf138626f68678f9174d13f6ec17fb10d69340b7b5680fa06c34277ad6",
        "据正文整理：艾森豪威尔在竞选连任期间向公众发表讲话，回顾其政府任期与国内议题，并讨论和平、外交政策及台湾海峡局势。",
        "Dwight D. Eisenhower; 1956 presidential campaign; peace; foreign policy; Formosa; Taiwan Strait",
    ),
    "https://www.presidency.ucsb.edu/documents/second-annual-report-the-congress-united-states-foreign-policy": (
        "7b2582a810e4ecf605a52fc94c4a6122a467985f3d0e2bf800d9fa488db8a18e",
        "据正文整理：尼克松政府向国会提交年度外交政策报告，回顾 1970 年外交政策的目标与实施，并讨论国际局势、美国对外关系及对中华人民共和国的政策。",
        "Richard Nixon; foreign policy report; Congress; 1970; People's Republic of China; U.S.-China relations",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-announcing-changes-trade-and-travel-restrictions-with-the-peoples-republic-china": (
        "2b4294b51d1b5886b6b3176d4914ba3082acfd0f244d3f43fcf460e1a2fb3522",
        "据正文整理：尼克松宣布调整美国对中华人民共和国的贸易与旅行限制，包括签证、货币使用、运输、贸易和出口等事项。",
        "Richard Nixon; People's Republic of China; U.S.-China relations; trade restrictions; travel restrictions; 1971",
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


def test_reviewed_bluesky_post_metadata_is_bound_to_its_captured_body_hash():
    url = "https://bsky.app/profile/nytopinion.nytimes.com/post/3llq3zdyafc2c"
    expected = (
        "02eaa007b41085b85d6ad90d96bf7198eee5d219ce2e6d830aa7d69d735d266f",
        "据正文整理：纽约时报意见账号转述台湾作者对台海安全的看法，主张台湾加强防卫以威慑攻击，并讨论台湾与中国和平解决关系的可能路径。",
        "New York Times Opinion; Taiwan; China; United States; cross-strait relations; deterrence",
    )
    assert BLUESKY_REVIEWED_HASHED_METADATA[url] == expected
    body = (
        '"With China growing in strength and the United States turning its back on the world, '
        'Taiwan is right to build up its military as a deterrence against attack," writes Yingtai '
        'Lung from Taitung, Taiwan. "But the only way for Taiwan to peacefully secure its freedom '
        'is to somehow reconcile with China."'
    )
    assert _reviewed_bluesky_metadata(url, body) == expected[1:]
    assert _reviewed_bluesky_metadata(url, body + " ") == ("", "")


def test_official_bluesky_accounts_have_hash_bound_metadata():
    posts = {
        "https://bsky.app/profile/nytopinion.nytimes.com/post/3loflwdo4yc2e": (
            "b35776b81acb1fca34f5646816ce3a2623993c2b8060389cf0b19a1df0a3ac1d",
            "据正文整理：纽约时报意见账号转述 Eric Schmidt 与 Selina Xu 对美国和中国科技竞争及全球领导地位的看法。",
            "New York Times Opinion; China; United States; technology competition; global leadership",
        ),
        "https://bsky.app/profile/freedomhouse.bsky.social/post/3lmhy4bmbvc2g": (
            "47b16b4ca1411d14e3af478faf0cd6e9bf7392fcd5488b803e899ffc87cbd62e",
            "据正文整理：Freedom House 表示台湾在《自由世界》2025 年评估中获评自由，并称其在亚太地区得分较高，同时提及中共对台湾民主的影响。",
            "Freedom House; Taiwan; Freedom in the World 2025; democracy; China",
        ),
        "https://bsky.app/profile/csis.org/post/3lrta7vqbrx26": (
            "097d212b9b1c078377f1d35ac1811dce291b1ec896a09837cc0953227d96c3c4",
            "据正文整理：CSIS 指出，台湾海峡发生隔离、封锁或入侵等情势可能严重扰乱该海峡贸易。",
            "CSIS; Taiwan Strait; China; trade; blockade",
        ),
        "https://bsky.app/profile/poqjournal.bsky.social/post/3lik4kd3sgc2a": (
            "986c466cce477f987c6ce09a4ca6cd2ec2509bbac8b78e9e5accf9be44c53125",
            "据正文整理：Public Opinion Quarterly 账号介绍一项研究，讨论台湾民众对两岸现状的偏好、民族主义情绪变化及中国政策的影响。",
            "Public Opinion Quarterly; Taiwan; public opinion; nationalism; cross-strait relations",
        ),
    }
    for url, expected in posts.items():
        assert BLUESKY_REVIEWED_HASHED_METADATA[url] == expected
        assert _reviewed_bluesky_metadata(url, "reviewed body") == ("", "")
    assert set(BlueskyPostAdapter.sources.values()) >= {
        "The New York Times", "Freedom House", "CSIS", "Public Opinion Quarterly"
    }


def test_bluesky_post_text_match_allows_platform_expanded_link_only():
    body = "Taiwan is rated Free. More details: freedomhouse.org/country/taiw..."
    page = "Taiwan is rated Free. More details: https://freedomhouse.org/country/taiwan/freedom-world/2025"
    record = {
        "text": body,
        "facets": [{"features": [{"$type": "app.bsky.richtext.facet#link", "uri":
                                   "https://freedomhouse.org/country/taiwan/freedom-world/2025"}]}],
    }
    links = ["https://freedomhouse.org/country/taiwan/freedom-world/2025"]
    assert _bluesky_post_text_matches(page, body, record, page_links=links)
    assert not _bluesky_post_text_matches(page.replace("Taiwan", "China", 1), body, record, page_links=links)


def test_bluesky_fallback_metadata_is_extractive_and_uses_only_body_terms():
    body = "U.S.-China competition is changing policy. Taiwan and Hong Kong appear in the debate."
    abstract, keywords = _derive_bluesky_metadata(body)
    assert abstract == "据正文整理：U.S.-China competition is changing policy."
    assert keywords == "U.S.-China; China; Taiwan; Hong Kong"
    assert _derive_bluesky_metadata(
        "TikTok signs a deal for its U.S. business."
    )[1] == "United States; TikTok"


def test_bluesky_fallback_keywords_cover_full_topic_phrases_in_post_body():
    _, keywords = _derive_bluesky_metadata(
        "Artificial intelligence and propaganda are shaping the China debate."
    )
    assert keywords == "China; artificial intelligence; propaganda"


def test_bluesky_fallback_keywords_cover_named_geopolitical_terms():
    _, keywords = _derive_bluesky_metadata(
        "Beijing is escalating while information operations and semiconductor policy shape the debate."
    )
    assert keywords == "Beijing; information operations; semiconductors"
