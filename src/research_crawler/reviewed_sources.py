"""Source-reviewed PBS snapshots; changed/new texts require another source review.

Original public HTML and review evidence: research/firecrawl/pre2017-media-20261106/
and data/reviews/pbs-pre2017-china-discourse-20261106/.
Values: exact source publication day, title, byline and extracted-body SHA-256.
"""

# Exact source URL -> full extracted-body SHA-256 and body-derived keywords.
# Publisher abstracts/keywords remain preferred. See the literature repair audit.
RESEARCH_REVIEWED_KEYWORDS: dict[str, tuple[str, str]] = {
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC12176173/": (
        "425b74e0d6db936aea80c603b4a883233c19c3b71e20e6ac6bf64c74fee61ccb",
        "China’s image; humanitarian aid; Western news media; COVID-19; Critical Metaphor Analysis; mask diplomacy",
    ),
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC9252629/": (
        "923a802d00dbce4441df496c2f67cc5dd2667d1ab265bf723fed6302600ec0c2",
        "national image; English-speaking media; public health emergencies; COVID-19; evidentiality",
    ),
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC7102532/": (
        "29df033d266dabac2e148adbc73ecf93b028ae0f7aa57dd804d73ad7d8137a59",
        "political warfare; sharp power; hard power; soft power; U.S.-China relations",
    ),
    "https://ijoc.org/index.php/ijoc/article/download/718/792": (
        "c64ff10a111b34dd64881ac07e4d5a084c83e81ec31ebccade570b58fedeed01",
        "Chinese diaspora; public diplomacy; Beijing Olympics; Pasadena Rose Parade; contentious politics; soft power",
    ),
    "https://ijoc.org/index.php/ijoc/article/download/238/116": (
        "37cf60c3926ef4a6a6c2d3f7b245a6645c3d3a6f8b800184b5afc98f3b99d67b",
        "U.S.-China mid-air plane collision; American hegemony; EP-3; strategic competitor; Asia Pacific",
    ),
    "https://www.nature.com/articles/s41599-023-02052-8": (
        "072da4b6b1f9b2d616bd3d96ff4c6ed324965ad69e164c038225626f79b9438d",
        "national image; environmental news; The New York Times; corpus-based discourse analysis; topoi",
    ),
}


# Exact Shorenstein Center landing-page/PDF pairs reviewed against the public
# page metadata and the complete PDF text layer.
SHORENSTEIN_REVIEWED_PDFS: dict[str, dict[str, str]] = {
    "https://shorensteincenter.org/wp-content/uploads/2012/03/turmoil_at_tiananmen_1992.pdf": {
        "metadata_url": "https://shorensteincenter.org/resource/turmoil-at-tiananmen-us-press-coverage-of-beijing-spring-1989/",
        "publisher": "The Shorenstein Center, Harvard Kennedy School",
        "published_on": "1992-06-01",
        "author": "未注明",
        "title": "Turmoil at Tiananmen: A Study of U.S. Press Coverage of the Beijing Spring of 1989",
        "abstract": "This report by the Shorenstein Center explores the U.S. media coverage of the 1989 Beijing Spring. Although the U.S. was not directly involved in the events that took place, media coverage made Americans deeply involved in them. Among the “firsts” in the coverage was the presence of television anchors night after night in an East Asian nation, providing live coverage, holding Americans spellbound for more than a month. To look back on Tiananmen is to review a story of how China nearly changed. Did the media, foreign and Chinese, help bring China to the brink of that change? Why was the story covered as it was? What drove the high volume of coverage? Was anything missing that could have provided better accuracy or understanding? This report evaluates the press’s coverage and impact, and offers suggestions for future U.S. media coverage of critical international events.",
        "keywords": "Tiananmen; U.S. press coverage; Beijing Spring; American media; public opinion; foreign policy",
        "pdf_sha256": "b7007e38de9152afced4041f9f23bd9c8db696a3fd5346d492e2235369168dc7",
        "body_sha256": "fcfe441ed8a09e54483facc1c741bd23a5c2594638cc22831c9c6eae7a79cec4",
    },
    "https://shorensteincenter.org/wp-content/uploads/2012/03/2000_11_mirsky.pdf": {
        "metadata_url": "https://shorensteincenter.org/resource/getting-the-story-in-china-american-reporters-since-1972/",
        "publisher": "The Shorenstein Center, Harvard Kennedy School",
        "published_on": "2000-01-01",
        "author": "Jonathan Mirsky",
        "title": "Getting the Story in China: American Reporters Since 1972",
        "abstract": "A paper by Jonathan Mirsky, fall 1999 fellow, follows the history of modern American reporting on China. Beginning with the 1972 post-Nixon euphoria of American reporters, Mirsky traces the American press’ growing awareness of the controls imposed on them by the Chinese state. The paper then provides personal accounts from journalists of their China careers, from 1980 through periods of tightening and relaxing control to the reimposition of official threats and surveillance in late 1999. After an analysis of the importance of secrecy and deception to the Chinese state and of the problems this presents to American reporters, Mirsky notes that these reporters have ignored Chinese writers’ recent scrutiny of previously taboo subjects. The paper also examines some American criticisms of American journalists in Tiananmen, focusing especially on the Shorenstein Center’s report Turmoil at Tiananmen. Finally, Mirsky considers Beijing’s preoccupation with the power of the press and the possible significance of American reporting in China.",
        "keywords": "China reporting; American reporters; press controls; Tiananmen; media and foreign policy",
        "pdf_sha256": "5d46cb33cb65a724fbe31522f25aadfa68555b26a436a2c794fda5f9f4924bbd",
        "body_sha256": "e53e99e2fd40424545ae17f27b87b3bac253e928ecd5f90d36daab48fb7ef50a",
    },
}


# Exact source URL -> full extracted-body SHA-256, derived abstract, keywords.
STATE_REVIEWED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/": (
        "bc26453aa4b00ba9f98b387d98075bd84342c7ccd88cd1e1cb435847e7356911",
        "据正文整理：演讲将对华供应链依赖描述为经济胁迫风险，并介绍美国支持伙伴、扩大替代市场和增强供应链韧性的政策。",
        "economic coercion; China; supply chains; economic security; allies and partners",
    ),
    "https://2021-2025.state.gov/secretary-antony-j-blinken-remarks-to-the-johns-hopkins-school-of-advanced-international-studies-sais-the-power-and-purpose-of-american-diplomacy-in-a-new-era/": (
        "4030660f2526f518e816610a2748394e35d67ff39e3bd1756e8ba226f59e3cbf",
        "据正文整理：布林肯阐述国际秩序变化及美国外交的作用，讨论对华竞争、与盟友伙伴协同、供应链韧性及投资、协同、竞争的对华战略。",
        "American diplomacy; China; international order; invest align compete; allies and partners; supply chains",
    ),
    "https://2021-2025.state.gov/secretary-antony-j-blinken-2023-international-religious-freedom-report-rollout/": (
        "dddd386637d0502cc94842b390c07bd097177c884b4562cd8ada33ce66617e77",
        "据正文整理：官员介绍国际宗教自由报告，讨论全球宗教自由与维权者，并表达对新疆等地宗教状况及跨国压制的指控和关切。",
        "international religious freedom; China; Xinjiang; transnational repression; religious communities",
    ),
    "https://2021-2025.state.gov/briefings/department-press-briefing-january-11-2024/": (
        "1bce9da1ac36fe73b3792b2853aef676f09b7194f1e5ccd56962df4db3ee4fcd",
        "据正文整理：记者会涵盖中东局势、台湾选举及中美沟通等议题；记者还就涉疆与加沙的政策用语提出质询。",
        "State Department briefing; Gaza; Xinjiang; Taiwan elections; U.S.-China communications",
    ),
    "https://2021-2025.state.gov/the-administrations-approach-to-the-peoples-republic-of-china/": (
        "b4a25de13ce70e889aa70bd7a89b97ceef03367c39c3cd81e03fff7bc42887bd",
        "据正文整理：布林肯阐述投资、协同、竞争的对华战略，将中国描述为国际秩序的长期挑战，同时讨论双边竞争、合作及避免冲突。",
        "U.S.-China relations; invest align compete; international order; strategic competition; bilateral cooperation",
    ),
    "https://2021-2025.state.gov/secretary-antony-j-blinken-at-freedom-house-2023-annual-awards-ceremony/": (
        "3f1a425d17f5664d311e42359f8750c9fe6d68ddf2e2a4de4337804bfa3bfad6",
        "据正文整理：布林肯讨论民主、人权、数字技术和监控风险，谈及针对新疆及西藏基因数据收集的指控，并呼吁与人权维护者合作。",
        "democracy; human rights; genomic surveillance; Xinjiang; Tibet; Freedom House",
    ),
    "https://2021-2025.state.gov/secretary-antony-j-blinken-and-peoples-republic-of-china-vice-president-han-zheng-before-their-meeting/": (
        "6bc3a5cae9d111b1b2d97c3bfe50a64b3377710c5f5eba93c51b7740a10bc5ca",
        "据正文整理：韩正与布林肯在会谈前讨论中美关系、近期高层接触、保持沟通、管控分歧及探索合作。",
        "U.S.-China relations; Han Zheng; Antony Blinken; high-level diplomacy; bilateral communication",
    ),
    "https://2021-2025.state.gov/briefings/department-press-briefing-april-24-2024/": (
        "724cf68f7cfd747886c4f602ed55e65fb5162d9749be90949467a797dd80104a",
        "据正文整理：记者会涉及对以安全援助、人权审查和布林肯访华议程；对华议题包括人权、印太稳定、禁毒合作、军事沟通及人工智能。",
        "State Department briefing; Blinken China visit; human rights; Indo-Pacific; counternarcotics; military communication; artificial intelligence",
    ),
    "https://2021-2025.state.gov/american-diplomacy-for-a-new-era-strengthening-our-national-security-through-the-modernization-agenda/": (
        "9bc740c198ff16132d4fe82ab7bd4497dde5fcbd5c2f14aa2cdaeead738d25f6",
        "据正文整理：材料回顾国务院现代化议程在关键任务、人员队伍和创新方面的措施，包括设立中国事务协调办公室、加强数字外交及改进领事服务。",
        "State Department modernization; China House; diplomatic workforce; cyberspace; artificial intelligence; consular services",
    ),
}

# Exact source URL -> full extracted-body SHA-256 and body-derived keywords.
# Website taxonomy/program/format tags are not presumed article subjects.
BROOKINGS_REVIEWED_KEYWORDS: dict[str, tuple[str, str]] = {
    'https://www.brookings.edu/articles/chinas-emergence-and-its-implications-for-the-united-states/': (
        'ec3ae3755c65c513da1c268f42dccc3cff5ce16b7360cf6bff87f19ae9652f0b',
        'U.S. perceptions of China; China image; U.S.-China relations; soft power; Asia-Pacific',
    ),
    'https://www.brookings.edu/articles/its-time-to-take-an-objective-view-of-china/': (
        '23254842049a070412f5b9406c2bb058bfabcb8f3347878fb54d525bc9d5a959',
        'American media; China image; U.S. public opinion; media framing; China-U.S. relations',
    ),
    'https://www.brookings.edu/articles/u-s-china-economic-relations-implications-for-u-s-policy/': (
        '3aa26b442c57fd16f005c491e7a52667f93525b257eb38cda7751b6d3e1fe12b',
        'U.S.-China economic relations; WTO accession; trade policy; trade deficit; economic reform',
    ),
    'https://www.brookings.edu/articles/china-is-not-the-soviet-union/': (
        '946f0d1eed41b8090877809f451c8ad0ff4edebb746e7b9451fc549f66a0fcb7',
        'China image; U.S. public debate; media framing; great power competition; U.S.-China relations',
    ),
    'https://www.brookings.edu/articles/working-on-positive-china-u-s-relations/': (
        '6cf6758b8b90c09e78bb5745b27f3a1ef697d9692f3d1052bcac01559bf23b43',
        'public discourse; U.S.-China relations; strategic competition; China policy; Jeffrey A. Bader',
    ),
    'https://www.brookings.edu/articles/americas-next-president-needs-a-new-china-policy/': (
        '7305108c86d1b5afd9fb545f743ed8b145c7bcce452ab3f2c0bd9ab2db7a088f',
        'U.S.-China relations; China policy; U.S. presidential election; Taiwan; regional security',
    ),
    'https://www.brookings.edu/articles/refocusing-the-china-debate-beijings-ideological-exports-and-the-question-of-who-lost-china/': (
        'c5e308053f9de2ecd8651fef77278f5828bde77e8eeae2e5de0d0d682ae57e8e',
        'China debate; ideological exports; U.S.-China strategy; engagement policy; China threat perceptions',
    ),
    'https://www.brookings.edu/wp-content/uploads/2016/06/1021_china_li.pdf': (
        'a735721b94372c4ae03d2363d2daaeacac97d49ec729e70a9c8d57ab985c3b72',
        'U.S. perceptions of China; China image; China studies; U.S.-China relations; media censorship',
    ),
    'https://www.brookings.edu/wp-content/uploads/2016/06/nakayama2006.pdf': (
        '8887192abf29deb102a8812b6afd31d739151ee37bf9d7983454c5a45f0f42a6',
        'U.S.-China policy; domestic partisanship; congressional debate; interest groups; China threat perceptions',
    ),
    'https://www.brookings.edu/articles/more-pain-than-gain-how-the-us-china-trade-war-hurt-america/': (
        '34b809c659836f5ab27be0def4a7842a446fe49946f0d4a8b04ae744189428b8',
        'trade war; phase one; tariffs; American economy',
    ),
    'https://www.brookings.edu/articles/developing-a-mutually-beneficial-us-china-economic-relationship/': (
        'd2240aca1194865e90380908890f4f2841cfad74d0afeba7d99967fb6d35ebb6',
        'U.S.-China economic relationship; WTO; tariffs; responsible stakeholder',
    ),
    'https://www.brookings.edu/articles/danger-ahead-taiwans-politics-chinas-ambitions-and-us-policy/': (
        '8827580746dc42d40562bf5e27d3e8a4e28b1c99d3ccf7335e760924ef0b7ac9',
        'Taiwan; public opinion; U.S. policy; cross-Strait',
    ),
    'https://www.brookings.edu/articles/responsible-competition-and-the-future-of-u-s-china-relations/': (
        '7bf958a34d935a0382226cd7287bc2162b429ebbb38108d414d4d5fbf61a85b3',
        'great power competition; authoritarianism; U.S.-China relations; allies',
    ),
    'https://www.brookings.edu/articles/pompeos-recent-speech-and-us-china-relations/': (
        '76a01743314838db078dcec1be1a16ffdb37b8b2ee6a7f824395389721359134',
        'Pompeo; US-China relations; decoupling; COVID-19',
    ),
    'https://www.brookings.edu/wp-content/uploads/2016/06/06_asian_regionalism_liu.pdf': (
        '2661e5498692f8f98f7134eb36398b58f239e7af3724fc64ce8ec21844c84c14',
        'Asian regionalism; Taiwan; APEC; regional security',
    ),
    'https://www.brookings.edu/articles/chinese-citizens-affection-for-taiwanese-may-reduce-risk-of-cross-strait-conflict/': (
        '278f008504ea5423902c2e274bf7601e56c326cf7c9ed363437f33098d35df7a',
        'public opinion; Taiwan; cross-Strait; survey data; state media',
    ),
    'https://www.brookings.edu/wp-content/uploads/2019/11/DollarAndSense_Transcript_Prasad.pdf': (
        'd91365fd73efcdc972397a2b73396948a6289a1f4ab57c7f9bdf253f52c56d9e',
        'trade war; tariffs; Chinese economy; U.S.-China relations',
    ),
    'https://www.brookings.edu/wp-content/uploads/2019/06/DollarAndSense_Huang_Transcript.pdf': (
        'e3f8f59156eec9e6ae6c4ec0a27963a69fb33606f8a0c552b9bb216267b7da6e',
        'trade liberalization; globalization; foreign direct investment; WTO; trade war',
    ),
    'https://www.brookings.edu/wp-content/uploads/2019/02/us_china_economic_relationship.pdf': (
        'f35f6c307393652d9d7b2042ba0b3c64fd755b49d847b815c115fc0ca2ea2c63',
        'WTO; state-owned enterprises; digital trade; national security; export controls',
    ),
}

CSIS_REVIEWED_KEYWORDS: dict[str, tuple[str, str]] = {
    "https://www.csis.org/analysis/understanding-temporary-de-escalation-us-china-trade-war": (
        "962e6d258fff9c41f6e5fa6ab404f9e0e52e40f900fe46c806cc8704bc8b0ec6",
        "tariff rollback; supply chains; U.S. credibility; inflation; trade policy",
    ),
    "https://www.csis.org/analysis/competition-confrontation-china-major-shift-us-policy": (
        "125808035b5b24a5bfa6dff15b96c91a6e729bd606a70dd37d4d80872d696789",
        "direct confrontation; propaganda; cyberattacks; disinformation; U.S. policy",
    ),
    "https://www.csis.org/analysis/us-china-relations-2024-managing-competition-without-conflict": (
        "5d50a56ffb1b46e326d73f5d118691b2103a8207b00fdc8c2d247c083c89e233",
        "U.S.-China relations; Taiwan Strait; diplomacy; decoupling; trade war",
    ),
    "https://www.csis.org/analysis/countering-threats-ccp-homeland": (
        "9b12deba35ae7810ce115bb36012de979e1a762a9fb3fa1b00b76ddba0d55576",
        "influence operations; cyber intrusion; espionage; surveillance; homeland security",
    ),
    "https://csis-website-prod.s3.amazonaws.com/s3fs-public/2025-01/250114_Hass_Advancing_Coordination.pdf?VersionId=aETLuLnI_NSH8889c_WNsevpuplHzk8b": (
        "3bcfb53ff19fd9042a2f8aaaa1ffead4819a1ecfd02a02bedaf7dfcc23585141",
        "strategic competition; U.S.-China coordination; track 2 dialogue; climate-smart agriculture; nonstate actors",
    ),
    "https://csis-website-prod.s3.amazonaws.com/s3fs-public/2024-02/240221_Shivakumar_Balancing_Ledger.pdf?VersionId=5juRJmop6MEsOnR.skVAafg5RGRDsVJz": (
        "6f30b277858a05fda4cefe1992e1267683855ec8545478878a9a73c15ed60e96",
        "export controls; semiconductors; China; chip restrictions; supply chains; artificial intelligence",
    ),
}

CSIS_REVIEWED_PDFS: dict[str, tuple[str, int]] = {
    "https://csis-website-prod.s3.amazonaws.com/s3fs-public/2025-01/250114_Hass_Advancing_Coordination.pdf?VersionId=aETLuLnI_NSH8889c_WNsevpuplHzk8b": (
        "1576e6b2bf5a23acffd81d34aa90de8d9edccf6f4be66f8af7325513002be612",
        10,
    ),
    "https://csis-website-prod.s3.amazonaws.com/s3fs-public/2024-02/240221_Shivakumar_Balancing_Ledger.pdf?VersionId=5juRJmop6MEsOnR.skVAafg5RGRDsVJz": (
        "995a66ea38bd2bbc3249d5d19fb3a57e91b36af6d01fea01740fa4d3a6d16d60",
        13,
    ),
}

USTR_REVIEWED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://ustr.gov/sites/default/files/Section%20301%20FINAL.PDF": (
        "583fe13fe2a0f54a858af31028435167d1b77a977edecb78e85f6d20e7e6d73f",
        "据正文整理：报告依据《1974年贸易法》第301条，审查中国与技术转让、知识产权和创新有关的行为、政策与做法。正文讨论外资持股和合资要求、行政审批与许可、技术许可条件、对美企及资产的投资收购，以及对美国企业计算机网络的未授权入侵与窃取。",
        "Section 301; technology transfer; intellectual property; foreign ownership restrictions; joint venture requirements; administrative approvals; cyber intrusions",
    ),
    "https://ustr.gov/sites/default/files/05.14.2024%20Four%20Year%20Review%20of%20China%20Tech%20Transfer%20Section%20301%20(Final).pdf": (
        "cd86fd04e7f8876f55ae40ed147b37de996687625dd16daa96a473826de5b8ce",
        "据正文整理：报告评估第301条关税在消除中国技术转让相关行为方面的作用，称部分领域出现改变，但相关做法仍持续，且对美国商业的负担增加。报告还讨论关税的经济影响、企业将采购与生产转出中国的情况，并考虑维持或调整部分关税措施。",
        "Section 301 tariffs; technology transfer; intellectual property; industrial planning; supply chain resilience; production shifts",
    ),
}

RFA_REVIEWED_KEYWORDS: dict[str, tuple[str, str]] = {
    "https://www.rfa.org/english/news/china/internet-09242012182444.html": (
        "64009a38daca7a0f2bbe2bd76da40de4d94d4f8384f71b3e53d7806a3a188507",
        "Internet freedom; China; Freedom House; social media; Internet restrictions; authoritarian countries",
    ),
    "https://www.rfa.org/english/news/china/internet-12042014162746.html": (
        "fd241d0b26d8fe8eefe2a184ef5694cfbb5b400c931782d884284a85802693d3",
        "Internet freedom; China; Vietnam; Freedom House; social media; public opinion struggle; online freedom",
    ),
}

GOVINFO_REVIEWED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://www.govinfo.gov/content/pkg/CHRG-115hhrg25846/html/CHRG-115hhrg25846.htm": (
        "411412cf2234397f571be7d17883e45f41c394bc8876286a63ef39b743afa51a",
        "据正文整理：听证记录讨论美国对台关系和台湾海峡安全，涉及对台湾的支持、美国印太政策及加强美台联系的议题。",
        "Taiwan; U.S.-Taiwan relations; Taiwan Strait; security; Indo-Pacific",
    ),
    "https://www.govinfo.gov/content/pkg/CHRG-118hhrg52143/html/CHRG-118hhrg52143.htm": (
        "9914047f0e99605cdfed9db3b95e90f4c53831332788462f26f5e7799fa55f83",
        "据正文整理：听证记录审视中国共产党在非洲的影响和美国在非洲的大国竞争，讨论中国对外政策、基础设施与“一带一路”以及美国应对。",
        "China; Africa; Chinese Communist Party; great power competition; Belt and Road; United States",
    ),
    "https://www.govinfo.gov/content/pkg/CHRG-118hhrg53672/html/CHRG-118hhrg53672.htm": (
        "0a541f59bd42763fc9ce8a553601833e45a7188274fbcc9ef147e8c08eb96e75",
        "据正文整理：听证记录评估美国应对中国“一带一路”外交和相关经济影响力的努力，讨论发展融资、对外援助、盟友伙伴协调及中国的胁迫手段。",
        "China; Belt and Road Initiative; coercion; U.S. efforts; development finance; Africa",
    ),
    "https://www.govinfo.gov/content/pkg/CHRG-118hhrg56065/html/CHRG-118hhrg56065.htm": (
        "1468e2f71e36248da9ac437edee2db9172ffad46d678f0b663f4e50e1f338103",
        "据正文整理：听证记录讨论中国共产党的政治战、影响行动、虚假信息和外国干预，重点涉及美国防范相关活动及提升政府和社会韧性。",
        "political warfare; Chinese Communist Party; United States; influence operations; disinformation; foreign interference",
    ),
    "https://www.govinfo.gov/content/pkg/CHRG-118hhrg55809/html/CHRG-118hhrg55809.htm": (
        "2d6384c09435ce9149eebd20d3eea403fd29cfc6af383b1ec45ec03f480f06f0",
        "据正文整理：众议院外交事务委员会印太小组听证回顾《台湾关系法》实施情况，评估美国对台关系及未来美台关系。",
        "Taiwan Relations Act; U.S.-Taiwan relations; Taiwan; China; House Foreign Affairs Committee",
    ),
}

NSARCHIVE_REVIEWED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://nsarchive.gwu.edu/news/china/2019-06-04/tiananmen-massacre-30th-anniversary-china-declassified": (
        "a286d4879dec51429ac45a0052c248d353f028846c05d6026cd776f1e23808b6",
        "",
        "Tiananmen Square; declassified documents; U.S. embassy; Chinese military; U.S. response",
    ),
    "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB16/": (
        "476c000b713b3b18de40d9c4b4f9f7b3bf5b8523df242ffcb1eb7d6d5f3c5762",
        "据正文整理：页面介绍《China and the United States: From Hostility to Engagement, 1960-1998》档案集，重点展示1989年天安门事件相关的美国使馆现场报告和国务院“Morning Summaries”，并提到1985—1986年学生示威等材料。",
        "China and the United States; Tiananmen Square; U.S. Embassy; diplomatic cables; Morning Summaries",
    ),
    "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB106/index.htm": (
        "af6ffef123435da31ffc89e1900902c51c35d6604269c581c6970656151c5a25",
        "据正文整理：页面介绍尼克松1972年访华的解密记录，包括与毛泽东会见、与周恩来讨论越南战争、台湾和上海公报，以及基辛格向中方介绍苏联军事力量和台湾问题保证。",
        "Richard Nixon; Henry Kissinger; Mao Zedong; Zhou Enlai; Taiwan; Shanghai Communique; Soviet military forces",
    ),
    "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB145/index.htm": (
        "b26a52f69310abe3f19fd818b843a1fff827b14ab3bdf025024bf5345425775e",
        "据正文整理：页面介绍以解密美国和中国文件为基础的电视纪录片《History Declassified: Nixon in China》，回顾1969年中国元帅提出“play the American card”、1972年基辛格情报简报及尼克松访华相关外交。",
        "Nixon in China; History Declassified; Discovery Times Channel; Henry Kissinger; intelligence briefing; Chinese files",
    ),
    "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB47/": (
        "2b9692b015e803a22cc535e9511b82779ab422366ab373f02d3aa242aaaa6cea",
        "",
        "Tiananmen Square; declassified State Department documents; CIA reports; U.S. ambassadors; Chinese leadership; Tiananmen Papers",
    ),
}

BROOKINGS_REVIEWED_PDF_METADATA: dict[str, dict[str, str]] = {
    "https://www.brookings.edu/wp-content/uploads/2016/06/1021_china_li.pdf": {
        "metadata_url": "https://www.brookings.edu/articles/the-china-paradox-and-american-misperceptions/",
        "page_title": "The China Paradox and American Misperceptions",
        "published_on": "2011-10-21",
        "title": "The China Paradox and American Misperceptions",
        "title_source": "https://www.brookings.edu/articles/the-china-paradox-and-american-misperceptions/",
        "pdf_sha256": "bca7aa00165b9f15a9e169648060a991e11d14ba726112b26943c35fd2e646e2",
        "body_sha256": "a735721b94372c4ae03d2363d2daaeacac97d49ec729e70a9c8d57ab985c3b72",
    },
    "https://www.brookings.edu/wp-content/uploads/2019/02/us_china_economic_relationship.pdf": {
        "metadata_url": "https://www.brookings.edu/articles/the-us-china-economic-relationship-a-comprehensive-approach/",
        "page_title": "The US-China economic relationship: A comprehensive approach",
        "published_on": "2019-02-28",
        "title": "The US-China economic relationship: A comprehensive approach",
        "title_source": "https://www.brookings.edu/articles/the-us-china-economic-relationship-a-comprehensive-approach/",
        "pdf_sha256": "78071d5ae381dd8dba4c4afcf86987541435c39d4f08baf5a1f879510131ff9f",
        "body_sha256": "f35f6c307393652d9d7b2042ba0b3c64fd755b49d847b815c115fc0ca2ea2c63",
    },
    "https://www.brookings.edu/wp-content/uploads/2019/06/DollarAndSense_Huang_Transcript.pdf": {
        "metadata_url": "https://www.brookings.edu/articles/chinese-perspectives-on-trade-and-the-economic-tension-with-the-us/",
        "page_title": "Chinese perspectives on trade and the economic tension with the US",
        "published_on": "2019-06-24",
        "title": "DOLLAR & SENSE: China’s perspectives on trade and the economic tension with the US",
        "pdf_sha256": "edebd59adc2a8767e845ed070dec8b1eb32fd1062530e1fe316fc54748161fa6",
        "body_sha256": "e3f8f59156eec9e6ae6c4ec0a27963a69fb33606f8a0c552b9bb216267b7da6e",
    },
}

ARCHIVED_STATE_REVIEWED_METADATA: dict[str, tuple[str, str]] = {
    "https://2009-2017.state.gov/p/eap/rls/rm/2016/04/256509.htm": (
        "据正文整理：拉塞尔阐述奥巴马政府的亚太再平衡与对华外交，讨论气候合作、竞争与分歧、南海航行自由及以国际法处理争端。",
        "U.S.-China relations; Asia rebalance; climate cooperation; South China Sea; freedom of navigation; international law",
    ),
    "https://2009-2017.state.gov/secretary/remarks/2016/06/258091.htm": (
        "据正文整理：中美官员在战略与经济对话及人文交流高层磋商开幕讲话中回顾双边合作，讨论战略沟通、经济关系、南海分歧、气候变化及全球议题。",
        "Strategic and Economic Dialogue; people-to-people exchange; U.S.-China relations; South China Sea; climate change",
    ),
    "https://2009-2017.state.gov/secretary/20092013clinton/rm/2011/05/162976.htm": (
        "据正文整理：克林顿与盖特纳在对话结束后的问答中谈及中东北非局势、中美互信、人文与商业往来、自主创新政策及双向投资。",
        "Strategic and Economic Dialogue; mutual trust; Middle East; indigenous innovation; bilateral investment",
    ),
    "https://2009-2017.state.gov/secretary/20092013clinton/rm/2011/05/162881.htm": (
        "据正文整理：中美官员在第三轮战略与经济对话开幕讲话中讨论合作伙伴关系、经济复苏、两国发展与改革，以及通过交往和对话增进理解。",
        "Strategic and Economic Dialogue; U.S.-China partnership; economic recovery; economic reform; bilateral engagement",
    ),
    "https://2009-2017.state.gov/secretary/20092013clinton/rm/2011/05/162925.htm": (
        "据正文整理：克林顿阐述气候、清洁能源与能源安全合作议程；戴秉国讨论中美合作伙伴关系、相互依存及探索大国互利合作的主张。",
        "Strategic and Economic Dialogue; climate change; clean energy; energy security; U.S.-China partnership",
    ),
}

PBS_REVIEWED_ARTICLES: dict[str, tuple[str, str, str, str]] = {
    'https://www.pbs.org/newshour/politics/asia-jan-june09-wang_06-02': (
        '2009-06-02',
        'Leader Profile: Student Activist Wang Dan',
        'PBS News Hour',
        '64d5c4c1e59725bdd75a013a4c6e48a42f206f3ebddf23576e747bca1b2d394a',
    ),
    'https://www.pbs.org/newshour/world/chinese-hackers-face-u-s-criminal-charges-says-doj-official': (
        '2015-11-10',
        'Chinese hackers could face U.S. criminal charges says DOJ official',
        'Tami Abdollah, Associated Press',
        '92762cad5ac352a83375d4249e6d9321078ecb1764f3b9078a42be923c3f3443',
    ),
    'https://www.pbs.org/newshour/nation/obama-authorizes-new-sanctions-cyber-criminals': (
        '2015-04-01',
        'Obama creates first sanctions program against cybercriminals',
        'Ken Dilanian, Associated Press',
        'cbf19dca533875d5e5cf245d700c9b4919505e967dd6073feb9bd12870f012bb',
    ),
    'https://www.pbs.org/newshour/nation/data-breach-might-help-chinese-government-identify-u-s-spies': (
        '2015-07-25',
        'Data breach may help Chinese government identify U.S. spies',
        'Kenzi Abou-Sabe',
        'b756d08d797ccc8727dcbe4db32a72069f82139bf0fb0dbc2b2819d4b33843e0',
    ),
    'https://www.pbs.org/newshour/world/china-has-reclaimed-3200-acres-in-south-china-sea-pentagon-says': (
        '2016-05-13',
        'China has reclaimed 3,200 acres in South China Sea, Pentagon says',
        'Lolita C. Baldor, Associated Press',
        '2f9ef8ae6be6693c1942661545ee6fd4d0fb76cf2e6deb0784be948bea3e1e80',
    ),
}

PBS_REVIEWED_VIDEO_TRANSCRIPTS: dict[str, tuple[str, str, int, str, str, str]] = {
    'https://www.pbs.org/newshour/show/what-are-the-ripple-effects-of-a-u-s-china-trade-war': (
        '2018-07-06',
        'What are the ripple effects of a U.S.-China trade war?',
        7812,
        '42968a0566a3d750c1d75ca58585ed4e368832412c9725cd37af6a4519afe90a',
        'Thank you.',
        '未注明',
    ),
    'https://www.pbs.org/newshour/show/30-years-later-the-lasting-tragedy-of-tiananmen-square': (
        '2019-06-04',
        "30 years later, the 'lasting tragedy' of Tiananmen Square",
        10451,
        'c4f187a78cf6fe87e783871a65542e95aec648f06d19cdc0c21674173fc61c5f',
        'Thank you.',
        '未注明',
    ),
    'https://www.pbs.org/newshour/show/tiananmen-square-massacre-casts-a-long-shadow-over-modern-chinese-politics': (
        '2021-06-04',
        'Tiananmen Square massacre casts a long shadow over modern Chinese politics',
        6357,
        'ab5c9f90bd2659309d3d500ac810ae3b9e08f9e21152e939c414820b3b653cf0',
        'For the "PBS NewsHour," I\'m Nick Schifrin.',
        'Nick Schifrin; Dan Sagalyn',
    ),
}

PBS_REVIEWED_PROGRAM_TRANSCRIPTS: dict[str, tuple[str, str, int, str, str, str, str]] = {
    'https://www.pbs.org/video/august-9-2024-unvdxv/': (
        '2024-08-09',
        'Amanpour and Company | August 9, 2024 | Season 2024',
        41162,
        '4c2923118e5f00b8b0d06d2adb19df3f938368958f2b4078cb748d6ec13e24d9',
        '>> [MUSIC]',
        '据正文整理：本集包含多段访谈，其中有关中国的讨论涉及美国国防创新、中国军民融合、台湾先进芯片供应对美国安全的影响，以及人工智能在未来武器体系中的应用。',
        'China, Taiwan, advanced chips, defense innovation, artificial intelligence',
    ),
}

VOA_REVIEWED_KEYWORDS: dict[str, str] = {
    'https://learningenglish.voanews.com/a/trade-dispute-between-us-china-rises/4440666.html': (
        'China; United States; tariffs; trade dispute'
    ),
    'https://learningenglish.voanews.com/a/counting-the-cost-of-the-us-china-trade-war/4905862.html': (
        'China; United States; tariffs; trade war'
    ),
}

TRUMAN_LIBRARY_VISIBLE_PUBLICATION_DATE_URLS = {
    "https://www.trumanlibrary.gov/library/public-papers/171/presidents-news-conference",
    "https://www.trumanlibrary.gov/library/public-papers/3/presidents-news-conference",
    "https://www.trumanlibrary.gov/library/public-papers/173/statement-president-situation-korea",
    "https://www.trumanlibrary.gov/library/public-papers/193/special-message-congress-reporting-situation-korea",
    "https://www.trumanlibrary.gov/library/public-papers/223/letter-ambassador-warren-austin-restating-us-position-formosa",
    "https://www.trumanlibrary.gov/library/public-papers/287/presidents-news-conference",
    "https://www.trumanlibrary.gov/library/public-papers/78/radio-report-american-people-korea-and-us-policy-far-east",
}


TRUMAN_LIBRARY_REVIEWED_METADATA: dict[str, tuple[str, str]] = {
    "https://www.trumanlibrary.gov/library/public-papers/171/presidents-news-conference": (
        "据正文整理：杜鲁门解释心理战委员会的职能，称其负责协调有助于赢得和平的工作，并表示该委员会隶属中央情报局。",
        "Psychological Warfare Board; public opinion; Central Intelligence Agency; press conference; Cold War",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/3/presidents-news-conference": (
        "据正文整理：杜鲁门宣读美国对中国与台湾问题的政策说明，回应有关中华人民共和国、台湾海峡与美国立场的记者提问。",
        "China policy; Formosa; Taiwan Strait; U.S. foreign policy; press conference",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/173/statement-president-situation-korea": (
        "据正文整理：声明说明朝鲜遭入侵后的美国军事行动，称台湾被占将威胁太平洋安全，并宣布第七舰队介入台湾海峡及要求台湾当局停止对大陆的空海行动。",
        "Korean War; Formosa; Taiwan Strait; U.S. Seventh Fleet; U.S. policy",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/193/special-message-congress-reporting-situation-korea": (
        "据正文整理：杜鲁门向国会报告朝鲜局势与美国应对，重申美国对台湾没有领土野心，并主张相关问题以和平方式解决。",
        "Korean War; Formosa; U.S. Congress; Taiwan policy; United Nations",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/223/letter-ambassador-warren-austin-restating-us-position-formosa": (
        "据正文整理：杜鲁门致函美国驻联合国大使，重申美国关于台湾的立场，并要求避免对美国意图产生误解。",
        "Formosa; U.S. foreign policy; United Nations; Warren Austin; Taiwan Strait",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/287/presidents-news-conference": (
        "据正文整理：杜鲁门在记者会上回应中国军队介入朝鲜战争的问题，并说明联合国安理会处理相关局势的决议与美国立场。",
        "Chinese intervention in Korea; Korean War; United Nations; press conference; U.S. policy",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/78/radio-report-american-people-korea-and-us-policy-far-east": (
        "据正文整理：杜鲁门向美国公众解释朝鲜战争和美国远东政策，论述冲突扩大的风险、联合国行动以及对中国军队介入和台湾问题的看法。",
        "Korean War; China; Far East policy; U.S. public address; Taiwan Strait",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/354/address-national-war-college": (
        "据正文整理：杜鲁门讨论美国的国家政策、国际信息传播与新闻分发，并将中国共产党在中国大陆取得胜利描述为对亚洲和平与进步的重大损失。",
        "China; international information; news distribution; U.S. national policy; Cold War",
    ),
    "https://www.trumanlibrary.gov/library/public-papers/16/presidents-news-conference": (
        "据正文整理：杜鲁门在记者会上回应中国共产党拒绝朝鲜停火提案的问题，表示美国将推动联合国把中国共产党政府列为侵略者，并谈及台湾方面对大陆采取行动的报道。",
        "Chinese intervention in Korea; United Nations; Taiwan; press conference; U.S. policy",
    ),
}


PRESIDENCY_REVIEWED_METADATA: dict[str, tuple[str, str]] = {
    "https://www.presidency.ucsb.edu/documents/conversation-with-the-president-interview-with-dan-rather-the-columbia-broadcasting-system": (
        "据正文整理：尼克松在接受丹·拉瑟采访时讨论即将访华的时间安排，否认出于选举考量，并回顾其主张与中国领导人恢复沟通及避免对抗的理由。",
        "Nixon China visit; Dan Rather interview; U.S.-China communication; 1972 election",
    ),
    "https://www.presidency.ucsb.edu/documents/memorandum-acid-imports-from-china": (
        "据正文整理：里根指示美国贸易代表根据《1974年贸易法》第406条，对从中华人民共和国进口的仲钨酸铵和钨酸作出进口救济认定。",
        "China; Reagan administration; ammonium paratungstate; tungstic acid; Trade Act of 1974",
    ),
    "https://www.presidency.ucsb.edu/documents/republican-party-platform-1988": (
        "据正文整理：1988年共和党纲领讨论中华人民共和国的市场改革、政治压制和双边贸易，并阐述台湾安全、地区防务及与台湾的贸易安排。",
        "Republican Party Platform; China; free market reform; U.S.-China trade; Taiwan security",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-the-decision-extend-normal-trade-relations-status-with-china": (
        "据正文整理：克林顿宣布续予中国正常贸易关系待遇，称此举符合美国经济和安全利益，并将对华贸易、接触和加入世贸组织的谈判与促进市场开放、人权和全球规则相联系。",
        "China NTR; WTO accession; U.S.-China trade; human rights; engagement",
    ),
    "https://www.presidency.ucsb.edu/documents/joint-united-states-china-statement-status-negotiations-chinas-accession-the-world-trade": (
        "据正文整理：克林顿与朱镕基共同说明中国加入世贸组织谈判的进展及未解决事项，列举已达成的市场准入和规则议题，并要求双方贸易部长恢复谈判。",
        "China WTO accession; Zhu Rongji; bilateral negotiations; market access; trade rules",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-world-trade-organization-luncheon-seattle": (
        "据正文整理：克林顿在西雅图世贸组织会议期间谈到新一轮全球贸易议程、就业与共同繁荣，并主张中国融入全球政治经济往来，同时讨论贸易增长与环境责任。",
        "World Trade Organization; China integration; global trade; shared prosperity; environment",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-china-european-union-negotiations-chinas-accession-the-world-trade-organization": (
        "据正文整理：克林顿欢迎中欧就中国加入世贸组织结束双边谈判，并敦促国会通过对华永久正常贸易关系，称此举有助于美国获得市场利益并推动中国改革。",
        "China WTO accession; European Union; PNTR; market access; economic reform",
    ),
    "https://www.presidency.ucsb.edu/documents/letter-congressional-leaders-permanent-normal-trade-relations-with-china": (
        "据正文整理：克林顿致函国会领导人，主张按已谈定的条件推动中国加入世贸组织并给予永久正常贸易关系，称其将扩大美国市场准入并使中国纳入国际规则体系。",
        "China WTO accession; PNTR; U.S. Congress; market access; international rules",
    ),
    "https://www.presidency.ucsb.edu/documents/message-the-congress-transmitting-proposed-legislation-permanent-normal-trade-relations": (
        "据正文整理：克林顿向国会提交对华永久正常贸易关系立法，说明中美世贸组织协议的市场准入、争端解决和进口保障条款，并称协议将促进中国国内改革、法治和国际合作。",
        "China PNTR; WTO agreement; market access; trade enforcement; rule of law",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-1085": (
        "据正文整理：克林顿宣布续予中国最惠国贸易地位并将其与年度人权条件脱钩，同时延续天安门事件后制裁、禁止进口中国军火，并提出扩大美国之音和自由亚洲电台广播等人权倡议。",
        "China MFN; human rights; U.S.-China engagement; Tiananmen sanctions; Voice of America",
    ),
    "https://www.presidency.ucsb.edu/documents/memorandum-most-favored-nation-trade-status-for-china-0": (
        "据正文整理：克林顿依据《1974年贸易法》第402条认定，继续适用于中华人民共和国的豁免将实质性促进该法相关目标，并指示国务卿公布这一决定。",
        "China MFN; Trade Act of 1974; Section 402; waiver authority; presidential determination",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-administration-policy-hj-res-373-disapproving-the-extension-mfn-china-hr-4590": (
        "据正文整理：行政部门反对撤销或限制中国最惠国待遇的议案，支持另一项中国政策法案，并主张通过接触、人权外交、扩大的对华广播和民间团体支持推进美国政策目标。",
        "China MFN; U.S. Congress; human rights; engagement; international broadcasting",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-most-favored-nation-trade-status-for-china-0": (
        "据正文整理：克林顿表示将继续推行促进美国对华各项利益、包括改善人权的对华政策，并期待与国会合作。",
        "China MFN; U.S.-China policy; human rights; U.S. Congress",
    ),
    "https://www.presidency.ucsb.edu/documents/memorandum-most-favored-nation-status-for-china-0": (
        "据正文整理：克林顿依据《1974年贸易法》认定，继续适用于中华人民共和国的豁免将实质性促进该法第402条目标，并指示国务卿公布决定。",
        "China MFN; Trade Act of 1974; Section 402; waiver authority; presidential determination",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-administration-policy-hj-res-182-disapproving-the-extension-mfn-china": (
        "据正文整理：行政部门反对撤销中国最惠国待遇的决议，称续期有助于维持对华接触并推进贸易、人权、防扩散及台湾相关利益，同时指出撤销可能引发中国报复措施。",
        "China MFN; U.S.-China engagement; human rights; Taiwan; trade relations",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-house-representatives-action-most-favored-nation-trade-status-for-china": (
        "据正文整理：克林顿欢迎众议院支持续予中国最惠国贸易地位的表决，称对华接触有助于推进人权、防扩散、贸易、地区安全和台湾关系等议题。",
        "China MFN; U.S. House of Representatives; engagement; human rights; Taiwan relations",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-645": (
        "据正文整理：记者询问杜鲁门是否决定承认中国共产党政府；杜鲁门回答称他尚未就此议题进行讨论。",
        "Communist Government of China; diplomatic recognition; Truman press conference; U.S. foreign policy",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-624": (
        "据正文整理：杜鲁门在记者会上回答朝鲜战事相关问题，说明联合国要求成员国援助韩国，并谈到美国支援行动和维持韩国独立的目标。",
        "Korean War; United Nations; Republic of Korea; U.S. military intervention",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-the-president-the-situation-korea": (
        "据正文整理：杜鲁门将朝鲜遭入侵描述为共产主义从颠覆转向武装侵略，并宣布美军支援韩国、派第七舰队防止台湾遭攻击，同时要求台湾当局停止对大陆的空海行动。",
        "Korean War; Taiwan Strait; Communist China; U.S. Seventh Fleet; Indochina",
    ),
    "https://www.presidency.ucsb.edu/documents/radio-and-television-address-the-american-people-the-situation-korea": (
        "据正文整理：杜鲁门向公众说明朝鲜战争的起因、联合国应对和美军部署，并将朝鲜战事描述为对国际和平与美国国家安全的挑战。",
        "Korean War; United Nations; U.S. public address; national security; communism",
    ),
    "https://www.presidency.ucsb.edu/documents/authorized-statement-the-secretary-state-following-his-review-with-the-president-the": (
        "据正文整理：声明说明美国对台湾海峡局势的立场，谴责对金门炮击，并主张反对武力、继续谈判。",
        "Taiwan Strait; Quemoy; U.S. defense policy; cross-Strait crisis",
    ),
    "https://www.presidency.ucsb.edu/documents/radio-and-television-report-the-american-people-regarding-the-situation-the-formosa": (
        "据正文整理：艾森豪威尔向美国公众说明金门、马祖炮击及美国对台海危机的政策，并主张通过谈判维护和平。",
        "Taiwan Strait; Quemoy; U.S. public address; cross-Strait crisis",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-191": (
        "据正文整理：肯尼迪在记者会上谈台湾海峡军情，重申反对以武力改变现状，并说明美国对台湾与澎湖的防务政策。",
        "Taiwan Strait; U.S. defense policy; Formosa Resolution; China",
    ),
    "https://www.presidency.ucsb.edu/documents/third-annual-report-the-congress-united-states-foreign-policy": (
        "据正文整理：尼克松向国会报告1971年外交政策，回顾与中华人民共和国接触及访华邀请，阐述推动关系正常化、避免冲突并寻求合作的目标。",
        "Nixon China initiative; U.S.-China normalization; 1972 visit; foreign policy",
    ),
    "https://www.presidency.ucsb.edu/documents/toasts-the-president-and-premier-chou-en-lai-the-peoples-republic-china-banquet-honoring": (
        "据正文整理：尼克松在北京宴会致辞感谢中国接待，指出美中虽曾为敌且仍有分歧，但拥有共同利益，并强调合作对和平的重要性。",
        "Nixon China visit; U.S.-China relations; bilateral cooperation; diplomacy; peace",
    ),
    "https://www.presidency.ucsb.edu/documents/address-the-nation-diplomatic-relations-between-the-united-states-and-the-peoples-republic": (
        "据正文整理：卡特向全国宣读中美建交联合公报，宣布美国自1979年1月1日起承认中华人民共和国政府并建立外交关系，同时说明与台湾保持非官方关系的安排。",
        "U.S.-China normalization; Joint Communique; Taiwan; diplomatic relations",
    ),
    "https://www.presidency.ucsb.edu/documents/diplomatic-relations-between-the-united-states-and-the-peoples-republic-china-united": (
        "据正文整理：美国政府宣布自1979年1月1日起承认中华人民共和国并与其建立外交关系，同时终止对台外交承认与共同防御条约。",
        "U.S.-China normalization; diplomatic recognition; Taiwan; mutual defense treaty",
    ),
    "https://www.presidency.ucsb.edu/documents/diplomatic-relations-between-the-united-states-and-the-peoples-republic-china-remarks": (
        "据正文整理：卡特在白宫简报会上解释中美关系正常化决定，回顾推动建交的进展，并说明美国对台湾相关安排的考虑。",
        "U.S.-China normalization; Taiwan; White House briefing; foreign policy",
    ),
    "https://www.presidency.ucsb.edu/documents/memorandum-from-the-president-united-states-relations-with-the-people-taiwan": (
        "据正文整理：卡特指示联邦部门自1979年1月1日起按建交安排处理对中华人民共和国及台湾的关系，并维持与台湾人民的非官方关系。",
        "U.S.-China normalization; Taiwan; executive memorandum; diplomatic relations",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-88": (
        "据正文整理：尼克松介绍访华行程，并在记者会上谈及与中国领导人会晤及两国关系。",
        "Nixon visit to China; U.S.-China relations; summit diplomacy",
    ),
    "https://www.presidency.ucsb.edu/documents/joint-statement-following-discussions-with-the-vice-president-the-republic-china": (
        "据正文整理：肯尼迪重申支持中华民国继续代表中国留在联合国，并反对中华人民共和国加入联合国。",
        "China representation at the UN; Republic of China; Taiwan; U.S.-China relations",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-1038": (
        "据正文整理：约翰逊说明美国对越政策，称中国支持北越，并表示美国仍愿通过谈判解决冲突。",
        "China; North Vietnam; U.S. policy; negotiations",
    ),
    "https://www.presidency.ucsb.edu/documents/visit-vice-premier-deng-xiaoping-the-peoples-republic-china-remarks-the-welcoming-ceremony": (
        "据正文整理：卡特欢迎邓小平访美，谈及中美关系正常化、扩大贸易与人员和思想交流，以及通过相互理解维护亚太和平。",
        "Deng Xiaoping visit; U.S.-China normalization; cultural exchange; trade; Asia-Pacific peace",
    ),
    "https://www.presidency.ucsb.edu/documents/visit-vice-premier-deng-china-remarks-reporters-following-meeting": (
        "据正文整理：卡特与邓小平在会谈后表示双方增进相互理解与友谊，并期待政治、经济、科技和文化领域的合作。",
        "Deng Xiaoping visit; U.S.-China talks; mutual understanding; bilateral cooperation",
    ),
    "https://www.presidency.ucsb.edu/documents/visit-vice-premier-deng-china-joint-press-communique": (
        "据正文整理：联合公报总结卡特与邓小平会谈及双方签署的科技、文化、教育、农业、航天和领事等协议，并提出便利对方常驻记者取得认证。",
        "Deng Xiaoping visit; joint communiqué; journalist accreditation; cultural agreement; U.S.-China relations",
    ),
    "https://www.presidency.ucsb.edu/documents/text-the-united-states-china-accord-for-cultural-exchange": (
        "据正文整理：1984—1985年中美文化交流安排涵盖艺术、广播电视、新闻出版、图书档案和教育等领域，并规定美国之音与北京广播电台交换人员及节目材料。",
        "U.S.-China cultural exchange; Voice of America; Radio Beijing; journalism; broadcasting",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-fudan-university-shanghai-china": (
        "据正文整理：里根在复旦大学演讲介绍美国的政治价值与社会特征，回顾中美关系和共同关切，并呼吁两国加强交流、合作与和平友谊。",
        "Ronald Reagan; Fudan University; U.S.-China relations; public diplomacy; cultural exchange",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-45": (
        "据正文整理：布什谴责中国军队对和平示威采取暴力，呼吁领导层避免暴力并恢复克制；宣布暂停军售和军事互访，审议中国学生延长在美停留的请求，并提供人道医疗援助。",
        "Tiananmen Square; George H.W. Bush; U.S.-China relations; human rights; military sanctions",
    ),
    "https://www.presidency.ucsb.edu/documents/statement-the-anniversary-the-suppression-the-demonstrations-tiananmen-square": (
        "据正文整理：布什在事件一周年声明中重申对武力镇压的谴责，支持言论、新闻和结社自由，表达对中国人权状况的关切，并呼吁恢复改革及发展双边关系。",
        "Tiananmen Square; anniversary statement; human rights; freedom of expression; U.S.-China relations",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-44": (
        "据正文整理：布什在记者会上谈及暂停对华军售后的外交应对，谴责暴力并呼吁尊重民众民主诉求，同时表示美国希望维持与中国人民及政府的关系。",
        "Tiananmen Square; U.S. military sales; diplomacy; democracy; U.S.-China relations",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-43": (
        "据正文整理：布什谈到中国暂停和平队赴华安排及中美人员交流，重申对天安门事件的关切，并表示希望避免损害中国民众、维持双边接触。",
        "Tiananmen Square; Peace Corps; student exchange; U.S.-China relations; public diplomacy",
    ),
    "https://www.presidency.ucsb.edu/documents/the-presidents-news-conference-with-president-mitterrand-france": (
        "据正文整理：布什在与密特朗的联合记者会上回应中国学生示威问题，支持言论、集会和新闻自由，呼吁克制、避免流血并和平解决局势。",
        "China student demonstrations; George H.W. Bush; freedom of speech; freedom of assembly; peaceful resolution",
    ),
    "https://www.presidency.ucsb.edu/documents/memorandum-disapproval-for-the-bill-providing-emergency-chinese-immigration-relief": (
        "据正文整理：布什说明其不批准《1989年紧急中国移民救济法案》的理由，并列出为在美中国公民提供的居留、就业和免遭遣返等行政保护，同时表示将继续支持学生与学者交流。",
        "Tiananmen events; Chinese students; immigration relief; deferral of departure; U.S.-China exchange",
    ),
}

PRESIDENCY_REVIEWED_HASHED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://www.presidency.ucsb.edu/documents/address-foreign-policy-luncheon-the-american-society-newspaper-editors": (
        "8d68b7219c58ac538efc51080b0aca889d8c36251a0e84f0cd2806d6af2641db",
        "据正文整理：杜鲁门向美国报纸编辑协会阐述公众、自由新闻与外交政策之间的关系，并讨论美国面临的国际事务及对外政策。",
        "Harry S. Truman; foreign policy; free press; newspaper editors; public opinion; international affairs",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-the-20th-anniversary-the-voice-america": (
        "d341001814c73073a361dca4009993cec5b3f3a52f57c74f17f5f182678a4202",
        "据正文整理：肯尼迪在美国之音成立二十周年活动上谈到该机构向海外介绍美国及其政治制度的广播职责。",
        "John F. Kennedy; Voice of America; international broadcasting; public diplomacy; United States",
    ),
    "https://www.presidency.ucsb.edu/documents/speech-senator-john-f-kennedy-american-legion-convention-miami-beach-fl": (
        "45c1bbb1399b327bfd0ed4469cb6b3069cf15b3edd59606485094c7705e04cd1",
        "据正文整理：肯尼迪在美国退伍军人协会大会演讲，讨论美国国防、国际共产主义竞争及美国在世界事务中的地位。",
        "John F. Kennedy; American Legion; national defense; foreign policy; communism; China",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-action-against-nuclear-proliferation-south-asia-and-most-favored-nation-trade": (
        "a85b51488c1b31cb95e14354570836bc346e2c9c590c4519d14cac4045164a4c",
        "据正文整理：讲话说明美方处理印度和巴基斯坦核试验及南亚核军备竞赛的目标，回顾核不扩散政策，并在结尾谈及中国的最惠国贸易地位。",
        "India; Pakistan; nuclear tests; China; MFN; nuclear non-proliferation",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-the-asia-pacific-economic-cooperation-summit-and-exchange-with-reporters-auckland": (
        "e27a4ea7838c3e3e5a9f9a4f0f84698d331c1c07df87e2a47b690711d5e74a41",
        "据正文整理：克林顿在APEC会议后介绍开放市场、农业和工业产品贸易议程，说明与江泽民会谈及中国加入WTO、武器扩散和西雅图新一轮贸易谈判。",
        "APEC; China; WTO; President Jiang; weapons of mass destruction; Seattle",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-the-american-embassy-community-ankara-turkey": (
        "95516f86c1d575ecfe8d4b84bf2f657f265fdd79ade43c6df012e872b091d6fa",
        "据正文整理：讲话宣布美国与中国达成中国加入WTO的协议，讨论其对中美关系、美国企业和世界经济的影响，并说明相关贸易安排和履约内容。",
        "China-U.S. Agreement on World Trade Organization Accession; WTO; China; United States; Jiang Zemin; trade agreement",
    ),
    "https://www.presidency.ucsb.edu/documents/republican-presidential-candidates-debate-phoenix-arizona": (
        "1a1f8cb4ff5e58a1ce2ce50f9a620808acaa9861298fe64e4585be981ace5b65",
        "据正文整理：CNN亚利桑那州共和党初选辩论记录六名共和党候选人对中国政策、贸易、人权、台湾关系和外交事务的看法。",
        "China; trade; human rights; Taiwan; China policy; Taiwan relations",
    ),
    "https://www.presidency.ucsb.edu/documents/republican-presidential-candidates-forum-durham-new-hampshire": (
        "51ba6c3408c1933461a234eb09125370b21ab307942f5d7e9414ff06a7e913fc",
        "据正文整理：新罕布什尔共和党候选人论坛讨论经济、医疗、外交、社会议题；正文涉及中国、台湾、贸易、人权和美国外交政策。",
        "China; trade; Taiwan; human rights; foreign policy",
    ),
    "https://www.presidency.ucsb.edu/documents/republican-party-platform-1992": (
        "139886790884f29ceba66c463b323a5744fb38da98d46200b8d8259055b29ce7",
        "据正文整理：1992年共和党纲领阐述外交与国家安全政策，涉及中国、台湾、贸易、人权和核不扩散。",
        "China; Taiwan; trade; human rights; nuclear proliferation",
    ),
    "https://www.presidency.ucsb.edu/documents/remarks-departure-from-tinker-air-force-base-oklahoma-and-exchange-with-reporters": (
        "5dd4882057e82716f8b3bd7caa783cd437df14653a7c940afe89598cfb1f77b6",
        "据正文整理：克林顿就北约空袭意外损毁中国驻贝尔格莱德使馆致歉，说明人员伤亡与科索沃军事行动背景，并讨论避免平民伤亡。",
        "Chinese Embassy; Belgrade; Kosovo; NATO airstrikes; China",
    ),
    "https://www.presidency.ucsb.edu/documents/press-briefing-joe-lockhart-168": (
        "733a1d08a1468367a54e416a805802c526ca15a1f3938ddae95b9ef4eeac9309",
        "据正文整理：白宫记者会讨论科索沃战争进展、米洛舍维奇和北约行动，也回应中国使馆被误炸及相关中美沟通。",
        "Kosovo; China; Chinese Embassy; NATO; Milosevic",
    ),
    "https://www.presidency.ucsb.edu/documents/presidential-debate-st-louis": (
        "51a68556e6f5c0a458324309aca7cc719b908574c2a520dd39e9e9a2a96e4ca2",
        "据正文整理：1992年总统辩论记录克林顿、布什和佩罗讨论国内外政策，正文涉及中国、人权、贸易、核武器和军备控制。",
        "China; human rights; trade; nuclear weapons; arms control",
    ),
    "https://www.presidency.ucsb.edu/documents/republican-candidates-debate-simi-valley-california-1": (
        "491c3d86abdc33a87d42d591070328bd774c8299357dc9077c4914f6d555c768",
        "据正文整理：2023年共和党总统初选辩论讨论中国、台湾、贸易、人工智能和国家安全等议题。",
        "China; Taiwan; trade; artificial intelligence; national security",
    ),
}

BUSH41_REVIEWED_METADATA: dict[str, tuple[str, str]] = {
    "https://www.bush41library.gov/digital-research-room/finding-aid/public-papers/statement-press-secretary-fitzwater-united-states": (
        "据正文整理：声明说明美国暂停与中国的高层官员及军事交流，并寻求推迟新的国际金融机构对华贷款，同时表示支持民主诉求和继续发展双边关系。",
        "Tiananmen events; U.S. sanctions; official exchanges; international loans; U.S.-China relations",
    ),
}

# Reviewed non-transcript statement: publication day, title, full extracted-body hash.
OBAMA_WHITEHOUSE_REVIEWED_STATEMENTS: dict[str, tuple[str, str, str]] = {
    "https://obamawhitehouse.archives.gov/the-press-office/us-china-joint-statement": (
        "2009-11-17", "U.S.-China Joint Statement",
        "b478253b25d3e60b293037d5d0efe4e01b5355794574b113a5913acb98f75e46",
    ),
}

OBAMA_WHITEHOUSE_REVIEWED_VIDEO_TRANSCRIPTS: dict[str, tuple[str, str, str, str, str]] = {
    "https://obamawhitehouse.archives.gov/photos-and-video/video/2013/09/06/president-obamas-bilateral-meeting-president-xi-china": (
        "107eaf5f90962f425fb8372daa5296fad0d7f8b92c492bd4002d73319ff7e399",
        "据正文整理：奥巴马与习近平在二十国集团峰会双边会晤前谈及中美双边关系、全球挑战、朝鲜核与导弹项目及气候变化，并强调合作和管理分歧。",
        "China; bilateral relationship; global challenges; North Korea; nuclear and missile programs; climate change",
        "2013-09-06",
        "President Obama's Bilateral Meeting with President Xi of China",
    ),
    "https://obamawhitehouse.archives.gov/photos-and-video/video/china-town-hall": (
        "7e071f0c6a8e1f51e949371effb981da77d4852d72bb771ac1e95973ac954bea",
        "据正文整理：奥巴马在上海同中国青年举行 town hall，回答有关中美关系、贸易、全球挑战和气候变化的问题，并谈到两国青年交流。",
        "China; Shanghai; U.S.-China relations; global challenges; trade; climate change",
        "2009-11-16",
        "President Obama Holds Town Hall with Chinese Youth",
    ),
    "https://obamawhitehouse.archives.gov/photos-and-video/video/2012/02/14/president-obama-s-bilateral-meeting-vice-president-xi-china-0": (
        "c67e947c229a23258d19ba69d519c14e54dce680644363932d1d40f0ee370c9f",
        "据正文整理：奥巴马与习近平在白宫会晤前讨论中美关系、亚太地区、贸易、人权及双方共同关切的国际和地区问题。",
        "China; U.S.-China relations; Asia Pacific; trade; Vice President Xi; human rights",
        "2012-02-14",
        "President Obama’s Bilateral Meeting with Vice President Xi of China",
    ),
}

OBAMA_WHITEHOUSE_REVIEWED_METADATA: dict[str, tuple[str, str]] = {
    "https://obamawhitehouse.archives.gov/the-press-office/2012/04/30/remarks-president-obama-and-prime-minister-noda-japan-joint-press-confer": (
        "据正文整理：奥巴马与野田举行联合记者会，谈及美日同盟、亚太安全与经济合作；回应中国相关问题时讨论人权、和平发展、国际规则及地区协作，并称美方行动并非旨在遏制中国。",
        "U.S.-Japan alliance; China; Asia-Pacific security; human rights; international rules and norms; regional cooperation",
    ),
    "https://obamawhitehouse.archives.gov/the-press-office/us-china-joint-statement": (
        "据正文整理：联合声明阐述中美关系、战略互信、经济合作和全球挑战，涉及台湾、人权、人文交流、核不扩散及气候与能源合作。",
        "U.S.-China relations; strategic trust; Taiwan; human rights; people-to-people exchanges; climate change",
    ),
    "https://obamawhitehouse.archives.gov/the-press-office/2010/11/11/remarks-president-obama-and-president-hu-china-bilateral-meeting": (
        "据正文整理：奥巴马与胡锦涛在首尔会谈前谈及双边关系、核不扩散、平衡可持续增长、战略与经济对话及胡锦涛访美筹备。",
        "U.S.-China relations; Seoul G20; nuclear nonproliferation; Strategic and Economic Dialogue; Hu Jintao visit",
    ),
    "https://obamawhitehouse.archives.gov/the-press-office/remarks-president-obama-and-president-hu-china-meeting/": (
        "据正文整理：奥巴马与胡锦涛在伦敦首次面对面会谈前讨论双边关系、金融危机与和平安全合作，并介绍战略与经济对话的双方代表。",
        "U.S.-China relations; London meeting; financial crisis; Strategic and Economic Dialogue",
    ),
    "https://obamawhitehouse.archives.gov/the-press-office/remarks-president-obama-and-president-hu-jintao-china-meeting/": (
        "据正文整理：奥巴马与胡锦涛在纽约会谈前谈及合作关系、全球与地区挑战、奥巴马计划访华及妥善处理敏感问题。",
        "U.S.-China relations; New York meeting; Obama China visit; bilateral cooperation; sensitive issues",
    ),
    "https://obamawhitehouse.archives.gov/the-press-office/2010/09/23/remarks-president-obama-and-premier-wen-jiabao-china-bilateral-meeting": (
        "据正文整理：奥巴马与温家宝在双边会谈前讨论应对金融危机、平衡增长、核不扩散、气候变化和战略与经济对话，并谈及胡锦涛访美。",
        "U.S.-China relations; Wen Jiabao; financial crisis; nuclear nonproliferation; climate change; Strategic and Economic Dialogue",
    ),
    "https://obamawhitehouse.archives.gov/the-press-office/2015/09/25/remarks-president-obama-and-president-xi-peoples-republic-china-arrival": (
        "据正文整理：奥巴马欢迎习近平访美，回顾中美合作，并谈及贸易、气候变化、伊朗核问题、人权与公平竞争。",
        "U.S.-China relations; Xi Jinping state visit; trade; climate change; human rights",
    ),
}

CLINTON_WHITEHOUSE_REVIEWED_METADATA: dict[str, tuple[str, str]] = {
    "https://clintonwhitehouse4.archives.gov/WH/Work/061198.html": (
        "据正文整理：克林顿论述美中关系、其访华目标及双边合作议程，讨论贸易、人权、台湾、地区安全和沟通交流等议题。",
        "U.S.-China relations; public diplomacy; trade; human rights; Taiwan; China visit",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/China/19980629-6683.html": (
        "据正文整理：克林顿在北京大学演讲，讨论教育、自由与中美交流，并回答有关双边关系和中国发展的问题。",
        "China visit; Peking University; education; U.S.-China exchange; freedom; public diplomacy",
    ),
    "https://clintonwhitehouse4.archives.gov/textonly/WH/New/China/19980627-9474.html": (
        "据正文整理：克林顿与江泽民在记者会上介绍会谈情况并回答记者提问，内容涉及中美关系、贸易、台湾及双方沟通。",
        "U.S.-China relations; Jiang Zemin; press conference; trade; Taiwan; bilateral dialogue",
    ),
    "https://clintonwhitehouse4.archives.gov/textonly/WH/New/China/19980627-13450.html": (
        "据正文整理：克林顿与江泽民在合影活动前致辞，表达对国事访问和两国领导人会谈的期待。",
        "U.S.-China relations; Jiang Zemin; state visit; bilateral meeting; diplomacy",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/China/19980629-6877.html": (
        "据正文整理：克林顿在北京大学赠书活动上谈及通过教育与青年交流增进相互了解，表达美中合作建设和平繁荣未来的期待，并回答有关两国交流的问题。",
        "China visit; Peking University; U.S.-China exchange; international education; mutual understanding; youth diplomacy",
    ),
    "https://clintonwhitehouse6.archives.gov/1994/05/1994-05-26-briefing-by-lake-et-al-on-mfn-status-for-china.html": (
        "据正文整理：白宫官员解释克林顿政府将中国最惠国贸易待遇与人权政策脱钩的决定，并讨论通过接触、国际广播、美国之音和新设的自由亚洲电台继续推进人权对话。",
        "China MFN status; U.S.-China relations; human rights; Voice of America; Radio Free Asia; international broadcasting",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19971024-3863.html": (
        "据正文整理：演讲讨论江泽民即将访美、中美关系，以及美国之音和美国新闻署推动全球思想自由流动的作用。",
        "U.S.-China relations; public diplomacy; Voice of America; free flow of ideas; Jiang Zemin state visit",
    ),
    "https://clintonwhitehouse4.archives.gov/textonly/WH/New/html/19971024-3863.html": (
        "据正文整理：演讲讨论江泽民即将访美、中美关系，以及美国之音和美国新闻署推动全球思想自由流动的作用。",
        "U.S.-China relations; public diplomacy; Voice of America; free flow of ideas; Jiang Zemin state visit",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19990408-1109.html": (
        "据正文整理：克林顿讨论美中关系、贸易与世贸组织谈判、信息获取、政治自由、人权及双边合作领域。",
        "U.S.-China relations; Zhu Rongji; WTO; human rights; information access; bilateral cooperation",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/20000308_2.html": (
        "据正文整理：克林顿认为中国加入世贸组织和给予永久正常贸易关系将促进改革、问责、开放、法治及信息和观点交流。",
        "U.S.-China WTO agreement; permanent normal trade relations; reform; openness; access to information",
    ),
    "https://clintonwhitehouse4.archives.gov/textonly/library/hot_releases/October_10_2000_6.html": (
        "据正文整理：在签署对华永久正常贸易关系法案时，发言者说明其预期带来的市场准入和中国融入国际体系，并提及美国对人权及防扩散的持续关切。",
        "China PNTR; U.S.-China trade; WTO accession; market access; human rights; nonproliferation",
    ),
}

CLINTON_WHITEHOUSE_REVIEWED_HASHED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19990407-2873.html": (
        "172bc5b22412fa5ba0b45ec31d38e24ff45ce5e389fc179605214e3d02a93bb6",
        "据正文整理：克林顿在美国和平研究所外交政策演讲中讨论美国与中国的关系和美国公众对中国的历史认知，涉及朱镕基访美、国际体系、贸易与人权等议题。",
        "relationship with China; perceptions about China; Zhu Rongji; international system; human rights",
    ),
    "https://clintonwhitehouse4.archives.gov/textonly/library/hot_briefings/September_14_2000.html": (
        "cbba2c19689954add28cc52ffed656907a127c25068a84d91a956562da4c3e1f",
        "据正文整理：记者会主要回应Wen Ho Lee案件、贸易议程和制裁措施，并在问答中涉及中国与印度的安全关系。",
        "Wen Ho Lee; Joe Lockhart; WTO; sanctions; China",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19971216-7308.html": (
        "04a0252a37b854dbbcb2d862fd09487eb392121f9260d416c21744db790d30d5",
        "据正文整理：记者会回顾政府工作并讨论对华接触，涉及与中国的“honest engagement”、亚洲金融危机、韩国国际货币基金组织计划以及冷战后的地区关系。",
        "China; honest engagement; South Korea; IMF; Cold War",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19991124.html": (
        "2ad03ba161d6c527db95ce9b1c207587139c0ff2c8a51aea82533f7cf38a7f60",
        "据正文整理：材料介绍克林顿为西雅图世界贸易组织新一轮谈判提出的议程，讨论农业、电子商务、劳工与环境等议题，并将谈判目标表述为扩大就业、发展和贸易机会。",
        "Seattle Round; World Trade Organization; jobs and development; agriculture; e-commerce",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19981119-14423.html": (
        "e41b1e2eb63204f86df4ccd6565d570beaa4110164821f82fb67672b210fce5e",
        "据正文整理：东京市民会谈讨论美国与日本的民主伙伴关系、亚洲金融危机、对华关系及北京申办奥运会等问题，克林顿也谈到世界贸易组织和区域合作。",
        "Japan; China; Asian economic crisis; WTO; Beijing; Olympics",
    ),
    "https://clintonwhitehouse4.archives.gov/WH/New/html/19991109_1.html": (
        "aedae8388f27b9bd2c98691b48d2ac51874d677b1b026e85f2693288e4fc9c62",
        "据正文整理：材料记录克林顿首次总统互联网市民会谈，讨论互联网传播、世界贸易组织西雅图会议的环境保障、导弹防御及中国的核与导弹能力。",
        "Internet; WTO; Seattle; missile defense; China",
    ),
}

TRUMP_WHITEHOUSE_REVIEWED_HASHED_METADATA: dict[str, tuple[str, str, str]] = {
    "https://trumpwhitehouse.archives.gov/briefings-statements/remarks-by-president-trump-and-president-xi-of-china-at-state-dinner-beijing-china/": (
        "cee2bd24c84a8a80a776af92e2c6f24f68d2b95bb1e3f5acb16ecb8cfe3e02e5",
        "据正文整理：特朗普与习近平在北京国宴致辞，回顾尼克松访华和两国交往，谈及双边贸易、朝鲜问题及两国合作。",
        "U.S.-China relations; state visit; trade; North Korea; bilateral cooperation",
    ),
    "https://trumpwhitehouse.archives.gov/briefings-statements/remarks-president-trump-signing-presidential-memorandum-targeting-chinas-economic-aggression/": (
        "4541f3a20616d846304147e4e79541d3cb4811968be1340fad68fdbac3b8c38d",
        "据正文整理：特朗普在签署针对中国经济政策的总统备忘录时批评中国贸易和技术转移做法，说明拟采取的贸易措施并回答记者提问。",
        "China trade policy; Section 301; technology transfer; intellectual property; U.S. tariffs",
    ),
    "https://trumpwhitehouse.archives.gov/briefings-statements/remarks-president-trump-actions-china/": (
        "80cad74187dc803c9f63d3613a336034c4dfbf7a8926e5f5a6001efa8f2037a4",
        "据正文整理：特朗普宣布美国对华采取一系列措施，讲话涉及双边关系、贸易、香港、南海及新冠疫情。",
        "U.S.-China relations; trade; Hong Kong; South China Sea; COVID-19; U.S. policy",
    ),
    "https://trumpwhitehouse.archives.gov/briefings-statements/remarks-vice-president-pence-administrations-policy-toward-china/": (
        "d0539786addc10c2c2aee05b0701a7bac4335829f4b8d992037757b78696f3cc",
        "据正文整理：彭斯在哈德逊研究所阐述特朗普政府对华政策，回顾中美关系并批评中国在贸易、知识产权、政治影响、宗教和台湾等方面的做法，强调美国在印太地区的回应。",
        "China; trade; intellectual property; propaganda; Taiwan; Indo-Pacific",
    ),
    "https://trumpwhitehouse.archives.gov/briefings-statements/remarks-vice-president-pence-frederic-v-malek-memorial-lecture/": (
        "dac180d9aba58bbdecee1d13976827ca94f18de4921eb38d1d5dfc02f1445f68",
        "据正文整理：彭斯在威尔逊中心弗雷德里克·马利克纪念演讲中将中国称为美国的战略和经济竞争者，讨论贸易、技术转让、维吾尔人、香港、台湾和印太安全政策。",
        "China; strategic and economic rival; trade; technology transfer; Uighurs; Hong Kong; Taiwan; Indo-Pacific",
    ),
}

PRCLEADER_REVIEWED_ARTICLES: dict[str, dict[str, object]] = {
    "https://www.prcleader.org/post/how-china-is-responding-to-escalating-strategic-competition-with-the-u-s": {
        "published_on": "2021-03-01",
        "title": "How China is Responding to Escalating Strategic Competition with the U.S.",
        "author": "Ryan Hass",
        "structured_date": "2021-03-02T06:00:00.000Z",
        "body_sha256": "0e12897654d5577ae5382641191345d93492f07b357014c29664329fb69e69a6",
        "first_body_prefix": "Understanding China’s evaluation of – and response to – sharp shifts in U.S.-China relations",
        "last_body_prefix": "[46] Shi Yinhong, “The U.S. and Other Major Countries' Policies Toward China",
        "body_paragraphs": 109,
        "abstract": (
            "据正文整理：文章梳理中国对美国战略竞争、国际体系和自身战略目标的判断，"
            "分析其维持非敌对外部环境、拓展伙伴关系及提升国际影响力等策略。"
        ),
        "keywords": "China; United States; strategic competition; foreign policy; international order",
    },
}

CARNEGIE_REVIEWED_ARTICLES: dict[str, dict[str, object]] = {
    "https://carnegieendowment.org/russia-eurasia/research/2024/10/us-china-relations-for-the-2030s-toward-a-realistic-scenario-for-coexistence": {
        "published_on": "2024-10-17",
        "title": "U.S.-China Relations for the 2030s: Toward a Realistic Scenario for Coexistence",
        "authors": (
            "Christopher S. Chivvis, Mariano-Florentino (Tino) Cuéllar, Evan S. Medeiros, "
            "Stephen M. Walt, John Culver, Rosemary Foot, C. Fred Bergsten, Edoardo Campanella, "
            "Meg Rithmire, M. Taylor Fravel, Eric Heginbotham, George Perkovich, Audrye Wong, "
            "Stephen Wertheim"
        ),
        "structured_date": "Oct 17, 2024",
        "citation_date": "2024-10-17T12:00:00.000Z",
        "body_sha256": "1d1e25dea66e29a394f16e16498bacc746d525cfe42b519278906009f089a42d",
        "body_sections": 12,
        "body_blocks": 531,
        "first_body_prefix": "Preface",
        "last_body_prefix": "These are all credible trajectories that would produce very different U.S. orientations toward China.",
        "abstract": (
            "It has become difficult to imagine how Washington and Beijing might turn their relationship, "
            "which is so crucial to the future of world order, toward calmer waters. If there is to be any "
            "hope of doing so, however, policy experts need some realistic vision of what those calmer waters might look like."
        ),
        "keywords": "U.S.-China relations; China; strategic competition; informational statecraft; international order",
    },
}

DAN_RATHER_REVIEWED_SCANNED_TRANSCRIPTS: dict[str, dict[str, object]] = {
    "https://danratherjournalist.org/sites/default/files/documents/05_18_1989.pdf": {
        "publisher": "CBS News",
        "published_on": "1989-05-18",
        "author": "Dan Rather",
        "title": "CBS EVENING NEWS WITH DAN RATHER",
        "page_title": "Document - CBS Evening News, May 18, 1989, Transcript | Dan Rather",
        "page_date_marker": "May 18, 1989",
        "pages": 5,
        "abstract": "据正文整理：Dan Rather 报道李鹏与学生代表会面、天安门广场示威与绝食情况，并收录 Charles Kuralt 对北京街头民众的采访。",
        "keywords": "China; Tiananmen Square; student protests; Li Peng; Charles Kuralt; CBS News",
        "pdf_sha256": "ebdbb7b592e8f2c23571b50df04d01792b09eb51d3a3a2f5461a0b6ffe656b4f",
        "body_sha256": "b4874ce27694bca588a9fbd811c72ac7eb000a183693f49102dc75bcbbbbf52c",
        "body": """DAN RATHER: China's Communist leaders make a desperate attempt at dialogue, but fail to end the mass movement for democracy.

(Music theme)

This is the CBS EVENING NEWS, Dan Rather reporting from Tiananmen Square in Beijing, China. Good evening.

Day by day, China's mass movement for democracy becomes more overwhelming and the situation becomes more ominous for the leaders of the world's most populous country. It's now Friday morning here in Beijing and there has been a late development. China's news agency now confirms that in the wee hours of this morning, Prime Minister Li Peng and Communist Party Leader Xhao Ziyang came to see the student hunger strikers right back here in the square where we went to see them earlier in the day. This is the seventh day of a hunger strike by some 3,000 students supported by more than a million protestors here in Beijing, and now hundreds of thousands more all over China.

The top leaders of the Communist Party and government made an extraordinary bid to try to talk their way out of the crisis today, but they came away with nothing but more humiliation. Premier (sic: Prime Minister) Li Peng finally invited leaders of the student hunger strike to a meeting, and he made it inside the Great Hall of the People. Li Peng lectured them, warning that if they don't call off their movement, it will turn to chaos even worse than Mao Zedong's Cultural Revolution. He said the students should leave the square immediately and without preconditions. Protest leader Wuer Kaixi, in his hospital pajamas, shot back, "Whether we leave the square or not is not ours to decide. It is up to the government side." Li Peng wouldn't budge. He said, "I don't care if you want to listen or not." He would not meet the students' demands. He would not agree to any live televised dialogue. Wuer Kaixi fainted and had to be rushed back to the hospital. Later, he said, "The government wants us to go back and forget about dialogue. They don't understand the power of this movement."

The meeting was broadcast on radio and television, but there are more radios than television in this country. People gathered in the streets to listen.

Earlier, Li Peng and three other leaders of the party Central Committee, all except 84-year-old Deng Xiaoping himself, went to the hospital where some of the hunger strikers are being kept alive. They made the rounds, trying to display some bedside sympathy.


But they couldn't pull it off unscathed. They had to stand for a stern lecture from one of the patients. He told the party leaders it is nonsense to say that the students want to overthrow the party. The problem is that some party members are corrupt. "I think we should do as in the United States. That is, to mobilize the hearts of the people, to give confidence to the people. Do you agree?"

The topmost leaders of the country all nodded and answered in unison, "Yes, yes." But then their lecturer shot them a zinger, reminding them of the charge that high government and party officials enrich their own families at the expense of the people. "If you want to solve corruption," he said, "begin with your own sons."

Meanwhile, in the streets, more than a million people were again flocking toward Tiananmen Square when, at 3:30 in the afternoon, a tremendous moonsoon–type rain came down, completely out of season. Students talked about an old Chinese belief that violent weather in the heavens is a sign of great change to come on earth. Government and party leaders hoped that was just superstition. In any case, this much rain would have been enough to break up most rallies of any kind anywhere in the world. But as far as we could see, nobody here went home. Among the marchers, a contingent from the People's Army, declaring a non–violent victory over their own government.

This big blue sign says, "Get rid of the fantasy." It's an indication of what has changed here in Tiananmen Square among the leaders. Anger is up, talk of compromise is out, talk that Deng Xiaoping himself must go, but even more talk that his second man, Li Peng, has to get out.

After five days of mass demonstrations, the normally spotless square is strewn with garbage and starting to reek. Medical people are warning of the danger of disease.

In the headquarters, in the core of the movement, the rebellion, with rain threatening this morning, they moved buses in, put the hunger strikers aboard the buses. There's been a desperate struggle all day against the elements. (Indistinct) this tremendous rain, everything here got wet, had to clean it out. In the midst of the grimness and the concern, the deep concern about the hunger strikers themselves, flowers with a ribbon that reads, loose translation, "Don't give up. The whole country is watching you and pulling for ya."


On the bus, we found one of the original leaders of the hunger strikers, a student who was hospitalized at one point, but then came back to join the strike. I asked him what their main demands are now.

"Li Peng must go," he said. "Every day our standard of living gets lower and lower. Li Peng must go, and Deng Xiaoping. He's a little emperor."

As wet night fell, the day's battle once again belonged to the students. The top leaders had entered into dialogue, all of it broadcast on Chinese television and radio, but the dialogue simply gave the students a platform for their agenda, which looks more and more now like, "Throw the rascals out." At the end of day six, the rebellion was still alive and, incredibly, still growing.


RATHER:

RATHER: What's happening here in Beijing this week is something new, something that's beyond the experience of everyone here—protestors, government officials, party authorities, journalists, police and even people just standing on the corner watching it all go by. That's what Charles Kuralt did today.

CHARLES KURALT: This happens to be a corner on Chegongzhuang Street, but the street corners are like this all over Beijing today, and all over the country. I've been in a lot of big crowds in a lot of big cities, all of us have, but I don't think I've ever been in a genuine popular uprising, something that just comes up from the people. The only strength all these people have is in their numbers, and their only armor is their idealism. It's a—a profoundly moving thing to stand on this street corner in Beijing today.

The only government authority in sight is the policeman locked in his booth over there. A man says to him, "Come out and speak for us. We're all thinking the same thing." The cop says, "Well, then, you speak for me." He says he'll talk to us when he gets off work at 6:00.

That man there is directing the traffic. He says he's taken on the job as his worker's duty. And the traffic comes in waves of trucks and bicycles. These are nursery school teachers. This is the patriotic place to be today, out in the streets trying to bring down the government.

What does that sign say?

LE CHUNG SHUN: "Mr. Deng Xiaoping, you are old, but China is not old yet."

KURALT: That's a pretty brave sign.

LE CHUNG SHUN: Yeah. They are very brave. They are calling for Deng Xiaoping to resign.

KURALT: His name is Le Chung Shun, he says.

Do you think all this is going to have an effect? Do you think it's going to lead somewhere and make a difference?

LE CHUNG SHUN: Sure. This is the turning point in China's history.

KURALT: You're a Communist Party member?

WOMAN: Yeah. I'm—I am. Yes.

KURALT: Are you surprised by what's happening today?


WOMAN: No, I'm not surprised because people just keep silent for so many years and they want to, just like a volcano, they want to—how to say that?—to explode. Yeah. To say what they want to say.

KURALT: He says, "I'm illiterate. I can't even read the signs. I just came out to see what's going on."

Did you ever think you'd see anything like this in China?

"I never saw anything like it," he says. "It's very nice."

KURALT: And so you like what you're seeing, huh?

MAN: Hao.

KURALT: "Hao," he says. "Yes."

A thunderstorm washed over the city in the late afternoon and the crowd ran for cover. For a few minutes there our street corner was nearly empty, and I thought, well, it's over. But there appeared in the rain more wheels and more bodies and more banners. On this corner, on this day, it's hard to imagine it ever being over.

RATHER: And that's tonight's CBS EVENING NEWS from China. Join us this evening for a special edition of the CBS News broadcast 48 HOURS. Tonight, "China Rebellion". That's coming up here soon at 8:00, 7:00 Central Time. Dan Rather in Beijing. See you then.

(ANNOUNCEMENTS)

(End credits over crowds of protestors; copyright notice shown, four seconds)

(ANNOUNCEMENT)

ANNOUNCER: This is CBS.""",
        "abstract_origin": "derived",
    },
    "https://danratherjournalist.org/sites/default/files/documents/e_zirin_00045.pdf": {
        "publisher": "CBS News",
        "published_on": "1989-05-19",
        "author": "Dan Rather",
        "title": "CBS EVENING NEWS WITH DAN RATHER",
        "page_title": "Document - CBS Evening News, May 19, 1989, Transcript | Dan Rather",
        "page_date_marker": "May 19, 1989",
        "pages": 3,
        "abstract": (
            "据正文整理：Dan Rather 按时间顺序报道北京实施戒严前后的天安门广场局势、学生绝食与静坐、"
            "李鹏宣布戒严以及军队尚未进入广场等情况。"
        ),
        "keywords": "China; Tiananmen Square; martial law; hunger strike; student protests; CBS News",
        "pdf_sha256": "9be4627fc65b83cd3d1e021c62f173ebbd865b6fb98da59bea96ae01f8840602",
        "body_sha256": "f9729360acac8e6ab544bf66c03c379faef894ccb15f0acdb0ab10c3b549221a",
        "body": """DAN RATHER: All night in Tiananmen Square China's movement for democracy awaits its critical hour.

(Music theme)

This is the CBS EVENING NEWS, Dan Rather reporting live from Tiananmen Square in Beijing, China. Good evening.

Another night of living dangerously is over for the hunger strikers here in Tiananmen Square. They are still here. The army is not. Incredible. China's Communist hard-liners are finally in control of the government and the party, and they have called out the army in yet another desperate bid to break the back of the mass movement for freedom and democracy and reform. After weeks of government paralysis while students took over the streets of Beijing and moved their protest into a national movement, soldiers are now massing to move against the protestors camped right here in the center of Beijing. The problem is the army has been massing for hours and it still is not here.

It's now Saturday morning in Beijing, a week after the start of a hunger strike that threatened to bring down the government. There is a feeling of ecstasy in this square at the moment because the hunger strikers expected that the army would be here by then—by now, and that they would be out. That hasn't happened. The square is filling back up again now with supporters, and the hunger strikers, their view is that the army is stymied, the pendulum is swinging back their way, and that again they have the government on the run.

Now this sequence of events began in the middle of the night. Premier Li Peng, the hard-line ally of 84-year-old Deng Xiaoping, declared a modified form of martial law for Beijing to end what he called a state of anarchy. That capped 24 riveting hours of roller coaster events and emotions.

5:00 AM: A final gesture by Premier Li Peng and Communist Party Chief Zhao Ziyang. They came down here to be seen talking with hunger strikers. Li Peng stayed only for a couple of minutes, shook hands, had his photograph taken and hurried out. Zhao Ziyang, who has recommended a soft line toward the students, appeared visibly moved. He delivered a conciliatory statement of sorts. "I came too late. I should have come earlier," he told the students. He promised them, "The government will not end its dialogue if you end your strike." Zhao signed autographs, but when he left the students gave the visit at best mixed reviews. With the pre-dawn visit, the government and the party had gone as far as they would go.

Dawn, 6:00 AM, seventh day of the hunger strike: Apprehension is in the air. Things are different. The crowds began to get a bit smaller.

Mid-morning, 10:00 AM: The square looks and smells more and more like a garbage dump. And as the day wears on, the mood goes steadily down.

(Chinese student playing guitar)

By early afternoon students are debating what 24 hours before would have been unthinkable: possibly giving up their strike.

MAN: I think the strike should stop now because now many students' life are in danger and then I think we also achieved a lot. We do not want to lose some students because they're very young and they have a long way to go in their lives.

RATHER: Late afternoon: It becomes apparent Deng Xiaoping has made his decision—go to the hard-line.

7:30 PM: The government and the party make their moves. All demonstrations would be banned as of midnight and steps would be taken to end them. At the same time, a report that Zhao Ziyang had offered his resignation. Not clear whether the party had accepted the resignation.

9:00 PM: The students announce they will no longer call their strike a hunger strike. Now it will be a sit-down strike. At the same time reports of army troops moving into place near the square.

It's 11 o'clock at night. The grapevine has been busy. Word has spread that the Communist Party Secretary may be out. That the army may be moving in here. What's been happening the last few hours as word spread one truck after another has steamed in here with people aboard. We've seen a number of trucks commandeered on the street, sympathy people saying let us have your truck or just taking the truck so they can get to Tiananmen Square. The sense is that something's up, and whatever it is will happen before dawn.

11:30 PM: Half an hour to go until the midnight deadline. Protest leaders call a meeting in the square, an intense discussion. A vote yields no decision.

Midnight: The deadline passes. More reports and rumors of troop movements, many close by.

12:30 AM: Premier Li Peng appears on radio and television, speaking to an audience of top officials and over loudspeakers to the crowds. He says anarchy and riots are threatening the state, threatening to wreck the economy. He blames it on a small group of conspirators trying to overthrow Communist rule. He declares a kind of martial law to put down the protest. Those listening on loudspeakers jeer and begin to chant, "Li Peng, come down! Li Peng, come down!"

2:00 AM: The army still hasn't arrived. Truckloads of strike supporters begin coming in agan. The students dare to hope.

4:00 AM: Reports increase that the army has tried to move closer, but has run into passive resistance from citizens.

Dawn: The army is still not here. A policeman rides into the square announcing, "I represent all of the police of Beijing. We support the students. We support the people. Long live democracy. Long live freedom."

"The leaders must be brought down," he says.

"This was a patriotic movement and the government brought in troops with weapons to put it down. The leaders must be brought down."

By dawn's early light, the students were still there. They had won the night.""",
        "abstract_origin": "derived",
    },
    "https://danratherjournalist.org/sites/default/files/documents/e_zirin_00043_0.pdf": {
        "publisher": "CBS News",
        "published_on": "1989-05-17",
        "author": "Dan Rather",
        "title": "CBS EVENING NEWS WITH DAN RATHER",
        "page_title": "Document - CBS Evening News, May 17, 1989, Transcript | Dan Rather",
        "page_date_marker": "May 17, 1989",
        "pages": 2,
        "abstract": (
            "据正文整理：Dan Rather 报道天安门广场抗议发展为大规模群众运动、绝食学生的医疗情况、"
            "工人和政府人员参与，以及抗议对戈尔巴乔夫访华活动的影响。"
        ),
        "keywords": "China; Tiananmen Square; student protests; labor; Mikhail Gorbachev; CBS News",
        "pdf_sha256": "2761b849f3f797fcd0cae278726775e87cae7805bfdc09ef307870f598f7c5df",
        "body_sha256": "f890abfd7647e63bcd51840214eecf01a899395e66b95213bf942bf8cacf3ba8",
        "body": """DAN RATHER: The Deng-Gorbachev summit is pushed to the side, as demonstrators for democracy take over the streets of Beijing. China's student protest becomes a mass movement.

(Music Theme)

RATHER: This is the CBS EVENING NEWS, Dan Rather reporting from Tiananmen Square in Beijing, China. Good evening.

The world's largest public square has now become the scene of the biggest demonstration in the history of Communist China. It is Thursday morning here, the dawn of day six of a hunger strike for 3,000 students, but the whole character of the protest changed today, as scores of organized groups, including workers, poured in to join the rally. At its height, the crowd was estimated at more than a million. The protests, the rebellion once again overshadowed the summit and forced Chinese officials to cancel Gorbachev's scheduled tour of the ancient Forbidden City adjacent to Tiananmen Square.

(Students chanting; drums)

RATHER: The strike took on the look and feel of an organized, disciplined mass movement. Armies of volunteers supplied everything needed to keep it going indefinitely. Medical care for the hard-core hunger strikers was the first priority. They estimated that 800 had been hospitalized by late in the afternoon, when we went back into the square.

The government no longer even pretends to control this area. Back there, beyond that sea of people, under the picture of Mao: Tiananmen Gate, the gate to the Forbidden City—that's where the Gorbachevs were supposed to go. As you can see, there was no way the government could get them in there. Unending lines of workers—elderly people, families with children—converged on the world's largest public square. Among the protestors today, we've seen these developments: first of all, there are many more of them; secondly, you begin to see government workers from the Foreign Ministry, the Ministry of Health, the Ministry of Education taking part; much more anger, much more talk about replacing high government officials and much more talk about death—rising concern about the hard core of hunger strikers. (ambulance siren) Some parents came to search through the crowd for their children. We asked this woman factory worker if she had a child among the hunger strikers. She said, "These are all our children. These are the people's children. If the government pressures them, we'll risk our lives with them."

One of the important developments of the day: more and more Chinese coming from outside Beijing—from Hunan, Canton, even from Tibet. Tibet's got a lot of problems with the Chinese, but one man from Tibet who arrived today said, "This may not help us, but it's important for China, and I wanted to be here for it."

(General hubbub surrounding Mikhail and Raisa Gorbachev at Great Wall)

RATHER: Mikhail and Raisa Gorbachev went ahead with their trip to the Great Wall of China today, outside Beijing, and had a friendly exchange with some Chinese tourists; but, for a Soviet leader to come to Beijing and not be able to visit the legendary Forbidden City was another humiliation for his hosts. He did go back to the Great Hall of the People for the major address of his visit, but he had to go in the back door--there was trouble at the front. An accommodation had been reached between the student leadership and the government for a while that they would keep the demonstration on the far half of Tiananmen Square, away from the Great Hall of the People. Today, the crowd is so large, it surged right up to, literally, right up to the steps. (cheers)

(Mikhail Gorbachev speaking to group of Chinese intellectuals)

RATHER: Gorbachev told his audience of Chinese academics that the Soviet Union would never again try to impose its form of communism on another nation. Later, at a news conference, Gorbachev was asked about the protest. He said he had received greetings from the Chinese students in messages sent to the Soviet Embassy, and he said the students praised the changes taking place inside the Soviet Union and added, "I appreciate their position." He said, "Change is painful, but these are the kinds of processes we need to provide socialism with a second wind."

(Demonstrators singing)

RATHER: The mood, the sense, the feel out here today is the protestors, they believe that they're on the brink of forcing change, change in the Communist Party, change in government. What kind of change? They're not quite sure. One of the things the demonstrators have been insisting upon is a freer press, and that's one battle they are winning. Today, they were joined by staff members of government-controlled Chinese television, which, two weeks ago, completely ignored a mass protest. Tonight, for the first time, the evening news in China made the demonstration its lead story, and it included scenes of television staff members among the protestors.""",
        "abstract_origin": "derived",
    },
    "https://danratherjournalist.org/sites/default/files/documents/e_zirin_00246.pdf": {
        "publisher": "CBS News",
        "published_on": "1989-05-16",
        "author": "Dan Rather",
        "title": "CBS EVENING NEWS WITH DAN RATHER",
        "page_title": "Document - CBS Evening News, May 16, 1989, Transcript | Dan Rather",
        "page_date_marker": "May 16, 1989",
        "pages": 3,
        "abstract": (
            "据正文整理：Dan Rather 报道戈尔巴乔夫访华期间天安门广场绝食抗议、学生与工人支持、"
            "政府回应及邓小平与戈尔巴乔夫会晤受到抗议影响的情况。"
        ),
        "keywords": "China; Tiananmen Square; student protests; Mikhail Gorbachev; Deng Xiaoping; CBS News",
        "pdf_sha256": "2644ba2973fd2b843e64614d56a67acbe91f8bf22c35c5e0d4275f6bfffb0c58",
        "body_sha256": "b2fa387a6218beefce9545045ccb603dc9d7f1ba992b7474cec9873c877ea381",
        "body": """DAN RATHER: A summit under siege in Beijing: Deng Xiaoping and Mikhail Gorbachev declare normalization while outside the Great Hall of the People the mass non-violent protest for Chinese democracy grows larger and more desperate.

(Music theme)

This is the CBS EVENING NEWS, Dan Rather reporting from Tiananmen Square in Beijing. Good evening.

It is Wednesday morning in China. As the sun rose here, it was clear that the Chinese students' protest for democracy is still gaining strength and urgency. After four days on hunger strike in this exposed, wind-swept area, students are dropping from exhaustion, some now are vowing to die if necessary. Their supporters—teachers, professionals and workers—are appealing in increasingly emotional tones to the Communist leaders at the summit. The government says it has responded.

Early this morning—in the middle of the night, really, Beijing time—a message is reported to have been delivered from the Communist Party chief promising, and I quote, "to work out concrete measures to enhance democracy and law." According to the state news agency, he also promised the government would not punish the students later.

That is according to the official state news agency. But we've been out among the students all night and into early this morning. The students and their leaders don't seem to know anything about that. This continues to be a strange and fascinating summit.

The planned high point of the summit took place today inside the Great Hall of the People. Gorbachev got what he came for—a handshake with Deng Xiaoping, no bear hug, just a handshake. Deng is the architect of economic reforms Gorbachev envies and has been unable to duplicate in Russia. But Deng is now 84 and fading, a symbol of the past and not enough change to protestors outside in the square.

(Protestors chanting)

Deng and Gorbachev* ignored the protestors, who surged right up to the steps of the Great Hall at the same time the men were meeting inside.

(Protestors chanting)

*Also seen: Mrs. Raisa Gorbachev

"Give us water!" they shouted, meaning, give us a sign that you care. No such sign came.

Nearby, a dozen students were refusing to take either food or water. At least one of them was hospitalized during the day, along with others felled by the combination of exhaustion, hunger and a pounding sun.

(Ambulance siren)

By the time we went back into Tiananmen Square in late afternoon, there was a constant stream of victims being carried to the hospital. In the middle of all of this is the hospital tent which handles the worst cases. Now, what they're trying to do is keep the number of hunger strikers, hunger strikers, at 3,000, saying they can't support any more than that. Every time one of them is carried away, then he's replaced by somebody else. Part of what they're trying to do is take care of the hunger strikers in places such as this when it's necessary and to hold the number of hunger strikers at 3,000.

Into this charged setting walked a member of the Communist Party Central Committee. A dramatic scene ensued. "I understand all of your demands," he said. "I have sent them to the government. But give us time." A girl in the back of the crowd called back, "There is no time, sir. People are dying." "You have no right to kill yourselves," he replied. Then, one of the original leaders of the student strike, Wuer Kaixi, rose to speak with an intravenous (sic) tube in his nose. "I personally believe the minister," he said, "but I beg you students to stand with me, trust me, don't give up."

Despite the increasingly desperate mood, support keeps building for the strike. The crowd swelled today with workers, some professionals, with parents, children and teachers looking for their students.

This is interesting because the workers are beginning to be visible in and around Tiananmen Square. The students early on were saying we have the support of the workers. We don't necessarily want to show that card to the government, we don't feel it's necessary, but today some of the workers are beginning to come out and that sign back there—with the red star on it?—"Workers of the Na—China National Airlines." Just below that there's a black sign that says, "Workers Support the Student Hunger Strike. The Nation Cannot Sleep."

At the end of the day, the strike was holding, indeed, still building, as students began arriving from other cities. Worry deepened for government and Communist Party leaders. Publicly, they held to the line protestors should just go home. But once again the protest had the summit on the run.

Gorbachev's meeting with Premier Li Peng was moved from the Great Hall of the People to a guest house in another part of Beijing. The Gorbachevs did get out of their car to greet people in other parts of town, much as they did in Washington not long ago. Raisa Gorbachev did make the usual rounds of cultural institutions, wooing crowds the way she has on every big trip. But this wasn't every other trip. This was a day when the turbulence in downtown Beijing overshadowed the summit, a day when the students set the agenda.

Late last night, a Soviet spokesman quoted Gorbachev as telling Chinese party leader Zhao Ziyang that both their countries have hotheads—Gorbachev's word, "hotheads"—who want to change the course of socialism overnight.

In a moment, I'll be back with the rest of the day's news and then—

(Music and graphics for "The New Face of Communism")

—we continue our special series of reports on two Communist giants amid a revolution in the Communist world: Gorbachev, China and "The New Face of Communism."

(ANNOUNCEMENTS)""",
        "abstract_origin": "derived",
    },
    "https://danratherjournalist.org/sites/default/files/documents/e_zirin_00041_0.pdf": {
        "publisher": "CBS News",
        "published_on": "1989-05-15",
        "author": "Dan Rather",
        "title": "CBS EVENING NEWS WITH DAN RATHER",
        "page_title": "Document - CBS Evening News, May 15, 1989, Transcript | Dan Rather",
        "page_date_marker": "May 15, 1989",
        "pages": 3,
        "abstract": (
            "据正文整理：CBS Evening News 报道戈尔巴乔夫访华期间的天安门广场学生示威、"
            "中苏会晤以及学生和教师对抗议诉求的说明。"
        ),
        "keywords": "China; Tiananmen Square; Mikhail Gorbachev; student demonstrations; CBS News",
        "pdf_sha256": "1e8e12e738641d48b239c7596ac69a3e59f4437b6b5da96de20e467a6361add8",
        "body": """(Band playing Soviet anthem at arrival of Mikhail Gorbachev in China)

DAN RATHER: Gorbachev comes to China seeking to heal old wounds and neutralize America's strategic advantage in Asia. (students chanting) He is upstaged by striking students seeking to change the face of Communism.

(Music Theme)

RATHER: This is the CBS EVENING NEWS, Dan Rather reporting tonight from Tiananmen Gate in Beijing, China. Good evening.

This is where, 40 years ago, Mao Zedong stepped into the place previously reserved for emperors handing down their edicts and proclaimed the triumph of his Communist revolution. Tiananmen Square is the heart of China. This is where most of the major confrontations of modern Chinese history have taken place, including the mass student demonstrations for democracy. Today, it is also the site of the first Soviet-Chinese summit in 30 years-the leaders of two huge nations groping with the realization that Communism as they and we have known it hasn't worked and with the question(s): \"What next? What now? Can Communism change enough fast enough to survive?\"

It was a watershed in the history of the world Communist movement, the reconciliation of the two Communist giants, the first Chinese-Soviet summit since 1959. (band music) But, right from the start, it was overshadowed by events within China. At the last minute, Chinese leaders cut back welcoming ceremonies to quick hellos at the airport only, canceling plans for longer ones that were to have included a stop at Tiananmen Square downtown. (students chanting) They did that to avoid confrontation with thousands of hunger-striking students and more than 100,000 supporters, all pressing demands for a more democratic government and more freedom; and so Gorbachev accepted the stiff greetings of Chinese Communist leaders on the airport tarmac, while those same leaders were being denounced in the square.

Getting to the center of the square means passing through an ocean of students, bicycles, banners, loud speakers, slogan-chanting, singing and applause. The mood is serious but not angry. Determination, not rage, is on the faces and in the voices. They defied a government order to be out of the square by the time Gorbachev arrived, and no one seemed afraid.

FEMALE STUDENT: Why should people (be) 'flaid?

RATHER: And you-

FEMALE STUDENT: I'm just a common student.

RATHER: Their numbers, their solidarity and the cause protected them against a crackdown.

MALE STUDENT: The government-they are not and cannot make that decision to crack down on the students.

MALE STUDENT: (Indistinct crosstalk) We have people behind us.

RATHER: Police were around in force; but, instead of breaking up the crowds, they broke into patriotic song, and the students sang back. (soldiers singing; students chanting) This is the Monument to Heroes in the middle of Tiananmen Square. Raisa and Mikhail Gorbachev were, according to the original schedule, supposed to lay a wreath here tomorrow. It isn't going to happen.

(Music at banquet)

RATNER: At a banquet tonight, Gorbachev delivered his summit theme. The feud between Chinese and Soviet Communists is over, he said, admitting that Moscow was partly to blame for the old troubles. Underscoring the shakiness of China's party leadership, 84-year-old Deng Xiaoping was not even there tonight. He didn't see Gorbachev during the day, either. He'll meet him tomorrow, it is said. The fill-in host, President Yang Shangkun, was non-committal, noting that Chinese-Soviet relations have traveled a \"tortuous course\". \"Today,\" he said, \"we have hope for a new future,\" hope that was echoed in Tiananmen Square by a young hunger striker for democracy. (hunger striker speaks in Chinese) He says, \"I'm touched, because my teachers and the principal of my school have come out to support the protest. This means all our pain and difficulties are not in vain. We're going to stick to it right to the end.\" What the end will be, and when it will come, no one even tries to guess.

I'll be back in a moment with the other news of the day and then:

(Oriental music)

RATHER: We begin our special series of reports on two Communist giants amid a revolution in the Communist world-Gorbachev, China and \"The New Face of Communism\".

(ANNOUNCEMENTS)

People in Tiananmen Square talk with a CBS cameraman about the movement, the government's response to the protesters and the breakdown of the May 14 talks between the two parties:

\"Will you continue to protest while Gorbachev is here?\"

One student answers: \"We want the whole world to know the strong will of the student(s).\"

One young teacher responds to cameraman:

\"We want the whole world to know the strong will of the students for democracy and liberty.\"

\"Of course the government is being embarrassed by the students.\"

\"(Talks broke down) because many questions are difficult for (the leaders) to reply to. I think their abilities are being doubted by the students...(That talks broke down was) the government's fault, not the students. Government refused to broadcast talks nationwide or recognize the movement as legal...\"

He also states that the student representatives to the talks broke down in tears at this outcome.

On student demands this teacher responds:

\"First of all we want the government to admit that our movement is right.\"

\"We want to have an equal talk between the government and students, but they don't agree...(The demonstrations are going on) not just because Gorbachev is here. We are not just influenced by him, but by the situation of our country. We want to have the freedom of news and democracy...all around democracy. I believe we can achieve that....I deeply hope the Americans will understand us, understand what we are doing here, and help us.\"""" ,
        "body_sha256": "8c34955ddfda874fe81c0acabc8c76fff176889b041dfb0148f15edee65fc52c",
    },
}


# Scan-based issue PDFs require a manually transcribed reviewed_body.
FRIENDS_JOURNAL_REVIEWED_ARTICLES: dict[str, dict[str, object]] = {
    "https://friendsjournal.s3.us-east-1.amazonaws.com/friendsjournal/wp-content/uploads/emember/downloads/1971/HC12-50499.pdf": {
        "publisher": "Friends Journal",
        "published_on": "1971-05-15",
        "author": "Colin W. Bell",
        "title": "China and the United States",
        "pages": [10, 11],
        "body_start": "IT IS AGAIN POSSIBLE",
        "body_end": "Happy New Year",
        "pdf_sha256": "a54699f30d8ff17ba6926f146d094da0e6c6338303cb13b1a73bf4c5a858fd3e",
        "body_sha256": "f12bdf10227bab606eba339488b2ea775eba68e88a2d23ee17c5e1d86d217d1d",
        "reviewed_body": (
            "IT IS AGAIN POSSIBLE to talk about the Chinese quarter of mankind as people with whom, someday, Americans might be on good terms. Not that as a nation we now say that Yellow is Beautiful (except perhaps Japan yellow), but we have moved some way from such things as invoking the China bogey as a nuclear threat to justify antimissile expenditures.\n\n"
            "An eminent Japanese Sinologist asserts (\"and I am very optimistic . . .\") that over the coming years Americans can expect changes for the better in relations with Peking; that Peking's attitude is growing more flexible and more concerned with national construction and national interests than sheer ideology; and that Americans anxious to see better relations can help best now by educating and influencing public opinion.\n\n"
            "I believe our Quaker agencies must promote recognition of one great fact of today: That the Western world is no longer necessarily the center of the historic stage. We whites have become inured to the idea that history happens around us, but East Asia is now the point on the globe where four great powers stare eyeball to eyeball - China, Japan, and the Soviet Union are there by geography and the United States by design. The relations of each to the others will become increasingly complex over the next decades.\n\n"
            "Caucasian man must take a new view of his role in world affairs. Americans in particular must focus on people and places whose reality has never yet come alive. Preeminently this is true concerning the Chinese. People of the West have had difficulty in relating to Asians in terms of real, human equality, even when we were busy saving their souls.\n\n"
            "Against this background, people need to know what is currently stirring about China. Some recent United States initiatives toward detente were too trivial to evoke Chinese response, but they did reveal something of a new American mind-set. \"Normalization\" of trade, social, and cultural relations, however, cannot progress significantly until the two central stumbling blocks are removed - the political future of Taiwan and the related question of Peking and the United Nations.\n\n"
            "These two issues are now the subjects of intense debate in governmental and other circles. All sorts of private meetings are being held. Perhaps the most interesting recent development is the number of legislators who have taken initiatives to move forward the American policy toward China. Senator McGovern took a bold step \"to dispel the fog and myth which have for the last twenty years befuddled our attitudes and actions toward mainland China.\" His speech in January at the University of the Pacific is an almost unexceptionable generalized call for a new China attitude and policy.\n\n"
            "More specific are two \"sense of the Senate\" resolutions, which are as significant for their appearance as for their content.\n\n"
            "Senator Gravel's resolution proposes that the United States inform the People's Republic of China and the Republic of China that it is not committed to indefinite separation of Taiwan from mainland China, shares the expressed interest of both in eventual reunification, and proposes the People's Republic of China and the Republic of China seek to reach a settlement themselves. It proposes also that the United States introduce at the United Nations a proposal that the People's Republic of China become a member of the United Nations and that the United States would not seek to oppose a United Nations determination concerning the occupancy of the China seat in the Security Council.\n\n"
            "The other resolution is known as the Javits Resolution, although it is cosponsored by Senators Case, Hart, Hughes, Inouye, Kennedy, Mondale, Stevenson, Symington, and Williams. It calls for the United States to cease opposing admission of the People's Republic of China to the United Nations while not accepting expulsion of the Republic of China as a condition of such membership.\n\n"
            "An interesting commentary on this resolution came from the Quaker-sponsored Geneva Conference, at which a group of China and United Nations experts from fifteen nations discussed the issue of China and the United Nations. The arguments there caused our own Quaker participants to change their viewpoints to the belief that the worst thing that could happen would be for the Javits Resolution to stimulate the United States to sponsor a \"Two-Seat\" resolution at the United Nations. Opinion was expressed that such an American move might well put the whole issue into another long deadlock.\n\n"
            "Let me make three further points, because they come up constantly in discussions about China.\n\n"
            "Much play is made regarding our solemn obligations to Chiang Kai-shek. Having lived under Nationalist China myself, my view is that we have long ago discharged any obligation we ever had to that group. But there is a treaty! Treaties become sacred when it suits nations to ride a high moral horse, less so at other times. Here is one such case. This treaty does contain a provision for orderly and proper termination, however. Article X states: \"Either party may terminate it one year after notice has been given to the other party.\" It is quite false to imply that there is no decent and honorable way of bringing the treaty to an end.\n\n"
            "The second point is the matter of other influences upon American public opinion about China at this time. The Committee of One Million is stirring and has announced a \"dramatic eye-witness television documentary, entitled 'Red China: Myths and Realities,'\" to be presented nationwide on educational and commercial television this fall prior to the United Nations admission vote. The Committee \"intends to use every possible means . . . to preserve one of the most successful foreign policies of the United States over the last twenty years . . . .\"\n\n"
            "The final point is the most important. Most of us feel that our present and basic effort must be to stop the Indochina War. Amen! The enormous and pervasive long-term issue of United States-China relations looms behind and beyond that war, however. One horrendous possibility is that United States action in North Vietnam or Laos may provoke an Indochina \"Yalu\" situation, although having lived and worked in Yunnan I believe the Chinese would be extremely reluctant to fight from this distance.\n\n"
            "Senator Goldwater, in a speech in the Senate December 13, 1970, described China as a \"rogue nation.\" If this view were to become United States policy, the end of the war would not mark the end of our \"guardian\" role of the prostrate little countries of Indochina, not to mention Thailand and potentially Burma. The era of bitter and dangerous United States-China relations would continue. If, on the other hand, American actions in Indochina and in other directions advance, rather than prevent, the gradual restoration of reasonable Sino-American relations, the history of the next decades could be profoundly affected for the better. Let us hope the \"table-tennis detente\" is a good augury!"
        ),
        "abstract": (
            "据正文整理：文章讨论美国社会对中国的认识变化、台湾与中国在联合国席位问题，"
            "以及美国公共舆论和政策辩论对中美关系走向的影响。"
        ),
        "keywords": "China; United States; Taiwan; United Nations; American public opinion; television documentary",
    },
}


# Public newspaper scan reviewed visually against the article column. The PDF's
# OCR layer has character errors, so the body transcript is retained separately
# and accepted only when the exact PDF hash and reviewed body hash both match.
DAILY_IOWAN_REVIEWED_ARTICLES: dict[str, dict[str, object]] = {
    "https://dailyiowan.lib.uiowa.edu/DI/1950/di1950-04-08.pdf": {
        "publisher": "The Daily Iowan",
        "published_on": "1950-04-08",
        "author": "Associated Press",
        "title": "AP Chiefs Declare Further Obstacles Block News Reports",
        "pages": [6],
        "body_start": "NEW YORK (AP)",
        "body_end": "Expecting Insurance Check, Gets Surprise",
        "boundary_start": "NEW YORK (JP)",
        "boundary_end": "Expecting Insdrance",
        "column": {"x_min": 525, "x_max": 675, "y_min": 880, "y_max": 1530},
        "pdf_sha256": "5ac77c5c7c47254b34346e7f84b0b4175c96a9752a7b85f3f3daf11b0d848994",
        "body_sha256": "44cd33ef70e4a2c2d67737906e4f073ea71e5f4e348ad83ab4b79503b8db2b32",
        "reviewed_body": (
            "NEW YORK (AP) — Further barriers to free, objective news coverage were erected in many countries during the past year, The Associated Press management said Friday.\n\n"
            "Despite the new obstacles, Associated Press men succeeded in telling the essentials of the news. Executive Director Kent Cooper and General Manager Frank J. Starzel said in their annual report.\n\n"
            "“We expect, of course, to persist in efforts to keep open the channels of news available to us, and to reopen those now closed,” the report said. “We expect to pursue the battle for freedom of news with all diligence. But it must be said that is is impossible from this point to see much light ahead; there is little prospect that our job will become easier in the months to come.”\n\n"
            "The report was distributed to Associated Press members in advance of the worldwide news gathering cooperative’s annual membership meeting in New York April 24.\n\n"
            "“The world made little progress toward peace and understanding among nations in 1949,” the report said. “Correspondingly, the path of free, objective news coverage did not become smoother.\n\n"
            "“As the areas of political conflict broadened, so the areas of mistrust of unhampered reporting broadened. The spread of Communist domination brought a corresponding spread in the territories which barred free journalistic endeavor.”\n\n"
            "Censorship restrictions were stiffened, the report said, and new barriers, notably in China and Eastern Europe, were erected to keep reporters from gaining access to news.\n\n"
            "There were evidences of additional harrassment even in the western world, the report said, adding that the trend was toward “official secrecy, off-the-record confidences, anonymous statements.”\n\n"
            "A heavy strain was put on The Associated Press distribution of news abroad because of “mounting costs and the march of communism.” The AP serves more than 1,200 newspapers and radio stations in 67 foreign countries."
        ),
        "abstract": (
            "据正文整理：文章转述美联社管理层关于1949年国际新闻报道环境的年度报告，"
            "涉及中国和东欧的新闻获取障碍、审查限制、新闻自由与海外发行压力。"
        ),
        "keywords": "Associated Press; China; censorship; news freedom; international reporting",
    },
    "https://dailyiowan.lib.uiowa.edu/DI/1971/di1971-07-22.pdf": {
        "publisher": "The Daily Iowan",
        "published_on": "1971-07-22",
        "author": "William L. Ryan",
        "title": "New 'Revolution' In China Seen",
        "pages": [2],
        "body_start": "Something like a cultural counter-revolution",
        "body_end": "CAMPUS SPECIAL!",
        "pdf_sha256": "9ef14963f72bd3c8d50f1becb0173c2825056082ff5f984ccda90ee81b8fd5dc",
        "body_sha256": "3759695fada3a0b3e1b72a4e2e7da4835bb8fbfabdea7ed3763ae0ef5cff660c",
        "reviewed_body": (
            "Something like a cultural counter-revolution may be going on in Red China.\n\n"
            "In all likelihood complex factors lay behind the announcement that Premier Chou En-lai intends to welcome President Nixon to Peking.\n\n"
            "These lines of speculation suggest themselves:\n\n"
            "• If Chou ultimately goes through with it, and the odds seem to favor that, it will be a clear signal that the Red Chinese leaders feel they have little fear any more from the country they have long nervously dubbed 'paper tiger.'\n\n"
            "• A big accumulation of internal political and economic problems piled up by the Great Proletarian Cultural Revolution of 1966-69 has forced the leaders toward moderation and policies which look more rational to the outside world.\n\n"
            "• Mao Tse-tung, at 77, may consider the major objectives of the cultural revolution achieved, now that his 'thoughts' are supreme law. Some of those who were his most trusted servitors in mounting the violence, including his wife Chiang Ching, seem to have been thrust into the shadows, possibly even with Mao's consent, now that their usefulness is ended.\n\n"
            "• Bureaucratic elements responsible for the nation's administration have recovered their balance. The structures of party and government had been all but destroyed, but new structures are being built.\n\n"
            "• Red China has a perplexing array of foreign policy problems, made more worrisome by the presence on the borders of Soviet troops who are less than friendly. This would dictate an approach to the West less bellicose than had been pushed by the exponents of armed revolutionary violence.\n\n"
            "Even while the cultural revolution was at its height, Red China's scientists had pushed ahead with the nuclear program. Now China is a nuclear power, even though its atomic forces are puny in comparison with Russia's or America's.\n\n"
            "Chou En-lai has stressed that China does not aspire to be a superpower. He thus identifies China with weaker nations, the champion of the bulk of the world's population against potential bullies. In a sense this could be read as an attempt to keep one superpower - the Soviet Union - at bay.\n\n"
            "Russia is thrusting aggressively into the Indian Ocean and showing the flag in a strikingly Victorian-style display of big power imperialism. China might feel safer if she were on speaking terms with the other superpower."
        ),
        "abstract": (
            "据正文整理：文章围绕尼克松访华计划讨论中国国内政治变化、对苏关系、核力量和中国在国际体系中的定位。"
        ),
        "keywords": "China; Nixon visit; Cultural Revolution; Soviet Union; foreign policy",
    },
    "https://dailyiowan.lib.uiowa.edu/DI/1950/di1950-09-22.pdf": {
        "publisher": "The Daily Iowan",
        "published_on": "1950-09-22",
        "author": "Sigrid Arne",
        "title": "Red China's Link With Moscow",
        "pages": [2],
        "body_start": "WASHINGTON (IP)",
        "body_end": "Wisconsin Raises Rates",
        "pdf_sha256": "d39c83a6fbe85d7aa1e4b9c1da7035805dff889237dabd0189ee10b0b8015022",
        "body_sha256": "76200f37d12ab9d5661b4ba12e9730e73324373995e41e6415c18cd7ae8763b3",
        "reviewed_body": (
            "WASHINGTON (IP) — Experts on the Far East acknowledge there are two unhappy channels through which the Korean fighting might spread to Red China:\n\n"
            "1. Through Chinese Communist troops' going into Korea.\n\n"
            "2. Through Formosa, which the Chinese Communists have said they will take, and which President Truman has said the U.S. will protect.\n\n"
            "So the leader of Red China, Mao Tse Tung, is watched for every move and word.\n\n"
            "State department experts say the main question is this: Will Mao conduct Chinese communism for the good of China alone, or will he sacrifice Chinese needs at the command of Moscow?\n\n"
            "Some American commentators hope that Moscow and Peking will finally tangle over Manchuria and the northwest Chinese provinces. But state department experts say that if Mao leans in any direction it's towards Moscow.\n\n"
            "The Chinese Reds have asked that Formosa be discussed in the UN. Is Mao acting as a purely Chinese leader? Or is he jumping as a Communist puppet?\n\n"
            "To these questions state department experts put forward these facts:\n\n"
            "The Chinese Reds want to represent their country in the UN. But the UN charter pledges its members to seek peaceful negotiation rather than war. Knowing the UN pledge, will the Chinese Reds abide by negotiations on Formosa and give up their threat to attack?\n\n"
            "In June, 1949, Mao had followed the rest of the world's Communist leaders with a statement that China would go to war on the Soviet side, if Russia became involved in a war.\n\n"
            "When Yugoslavia, a Communist government in bad standing with Moscow, made a move to recognize Red China, Mao ignored the Yugoslavs.\n\n"
            "A few days ago Pravda, Moscow's most authoritative newspaper, carried a story about 50 incidents of British planes flying over Chinese lands, from June 1 on, in the neighborhood of Hong Kong."
        ),
        "abstract": "据正文整理：文章讨论朝鲜战争可能扩大的路径、台湾问题、中国在联合国的席位，以及毛泽东对苏联和莫斯科的关系。",
        "keywords": "China; Korean War; Formosa; Mao Tse Tung; Soviet Union; United Nations; U.S. public discourse",
    },
    "https://dailyiowan.lib.uiowa.edu/DI/1955/di1955-07-30.pdf": {
        "publisher": "The Daily Iowan",
        "published_on": "1955-07-30",
        "author": "未注明",
        "title": "Recognition of Red China—",
        "pages": [2],
        "body_start": "The foreign ministers conference in Geneva next Monday",
        "body_end": "GENERAL NOTICES",
        "pdf_sha256": "0536f5132a04e7ac9a75e0198c95efc4bad25d60dff4b57f4f5d17373c69300a",
        "body_sha256": "d6c1209eed698f4a8e4c7d29fff425f9721daebbc137589dd2bd1dc51e0579a1",
        "reviewed_body": (
            "The foreign ministers conference in Geneva next Monday will find the United States negotiating with the representatives of Communist China over the question of a possible cease-fire in the Formosa Straits.\n\n"
            "Our negotiations with the Peiping regime will not constitute in any way any recognition of the Communist Chinese government, Secretary of State John Foster Dulles carefully pointed out in a news conference earlier this week.\n\n"
            "It is rather difficult for us to see how we can say that we are going to negotiate with a government that we do not officially recognize as in existence.\n\n"
            "It seems to us that the United States ought to reconsider its policy of refusing to recognize the Peiping government. Chiang Kai-shek is in reality only the leader of the Chinese Nationalists who are concentrated on Formosa and a few of the surrounding islands. It is quite certain that he cannot speak for the mainland of China. If he does claim to do so, he cannot enforce any agreements which he might make involving the Chinese mainland.\n\n"
            "In fact Mao Tse-tung and his Communist cohorts maintain practical control of the Chinese mainland. The United States has had many dealings with this government but always there is the necessity of going through the diplomatic channels of the embassies of nations that have recognized the Chinese Communists.\n\n"
            "The argument is often advanced that if we were to recognize Peiping, we would be selling the Nationalists \"down the river.\" So we continue to ignore diplomatically the most powerful nation in the Far East.\n\n"
            "If we were to recognize the Communist government we would not have to turn our backs on the Nationalists. We could continue to support them and prevent the Communists from driving them from Formosa. It seems very evident that without U.S. support, Chiang is not going to successfully return to the mainland. And that support the U.S. has refused to give.\n\n"
            "England was one of the first nations to admit that - legally or not - Mao's government was in control of the Chinese mainland. On the basis of that fact, England recognized the new government.\n\n"
            "We think that it is time the U.S. made a similar decision. We cannot continue to ignore this powerful Communist nation merely because we do not approve of the methods used by the regime in power. It is time that we dealt with facts."
        ),
        "abstract": "据正文整理：社论以日内瓦谈判和台湾海峡停火问题为背景，讨论美国是否承认中华人民共和国政府及其对台湾国民党政府的支持。",
        "keywords": "China; U.S. recognition; Formosa Strait; Chiang Kai-shek; Mao Tse-tung; editorial",
    },
}
