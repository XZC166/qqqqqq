# Research Crawler

本项目为学位论文“美国对华舆论传播与话语竞争的历史演变（1949—2025）”生成检索计划、采集允许公开访问的原始页面、保存来源证据、核验全文并导出资料表。

## 最新口径：复核合格正式表（2026-11-09）

正式 Excel 当前仅含 **873 条**来源与逐篇主题审核共同通过的唯一全文，四时期为 **320、185、133、235**，其中 1949—1991 年 505 条。1972 年归第一段，第二段从 1973 年开始。源库 materials 表是采集工作池；旧日志中的 verified 或材料数量不等于当前正式全文数。

本轮逐条来源检查覆盖启动时全部 6,149 条工作记录，4,964 条通过程序来源核验、1,185 条需继续处理；来源核验通过本身不授予主题批准。审核记录写入 quality_reviews，并绑定正文、全部导出字段与审核证据哈希。CLI export/deliver 默认只将当前复核合格记录写入正式 Excel；导出时重新核验，未审或过期审核不混入正式表。原始采集池、历史证据、操作前备份和 pending 均保留。

详见 [最新后续批次报告](docs/reports/2026-11-09-quality-followup-batch.md) 和 [逐年、来源、事件线索统计](docs/reports/2026-11-09-quality-followup-batch.json)；[此前 614 条快照](docs/reports/2026-11-09-quality-gate-batch.md) 保留。本地 data/materials.xlsx 与 ZIP 仅供授权范围内私人研究；不随 GitHub 公开提交。10,000 条仍是扩展目标，尚未达成；继续全库主题复核、早期资料补充和其余时期并行检索。

## 历史运行日志（以下为当时工作池及技术核验口径，不能作为当前正式数量）

截至 2026-11-09，本地材料表有 5,442 条唯一的正文与字段核验记录，摘要、关键词、正文和作者字段均非空。按发布日期统计：1949—1972 年 126 条、1973—1991 年 177 条、1992—2016 年 707 条、2017—2025 年 4,432 条。区间统计将 1972 年归入 1949—1972 段，后一段从 1973 年起。此数仍是主题审计中的工作池，不代表 5,442 条都已最终确认与论文直接相关；候选状态为 5,790 条 verified（含重复候选）、1,127 条 pending、117 条 restricted、2,956 条 excluded、50 条 candidate。覆盖矩阵及逐年数量见本地 `data/coverage-audit-20261109.json`；正式数量只按来源、日期、字段、全文和主题核验共同通过的唯一材料计算。

扩展目标调整为尽可能接近或超过 10,000 条正式核验全文；相对当前工作池的名义差额为 6,030 条，但在未完成主题审计前不把这个差额当作有效资料缺口。本次离线重验从本地证据中晋级 199 条 pending 候选；随后逐条做题名、来源和正文主题筛查，仅保留 26 条直接涉及媒体、舆论、宣传、信息操作、公共外交、中国形象、台港议题或已核验机构社交帖的记录，173 条明显偏离论文主题或已撤稿的记录退回 `excluded`，审计见 `data/reviews/revalidation-topic-screen-20261109.json`，数据库备份见 `data/research-pre-revalidation-topic-screen-20261109.sqlite3`。随后批量抓取 792 条 Bluesky 机构文字候选，2,166 个请求得到 1,296 个 HTTP 200 和 870 个 HTTP 429；502 条进入正式材料，111 条无直接中国/台港/北京等主题指向的帖子退回 `excluded`，776 条保留，审计见 `data/reviews/bluesky-post-topic-screen-20261109.json`，限流条目保留 pending。最新一批扩展到 Foreign Affairs 与 Chatham House，685 条候选经 1,190 个 HTTP 200 与 546 个 HTTP 429 处理，503 条通过技术核验，按正文主题筛选后保留 428 条、撤回 75 条，182 条仍 pending，审计见 `data/reviews/bluesky-new-institutions-topic-screen-20261109.json`；Reuters 与 CNN 公开时间线本批未追溯到 2025 年，未产生正式记录。PMC 扩展检索继续覆盖 2017—2025 年更早结果页：2,000 条候选批次保留 4 条、排除 1 条，1,476 条候选后续批次的 16 条全文队列又保留 4 条，审计见 `data/reviews/pmc-targeted-start2000-topic-screen-20261109.json` 和 `data/reviews/pmc-targeted-start4000-topic-screen-20261109.json`；前一页批次保留 2 条，审计见 `data/reviews/pmc-targeted-topic-screen-20261109.json`。当前正式材料按来源类别为 research_literature 2,180、government 388、new_media 1,240、media 120、think_tank 42。视频帖在发现阶段跳过，不抓视频内容，也不把视频摘要当作全文；数量目标不改变合法访问、来源对应、全文完整或主题相关要求。

逐年审计显示，1949—1972 段没有正式记录的年份为 1957、1959、1963、1968、1970；1973—1991 段没有正式记录的年份为 1973、1974、1976、1977、1982、1983、1986；1992—2016 段没有正式记录的年份为 1995、2002。按来源类别的覆盖审计仍有两个无核验全文单元：1949—1972 年智库（3 个候选）和 1972—1991 年研究文献（10 个候选）。早期媒体档案、政府/国会材料、VOA、FRUS 与智库/研究材料仍需按可访问性逐项检查；早期总量仍偏少，需继续扩展，不用人为拉平数量替代实质覆盖。

本轮新增 Foreign Policy 官方 Bluesky 文字帖 321 条，原帖和平台 API 全部完成技术核验；正文主题筛选保留 257 条、撤回 64 条，审计见 `data/reviews/bluesky-additional-media-topic-screen-20261109.json`。当前正式材料按来源类别为 research_literature 2,180、government 388、new_media 1,497、media 120、think_tank 42；10,000 条名义差额为 5,773 条。

本轮继续扩展到 Lawfare、Carnegie Endowment、Axios、USIP 和 Wilson Center 等公开 Bluesky 账号，发现 211 条候选，210 条技术核验通过，1 条 pending；正文主题筛选保留 122 条、撤回 88 条，审计见 `data/reviews/bluesky-policy-media-topic-screen-20261109.json`。当前正式材料按来源类别为 research_literature 2,180、government 388、new_media 1,619、media 120、think_tank 42；10,000 条名义差额为 5,651 条。视频帖继续在发现阶段跳过。

随后扩展到 Human Rights Watch、Amnesty International、Just Security 和 Gallup，发现 149 条候选，148 条技术核验通过，1 条 pending；正文主题筛选保留 92 条、撤回 56 条，审计见 `data/reviews/bluesky-rights-polling-topic-screen-20261109.json`。当前正式材料按来源类别为 research_literature 2,180、government 388、new_media 1,711、media 120、think_tank 42；10,000 条名义差额为 5,559 条。

本轮扫描 American Presidency Project 早期索引 0—849 页，发现 105 条 1972—1991 候选；其中 79 条为已有链接，26 条进入抓取，18 条技术核验为新正文。逐篇主题筛选保留 17 条、撤回 1 条，新增记录均为 1972—1991 年总统/政府公开文本，审计见 `data/reviews/app-early-fast3-topic-screen-20261109.json`。该批没有发现新的 1949—1972 正式记录。

随后扫描 American Presidency Project 索引 1151—1512 页，发现 41 条 1949 年以前的历史页面；其中 40 条经来源页日期核验超出本研究范围，已标记 `excluded`，1 条为既有正式链接重复发现，未新增正式全文。审计见 `data/reviews/app-early-fast4-scope-screen-20261109.json`。该批没有把范围外材料计入早期正式数量。

本轮对 American Presidency Project `statements` 分类页 850—1150 的 40 个早期候选做了合规性和主题抽审。站点 `robots.txt` 规定 `Crawl-delay: 10`，此前抓取频率没有满足该要求；因此将 8 条已抓取材料全部撤出正式表，其中 2 条保留 pending 等待合规复抓，6 条因全文主题关联不足排除。正式数量没有净增。逐条审计和数据库备份见 `data/reviews/app-statements-crawl-delay-topic-audit-20261109.json`、`data/research-pre-app-crawl-delay-audit-20261109.sqlite3`。后续不继续高速请求该站分类页。

本轮回溯 CNN 官方 Bluesky 账号 25,000 条公开时间线帖，发现 745 条 2017—2025 年文字候选；Reuters 账号同量回溯最早仍为 2026 年，未产生研究期候选。CNN 候选中 744 条通过原帖/API 技术核验，随后按直接涉及中美关系、台港疆藏、对华政策、媒体/信息传播、网络与芯片竞争等正文信号筛查，保留 132 条正式全文，612 条明显属于体育、天气、医学、消费或其他非论文主题内容并标记 `excluded`，1 条受限。审计见 `data/reviews/bluesky-cnn-topic-screen-20261109.json`，候选清单为 `data/candidates-bluesky-reuters-cnn-backfill-20261109.csv`。视频帖在发现阶段跳过。

随后回溯 The Diplomat、NPR 和 Politico 的官方 Bluesky 文字时间线，发现 1,709 条候选；因平台对批量原帖请求返回 429，抓取在完成 1,408 条技术核验后停止，未完成条目保留 candidate/pending。逐条主题筛查保留 460 条正式全文，948 条泛新闻或与论文主题无直接关系的帖子标记 `excluded`；视频帖在发现阶段跳过。审计见 `data/reviews/bluesky-media-topic-screen-20261109.json`，候选清单为 `data/candidates-bluesky-media-backfill-20261109.csv`。

随后核验 Axios 和 U.S. Institute of Peace 的 327 条公开文字候选，289 条技术核验通过；主题筛查保留 55 条，其中 20 条是既有正式链接重复发现，净增 35 条，234 条偏题内容标记 `excluded`。视频帖在发现阶段跳过。审计见 `data/reviews/bluesky-axios-usip-topic-screen-20261109.json`，候选清单为 `data/candidates-bluesky-axios-usip-backfill-20261109.csv`、`data/candidates-bluesky-usip-backfill-20261109.csv`。

交付复核还修复了 1 条 Foreign Policy 帖子的空关键词：正文明确出现 Tibet，已补入 `Tibet`，并重新生成工作簿与 ZIP。

随后核验 Council on Foreign Relations 和 RAND 的 239 条公开文字候选，全部通过技术核验；主题筛查保留 111 条，128 条泛新闻或与论文主题无直接关系的帖子标记 `excluded`。视频帖在发现阶段跳过。审计见 `data/reviews/bluesky-cfr-rand-topic-screen-20261109.json`，候选清单为 `data/candidates-bluesky-cfr-rand-backfill-20261109.csv`。

The Diplomat 初次高并发抓取因 Bluesky 返回 HTTP 429，246 条仍为 candidate。随后用并发 4、单域并发 2、1 秒延迟和平台自动限流目标 1 的配置分五批重试，196 条得到 HTTP 200 并通过原帖/API 核验进入正式表，55 条继续保持 pending；未绕过限流或访问控制。审计见 `data/reviews/bluesky-diplomat-rate-limit-retry-20261109.json`。

交付前字段复核发现 The Diplomat 新增记录中有 5 条关键词为空；已回到同一平台正文逐条补入正文明确出现的关键词，并以正文 SHA-256 绑定审核。修复后工作簿九列空值为 0，审计见 `data/reviews/bluesky-diplomat-keyword-repair-20261109.json`。

为审计早期国会材料，本轮以 600 秒超时重新抓取 GovInfo 1966 年 Congressional Record PDF；原始文件 HTTP 200、55,334,014 字节完整返回，但其卷册/页码文件无法确认为具有独立发布日期和单篇正文的材料，仍保持 pending，不进入正式表。审计见 `data/reviews/govinfo-1966-congressional-record-long-download-20261109.json`。

本轮对 1949—1991 年 pending 链接做了 117 个唯一 URL 的合规复抓；116 个响应完成解析，未新增正式全文，GovInfo 的约 51 MB 国会卷册仍因无法界定为单篇正文而 pending。另检索 PMC 2017—2025 年第 6,000 位后 2,000 个开放候选，49 条进入人工复核，8 条通过技术全文门槛但均为医学、航天或其他非传播主题，已全部退回 `excluded`，审计见 `data/reviews/pmc-targeted-start6000-topic-screen-20261109.json`。本轮结果说明早期缺口不能靠宽泛检索词填充，后续继续优先公开政府档案、FRUS、VOA、国会单篇听证和可核验媒体正文。

质量审计发现 2025 年资料曾集中于 PMC，早期抽样及后续批抓均发现宽泛检索词造成的主题误收。139 条新增 PMC 全文经题名/摘要批筛后，1 条通过高相关筛查、105 条转 pending、33 条 excluded。另对跨时期开放候选清单执行 839 个唯一 URL 的合规重试：821 条目标请求进入抓取，Scrapy 记录 838 个 HTTP 200 响应、16 个 404、3 个 406、2 个 420、2 个 502 和 11 个连接/超时异常；GovInfo 两个约 50 MB 国会记录 PDF 未能在 180 秒内完成下载。抓取器核验成功不代表主题相关，本轮 669 条 PMC 候选的元数据筛查为 11 条高相关、287 条需人工复核、371 条题名/摘要未显示主题信号；重试材料中 90 条移至 pending、28 条移至 excluded。报告见本地 `data/reviews/open-retry-pmc-screening-20261109.json`。Social media 方面，当前共有 65 条 Bluesky 官方媒体、智库和研究机构账号文字帖正式记录。近期批次从 NYT Opinion 5,000 条公开时间线帖中筛选 29 条主题候选（28 条新增、1 条已存在），从 AP 14,000 条公开时间线帖中筛选 30 条主题候选（30 条新增）；59 条候选均经原帖页面与平台 `getPosts` API 交叉核验，候选报告见 `data/reviews/bluesky-official-institutions-20261109.json` 及 `data/reviews/bluesky-social-bulk-20261109.json`。摘要采用同篇正文首句摘取并标注“据正文整理”，关键词仅取正文明确出现的主题词。Bluesky 搜索 API 返回 403，未绕过；X 与 DVIDS 候选仍受访问限制。按用户最新要求跳过视频，不抓视频内容，也不把视频摘要当作全文；继续寻找可核验的公开文字帖和文字稿。社交候选清单留在 `data/candidates-bluesky-official-institutions-2025.csv`、`data/candidates-bluesky-nytopinion-2025-bulk.csv` 和 `data/candidates-bluesky-ap-2025-bulk.csv`；跨来源重试 CSV 和审计详情留在本地，以免未经许可再分发全文。

版权与再分发口径：GitHub 提交仅含采集器代码、候选清单和审计元数据，不提交原始全文。`data/materials.xlsx` 与 `data/delivery.zip` 是本地研究用私有副本，不代表已取得公开再分发许可；公开发布前必须逐项核对许可或授权。当前证据库没有统一、逐条的再分发许可字段，故这些全文包不得直接公开上传或作为公开数据集发布。

本批继续并行覆盖早期与 1991 年后来源，重试 Reagan 1984 年访华记者问答、1984 年全国广播稿及 1988 年贸易协议备忘录。记者问答原始页 HTTP 200，发布日期 1984-05-01、正文与同页元数据核验通过，新增 1 条正式全文；其摘要和关键词按正文整理并绑定正文 SHA-256。全国广播稿返回 HTTP 404，1988 年备忘录未能核实为完整正文，均保留 pending。候选清单见 `data/candidates-reagan-china-remarks-trade-1984-1988.csv`。

随后从 PMC E-utilities 为 1992—2016 与 2017—2025 年检索开放全文候选，分别发现 21 与 357 条。元数据筛选将前者全部留待人工复核，将后者 333 条留待人工复核、24 条送全文核验；全文抓取检查 5 条新抓材料后，仅保留 1 条直接比较《人民日报》和《纽约时报》疫苗传播的研究正式入表，2 条偏题记录排除、2 条相关性不足的记录转 pending。其余候选均只作为候选，不计入正式全文。本批也触发对旧 PMC 批次的范围审计：2025 年正式记录高度集中，且已有明显主题误收；后续批次必须先复核这些旧记录，再据逐年和来源类别覆盖缺口继续并行采集。

本批从 American Presidency Project 并行补入 1972—1991 年及 2017—2025 年资料：1984-04-27 Reagan 对华讲话、2024-11-16 拜习利马会晤通报，以及 2025-10-24、2025-10-31 两份特朗普对记者发言，四条来源页均 HTTP 200，正文和同页元数据核验通过，新增 4 条正式全文。重抓时发现四条均缺来源摘要和关键词，已按同页正文逐条整理并将派生摘要、关键词绑定各自正文 SHA-256；空字段复核为 0。批次候选及元数据审计见 `data/candidates-app-reagan-biden-trump-mixed-period-20261109.csv`、`tests/test_app_batch_reviewed.py`。全量测试 438 项通过，Scrapy 合约检查通过，Excel 与交付 ZIP 已刷新。

随后继续补查里根 1984 年访华沟通材料：中国中央电视台采访、北京美国侨民讲话、李先念欢迎晚宴祝酒词、上海宴会祝酒词 4 条新增正式全文，均有精确日期和完整原文；全国广播稿候选返回 HTTP 404，保留 pending。四条新记录的摘要和关键词按正文整理，并以 SHA-256 哈希绑定；正式表摘要、关键词、正文空值均为 0。候选清单见 `data/candidates-reagan-china-visit-1984-communications.csv`，元数据哈希检查见 `tests/test_app_batch_reviewed.py`。此批将 1972—1991 年累计正式全文增加至 59 条。

本次小批次同时补查 1972—1991 年与 2017—2025 年材料：抓取 4 个公开候选页，全部依法按 restricted 保留，新增正式全文 0 条。SAGE 的 1989 年期刊目录为相关研究条目列出 1989-06-01，但原始正文 HTTP 403；伯克利 Institute of East Asian Studies 的 1987 年书章全文链接也 HTTP 403，尽管内容可在公开索引中发现，未以索引或二级副本替代原文。国务院“United States Public Diplomacy in China”页面标注 December 1989，缺精确日；国务院 2023 年全球信息环境报告的候选本轮同样受限。已有 Iowa State 1984 年论文全文候选仍 pending：题名页可核作者和年份，但没有可验证的精确发布日期。批次候选清单为 `data/candidates-mixed-1989-public-diplomacy-2023-info-environment-20261109.csv`。此轮之后正式记录仍为 2,622 条，四时期分别为 95、54、723、1,750；后续继续按覆盖矩阵并行补早期与 1991 年后来源。

本轮继续平衡早期与 1991 年后覆盖：从 American Presidency Project 抓取并核验三份 1990—1991 年布什政府对华最惠国待遇公开材料，均有原始页面、精确发布日期和完整正文，正文整理摘要及关键词绑定正文 SHA-256 后新增 3 条。同期检索 Pew Research Center 2024、2025 年美国对华观感报告；2024 年页面及 2025 年页面的本轮响应未通过完整性检查，保留 pending，不用摘要代正文。2025 年该 URL 先前已有正式全文，本次重抓未改变原正式记录。Scrapy 请求遵守 robots.txt；当次 4 个页面抓取均 HTTP 200，另有 1 个已验证 URL 跳过。候选清单见 `data/candidates-bush-pew-mixed-period-20261109.csv`；三份总统档案的离线字段核验见 `tests/test_bush_china_metadata.py`。

紧接着的均衡批次从 Truman 与 Obama 总统档案检索原始公开材料：1950 年援助法签署声明、1950 年朝鲜战争记者会和 1951 年记者会各新增 1 条；2015 年习奥记者会与白宫国事访问声明各新增 1 条。五条页面均 HTTP 200，按来源发布日期分别归入 1949—1972 与 1992—2016；正文完整性和来源字段通过核验，正文整理摘要及关键词绑定各自正文 SHA-256。新增记录均已补足非空摘要和关键词。候选清单见 `data/candidates-early-truman-obama-xi-20261109.csv`，离线核验见 `tests/test_truman_china_metadata.py`。这批补足了早期朝鲜战争对华公开表述，同时纳入 2015 年材料，继续维持各时期并行覆盖。

下一批从 American Presidency Project 并行补充早期对华公开表述、建交及贸易话语。1955 年两份艾森豪威尔材料、1967 年约翰逊欢迎中华民国副总统严家淦讲话、1984 年里根在美中协议签署仪式上的讲话、1989 年布什关于学生示威的声明，以及 2018 年两份白宫对华公开声明共新增 7 条正式全文；页面原文、精确发布日期及正文哈希核对通过。另一份 2018 年代表团声明候选在两次抓取中均返回 HTTP 404，保留 pending。七条正文整理摘要和关键词均与正文 SHA-256 绑定；候选清单见 `data/candidates-eisenhower-johnson-reagan-bush-trump-20261109.csv`，离线核验见 `tests/test_eisenhower_trump_metadata.py`。

随后拓展至 2024—2025 年 AP 对华报道，包含 2025 年美中关税升级、关税措施说明与贸易休战，以及 2024 年台湾与美中外交报道。四个 AP 原始页面均返回 HTTP 403，记录为 restricted；没有改用搜索摘要、付费墙外镜像或其他媒体转载代替正文。该批正式全文新增 0 条，受限链接清单见 `data/candidates-ap-china-us-discourse-20261109.csv`。

早期 91 条候选的合规重试本身未新增正式全文；本次新增 2 条 1950 年总统原始文件，另 1 条 1951 年记者会因正文/元数据完整性核验未通过而 pending。Daily Iowan 历史报纸候选本轮也未新增唯一全文。118 条 2017—2025 PMC 候选中，38 条已核验链接被跳过，80 条重新抓取后曾有 54 条通过全文技术门槛；主题审计检查发现其中 37 条属于先前已逐篇排除的偏题记录，已撤出正式表。采集器现会持久尊重 `excluded` 状态，即使材料已从正式表移除或启用 `--refresh-verified`，也不会自动再次抓取。另两组 2017—2025 论题扩展检索通过正文核验新增 3 条；1992—2016 年的 13 条候选中 11 条进入人工复核，2 条排除；1973—1991 年该组检索无结果。GovInfo 约 51/55 MB 的国会记录卷册无法界定为单篇材料，仍未转正。另有 7 条杜鲁门图书馆记录从保存的原始 HTML 离线重解析，仅修正来源字段并保留原正文。仍需并行补查早期材料及 1991 年后的政府、媒体、智库和研究文献；最新覆盖明细见 `data/coverage-audit.json`。

本次均衡补查从 Brookings 官方页面重新核验两条 1991 年后的候选：1997 年《The United States and China: A New Framework》是已有材料的重复发现，重复计数增加 1；Jeffrey A. Bader 的《China’s Emergence and its Implications for the United States》页面显示发布日期为 2006-02-14，正文 20,614 字符，新增 1 条正式全文。两页和 robots.txt 均在允许访问下返回 HTTP 200。另复查 Truman Library 的 Voice of America 页面，因来源页没有可核实的精确发布日期，仍为 pending。另从 American Presidency Project 核验并新增 1950-07-19 Truman 国会咨文（33,377 字符）和 1950-08-27 致 Warren Austin 的信（4,659 字符）；1951-01-11 Truman Library 记者会仍 pending。最新覆盖报告有 20 个时期/来源格子、0 个缺候选格子、2 个适用且无已核实全文格子；早期补查继续与 1992 年后批次并行。材料表及 ZIP 已刷新。

后续检索补查 1973—1991 研究文献和 1992 年后的开放研究：2011 年 Taylor & Francis 原始期刊页返回 HTTP 403，标记 restricted；2021 年 Nature 原始期刊页返回 HTTP 406，正文及元数据未通过核验，保留 pending。Gallup 1972 年公众态度 PDF 已在此前记录为 restricted，没有重复请求。此轮只增加候选状态证据，没有增加正式全文；不以开放摘要或镜像检索片段代替正文。

批次 483—487 继续并行补查 2017—2025 年智库与政府来源：两篇 Brookings 正文分别为 2021 年美国公众对华态度和 2024 年中美全球观感比较，均逐项核对来源页、发布日期、作者、标题、摘要和完整正文，正式全文新增 2 条。两篇关键词按正文人工复核，并以正文 SHA-256 绑定；离线重解析同步修复既有记录的空关键词和验证快照。CSIS 页面只验证到摘要与报告下载入口，保留 pending；国务院两个来源页返回技术故障响应，保留 restricted。该批次没有用摘要或非原文替代全文。随后对政府和智库原始证据进行字段复核，补齐 20 条记录的正文摘要和关键词，并排除 1 条正文无关的记者会；该次复核报告为 `data/reviews/metadata-topic-review-20261109.json`。当前正式唯一全文总数为 2,578；早期补查与 1992 年后的媒体、政府和智库批次继续并行。批次 483—487 各自的核验报告及完整覆盖矩阵随交付包刷新。

批次 488—492 继续早期政府档案检索。Truman Library 的 1951 年基韦斯特记者会与解除麦克阿瑟职务声明，通过来源页日期、完整正文及正文 SHA-256 核验，新增 2 条；同一轮对 Pew Research Center 的 2024/2025 年报告章节修复了块式正文适配器，三篇页面由已保存的原始 HTML 离线核验后新增 3 条。FRUS 的三篇 1949 年页面均可访问且正文可抽取，但来源页没有独立显示精确发布日期；文内档案成文日期不能替代页面发布日期，因此三条仍 pending。检索遵守 robots.txt；FRUS 页面与 Truman 页面证据及离线复核报告均随交付包保留。正式表现有 2,583 条；四个时期的收集继续并行。

批次 493—496 从 Truman Library 与 Pew Research Center 并行补查早期政府文本和近现代公众态度材料。两篇 Pew 2023 年原始页面经适配器扩展后，从保存的 HTTP 200 原始 HTML 核对页面日期、标题、署名、摘要及全部正文文字块，新增 2 条正式全文；无文字图注的图表保留在原始 HTML 证据中，不以图表描述代替正文。两篇 Truman 1952 年页面虽返回 HTTP 200，但响应正文没有文章容器，仍为 pending。共发现 4 条候选，2 条 verified、2 条 pending、无重复；来源页抓取耗时约 15 秒。正式库增至 2,585 条，时期数量为 86、41、718、1,740。Scrapy 离线重验只晋级了这 2 条 Pew 材料，其他本地证据不足的记录继续 pending。

批次 497—500 沿 Pew 2023 年公开报告的章节目录扩展四篇来源页：国际行为、全球领先经济体、中国软实力、对习近平的信任。四页及 robots.txt 均 HTTP 200，抓取用时约 11 秒；逐页核对发布日期、作者、标题、摘要和完整文字正文后，4 条全部 verified。另复用已有 pending 的 chapter 1 原始 HTML 离线重验通过。该组共新增 5 条正式全文，四个图表页中的图片仅保留在原始 HTML 证据中，不以图像描述补写正文。正式库增至 2,590 条，四时期为 86、41、718、1,745；pending 候选仍有 591 条，早期补查继续并行。

批次 501—502 回到早期总统公开文本，新增 1951-01-18 Truman 记者会与 1955-01-29 Eisenhower 保卫福尔摩沙决议签署声明。American Presidency Project 两个来源页及 robots.txt 均 HTTP 200，正文分别为 14,790 和 782 字符。首次入库后字段审计发现这两条缺摘要和关键词；现已根据同页正文整理字段，以正文 SHA-256 绑定审核，并更新记录的验证快照。批次 2/2 verified；正式库增至 2,592 条，1949—1972 年增至 88 条。全库摘要、关键词和正文均无空值。

批次 503—504 并行补查早期及近现代官方文本。1964-10-16 Johnson 对中国首次核试验的声明来源页 HTTP 200，逐项核对发布日期、作者、标题及完整正文后 verified；另一个 1960 年艾森豪威尔讲话候选返回 HTTP 404，保留 pending。批次 505—509 从 American Presidency Project 补抓中美 PNTR、WTO 入会与 Section 301 贸易政策材料，2000、2001、2018 年五个原始页面及 robots.txt 均 HTTP 200，五条全部通过全文核验。两批共新增 6 条正式全文，正式库增至 2,598 条；四时期为 89、41、721、1,747。覆盖审计 20 格中 0 格缺候选、2 格暂无已核验全文。工作簿与交付包已刷新；早期补查继续与 1992 年后的媒体、政府、智库和研究来源并行。

本次字段完整性复核发现上述 6 条新总统档案页面没有发布者摘要，采集器初次入库时摘要和关键词留空。已从同页原始正文逐条整理摘要及关键词，以正文 SHA-256 绑定审核后重新抓取并更新验证快照；回归测试覆盖 6 条来源和字段。当前正式库摘要、关键词、正文空值均为 0。

批次 510—514 补查卡特政府对台行政命令、1979 年记者会、1984 年里根与赵紫阳国宴讲话及 Pew 2025 全球中国观感报告。行政命令、国宴讲话原页 HTTP 200，完整正文核验后新增 2 条；1979 年记者会为已有记录的重复发现。Pew 2025 网页与报告 PDF 均 HTTP 200；网页适配器新增对结构化 callout 区块的校验，保留图表以外的 8,198 字符原文，并由离线重验晋级 1 条。PDF 候选目前未能通过来源页配对及完整性核验，保持 pending；网页搜索片段未用于正文。该批净增 3 条，正式库增至 2,601 条，四时期为 89、43、721、1,748。覆盖矩阵仍有 2 个适用格暂无已核验全文，来源与时间分布仍需继续扩展。

批次 515—517 扩展 1972—1991 年美国总统公开文本，抓取 1984 年里根回答《远东经济评论》问题的书面答复，以及 1985 年欢迎李先念仪式讲话和国宴祝酒词。三个原始页及 robots.txt 均 HTTP 200；经正文、来源字段核验后全部 verified，新增摘要和关键词按正文整理并绑定正文哈希。正式库增至 2,604 条；四时期为 89、46、721、1,748，摘要、关键词和正文空值均为 0。继续补充早期来源，同时维持 1992—2025 年采集。

批次 518—521 再补查里根政府 1987—1988 年对华贸易及关系公开文本，包括最惠国待遇声明、贸易法豁免致国会信件、建交十周年白宫声明和续签双边贸易协定备忘录。四个原始页面及 robots.txt 均 HTTP 200；前 3 条核验通过，摘要与关键词按原文整理并以正文哈希绑定，新增 3 条。1988-12-19 贸易备忘录未通过现有正文/元数据完整性核验，保持 pending。正式库增至 2,607 条，四时期为 89、49、721、1,748；摘要、关键词和正文空值均为 0。

随后以 American Presidency Project 补查 1979—1989 年官方传播文本，新增 4 条正式全文：Carter 1979-01-01 对华新年贺词、1979-01-31 中美文化协定、Bush 1989-02-26 接受中国电视记者采访，以及 1989-06-20 对华制裁声明。四个原始页均返回 HTTP 200，Robots 允许；日期、作者、标题与完整正文均逐页核对。正式表已更新至 2,480 条，工作簿与交付包已刷新。

J-STAGE 1998 年中美关系论文的原始页返回 HTTP 200，显示准确出版日、作者、DOI 和公开 PDF 链接；页面本身只有摘要。Scrapy 遵守 robots.txt 请求 PDF 时被拒绝，PDF 候选为 restricted，期刊页候选保持 pending，未增加正式全文。新增的 J-STAGE PDF 适配器会把来源页元数据与 PDF 正文逐项匹配；两条合成测试通过。全套测试 309 passed，`scrapy check` 为 0 contracts、OK。该论文仍不属于已取得全文，当前材料表数量仍为 2,480。

### PMC 两阶段提速

提交后的批次 315—319 继续兼顾早期与近现代资料。对 1949—1991 年 91 条 pending 原始链接复抓，共收到 103 个 HTTP 响应（200: 93、302: 3、404: 5、420: 2），另有 26 次连接异常；91 条候选均仍未核实为完整单篇正文，正式全文净增 0。Truman Library 的三个 1950 年原始页中，1 页 HTTP 200、2 页 HTTP 503；HTTP 200 页正文首行日期是发布会发生日，页面没有可核实的发布日期，因此不转正。2021 年 Nature 与 2025 年 SAGE 开放研究候选各 1 条，来源页受限/未核实，正式全文净增 0。复抓详情见 `data/reviews/early-pending-refresh-20261108.json`；新候选批次 315—319 已进入数据库与交付包。随后 1998 年 Clinton 白宫旧模板页面离线重核新增 3 条正式全文，1994、1997、1998、2012 白宫来源批次新增 4 条；截至当前数据库总数更新至 2,446。

PMC 批量队列先用公开书目信息预筛题名，再让 Scrapy 请求留下的来源页；无书目信息的项目会保留待人工复核。预筛不形成正式资料，也不替代原文核验。示例：

```powershell
research-crawler discover-pmc --period 2017-2025 --retmax 500 --retstart 0 --output data/candidates-pmc-page.csv
research-crawler screen-pmc-candidates --csv data/candidates-pmc-page.csv --output data/candidates-pmc-screened.csv --review-output data/candidates-pmc-manual-review.csv --report data/reviews/pmc-screen-page.json
research-crawler crawl-candidates --csv data/candidates-pmc-screened.csv --db data/research.sqlite3 --evidence-dir data/evidence --fast --concurrency 24 --per-domain 2
```

本轮实测宽队列 777 个唯一候选耗时约 18 分钟，603 个 URL 实际进入请求；页面抓取后主题复核净增 4 条。针对 118 条 PMC 候选的元数据预筛耗时约 10 秒，34 条进入全文队列、10 条转人工复核、74 条排除；Scrapy 抓取用时约 11 秒、跳过 20 条已有正式全文，入库 9 条再经全文主题检查净增 3 条。FRUS 50 条页面约 54 秒可访问，但因页面只标示历史文件日期、无法核实精确发布日期，未转正。未来扩量应优先采用题名/摘要预筛、域名分组和失败重试队列；抓取响应数不等于正式记录数。

PMC 批次 271、307 本轮从开放全文索引发现 134 条候选，跳过 26 条已有已核全文的 URL，实际请求 108 个页面（加 robots.txt 共 109 个响应，全部 HTTP 200），耗时约 77 秒。自动晋级的 47 条全文经主题筛查后仅保留 5 条直接涉及中美媒体框架、公共外交或传播竞争的研究；另 42 条由于主题不直接相关而从正式表撤下，候选标记 excluded，原始抓取证据保留。正式库净增 5 条至 2,408 条。详细筛查记录见 `data/reviews/pmc-topic-screen-20261108.json`；批次 271 为 13 条 verified、40 条 excluded，批次 307 为 0 条 verified、2 条 excluded（批次中其他状态含先前积累候选）。

2026-11-08 收紧 PMC 标题检索式后新增发现 6 条中美媒体/话语研究候选，抓取 4 个原始页面并跳过 5 条已有全文身份（重复抓取时复核了 1 条 pending）；2 条首次核验全文入库，3 条既有全文的候选状态同步为 verified，1 条保持 pending。正式库净增 2 条至 2,410 条。候选清单见 `data/candidates-pmc-discourse-targeted-20261108.csv`，审计见 `data/reviews/pmc-targeted-discourse-20261108.json`。已修复 Clinton White House 旧档案中混合 UTF-8/Windows-1252 字节导致的替代字符问题，证据哈希仍基于原始响应字节。

批次 287 新增 The Daily Iowan 于 1969-02-05 刊载的 AP 报道 “China Seeks Concessions For Better U.S. Relations”。第 3 页扫描版显示完整两栏正文、标题、日期和 AP 电头；逐段人工核对转录后新增 1 条正式全文。整期 PDF 抓取和其他历史候选复核情况见 `data/reviews/daily-iowan-china-relations-ap-1969-20261108.json` 及批次报告 284—294；OCR 层仅用于交叉校对，没有直接作为正文。

批次 306 对 Daily Iowan 三期历史报纸 PDF 进行复查，含 robots.txt 共 4 个 HTTP 200 响应，下载 54.5 MB，用时约 40.8 秒。1950-09-22 与 1971-07-22 两篇已在正式库中，后者本次计入 1 次重复发现；1964-08-06 的目标 AP 报道仍未能从整期扫描中核实单篇完整正文，保持 pending。净增唯一正式全文 0 条，正式库仍为 2,403 条。审计见 `data/reviews/daily-iowan-early-ap-refetch-20261108.json`。候选抓取现默认跳过已有 verified 全文的 URL，`--refresh-verified` 可显式重新抓取；pending 与 restricted 仍可按后续批次复查。

新补来源线索批次 302—303：Wayne State University 2013 年博士论文研究 1963—1972 年中美接近过程中的美中媒体，但官方论文下载返回 HTTP 403；Minnesota Conservancy 2021 年新闻话语论文的记录页和原始 PDF 均返回 HTTP 403。两条按访问结果保留为 restricted，未使用搜索摘录或搜索索引中的 PDF 文字代替原始文件，也未增加正式全文。

为提速，已修复 Scrapy 2.13 pipeline 生命周期参数兼容问题，并用 48 路全局并发、每站点 3 路并发复跑 PMC 批次 261 的 300 个候选，耗时约 99 秒；批次累计为 91 条 verified、209 条 pending，本次正式库净增 3 条，表明应将后续时间用于新候选发现和 pending 定向复核，而非重复抓取已处理队列。保持 robots.txt 和逐条正文核验。更新后的正式资料表为 `data/materials.xlsx`，交付包为 `data/materials-delivery.zip`。

早期研究文献缺口补查批次 300、301：密歇根大学 Survey Research Center 的 1964 年公众意见报告 PDF 原链接返回 HTTP 403，列 restricted；ERIC 线索对应 PDF 返回 HTTP 200，但实际文件是 1992 年 300 页会议论文集，不是检索线索所称的 1983 年学位论文，且不能由该文件核实精确发布日期，维持 pending。两条均未进入正式资料表；当前审计与原始响应已包含在交付包中。

本轮提速采集从 Daily Iowan 历史报纸档案批量抓取 11 个日期的原始 PDF，约 209 MB，HTTP 抓取耗时约 61 秒；逐篇核验后仅 1955-07-30 社论 “Recognition of Red China—” 满足全文转正条件，批次 286 为 1 verified。其余 10 个整期报纸 PDF 仍为 pending，因为不能仅凭整期 OCR 文本或检索索引将单篇文章正文视作已核实。原件保存在 `data/evidence/`；候选与状态见批次报告 284—294、`data/candidates-daily-iowan-china-history-20261108.csv` 和 `data/candidates-daily-iowan-korea-taiwan-20261108.csv`。更新后的正式资料表为 `data/materials.xlsx`，交付包为 `data/materials-delivery.zip`。

批次 295—296 从美国之音公开站点抓取 8 篇天安门事件回顾及对华政策报道，robots.txt 和 8 个页面均返回 HTTP 200，抓取耗时 5.8 秒。按来源页所示发布日期和正文核验后 6 条 verified；另 2 条因正文与保存证据不匹配、或元数据/全文不完整而保持 pending。批次 295 的一篇 2017 年报道最初误分至 1992—2016，核对来源页发布日期后已改列 2017—2025 并离线重验。批次报告随交付包保存；候选清单见 `data/candidates-voa-tiananmen-discourse-20261108.csv`。FRUS 检索发现若干高度相关档案，但网页只显示历史文件日期而无可核验网页发布日期，因此没有加入正式资料或候选抓取批次。

批次 297 补充 7 篇 VOA 单篇报道，主题涉及中国审查、网络安全及美国驻华社交媒体外交。robots.txt 和 7 个页面均返回 HTTP 200，抓取耗时 6.7 秒；6 条 verified，1 条因正文/元数据不完整保持 pending。美国之音 295—297 批次共 15 个候选，12 条 verified、3 条 pending。候选清单见 `data/candidates-voa-china-cyber-censorship-diplomacy-20261108.csv`。

以下是积压候选复抓批次完成时的历史快照：本轮从数据库提取待处理唯一 URL 队列，按 12 路全局并发、每站点 2 路并发、遵守 robots.txt 和自动限速分五轮复查 3,238 次候选请求（跨轮重复是为补取 transient 失败和重新核验原始页面，不代表 3,238 条新增材料）。当时新增 284 条正式全文资料，唯一正式资料总数由 2,082 增至 2,367（含后来核验的 1971 年 Friends Journal 文章和 1981 年 John Glenn 国会发言）。各轮待处理队列分别为 827、684、614、569、544 个唯一 URL；Scrapy 每轮报告平均吞吐约 98—132 个候选响应/分钟。大量待处理状态是由于日期/元数据/正文完整性门槛未通过，不能按抓取响应数量视为全文。五轮结束时尚余 535 条 pending、89 条 restricted、1 条 candidate；其中 Air University PDF robots.txt 请求连接失败，GovInfo 46 MB 国会记录 PDF 多次出现传输损坏，均未越过核验门槛。Friends Journal 和 John Glenn 的正文逐字校订均保存来源 PDF、正文 SHA-256 与页码边界审计，分别见 `data/reviews/friends-journal-china-united-states-1971-20261107.json` 和 `data/reviews/china-factor-john-glenn-1981-20261108.json`。五轮结束时的覆盖矩阵见 `data/reviews/coverage-audit-20261108-pending-queue.json`。

交付前字段检查发现 4 条新入库记录缺来源摘要/关键词；利用同一 URL 的公开原文重新核验后，从匹配正文整理摘要与关键词，并绑定来源 URL 和正文 SHA-256。修复记录为 GovInfo 国会听证 1 条及 The American Presidency Project 3 条。正式表 2,367 条资料现在摘要、关键词和正文均无空值；证据保留在原始抓取记录中。

批次 369 补充 PBS NewsHour 2018 年中美贸易争端公开报道。5 个候选原始页及 robots.txt 均返回 HTTP 200；其中 “What are the ripple effects of a U.S.-China trade war?” 的 2018-07-06 来源页全文与 transcript 完整标记、元数据及正文 SHA-256 一致，新增 1 条 verified。另 4 个页面虽可抓取，但当前适配器未能核验完整正文或元数据，保持 pending，不以页面摘要替代全文。批次统计 5 candidate、1 verified、4 pending、0 restricted/duplicate/unprocessed；正式表由 2,480 增至 2,481 条。当前四个时期分别为 42、29、693、1,717 条；早期材料仍是明显缺口，后续继续补充，同时维持 1992—2025 的来源采集。候选和逐条状态见 SQLite 批次 369；本批测试全套 311 passed，`scrapy check` 为 0 contracts、OK。

批次 374—377 按“全时期并行”补充早期美国之音政策材料和 2023—2024 年信息传播材料。1950、1962、1969 年三篇 FRUS 页面均 HTTP 200 且正文区可读取，但原始网页适配器不能核实符合正式表规则的发布日期/字段对应，保持 pending。2023 年国务院 Global Engagement Center 报告的官方 PDF URL 被同站响应为 “Technical Difficulties” HTML，原记录已有 restricted 状态；未将浏览器解析文本或摘要充作 PDF 正文。PBS《Amanpour and Company》2024-08-09 页面含 281 个 transcript 段落，JSON-LD 日期、节目标题及完整正文哈希和结尾标记核验通过；新增 1 条 verified（正文 41,162 字符，作者未注明），详情见 `data/reviews/pbs-amanpour-chips-2024-20261108.json`。采集器新增对此版式的精确来源/全文核验和变更拒绝测试。正式表现为 2,482 条，四时期为 42、29、693、1,718；早期仍需持续扩展，1992 年后继续并行采集。

批次 378—384 继续同时覆盖早期总统公开传播和 1991 年后的公众态度研究。American Presidency Project 的 1950-01-05 Truman 记者会（19,281 字符）及 1960-06-18 Eisenhower 台北演说（8,973 字符）通过页面日期、署名、标题及正文核验，新增 2 条 verified；1958 年两条台湾海峡材料已在正式表中，分别记录重复发现 1 次和 2 次。Pew Research Center 的 2024、2025 三个中国观感/竞争章节页均为 HTTP 200，页面日期、作者与标题可见；但文章主体含图表/可视化，当前提取不能确认完整保留其内容，3 条均 pending，不用文字摘要替代。批次统计为 7 个 URL、2 条新增全文、2 次重复发现、3 条 pending；正式表增至 2,484 条，四时期为 44、29、693、1,718。资料表和批次状态见交付包及 SQLite 批次 378—384。

批次 385—389 通过 American Presidency Project 与白宫官方页面新增 5 条全文：1979-01-26 Carter 记者会（10,592 字符）、1980-09-17 中美协议签署发言（8,612 字符）、1998-06-27 Clinton—Jiang 记者会（29,847 字符）、1999-04-08 Clinton—Zhu 记者会（41,813 字符）及 2025-11-01 白宫经贸事实清单（5,398 字符）。五个来源页面和对应 robots.txt 均 HTTP 200；各页显示的发布日期、作者标注、标题与完整正文均通过来源适配器核验，5/5 verified。正式库增至 2,489 条，四时期分别为 44、31、695、1,719；政府原始文本仍是本轮增量主力，其他媒体与公众态度来源继续扩展。

批次 390—397 继续补充 1949—1991 年总统公开传播材料：1950 年 Truman 三场记者会、1960 年 Eisenhower 与 Chiang 的联合声明及 Eisenhower 离台讲话、1975 年 Ford 与 Deng 小平国宴敬酒词、1991 年 Bush 面向外国记者的记者会，共新增 7 条 verified；每个新请求均 HTTP 200，页面元数据和完整正文通过 APP 适配器核验。另 1994 年 Clinton 对华人权记者会已存在于正式表，重复计数增加 1、没有新建记录。批次 390—397 共 8 个 URL，7 条新增全文、1 条重复；数据库增至 2,496 条，四时期分别为 49、33、695、1,719。早期政府原始材料继续增加，1992 年后的来源并行补充。

批次 398—402 并行补查早期与 1991 年后媒体原始材料。两篇 Guardian 1989 年社论、ABC《The World Today》2014 年 Tiananmen 纪念报道、ABC Four Corners 2019 年《Tremble and Obey》均从公开原始页取得完整正文，逐篇核对题名、来源页发布日期、署名及段落正文 SHA-256 后新增 4 条 verified。五个候选 URL 中另有一条把 Guardian 原文路径误写为 `/commentisfree/`，返回 404，保留 pending；正确的 `/world/` 页面已另行核验并正式收录。批次 verified 4、pending 1、重复 0；正式唯一全文增至 2,500 条，按发布日期四时期分别为 49、35、696、1,720。批次 398—402 的状态见 SQLite 和交付包；覆盖矩阵仍有 2 个适用单元没有 verified 全文。早期补查与 1992—2025 年媒体、政府、智库及研究材料继续并行。

批次 403—410 从 Guardian 官方原始页继续扩展 Tiananmen 相关采样：1 篇 2014 年回顾档案文章、3 篇 1999 年现场/回顾报道、1 篇 2001 年 Tiananmen Papers 报道、1 篇 2005 年评论，以及 2 篇 2019 年报道，共 8 个 URL、8/8 verified、0 重复。正文逐段提取后固定段落数、长度与 SHA-256；书籍推广、作者邮箱/简介、相关链接及 archive 尾注没有混入正文。2014 档案文章虽然回顾 1989 年事件，来源页发布日期为 2014-05-31，因此按来源日期计入 1992—2016。正式唯一全文增至 2,508 条，四时期为 49、35、702、1,722；覆盖矩阵仍有 2 个适用格子无 verified 全文。此次抓取 8 个页面均 HTTP 200，Scrapy 约 80 页/分钟，遵守 robots.txt 和每域并发限制。

批次 411—420 转向 TIME Vault 补充早期媒体原始报道。TIME 官方档案的 10 个页面覆盖 1949 年国共内战与新政权建立、1954 年台湾报道、1958 年金门炮战，以及 1972 年尼克松访华专题；页面日期、TIME 署名、标题、完整 `<article>` 正文段落数、字符数和正文 SHA-256 均逐篇核验，10/10 verified、0 重复。网页和 robots.txt 均在允许抓取下返回 HTTP 200，原始 HTML 已保存供离线复核；非空段落哈希与来源页提取一致，空 `<p>` 不计入正文。正式唯一全文增至 2,518 条，四时期为 59、35、702、1,722。批次 411—420 只提高 1949—1972 年计数；1973—2025 年仍保持并行采集，不能因早期补查而减少该段检索投入。离线重解析转正 10 条，本批详细证据及候选状态保留于 SQLite 和交付包；后续还将继续查找早期材料与 1991 年后的媒体、政府、智库和研究来源。

批次 421—431 继续同时覆盖早期与 1991 年后的媒体。TIME Vault 6 篇 1949 年原始报道覆盖重庆撤退、上海易手、广州战事、国民党航空公司接管及国共和谈；ABC Radio 官方档案 5 篇 2000—2001 年广播稿涉及美国对华永久正常贸易关系、APEC期间双边关系和 EP-3 事件。11 个候选页面和 robots.txt 均 HTTP 200，抓取耗时约 5.6 秒；逐页固定来源栏目、来源页日级日期、标题、署名行、正文段落数及 SHA-256 后 11/11 verified，0 重复。正式唯一全文增至 2,529 条，四时期为 65、35、707、1,722；本批同时增加早期 6 条及 1992—2016 年 5 条，仍未减少对 1991 年后资料的检索。证据 HTML 与候选状态已保存，pending 数量仍为 586，完整性失败记录不作正文。后续继续平行检索早期官方/媒体档案以及 1992—2025 年媒体、政府、研究机构和公众态度材料。

批次 432—444 继续补查朝鲜战争时期的 TIME 同期报道，并纳入 ABC 2010、2015、2016 年中美区域安全及南海材料。TIME 十篇文章均从 TIME Vault 原始页取得完整 `<article>` 正文，日期、标题、TIME 署名、段落结构、字符数和正文哈希通过复核，10/10 verified；ABC 2010、2015 年两篇广播/访谈稿及 2016 年新闻稿随后分别以栏目署名与文章边界规则复核，三篇均通过正文 SHA-256 和元数据核验。2016 页面另外排除推荐侧栏、“Reuters”署名行及页面提示，只保留 18 段新闻正文。该批 13 个候选 URL 抓取约 9.1 秒，0 重复；正式全文增至 2,542 条，四时期为 75、35、710、1,722。本批新增 10 条集中于 1949—1972，另 3 条增加到 1992—2016，后续继续优先提高 1991 年后媒体、政府、智库及公众态度来源覆盖。批次 432—444 状态及原始响应保存于 SQLite 和交付包；revalidation 审计见 `data/revalidation-20261109-abc-news-2016.json`。

批次 445—461 平行补查 TIME 1964—1972 年同期报道和 ABC News 2018—2023 年中美贸易、华为、疫情及美台经贸报道。17 个 URL 与相应 robots.txt 均在允许访问下返回 HTTP 200，Scrapy 请求阶段约 13 秒；14 条（10 条 TIME、4 条 ABC）经来源页元数据、非空正文段落、完整性和 SHA-256 核验后转正，0 重复。另 3 条 ABC 2020 页面因正文结构/署名无法通过完整性门槛，留在 pending；未用摘要或抓取片段替代。重核后正式全文增至 2,556 条，四时期为 85、35、710、1,726；候选状态为 2,600 verified、589 pending、106 restricted、64 excluded、2 candidate。此次同时增加早期和 1991 年后的记录，后续批次仍覆盖全部时期。批次和原始响应保存在 SQLite、证据目录及交付包；离线重核报告为 `data/revalidation-20261109-time-abc-modern.json`。

批次 462—468 补查 TIME 1979、1989 年中美关系正常化与天安门事件报道，并加入 PBS News 2001 年中美关系 transcript。Scrapy 在 robots.txt 允许下取得 7 个原始页（连同 2 个 robots.txt 请求共 9 个 HTTP 200，约 6.4 秒）；6 篇 TIME 正文逐段核对完整 `<article>`，PBS transcript 按节目逐字稿容器边界排除唯一尾部空段落，再以日期、标题和 SHA-256 核验。7/7 verified，0 重复。正式全文增至 2,563 条，四时期为 85、41、711、1,726；候选状态为 2,607 verified、589 pending、106 restricted、64 excluded、2 candidate。PBS 记录归入 1992—2016 年，故早期档案补查同时带动 1991 年后的覆盖。重核报告见 `data/revalidation-20261109-time-pbs-2001.json`；候选与原始 HTML 证据保存在数据库及证据目录。

批次 469—475 继续覆盖 1991 年后的 TIME 对华传播材料：1999 年驻南联盟使馆被炸、2001 年EP-3撞机危机、2010 年胡锦涛访美、2014 年网络安全和 2015 年中国全球影响。7 个 TIME 原始页与 robots.txt 均返回 HTTP 200，抓取约 7.3 秒；正文段落、日级日期、署名、标题、正文长度和 SHA-256 逐篇核验，7/7 verified，0 重复。正式全文增至 2,570 条，四时期为 85、41、718、1,726；候选状态为 2,614 verified、589 pending、106 restricted、64 excluded、2 candidate。该批全部进入 1992—2016 年，继续补强近现代段而不减少早期检索。重核报告见 `data/revalidation-20261109-time-1999-2015.json`。

批次 476—482 覆盖 TIME 2017—2025 年贸易战、台湾选举、拜习通话和中美 AI/芯片竞争报道。7 个原始页及 robots.txt 均 HTTP 200，抓取约 9.4 秒；7/7 verified，0 重复。正文逐项校验段落结构与 SHA-256，并排除 2019 页面内嵌的 “Advertisement” 段；2025 页面明确使用 “Published” 时间作为发布日期，单独区分较新的 “Updated” 时间，日期变更测试通过。正式全文增至 2,577 条，四时期为 85、41、718、1,733；候选状态为 2,621 verified、589 pending、106 restricted、64 excluded、2 candidate。本批全部进入 2017—2025 年，保持现代段持续扩充。离线重核报告见 `data/revalidation-20261109-time-2017-2025.json`。

上一批来源发现与逐条核验结论（批次 265—270）如下：

已增加目录级批量抓取和 NCBI PMC 开放全文批量发现。通过 PMC E-utilities 分页发现 2,523 个候选，Scrapy 在 ROBOTSTXT_OBEY 下分 7 个时期批次抓取，原始来源页响应均为 HTTP 200；`--fast` 配置的实测总体吞吐约 63—71 页/分钟。经原始页面适配器、日期/元数据/全文门槛和去重后，正式资料为 2,082 条，候选记录 3,002 条（其中 5 条明确排除的离题误检）。批次 265—270 从 Voice of America 新增 6 篇对华舆论、选举影响与台湾虚假信息报道；原始页面均 HTTP 200，逐条核验日期、标题、作者及完整正文，合计 6 条 verified。批次报告见交付包 `reports/batch-265.txt` 至 `reports/batch-270.txt`，合并审计见 `data/reviews/voa-open-broadcast-batch-20261108.json`。正式表当前 9 列字段完整性审计无空值；数据库 `integrity_check` 与外键检查通过。批次 255—258 首页及 259—260 第二页各批报告随交付包保存；第三页批次 261 见 `reports/batch-261.txt`，批次 262 见 `reports/batch-262.txt`。批次 262 的 Jakobson 1990 扫描 OCR 报告和批次 245 的 Friends Journal 扫描期刊文章均因未逐字校订而保持 pending；更正审计分别见 `data/reviews/shorenstein-jakobson-1990-20261108.json` 与 `data/reviews/friends-journal-china-united-states-1971-20261107.json`。

本轮吞吐实现和 PMC 抽取式元数据修复记录见 `data/reviews/pmc-derived-metadata-repair-20261108.json`、`data/reviews/pmc-derived-metadata-repair-20261108-batch2.json`；7 条缺少可核验字段或与主题不直接相关的 PMC 记录已从正式表撤出，候选和全文证据保留，备份及审计见 `data/reviews/pmc-unresolved-materials-withdrawal-20261108.json`。

批次 251 新增并核验哈佛 Kennedy School Shorenstein Center 研究报告 “Getting the Story in China: American Reporters Since 1972”（Jonathan Mirsky，2000-01-01）。官方落地页和 PDF 均由 Scrapy 在 robots.txt 允许下取得 HTTP 200；标题、作者说明、发布日期和可见 PDF 链接逐项匹配。PDF 共 33 页，完整文本 84,853 字符，PDF SHA-256 为 `5d46cb33cb65a724fbe31522f25aadfa68555b26a436a2c794fda5f9f4924bbd`，正文 SHA-256 为 `e53e99e2fd40424545ae17f27b87b3bac253e928ecd5f90d36daab48fb7ef50a`。正文超过 Excel 单元格上限，工作簿“正文”列写入 `materials_bodies/body-6b99d3bf1aa85ba24cd52fcacbbe5fa16a000a0940df0d3717e642e2621eaab9.txt`，随 ZIP 一并交付。审计见 `data/reviews/shorenstein-mirsky-2000-20261107.json`，报告见交付包 `reports/batch-251.txt`。

批次 249—250 记录了两条补充候选：Heritage Foundation 1991 页面因 Cloudflare HTTP 403 标记 restricted；Shorenstein Center 1990 Jakobson 报告在批次 262 完成来源元数据和页面覆盖核对，但嵌入 OCR 文本存在错误且未逐字校订，故继续保持 pending，不纳入正式资料表。原件、SHA-256 和更正审计见 `data/reviews/shorenstein-jakobson-1990-20261108.json`。

批次 252 检索 CIA Reading Room 关于中国对外广播/宣传机构的历史 PDF 线索。Scrapy 遵守 robots.txt，robots.txt 和目标 URL 均返回 HTTP 403，候选标记为 restricted；未使用搜索摘录或受限响应作为正文。审计见 `data/reviews/cia-china-broadcasting-1960-20261107.json`，报告见交付包 `reports/batch-252.txt`。

批次 253 补查 Shorenstein Center 1992 年《Turmoil at Tiananmen: A Study of U.S. Press Coverage of the Beijing Spring of 1989》。官方落地页和 PDF 均由 Scrapy 在 robots.txt 允许下取得 HTTP 200，落地页显示精确日期 1992-06-01、题名、摘要和 PDF 链接；但 230 页扫描 PDF 的嵌入文字仅能提取 2,878 字符，不能证明正文完整。该候选维持 pending，不把 OCR 或搜索提取代替原文正文。审计见 `data/reviews/shorenstein-turmoil-tiananmen-1992-20261107.json`，报告见交付包 `reports/batch-253.txt`。

批次 254 复查 Heritage Foundation 1983 年打印版候选。Scrapy 遵守 robots.txt 后请求官方 `print-display` 页面，目标响应为 HTTP 403；该候选标记 restricted，未使用搜索结果日期、摘录或受限响应作为正文或正式字段。审计见 `data/reviews/heritage-china-card-1983-20261107.json`，报告见交付包 `reports/batch-254.txt`。

`data/reviews/field-completeness-20261108.json` 是 2,367 条材料时生成的历史审计；当前 2,375 条的必填字段空值检查已直接针对 SQLite 数据库复核为 0。历史段落中的字段和队列数量是各自批次当时的快照，不代表当前数据库状态。

批次 248 检查《Current History》1988 年文章 “Sino-American Relations”（John Bryan Starr）。出版社元数据页显示发布日期 1988-09-01、作者和题名，但 Scrapy 遵守 robots.txt 请求时 robots.txt 与来源页均返回 HTTP 403/Cloudflare challenge；正文 PDF 也未取得。该候选标为 restricted，仅保存元数据依据和受限响应审计，不进入正式资料表。详情见 `data/reviews/current-history-sino-american-relations-1988-20261107.json`；报告见交付包 `reports/batch-248.txt`。

批次 247 找到并以 Scrapy 合规取得 1981-03-31《Congressional Record》刊载的《The China Factor: Final Report of the Fifty-Ninth American Assembly》全文 PDF（HTTP 200，robots.txt 允许）。报告原件来自 American Assembly 与 CFR 合办项目，govinfo 托管的是公开国会记录副本。PDF 第 108—111 页可定位到完整报告；但文字层存在实质 OCR 错误，尚未逐字对照扫描图像修正，因此报告仍为 pending，不写入正式 Excel。另将同页 John Glenn 的独立发言从 “THE CHINA FACTOR” 标题核至 “The report follows:” 边界，作为 1981-03-31 政府来源正式入库；该记录不包含后续 OCR 未校订的大会报告。原始 PDF、SHA-256 和逐字核验见 `data/reviews/china-factor-john-glenn-1981-20261108.json`；报告全文限制见 `data/reviews/american-assembly-china-factor-1981-20261107.json`。

批次 246 新增并核验《The Daily Iowan》刊载的美联社报道 “AP Chiefs Declare Further Obstacles Block News Reports”（1950-04-08）。Scrapy 遵守 robots.txt，robots.txt 与公开 PDF 均返回 HTTP 200。扫描 PDF 的 OCR 层存在字符错误，因此正文依据第 6 页渲染图逐段人工核对，保留原文中的拼写和语病；正文为 1,912 字符，以中央栏坐标和下一篇文章标题界定，PDF 与正文 SHA-256 双重核验。来源字段记录实际刊载报纸，作者按 AP 署名记录；不声称取得 AP 官网原始线稿。该批次 1 candidate、1 verified。审计见 `data/reviews/associated-press-news-freedom-china-1950-20261107.json`，报告见交付包 `reports/batch-246.txt`。

批次 245 取得 Friends Journal 1971-05-15 文章 “China and the United States”（Colin W. Bell）的公开 32 页扫描 PDF，并定位第 10—11 页正文。后续审计确认当前文字层为 OCR，原复核只核对了页面边界而未逐字校订，故已撤出正式表并改为 pending；原件及哈希保留。更正审计见 `data/reviews/friends-journal-china-united-states-1971-20261107.json`，最新批次报告随交付包保存。

上一批次完成最后 9 条缺失摘要/关键词记录的修复：7 条 The American Presidency Project 记录（材料 ID 171—173、266—267、269—270）和 2 条 Trump White House 档案（ID 102、174）。随后从已有允许访问的 Obama White House 原始 HTML 中核验并提升 3 条官方视频 transcript（材料 ID 295—297），提升 1 条 VOA 官方档案页（材料 ID 298），并提升 3 条公开 PMC 研究文献（材料 ID 299—301）。所有派生字段均由对应原始正文整理，来源、日期、作者、标题和正文保持不变；视频 transcript 适配器精确排除页面控制项并以完整正文 SHA-256 门控。审计见 `data/reviews/presidency-additional-metadata-repair-1992-2023-20261107.json`、`data/reviews/trump-whitehouse-metadata-repair-2018-2019-20261107.json`、`data/reviews/obama-whitehouse-video-transcripts-2009-2013-20261107.json`、`data/reviews/insidevoa-mission-2007-promotion-20261107.json` 和 `data/reviews/pmc-research-promotion-2021-2024-20261107.json`。该批次结束时正式表 248 条；当前摘要、关键词和正文缺口均为 0。资料库仍不是绝对穷尽，当前 4 个验证缺口及历史正文/日期审计限制见交付包报告。

随后修复 5 条 National Security Archive 材料（ID 39—43）的字段缺口。现代页面、旧版文章布局和旧版表格布局均使用已保存原始 HTML 本地重解析；出版方已有摘要保持不变，缺失摘要和关键词按正文整理，并以精确 URL 与正文 SHA-256 限定。未新增材料。审计见 `data/reviews/nsarchive-metadata-repair-20261107.json`；该批次完成时空摘要降至 22 条、空关键词降至 24 条。

随后修复 6 条 Clinton White House 档案（ID 80、81、162—165）的字段缺口。新增字段使用独立的精确 URL+正文 SHA-256 白名单，覆盖现代档案页、文字版记者会和旧版档案布局；来源日期、作者、标题和正文均保持不变。未新增材料。审计见 `data/reviews/clinton-whitehouse-metadata-repair-1997-2000-20261107.json`；该批次完成时空摘要降至 16 条、空关键词降至 18 条。

随后修复 3 条 The American Presidency Project 记录（ID 198、200、201）的字段缺口。新增字段使用精确 URL+正文 SHA-256 白名单，覆盖南亚核不扩散、APEC/WTO 和中美 WTO 加入协议材料；来源日期、作者、标题和正文均保持不变。未新增材料。审计见 `data/reviews/presidency-metadata-repair-1998-1999-20261107.json`；该批次完成时空摘要降至 13 条、空关键词降至 15 条。

随后修复 2 条 Radio Free Asia 文章（ID 276、277）的关键词缺口。两条原始 HTML 的出版方摘要、日期、作者、标题和正文保持不变；关键词按正文整理并绑定精确 URL+正文 SHA-256。未新增材料。审计见 `data/reviews/rfa-keywords-repair-2012-2014-20261107.json`；该批次完成时空摘要和空关键词均为 13 条。

随后修复 4 条 U.S. Government Publishing Office 听证记录（ID 184—187）的字段缺口。使用已保存 transcript 和官方详情页证据复核日期、作者、标题和完整正文；摘要、关键词仅从同一 transcript 正文整理，并绑定精确 transcript URL+正文 SHA-256。未新增材料。审计见 `data/reviews/govinfo-hearing-metadata-repair-2017-2024-20261107.json`；当前剩余缺摘要 9 条、缺关键词 9 条。

随后修复 7 条 The American Presidency Project 记录（ID 171—173、266—267、269—270）的字段缺口。复用已保存允许访问的原始 HTML，核对来源、日期、作者、标题和完整正文未变；摘要、关键词以精确 URL+正文 SHA-256 门控并附正文支持片段。审计见 `data/reviews/presidency-additional-metadata-repair-1992-2023-20261107.json`；该批次完成时空摘要和空关键词均降至 2 条。

随后修复 2 条 Trump White House 档案（ID 102、174）的字段缺口。两条 Pence 演讲均从已保存原始 HTML 重新解析，保留原始来源字段并以精确 URL+正文 SHA-256 门控派生摘要和关键词。审计见 `data/reviews/trump-whitehouse-metadata-repair-2018-2019-20261107.json`；当前正式表的摘要、关键词和正文缺口均为 0。

随后提升 3 条 Obama White House 官方视频 transcript（材料 ID 295—297）：2013 年奥巴马与习近平 G20 会晤、2009 年上海中国青年 town hall、2012 年奥巴马与习近平会晤。页面均提供可逐段提取的完整 transcript、可核实日期和 White House 发布标识；适配器以页面标题/日期及完整正文 SHA-256 核验，排除唯一的 “Close Transcript” 控件。审计见 `data/reviews/obama-whitehouse-video-transcripts-2009-2013-20261107.json`；该批次关闭 `1992—2016 / new_media` 的验证缺口，未新增候选。

随后提升 1 条 Voice of America Office of Public Relations 档案页（材料 ID 298）：“VOA's Mission in the 1960s and 1970s”。原始页面为公开 HTTP 200，页面日期为 2007-02-13，作者、标题、发布机构和完整正文均可复核；未使用搜索摘要或受限副本。审计见 `data/reviews/insidevoa-mission-2007-promotion-20261107.json`。

随后提升 3 条公开 PMC 研究文献（材料 ID 299—301）：2021 年公众对中国的多维认知、2020 年亚洲个体对中国影响的认知，以及 2024 年北京冬奥会新闻中的中国国家形象话语。三条原始 PMC HTML 均提供公开完整正文、精确出版日期、作者、出版方摘要和关键词；审计见 `data/reviews/pmc-research-promotion-2021-2024-20261107.json`。

批次 242—244 对早期覆盖缺口进行了合法公开页面补查：1981 年 Columbia/CIAO 的《The China Factor》页面可读但未显示可核实的精确发布日期，1953 年 U.S. Naval Institute 页面返回 HTTP 403，1979 年 JSTOR 开放章节返回 HTTP 420；三条均保留为 pending/restricted，未把页面摘要或受限响应写入正式表。批次报告见交付包中的 `reports/batch-242.txt`、`reports/batch-243.txt` 和 `reports/batch-244.txt`。

本轮修复 6 条 CSIS 材料的主题关键词。对现存原始页面/PDF及配套发布页本地重解析，未声称重抓；每条关键词均有正文片段作依据，并按精确来源 URL 与正文 SHA-256 限定。CSIS 分类标签和页面 `keywords` 标签不再自动视为文章主题。另修复一份 10 页双栏 PDF 首页阅读顺序：依据首页嵌入文字坐标排列封面标题、署名、日期和摘要框，再接续原始左右栏正文顺序；仅删除重复页眉页脚，逐词核对来源文本，缺末页版本测试拒收。保留原发布日期、作者、标题及发布者摘要。正式表仍为 241 条，缺摘要 27 条、缺关键词 31 条，覆盖矩阵仍有 6 格未发现已核实全文。本轮无新增材料或候选。审计见 `data/reviews/csis-keywords-and-pdf-order-repair-20261107.json`。全套 246 项测试通过；`scrapy check` OK（0 contracts）；数据库完整性/外键检查、本地与 ZIP 工作簿九列和 241 条正文对应、241 条证据哈希及 ZIP CRC 均通过。当前交付包 751 个文件：71 个正文附件、271 个证据、165 个审计、240 个批次报告及 3 个索引/覆盖报告，另含工作簿。

本轮纠正布鲁金斯字段与全文对应问题：9 条既有材料的关键词原含栏目、研究中心与格式标签，已根据逐篇正文整理替换，原关键词及每个新关键词的正文片段保存在审计中。来源、日期、作者、标题、出版者摘要与正文未变。2019 年中美经济关系政策简报网页仅为 14,766 字符的缩略版，已从正式表撤出；批次 241 在遵守 robots.txt 下取得官方 25 页 PDF（80,921 字符），与原始发布页日期 2019-02-28、作者和标题核对后替换。PDF 首面无机构名，使用经核对的精确 URL/发布页/日期/标题/原始文件与全文 SHA-256 约束验证，未知或变更文件不得套用该规则。当前仍为 241 条正式资料，空摘要 27 条、空关键词 37 条，6 个覆盖缺口尚在。审计见 `data/reviews/brookings-keywords-and-full-brief-repair-20261107.json`。243 项测试通过；本地及包内 Excel 241 条、严格九列；全文、附件和全部证据哈希匹配数据库，ZIP CRC 与数据库完整性/外键检查通过。最新 ZIP 750 个文件：工作簿、71 个长正文附件、271 个原始证据、164 个审计文件、240 个批次报告和 3 个索引/覆盖报告。下方数字为历史批次记录。

本轮复核 6 篇 2008—2025 年研究文献的既有原始 HTML/PDF 和发布页，补齐正文有依据的关键词；来源、发布日期、作者、标题、出版者摘要与正文保持一致。关键词按精确 URL 和完整正文 SHA-256 绑定，来源关键词优先，每个派生关键词在审计中附正文片段。PMC 2022 年公共卫生论文的原页已标注撤稿，随包审计单独记录该提示和通知链接，不修改原题名或原文、不增加 Excel 列。本轮没有新增抓取或唯一材料。当前正式资料 241 条，空摘要 27 条、空关键词 37 条；审计见 `data/reviews/research-literature-keywords-repair-20261107.json`。241 项测试通过；本地与包内工作簿均 241 条、严格九列，ZIP CRC、SQLite 完整性及外键检查通过。当前 ZIP 746 个文件：70 个长正文附件、270 个原始证据、163 个审计文件、239 个批次报告和 3 个索引/覆盖报告，另含工作簿。其余缺失字段、历史正文核验和 6 个时期/来源覆盖缺口仍待处理；下方为历次进度记录。

本轮补齐九份 2022—2024 年国务院材料的摘要和关键词，范围包括对华政策、外交战略、宗教自由报告发布、记者会、韩正会见前讲话和国务院现代化议程。基于已保存的原始 HTML 本地重解析，逐项核对来源、日期、作者、标题及完整正文；沿用原证据与抓取时间，不声称本轮重抓。派生摘要以“据正文整理：”开头，并按精确 URL 与完整正文 SHA-256 绑定，防止正文变化后套用旧摘要。无新增候选或唯一材料。审计见 `data/reviews/state-metadata-repair-2022-2024-20261107.json`；剩余空摘要 27 条、空关键词 43 条。

本轮完成 Huang 播客 PDF 对应关系复核：原页直接链接 PDF，发布日期 2019-06-24 与封面日期一致，参与者对应；PDF 14 页均有文字，正文 24,954 字符。正式标题照录 PDF 封面的 “DOLLAR & SENSE: China’s perspectives on trade and the economic tension with the US”，不改写为发布页略有不同的标题；标题证据指向 PDF，日期证据指向发布页。已按精确 URL、页面标题、日期、原始 PDF 与完整正文哈希登记核验规则，并要求发布页确实链接该 PDF。新增 1 条全文、无新增候选，正式表为 241 条。审计见 `data/reviews/brookings-huang-transcript-2019-20261107.json`。

本轮全文审查撤出四条介绍页：2018/2024 两份听证议程、两份 Brookings 播客介绍。原记录与证据保留在审计中；听证网页发布日期不套用到另一个 PDF。2018 正式听证记录 PDF 已重抓（HTTP 200，60 页），但只确认听证日期和出版年份，缺精确发布日期，保持 pending。批次 240 从播客原页直接链接取得两份官方文字稿：Prasad 节目稿通过原页/封面标题、日期、参与者及九页全文核对，新增一条 27,582 字符正文；Huang 节目稿因封面标题措辞不一致保留 pending。审计见 `data/reviews/hearing-podcast-landing-withdrawals-20261107.json`。本轮合计撤出 4 条、新增全文 1 条，正式资料为 240 条。

本轮纠错：原记录 177（GEC 2023 全球信息环境报告）实为执行摘要网页，含语言下载菜单，不能代替报告全文；已从正式表及交付索引撤出，候选与原始记录保留供审计。官方报告 PDF 再核查返回 HTTP 200 的 “Technical Difficulties / Exception: forbidden” HTML，记 restricted，未取得全文。修复摘要落地页误入库及报告 PDF 适配器对 HTML 错误页的访问分类/证据类型；236 项测试通过。审计见 `data/reviews/gec-executive-summary-withdrawal-20261107.json`。当前正式资料为 243 条，空摘要 37 条、空关键词 53 条；本轮数量减少来自撤出，不是补齐字段。

本轮补齐国务院 2011/2016 年五份对华演讲及战略与经济对话记录的摘要和关键词，使用此前已保存、哈希核对一致的完整原始 HTML，沿用原证据 ID 和抓取时间；正文、标题、日期、作者均重解析匹配。此次重抓五页虽 HTTP 200，却是 “Technical Difficulties / Exception: forbidden”，保留 restricted 状态，不作为正文，也不声称本次取得全文。解析器新增排除 `flex-video` 播放器控件，防止界面文字混入正文。审计见 `data/reviews/state-china-metadata-repair-2011-2016-20261107.json`。当前空摘要 38 条、空关键词 54 条；唯一材料仍为 244 条。

本轮修复 2009—2010 年奥巴马白宫五份中美关系材料的摘要与关键词，复用批次 129，未增加候选或唯一材料。五个来源页 HTTP 200，robots.txt HTTP 404；五份正文均与先前原始响应一致。2009 年联合声明共 51 个正文块、28,089 字符，新增精确 URL/发布日期/标题/全文 SHA-256 的完整性规则，避免对非讲话稿强求 END 标记；修改或截断正文均被拒绝。审计见 `data/reviews/obama-china-metadata-repair-2009-2010-20261107.json`。当前剩余空摘要 43 条、空关键词 59 条，均位于 1992—2025 年；早期来源覆盖缺口仍待推进。

字段修复批次：已逐条重抓 4 条克林顿白宫档案原始页面，补齐对华关系、公共外交、WTO 和 PNTR 材料的摘要与关键词；根据正文整理的摘要和关键词均绑定到对应原始 URL，材料唯一行数不变。审计见 `data/reviews/clinton-whitehouse-metadata-repair-1997-2000-20261107.json`。此前已修复 9 条总统项目记录，见 `data/reviews/presidency-metadata-repair-1949-1991-20261107.json`。当前剩余空摘要 80 条、空关键词 96 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

字段修复批次：复用既有批次，Scrapy 在遵守 robots.txt 的情况下重抓 5 条总统项目原始页面，补齐邓小平访美、中美文化交流及里根复旦演讲资料的摘要和关键词。原始页与 robots.txt 返回 HTTP 200；候选、批次和唯一材料数量不变。审计见 `data/reviews/deng-cultural-exchange-metadata-repair-1979-1984-20261107.json`。当前剩余空摘要 75 条、空关键词 91 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

字段修复批次：复用既有候选批次，Scrapy 在遵守 robots.txt 的情况下重抓 7 条 1989—1990 年总统项目及布什总统图书馆页面，补齐天安门事件后公开表态、双边政策措施、人员交流和移民救济材料的摘要和关键词。7 个原始页均返回 HTTP 200，唯一材料数不变。审计见 `data/reviews/bush-tiananmen-metadata-repair-1989-1990-20261107.json`。当前剩余空摘要 68 条、空关键词 84 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

字段修复批次：重抓 1949 年杜鲁门记者会和 1950 年朝鲜战争初期 3 条总统公开材料，复用既有候选批次；原始页均返回 HTTP 200。补充的摘要和关键词逐条根据正文整理，材料数不变。审计见 `data/reviews/truman-china-korea-metadata-repair-1949-1950-20261107.json`。当前剩余空摘要 64 条、空关键词 80 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

字段修复批次：重抓 1994、1996 年 7 条总统项目原始材料，涵盖最惠国待遇的政策决定、行政部门立场、总统记者会及众议院表决回应。Scrapy 在遵守 robots.txt 的情况下抓取，原始页均返回 HTTP 200；候选、批次和唯一材料数不变。审计见 `data/reviews/clinton-mfn-metadata-repair-1994-1996-20261107.json`。当前剩余空摘要 57 条、空关键词 73 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

字段修复批次：重抓 1999—2000 年 6 条总统项目原始材料，涵盖中美 WTO 谈判、对华正常贸易关系续期和 PNTR 立法。Scrapy 遵守 robots.txt，6 个来源页均返回 HTTP 200；复用既有候选批次，没有增加候选或唯一材料。审计见 `data/reviews/clinton-wto-pntr-metadata-repair-1999-2000-20261107.json`。当前剩余空摘要 51 条、空关键词 67 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

字段修复批次：重抓尼克松 1972 年 CBS 采访、里根 1987 年对华钨酸进口备忘录和 1988 年共和党纲领 3 条总统项目原始材料。页面均返回 HTTP 200，继续复用既有候选批次；1988 年党纲全文 234,842 字符，交付导出将按 Excel 单元格限制外置完整 UTF-8 文本。审计见 `data/reviews/nixon-reagan-republican-china-records-metadata-repair-1972-1988-20261107.json`。当前剩余空摘要 48 条、空关键词 64 条，逐条清单见 `data/reviews/field-completeness-20261107.json`。

批次 238 检索到 NARA 维护的 @ObamaWhiteHouse 2015 年 X 帖文，内容与中美合作直接相关；Scrapy 在 ROBOTSTXT_OBEY 下收到 robots.txt 禁止，原帖页面未请求，故记 restricted。Firecrawl 的处理结果只作为发现线索，不用作正文或正式字段。审计见 `data/reviews/obama-whitehouse-x-us-china-cooperation-2015-20261107.json`。

批次 239 新增白宫官方档案中奥巴马与习近平 2015-09-25 抵达仪式讲话。Scrapy 页面返回 HTTP 200，原页明确日期、标题及 White House/Press Secretary 来源信息；正文 6,396 字符完整。根据正文整理摘要与关键词已经针对该 URL 审核登记。审计见 `data/reviews/obama-xi-arrival-remarks-2015-09-25-20261107.json`。

批次 237 新增尼克松 1972 年访华前新闻发布会记录。The American Presidency Project 来源页与 robots.txt 均 HTTP 200；来源页日期为 1972-02-10，作者 Richard Nixon。正文 35,317 字符由现有总统项目适配器提取，来源页/标题/日期/作者/全文通过核验；根据正文整理摘要与关键词仅登记在该 URL 的审核元数据中。正式资料计 1 条。审计见 `data/reviews/nixon-presidency-news-conference-1972-20261107.json`。

同主题 USC China Institute 镜像已按 Scrapy 重抓，但其页面日期只能确认是新闻发布会的历史日期，不能据此证明 USC 页面发布日期，故继续 pending，未纳入 Excel。审计见 `data/reviews/nixon-usc-press-conference-1972-20261107/review.json`。

批次 227 新增 CSIS 研究文章 “China’s Power Play Across the Pacific”。来源页和 robots.txt 均 HTTP 200；页面发布日期为 2025-04-08，作者为 Charles Edel and Kathryn Paik。正文完整抽取 12,576 字符，正文 SHA-256 为 `76b1fcd26ccef58f65fe2c68e32b536b79d3aec540b97d82ffc9f8df2427de47`。页面可见标签经来源页核验后写入关键词：Australia, New Zealand, and Pacific；China；Defense and Security；International Development。审计见 `data/reviews/csis-china-power-play-pacific-2025-20261107.json`。

批次 228—231 补查 CNN、AP 和 Reuters 原始页面。CNN 两页及 Reuters 一页的 robots.txt 均禁止访问；AP 页面 robots.txt 允许请求但原页返回 HTTP 403 浏览器挑战。四条均为 restricted、0 verified，搜索摘要不作正文或正式元数据。审计见 `data/reviews/cnn-us-china-dialogue-2018-20261107.json`、`data/reviews/ap-china-trade-negotiator-2025-20261107.json`、`data/reviews/cnn-taiwan-strait-2018-20261107.json` 和 `data/reviews/reuters-china-taiwan-election-2024-20261107.json`。

批次 232 发现 Zengjun Peng 2004 年研究《Representation of China: An across time analysis of coverage in the New York Times and Los Angeles Times》。Firecrawl 只作发现线索；Scrapy 获取 robots.txt 为 HTTP 200，Taylor & Francis 出版方页面返回 HTTP 403，记录为 restricted（1 candidate、0 verified），未抓取搜索摘要或第三方上传全文。审计见 `data/reviews/peng-representation-china-2004-20261107.json`。

批次 233 检索 RAND 原始出版物 P-6590 “The China Factor in America's Foreign Relations”。Scrapy 请求 robots.txt 返回 HTTP 403，按规则未请求出版页面；针对 archives.gov、dtic.mil 和 RAND 的有限补充搜索未找到相关官方公开副本。记录为 restricted（1 candidate、0 verified），审计见 `data/reviews/rand-china-factor-foreign-relations-p6590-20261107.json`。

批次 234 核查 ERIC ED073276：ERIC 记录页和官方 PDF 均 HTTP 200，记录发布日期为 1973；PDF 是 69 条 ERIC 摘要汇编，不是这些底层研究的全文，汇编本身也不直接研究美国对华传播，因此保持 pending、不入正式表。其第 42 页列出 Donald R. Browne 1971 年 “International Radio Broadcasting: Who Listens?”，涉及亚洲国际广播听众及 VOA；后续 Firecrawl 补查仍只发现该汇编、Browne 1982 年的书及非对应文献，未确认独立原文全文，未使用摘要替代正文。审计见 `data/reviews/eric-communication-occupational-cluster-ed073276-20261107.json`。

批次 235 检查 CFR《Foreign Affairs》1965 年文章 “Communist China's Capacity to Make War”。Scrapy 获取 robots.txt 和出版页均 HTTP 200，但来源页显示访问受限，故记为 restricted。JSTOR 搜索结果未证明可开放访问，Samuel B. Griffith Foundation 页面也未确认该已发表文章的授权全文；未访问可能受控的 PDF。0 verified，不进入正式表。审计见 `data/reviews/cfr-foreign-affairs-communist-china-capacity-war-1965-20261107.json`。

批次 236 检查 Harold R. Isaacs《Scratches on Our Minds: American Images of China and India》（馆藏目录给出的年份线索为 1958）。Internet Archive 的公开目录页及 robots.txt 均 HTTP 200；页面虽列 EPUB/PDF 链接，但版权持有人字段为 Massachusetts Institute Of Technology，且未见明确开放授权，故没有请求文件端点。目录页也不能证明精确到日的出版日期及许可范围内的完整全文可用，因此保持 pending，不进入正式表。审计见 `data/reviews/isaacs-scratches-on-our-minds-1958-20261107.json`。

核验闸门已补强：来源和证据链接必须为 HTTP(S)，正文拒绝 HTML 标签，并在 HTML/JSON 采集项入库前检查正文首尾词序能在同一原始响应中按归一化文本找到；不满足时自动保持 pending。

历史材料重验证已完成：使用本地原始证据和当前适配器逐字段重解析，122 条 legacy 材料与原记录完全一致，已补建 `material_verifications` 快照；48 条正文/字段不一致、5 条当前适配器无法重现，继续保留 legacy，不伪称为精确复核。审计见 `data/reviews/legacy-revalidation-20261107.json`，并已随交付包保存。

批次 218—219 核查 USCC 2025 年年度报告的官方发布页与 PDF。页面可访问，但其 JSON-LD `datePublished` 只到年份；页面中隐藏的 `contentDate` 供直播组件使用，不是报告发布日期。PDF 标注 November 2025，含 2025-11-18 致国会转送信；这不能替代来源页的精确发布日期。PDF 共 745 页，通用抽取器遇到 XForm 解码警告且有 14 页未抽出文字，故正文完整性也未核实。两条记录均 pending，不进入正式表。详情见 `data/reviews/uscc-2025-annual-report-page-20261107.json` 和 `data/reviews/uscc-2025-annual-report-pdf-20261107.json`。

批次 220 核查 Air University《China and “Deep Bench” Diplomatic Power》PDF。Scrapy 在获取 robots.txt 与 PDF 时连接连续中断，无法判断访问规则；未尝试其他请求方式。候选保持未处理，不把搜索结果当作正文。详情见 `data/reviews/air-university-china-deep-bench-2025-20261107.json`。

批次 221—222 检索 State Department 公共外交会议纪要与 2025 年 Senate hearing transcript。前者 robots 与页面均 HTTP 403，后者 robots.txt 明确禁止请求；未进行绕行。Congress.gov 搜索结果中 2025-10-07 是听证发生日，不作为发布日期。两条各为 1 candidate、0 verified、1 restricted，未纳入正式表。详情见 `data/reviews/state-acpd-prc-public-diplomacy-2025-20261107.json` 和 `data/reviews/senate-hearing-china-behavior-2025-20261107.json`。

批次 223 检索 AP 关于 2025 年中美贸易战的报道线索；robots.txt 返回 HTTP 200，原文页面返回 HTTP 403。未尝试其他访问方式；检索摘录只作发现线索。1 candidate、0 verified、1 restricted。审计见 `data/reviews/ap-us-china-trade-war-2025-20261107.json`。

批次 224—225 找到两条 Brookings 台湾议题文章，但原页日期分别为 2026-09-09 和 2026-03-20，均超出 1949—2025 范围，留作 pending 候选，不入正式表。

批次 226 新增 Brookings 文章 “Chinese citizens’ affection for Taiwanese may reduce risk of cross-Strait conflict”，页面发布日期 2025-12-18，作者 Dina Smeltz、Craig Kafura。原页及 robots.txt 均 HTTP 200；正文完整抽取 8,361 字符，标题、作者、可见发布日期与 JSON-LD 日期匹配。正文 SHA-256 为 `278f008504ea5423902c2e274bf7601e56c326cf7c9ed363437f33098d35df7a`。审计见 `data/reviews/brookings-chinese-public-opinion-taiwan-2025-20261107.json`。

当前正式表有 251 条唯一全文；468 条候选（256 verified、134 pending、77 restricted、1 candidate）。

按完整 4 时期 × 5 来源类型矩阵审计，当前没有适用格子缺候选 URL；1949—1991 两个新媒体格子按规范（2006 年以后）标记为不适用。2 个适用格子仍无已核实全文：1949—1972 think_tank（3 restricted）；1972—1991 research_literature（3 pending、1 restricted）。矩阵区分候选数与唯一 verified 材料数；审计见 `data/coverage-audit.json`，ZIP 的 `reports/coverage.json` 收录完整矩阵。

字段质量审计发现既有正式记录仍有 27 条摘要为空、43 条关键词为空；这些字段不能用占位文本掩盖，待依据各自正文和来源逐批补齐。逐条清单见 `data/reviews/field-completeness-20261107.json`。新入库材料的摘要/关键词按正文整理并登记来源。

批次 239 新增 1 条 verified 全文；批次 238 为 1 candidate、0 verified、1 restricted；批次 237 新增 1 条 verified 全文；批次 236 为 1 candidate、0 verified、1 pending；批次 235 为 1 candidate、0 verified、1 restricted；批次 234 为 1 candidate、0 verified、1 pending；批次 233、232 各为 1 candidate、0 verified、1 restricted；批次 228—231 各为 1 candidate、0 verified、1 restricted；批次 227 和 226 各新增 1 条 verified 全文；批次 224—225 各为 1 candidate、0 verified、1 pending（范围外）。批次 223、221 与 222 各为 1 candidate、0 verified、1 restricted。批次 220 报告：1 candidate、0 verified、1 unprocessed。批次 219 与 218 各为 1 candidate、0 verified、1 pending。

当前交付包已按批次 252 重建：工作簿为 251 条数据、严格九列；ZIP 共 984 个文件，含 76 个正文附件、282 个正式材料证据、189 个唯一候选证据副本、181 个 review 审计文件和 251 份批次报告。`reports/candidate-evidence-index.json` 含 pending/restricted 证据索引记录，其中重复响应按哈希共用文件；ZIP CRC 校验通过。候选证据仅位于 `candidate-evidence/`，标记为 `not_verified`，不进入正式 `provenance-index.json` 或 Excel。长正文继续以 UTF-8 侧文件或相对路径交付；SQLite 完整性、外键、工作簿回读和证据哈希均在交付检查中复核。

批次 217 检索 RAND 关于中美人工智能市场竞争的研究报告线索。Scrapy 在 `ROBOTSTXT_OBEY` 下请求，robots.txt 与原始页面均返回 HTTP 403；未尝试替代请求方式。候选仅作为受限记录保留，Firecrawl 搜索结果不作为正式元数据或正文。1 candidate、0 verified、1 restricted。详情见 `data/reviews/rand-us-china-ai-competition-2025-20261107.json`。

当前正式表有 240 条唯一全文；432 条候选（250 verified、126 pending、56 restricted）。

批次 217 报告：1 candidate、0 verified、1 restricted、0 pending/duplicate/unprocessed。

## 批次 216（2026-11-07）

批次 216 检查 Nature Portfolio 上的 2025 年学术文章线索。Scrapy 在 `ROBOTSTXT_OBEY` 下请求，但 robots.txt 和来源页均返回 HTTP 406；未尝试替换请求方式。因 406 不能单独证明访问受限，候选保留 pending；Firecrawl 搜索标题和摘录仅用于发现，不作正式元数据或正文。1 candidate、0 verified、1 pending。详情见 `data/reviews/nature-china-us-national-military-image-2025-20261107.json`。

当前正式表有 240 条唯一全文；431 条候选（250 verified、126 pending、55 restricted）。

批次 216 报告：1 candidate、0 verified、1 pending、0 restricted/duplicate/unprocessed。

批次 215 检索开放学术文献候选，Firecrawl 搜索将 Oxford University Press 的 “Strategic Competition and US–China Relations: A Conceptual ...” 列为相关线索；随后 Scrapy 遵守 robots.txt 抓取来源原页，robots HTTP 200、原页 HTTP 403。未使用登录、代理或其他绕过方式；搜索结果标题及摘录仅作发现线索，不当作正式元数据或正文。1 candidate、0 verified、1 restricted；详情见 `data/reviews/oup-strategic-competition-us-china-2023-20261107.json`。

当前正式表有 240 条唯一全文；430 条候选（250 verified、125 pending、55 restricted）。

批次 215 报告：1 candidate、0 verified、1 restricted、0 pending/duplicate/unprocessed。

批次 214 核查 USCC “The Chinese View of Strategic Competition with the United States” 官方听证页。Scrapy 遵守 robots.txt，robots 与页面均 HTTP 200；页面日期标记 “Wednesday, June 24, 2020” 位于听证议程，明确指听证发生日，不是发布日期。页面无可核实的发布日期和作者字段，故 1 candidate、0 verified、1 pending，不进正式资料表。审计见 `data/reviews/uscc-chinese-view-strategic-competition-source-page-2020-20261107.json`。

批次 213 抓取该听证官方 PDF 全文文件，Scrapy 遵守 robots.txt，robots 与 PDF 均 HTTP 200；PDF 有 218 页，封面日期为听证发生日 2020-06-24，文件 CreationDate 为 2020-08-05。官方 hearing 页也未显示发布日期；文件属性创建日不足以证明来源发布日期，通用解析器亦未核验完整、可归属的正式资料记录。1 candidate、0 verified、1 pending，不进正式表。审计见 `data/reviews/uscc-chinese-view-strategic-competition-transcript-2020-20261107.json`。

当前正式表有 240 条唯一全文；429 条候选（250 verified、125 pending、54 restricted）。

批次 214 报告：1 candidate、0 verified、1 pending、0 restricted/duplicate/unprocessed。批次 213 报告：1 candidate、0 verified、1 pending、0 restricted/duplicate/unprocessed。

批次 212 新增 Carnegie Endowment for International Peace 多作者报告 “U.S.-China Relations for the 2030s: Toward a Realistic Scenario for Coexistence”，来源页日期 2024-10-17。Firecrawl 用于发现原始页面，随后 Scrapy 在遵守 robots.txt 的情况下抓取；robots 与页面均 HTTP 200。可见作者、citation 元数据与 JSON-LD 核对一致。正文包含 12 章、531 个正文块、330,934 字符，SHA-256 与审阅版一致；排除目录、作者简介和机构免责声明，保留正文及注释。全文超出 Excel 单元格限制，已保存为 UTF-8 附件。详情见 `data/reviews/carnegie-us-china-2030s-2024-20261107.json`。

当前正式表有 240 条唯一全文；427 条候选（250 verified、123 pending、54 restricted）。

批次 212 报告：1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。

批次 211 新增 China Leadership Monitor 的 Ryan Hass 文章 “How China is Responding to Escalating Strategic Competition with the U.S.”，来源页显示发布日期 2021-03-01。Scrapy 遵守 robots.txt；robots 与原始页均 HTTP 200。JSON-LD UTC 时间戳为次日，未找到可据以换算的来源时区，因此按页面明确显示日期入表并在审计记录中披露差异。正文核验为 109 段，41,612 字符，SHA-256 与审阅版本一致；排除了 PDF 下载控件、图片署名和页面标签。因正文超出 Excel 单元格限制，完整 UTF-8 正文另存并在“正文”列引用。详情见 `data/reviews/clm-ryan-hass-strategic-competition-2021-20261107.json`。

当前正式表有 239 条唯一全文；426 条候选（249 verified、123 pending、54 restricted）。

批次 210 新增约翰·F·肯尼迪与中华民国副总统会谈后的联合声明，标题 “Joint Statement Following Discussions With the Vice President of the Republic of China.”，发布日期 1961-08-02。APP 原页可见日期与结构化日期一致；正文 5,081 字符、10 段，讨论联合国中国代表权、中华民国继续留在联合国及反对中华人民共和国加入。摘要和关键词均逐条依据正文整理。详情见 `data/reviews/kennedy-roc-un-joint-statement-1961-20261107.json`。

批次 211 报告：1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。

批次 209 新增约翰逊总统 1965-07-28 记者会全文 “The President's News Conference”，作者 Lyndon B. Johnson。APP 原页可见日期与结构化时间一致，正文 30,913 字符、135 段；其中称越战受中国支持，并回应记者关于中国共产党反应的提问。摘要据正文整理，关键词经来源正文审核。检索结果建议的年份不准确，正式日期及批次标签均按原始页面更正。详情见 `data/reviews/johnson-china-vietnam-news-conference-1965-20261107.json`。

当前正式表有 237 条唯一全文；424 条候选（247 verified、123 pending、54 restricted）。

批次 208 发现一条美国公共电视节目目录记录：“Dialogue on Red China”（National Educational Television，1964-02-03）。AAPB 展示页触发网络验证挑战；Digital Commonwealth 合作馆藏页经 Scrapy 请求也返回 “Sorry, we can't verify your browser!”。已将其纳入受限候选，不尝试通过挑战；目录/搜索元数据不作为正文。1 candidate、0 verified、1 restricted；资料库仍为 236 条唯一全文，423 条候选（246 verified、123 pending、54 restricted）。审计见 `data/reviews/aapb-dialogue-red-china-1964-20261107.json`。

当前交付包校验：Excel 240 条数据、严格九列；ZIP CRC 通过，包含 69 个正文附件和 276 个 SHA-256 命名的已核实材料证据文件。全量测试 207 项通过，`scrapy check` 为 OK；SQLite integrity_check 与外键检查通过。

批次 207 对 1949—1972 年美国媒体做早期报纸发现：Firecrawl 搜索获得 2 个含中国/朝鲜战争报道线索的 1950 年报纸整版页面（Virginia Chronicle、国会图书馆），但两站 `robots.txt` 均禁止请求页面，且命中不是可独立核验的文章记录；未访问正文、未将摘要作正文。另检查马里兰大学相关数字档案，所列均为外交/军事文件而非美国媒体。搜索到的艾森豪威尔 1958 年台湾海峡广播讲话经 Scrapy 核验后发现已在早期批次入库，按原始 URL 记为重复发现，重复计数增加 1。批次 207 新增 0 条唯一全文，正式表仍为 236 条；候选状态 422 条（246 verified、123 pending、53 restricted）。早期媒体覆盖仍待补。检索记录见 `research/firecrawl/early-us-media-1949-1972-20261107/`。

当前资料库有 236 条唯一全文；421 条候选（245 verified、123 pending、53 restricted）。批次 206 新增 Dean G. Acheson 的 “Crisis in Asia - An Examination of U.S. Policy”：WorldJPN 完整演讲页注明其载于《Department of State Bulletin》1950-01-23 第 111—118 页，FRUS 官方脚注交叉确认刊载日和来源。数据库中的 1950-01-12 是演讲日，未用作“时间”。原文保存 35,775 字符、78 段，按原页全文标记和末句核验；详情见 `data/reviews/acheson-crisis-in-asia-1950-20261107.json`。批次 202 核验 4 份 1989 年 CBS 天安门新闻 PDF 的来源元数据与独立附件；May 16—19 transcripts 均经逐页核对后入表。详情见 `data/reviews/cbs-may16-1989-transcript-20261107/`、`data/reviews/cbs-may17-1989-transcript-20261107/`、`data/reviews/cbs-may18-1989-transcript-20261107/` 和 `data/reviews/cbs-may19-1989-transcript-20261107/`。批次 199—201 进一步检查 Dan Rather 档案文档页，未确立精确日期的扫描稿与索引页仍 pending，不进入正式资料表。批次 203 核验一篇 VOA 官方历史回顾的全文和日期，但正文没有中国相关内容，故从正式表撤回；批次 204 找到一篇直接讨论中国与朝鲜战争的杜鲁门记者会全文，但页面只给出会议发生日期，未证明独立发布日期，仍 pending。发布日期审计还将两条杜鲁门图书馆资料（1950 年记者会、1952 年演讲）从正式表撤回：其日期仅在正文首行出现，没有页面发布日期字段或元数据；原始证据保留，适配器已改为只接受页面明确标记的发布日期。批次 205 的 GovInfo Congressional Record PDF 虽公开且涉及中国，但 22 页文件在末页中途截断，仍 pending。复核见 `data/reviews/truman-china-news-conference-1951-20261107/publication-date-audit.json`、`data/reviews/voa-mission-1960s-1970s-20261107/review.json`、`data/reviews/truman-china-news-conference-1951-20261107/review.json` 和 `data/reviews/govinfo-congressional-record-china-1951-20261107/review.json`。

批次 198 后正式表仍为 233 条唯一资料；404 条候选（242 verified、109 pending、53 restricted）。本批通过 Firecrawl 发现 VOA 对华广播史相关学术研究线索，随后用 Scrapy 遵守目标站 `robots.txt`；站点禁止请求该页面，因此候选 405 标记 restricted，没有使用搜索摘要替代正文。发现记录保存在 `research/firecrawl/early-voa-discovery-20261107/search.json`。

最新状态：正式表 233 条唯一资料；403 条候选（242 verified、109 pending、52 restricted）。批次 197 新增 CBS Evening News with Dan Rather 的 1989-05-15 扫描 transcript，作者 Dan Rather，正文 5,761 字符；三页 PDF 与存档页逐项核对，详情见 `data/reviews/cbs-may15-1989-transcript-20261107/review.json`。本轮修正了 Scrapy 对 HTTP 3xx 的处理：错误响应仍交给访问策略，但普通重定向可继续跟随；明确检测 Cloudflare Turnstile 后将其标记为 restricted，不尝试通过。批次 193 的 C-SPAN 页面被 robots.txt 以 HTTP 403 拒绝；批次 194-196 核查 Dan Rather Tiananmen 档案索引、transcript compilation 和单篇文档页，只有链接索引的页面保留为 pending；批次 197 通过原始附件 PDF 与其元数据页面完成全文核验。批次 192 核查 American Archive of Public Broadcasting 一条涉及尼克松对华政策的公开目录线索。原页面 302 跳转到 Cloudflare Turnstile challenge；challenge 页 HTTP 200，但明确要求人机验证，故标记 restricted，不尝试通过挑战或访问媒体文件。批次 191 检查 NYT 1949 年“中国共产党政府公告”档案页面；robots.txt 返回 HTTP 200，但禁止抓取文章路径，因此标记 restricted，未请求文章页、未用 Firecrawl 抓取受限正文，也未将搜索摘要作为正文。发现记录见 `research/firecrawl/nyt-1949-prc-proclamation-20261107/`。批次 190 新增 Radio Free Asia 2014-12-04 报道 “China, Vietnam Among ‘Worst Abusers’ of Internet Freedom”，作者 Joshua Lipes，正文 6,297 字符。原页可见日期为 2014.12.04，结构化时间为 2014-12-05T00:31:00Z；按原页显示日期入表。robots.txt 与来源页均返回 HTTP 200。详情见 `data/reviews/rfa-2014-internet-freedom-20261107/review.json`。批次 189 新增 RFA 2012-09-24 报道 “China Blazes Net-Muzzling Trail”，作者 Parameswaran Ponnudurai，正文 6,019 字符。可见日期与结构化日期一致；Scrapy 遵守 robots.txt，页面 HTTP 200。详情见 `data/reviews/rfa-2012-net-muzzling-20261107/review.json`。批次 188 检查 CNN 2019 年天安门回顾页；Scrapy 收到 robots.txt 的禁止指令后未请求文章页，candidate 标记 restricted，未用 Firecrawl 或搜索摘要替代正文。早期媒体覆盖缺口核查发现 UCLA Special Collections 的 Tiananmen 档案包含广播录像与索引，但录像需到馆观看，研究指南也仅限现场查阅，不构成可在线取得的全文，因此没有建立正式材料记录。批次 187 新增 VOA Learning English 对中美贸易争端影响的解释报道 “Counting the Cost of the US-China Trade War”，来源页日期为 2019-05-06，正文 4,333 字符，robots 与原页均 HTTP 200。对批次 185、187 的来源字段复核发现 VOA Learning English 的 `keywords` 元数据是栏目名而非主题词；已从原 HTML 重新核验正文，将两条关键词更正为正文可证的主题词，并为适配器增加规则避免将这些栏目名写入未审阅记录。批次 186 新增 VOA 2018-07-06 报道 “US, China Slap Tariffs on Billions of Dollars of Each Other's Exports”，正文 4,143 字符，robots 与原页均 HTTP 200。批次 185 新增 VOA Learning English 对 2018 年中美贸易摩擦的同期报道 “Trade Dispute between US, China Rises”，来源页可见日期与结构化发布日期同为 2018-06-15，正文 3,319 字符，robots 与原页均 HTTP 200。两个 2018 年原始 URL 分别保留。批次 184 检查 AP News 的 “AP Was There: Tanks rumble out of Tiananmen Square” 档案重刊线索；Firecrawl 仅用于发现，AP robots.txt 返回 HTTP 200，原文页返回 HTTP 403，故标为 restricted，不以搜索摘要代替正文，也不改用 Firecrawl 抓取受限原页。该报道的发现描述称其最初发表于 1989-06-05，但没有将其作为来源页发布日期写入正式表。批次 183 检查国务院历史办公室 FRUS《上海公报》页面；Scrapy 遵守 robots.txt，robots 与原页均 HTTP 200，适配器提取到来源标题与正文，但页面没有可独立核实的精确发布日期。公报落款日期不能替代来源发布日期，因此 candidate 保持 pending、不纳入正式表。批次 182 新增 APP 所载尼克松与周恩来 1972-02-21 北京宴会祝酒词全文，正文 3,291 字符，robots 与来源页均 HTTP 200。批次 181 的 USC 尼克松记者会页面显示事件日，但未能证明为页面发布日期，仍 pending，不纳入正式表。

以下是批次 179 时的既有说明，后续批次状态以本节“最新状态”和对应批次记录为准：

当前正式表有 226 条唯一资料。批次 180 发现一篇直接研究 VOA 与中国普通话广播的开放期刊论文，期刊页显示 2021-12-08 和 CC BY-SA 4.0，但 Scrapy 请求前即由 robots.txt 拒绝；未请求 PDF，候选标为 restricted，不加入正式表。当前资料库有 387 条候选状态行（235 verified、104 pending、47 restricted）和 226 条正式资料。批次 179 新增约翰·F·肯尼迪 1962 年总统记者会记录，来源页日期为 1962-06-27，正文 30,438 字符，包含台湾海峡、金门与马祖的政策表述。批次 177 新增 2023-09-27 西米谷共和党候选人辩论逐字稿，正文 103,680 字符，包含中国与台湾议题。批次 176 新增 1992 年圣路易斯总统辩论逐字稿，来源页日期为 1992-10-11，正文 91,421 字符，包含专门的 “China-U.S. Relations” 环节；来源页没有摘要，摘要字段留空。批次 175 对 PBS NewsHour 2021 年 Tiananmen 访谈页完成视频文字稿版式复核并新增 1 条全文；原页和 robots.txt 均 HTTP 200，页面日期为 2021-06-04，署名 Nick Schifrin、Dan Sagalyn，正文 6,357 字符，末段为播报署名。批次 178 检查国务院旧档案的 “China Conference Transcript” 线索时，robots 与页面 HTTP 200，但页面标题为 Technical Difficulties，正文明确写着 “Exception: forbidden”；候选及证据已标为 restricted，未尝试绕过或从搜索摘要取正文。批次 170 对 2019 PBS NewsHour transcript 完成来源版式复核并新增 1 条全文；批次 173 和 174 新增两条独立的 1999 年白宫/总统公开问答记录。下方较早批次数字属于历史运行记录，不能替代这一复核结果：旧 FRUS 适配器错误地将档案成文日期作为发布日期，40 条唯一 FRUS 材料已从正式表撤出，其 42 条候选状态改为 pending，保存的原始证据和撤出前备份均保留；今后该版式不凭 dateline 自动入表，须另行证明精确发布日期。此前工作簿中的这 40 条不符合用户日期规则，不应继续使用。

覆盖缺口核查（非采集批次）：对 1989 年 6 月 5 日 PBS NewsHour/MacNeil-Lehrer 及 AP 的同期材料做定向 Firecrawl 搜索，仅找到 YouTube 视频条目（描述明确提示部分报道片段已删除）与 PBS FRONTLINE 页面中的 AP 新闻摘录；未发现可核验的原始完整稿件，因此新增候选和正式资料均为 0。PBS 的 2001 年 retrospective transcript 已在批次 169 登记为 pending，尾部不完整，未提升为全文。搜索输出只作缺口核查，不作为正文证据；明细见 `research/firecrawl/early-media-tiananmen-1989-gap-20261107/search.json`。

批次 175 起初因视频文字稿版式未被普通文章适配器识别而保持 pending。对原始 HTML 逐段复核后，确认 56 个 transcript 段落块、6,357 字符，末段为 “For the ‘PBS NewsHour,’ I’m Nick Schifrin.”，可见与结构化日期同为 2021-06-04，页面列出 Nick Schifrin 和 Dan Sagalyn。增加仅匹配该 URL 的审阅指纹和末段门槛；正文、标题、日期、URL 变异及末段截断测试均拒绝。生产重抓时 robots 和页面 HTTP 200，候选转为 verified，正式表净增 1 条。本批是回顾报道，不能替代 1972—1991 同期媒体材料。复核见 `data/reviews/pbs-tiananmen-legacy-2021-20261107/review.json`。

批次 169 检索并抓取 PBS NewsHour《Tiananmen Papers》原始页面（2001-01-11）。Scrapy 遵守 robots.txt，robots 与页面均 HTTP 200；页面可见日期与 `article:published_time` 同为 2001-01-11，标题为 “Tiananmen Papers”，页面未标作者。正文 transcript 有 40 个段落/说话人块、6,325 字符，但最后一块只有 “ANDREW”，且 HTML 正文容器到此结束，无法确认全文完整。1 candidate、0 verified、1 pending、0 restricted/duplicate/unprocessed；不导出为已取得全文。原始页面证据及复核记录见 `data/evidence/` 与 `data/reviews/pbs-tiananmen-papers-2001-20261107/review.json`。本批不是穷尽性检索。

批次 170 重新核验 Firecrawl 发现的另一条 PBS NewsHour 节目 transcript，并经 Scrapy 遵守 robots.txt 直接抓取原页（robots 与页面均 HTTP 200）。可见日期 `Jun 4, 2019` 与 `article:published_time` 同日，`h1`、`og:title` 和 JSON-LD headline 一致；来源未标注作者，填“未注明”。对 transcript 容器内 84 个有序段落/说话人块进行来源版式核对，完整正文 10,451 字符，末段为嘉宾答谢；正文指纹必须与审阅快照完全相同。摘要和关键词照录 PBS 页面元数据。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。该 2019 年纪念报道属于后期回顾，不能替代 1972—1991 同期媒体材料。逐项记录见 `data/reviews/pbs-tiananmen-30-years-2019-20261107/review.json`。

批次 171 检索 Thomas Pickering 1999 年向中国政府作的使馆轰炸口头说明。Scrapy 的 robots 与原页响应均 HTTP 200，但原页正文实际是 “Technical Difficulties / Exception: forbidden” 错误页；该响应从 allow 更正分类为 restricted，不使用 Firecrawl 搜索结果中展示的正文片段。1 candidate、0 verified、1 restricted。

批次 172 检查了另一官方美国使馆档案 URL；robots.txt 与目标页均返回 HTTP 403。遵守访问限制后停止，不读取搜索摘要作为正文，也未尝试改用其他代理。1 candidate、0 verified、1 restricted。

批次 173 新增克林顿总统在 1999-05-08 离开 Tinker 空军基地时关于中国驻贝尔格莱德使馆遭轰炸的记者问答。APP 原始页及 robots.txt 均 HTTP 200；来源页面的标题、署名 William J. Clinton、发布日期 1999-05-08 和正文边界核验通过，正文 5,122 字符。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。三批逐项记录见 `data/reviews/` 中对应 JSON；三批均非穷尽性检索。

批次 174 新增 APP《Press Briefing by Joe Lockhart》全文，发布日期 1999-05-10，作者字段照录 APP 页面归属 William J. Clinton，正文 17,248 字符并以页面原始 `END 4:00 P.M. EDT` 标记闭合。页面及 robots.txt 均 HTTP 200，正文含媒体对 5 月 7 日使馆轰炸的提问和白宫答复。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。该记录与批次 173 为不同原始来源链接，分别保留。

批次 158 核验 Timothy B. Weston 的开放论文 “Mediating Asia| Pressing the Issue: Sino-American Discourse on the Proper Role of the Media, Past and Present”。IJoC 原页显示发布日期 2017-03-22，并与 `citation_date` 一致；不采用 `DC.Date.issued` 中的卷年 2017-01-01。Scrapy 对 robots.txt 和官方 PDF 均返回 HTTP 200。专用版式适配器核对原页作者、标题、摘要、关键词及 PDF URL，并确认 PDF 首页题名/作者/期刊名匹配且 15 页均有正文文本。正文 50,544 字符；1 candidate、1 verified，无其他状态。

批次 159 新增三篇 VOA 2014 年天安门周年报道全文，分别发表于 2014-06-02、2014-06-03 和 2014-06-03，正文为 13,161、4,459、1,812 字符。三条来源页及 `robots.txt` 均为 HTTP 200，相关路径未被禁止。复核发现两篇长报道采用 `<em>` 导语和 `<br>` 分段，旧适配器一度只抽取 dateline；该不完整结果已由完整换行版正文重提取覆盖，并新增回归测试，禁止仅凭 dateline 标记全文核验通过。批次 3 candidate、3 verified、无其他状态。这些是 2014 年回顾/周年报道，不能补作 1972—1991 同期材料。

批次 160 检索到 UPI 档案报道 “China accuses VOA of reporting 'lies'”，线索标注日期 1989-06-12。Scrapy 获取 `robots.txt` 后请求原发布页收到 HTTP 403，候选按访问限制记为 restricted；未使用 Firecrawl 或镜像尝试绕过，未取得正文，不纳入正式表。批次 1 candidate、0 verified、1 restricted。

批次 161 发现李秋杨《“中国制造”国际形象的 媒体话语研究 = International Image of “Made in China” in Media Discourse》，研究对象直接包含《纽约时报》约 25 年报道。期刊原页 Firecrawl 原始 HTML 显示 Published 与 `citation_date` 同为 2015-11-15，并声明 CC BY-NC-SA 4.0；但遵守 `robots.txt` 的 Scrapy 取得 robots、原页面/PDF 请求均遇 HTTP 403。未以 Firecrawl 再取受限 PDF，候选列为 restricted，正文不入表。为可访问的 OJS 期刊 PDF 增加通用元数据/许可/首页及逐页全文核验适配器，并通过独立测试；批次 1 candidate、0 verified、1 restricted。

批次 162 新增 Ran Wei、Ven-hwei Lo、Guy Golan 的 IJoC 论文 “Examining the Relationship Between Presumed Influence of U.S. News About China and the Support for the Chinese Government’s Global Public Relations Campaigns”。官方发布页与 PDF 均 HTTP 200，`robots.txt` 允许；发布日期可见标签和 `citation_date` 同为 2017-07-14。核对了原页题名、三位作者、期刊、PDF 链接及 PDF 首页信息，18 页均有正文文本，全文 50,921 字符。修正了作者名被机构信息隔开的匹配规则，以及题名元数据多空格导致的误判；增加回归测试。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。详细核验见 `data/reviews/ijoc-us-news-presumed-influence-2017-20261107/review.json`。

批次 163 新增 VOA 2016-10-07 报道 “Who Are the Chinese Trolls of the '50 Cent Army'?”（Joyce Lau，6,101 字符），内容讨论中国网络评论员、对外社交平台活动与网络舆论引导。原页面及 `robots.txt` 均 HTTP 200；页面可见日期、作者和标题已核对，正文完整性与元数据核验通过。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。此前检索 1949—1991 年 VOA 同期报道未找到符合精确发布日期和可访问原文条件的新增页面；结果多为后期回顾或检索线索，不计为同期材料。批次详情见 `data/reviews/voa-china-information-operations-2016-20261107/review.json`。

批次 164 新增 PBS FRONTLINE《THE TANK MAN》完整节目文字稿，播出日和页面发布日期均为 2006-04-11，署名 Antony Thomas，正文 65,347 字符。原页与 `robots.txt` 均 HTTP 200。适配器按页面结构截取开场文字稿至最后一段节目对白，并以转入制作名单的重复节目标题作为闭合标记；保留源页面中的 112 个 U+FFFD 字符，不猜补丢失字符。AAPB 对应档案页返回 Cloudflare 验证挑战，没有绕过；PBS 原始文字稿页可合法访问。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。具体检查见 `data/reviews/pbs-frontline-tank-man-2006-20261107/review.json`。

批次 165 新增 Hongmei Li 的 IJoC 论文 “The Chinese Diaspora and China’s Public Diplomacy: Contentious Politics for the Beijing Olympic Float”，期刊原页 Published 与 `citation_date` 同为 2012-09-17；官方 PDF 35 页、正文 109,725 字符。批次 166 新增 Dexin Tian、Chin-Chung Chao 的 “The American Hegemonic Responses to the U.S.-China Mid-air Plane Collision”，原页 Published 与 `citation_date` 同为 2008-01-17；官方 PDF 19 页、正文 62,028 字符。两篇原页、PDF 均 HTTP 200，遵守 robots.txt；均核对了题名、署名、期刊、PDF URL、首页题名/作者/期刊以及逐页全文文本。作者与首页的分隔排版按逐人核对；发布日期采用可见 Published 标签，不用卷期日期或事件日期。两份 PDF 首页均载有 CC BY-NC-ND 授权声明。每批 1 candidate、1 verified，无 pending/restricted/duplicate/unprocessed。详情分别见 `data/reviews/ijoc-chinese-diaspora-public-diplomacy-2012-20261107/review.json` 与 `data/reviews/ijoc-us-china-midair-discourse-2008-20261107/review.json`。

批次 131 发现两篇 PMC 候选，但全文表明其自身研究语料主要为中国媒体，纽约时报等仅为文献回顾或背景，故均转为 pending 并排除正式表，统计为 2 candidate、0 verified、2 pending。此次同时重新解析 17 篇既有 PMC 论文：7 篇正文清除平台自动生成的 Associated Data 模块，13 篇摘要剔除嵌套关键词栏；保留作者自己的原始数据声明及正文段落，来源、作者、标题和日期未变。

批次 132 实际取得并核验三篇直接相关的开放论文：2020-10-04 “US–China Relations: Nationalism, the Trade War, and COVID-19”（48,374 字符）；2020-09-01 “The Politics of Blaming: the Narrative Battle between China and the US over COVID-19”（49,573 字符）；2023-02-13 “Diversionary Words: Trump, China and the COVID-19 Pandemic”（62,439 字符）。各篇原始页面及 robots.txt 均 HTTP 200，摘要和关键词优先采用来源原文。批次统计 3 candidate、3 verified、0 pending/restricted/duplicate/unprocessed。

批次 133 尝试两篇 AP 原始页面，均返回 HTTP 403：0 verified、2 restricted。复查既有未处理候选后，17 条明确受 robots.txt 限制的记录已归入 restricted；其中 13 条原有失败备注被正确分类，另 4 条 CNN/Reuters URL 经本轮 robots.txt 检查确认禁止抓取，未请求被禁止的正文。普通网络错误保持可重试，不伪称为访问限制。

批次 134 核验三份 PBS News 发布的 AP 报道：2023-08-09 “Biden issues an executive order restricting tech investments in China”（4,552 字符，Josh Boak, Associated Press）；2024-12-03 “China bans exports to U.S. of key high-tech materials in response to chip sanctions”（5,275 字符，Elaine Kurtenbach, Associated Press）；2024-05-15 “In first AI dialogue, U.S. cites 'misuse' of AI by China, Beijing protests Washington's restrictions”（3,451 字符，Jamey Keaten, Associated Press; Kelvin Chan, Associated Press）。发布日期须同时通过可见 time、time content 与 article:published_time 核验，标题与 og:title 一致；只取唯一文章正文，排除 READ MORE 推荐和捐款模块，保留原始段落、段标题及贡献者结尾。批次为 3 candidate、3 verified、0 pending/restricted/duplicate/unprocessed。发布来源按 PBS 页面照录，不假称取得 apnews.com 的受限全文。

批次 135 的国务院 X 帖文被 robots.txt 禁止抓取；批次 136/137 的两条 DVIDS 视频发布页均 HTTP 403，三条合计 0 verified、3 restricted。批次 138 获取三页白宫公开视频原始 HTML，虽含文字稿，但日期无明确发布标签或独立发布时间字段，全部 pending。没有用事件日期、搜索摘要或推荐视频日期补填。

批次 139 新增两条公开新媒体全文：The Associated Press（`apnews.com` 账号，2025-05-10，中美关税会谈，208 字符）和 The New York Times（`nytopinion.nytimes.com` 账号，2025-06-23，涉华观点引用，225 字符）。标题照录发布页真实 `<title>`，分别为 `@apnews.com on Bluesky`、`@nytopinion.nytimes.com on Bluesky`，不借用链接文章标题；作者保留账号显示名，不把被引用作者当作发帖作者。原始 HTML 与 Bluesky 文档公开的无须认证 `getPosts` JSON 双重保存；账号域名、DID、AT URI 和记录键必须一致。正文逐字取 `record.text` 并与发布页对应，排除平台附加的外部卡片链接、描述和回复；时间取 `record.createdAt`，不用 `indexedAt`，并核对原页 `datePublished` 同日。摘要按正文整理并加规定前缀。批次为 2 candidate、2 verified、0 pending/restricted/duplicate/unprocessed。

Bluesky 采集只对这两个已观察账号/版式启用。CSV 的 `metadata_url` 指向官方公开 `https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris=...`；`platform_id` 必须使用包含 DID 和记录键的完整 `at://.../app.bsky.feed.post/...`，避免不同账号间记录键冲突。字段不一致或缺少接口证据时保持 pending。官方参考：[公开读取接口](https://docs.bsky.app/docs/api/app-bsky-feed-get-feed)、[帖文 text/createdAt 字段](https://docs.bsky.app/docs/tutorials/creating-a-post)、[域名账号验证](https://bsky.social/about/blog/4-28-2023-domain-handle-tutorial)。X/Twitter 的已知域名别名在明确同一平台内容 ID 时共用身份键，原始 URL 不改写；不同平台同号仍分别保留。

批次 167 检索 OpenSIUC 的 “NEWS FRAMING OF GOOGLE’S WITHDRAWAL FROM CHINA: A COMPARISON BETWEEN AMERICAN AND CHINESE NEWSPAPER”。候选元数据记录了精确在线发布日期 2011-02-10，但 Scrapy 遵守 robots.txt 后，PDF 原始下载端返回 HTTP 403，因此全文不可核验，记录为 restricted，不纳入正式表，也未改用其他方式获取受限全文。批次 1 candidate、0 verified、1 restricted。Firecrawl 针对该开放研究文献主题的补充搜索未返回相关网页结果。审计见 `data/reviews/bepress-google-withdrawal-china-2011-20261107/review.json`。

批次 168 核验 Canadian Center of Science and Education 期刊 English Language and Literature Studies 论文 “Neighbor by Miles and Neighbor by Steps: A Comparative Study of China’s National Image Construction”。期刊 PDF 原始下载端和 robots.txt 均 HTTP 200；文章元数据落地页返回 HTTP 404，但 PDF 首页自身明确列出在线发布日期 2025-08-26、作者 Jie Zhang、Mohd Azidan Bin Abdul Jabar、Farhana Muslim Binti Mohd Jalis、DOI、摘要和关键词，并含 CC BY 4.0 许可。核对了 15 页连续页码 16—30，逐页均含文本；全文 63,275 字符。论文直接分析《纽约时报》对中国国家形象的建构，全文取自原始 PDF，不使用搜索摘要补字段。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。详情见 `data/reviews/ccsenet-china-image-construction-2025-20261107/review.json`。

数据库累计 374 条候选状态记录：228 verified、103 pending、43 restricted、0 unprocessed；另有 17 次历史重复发现，其中 2 次对应已撤出资料，正式表重复计数合计为 15。正式表按唯一材料保存 219 行。质量修正明细保存在 `data/reviews/pmc-cleanup-2026-11-06/`、`data/reviews/frus-publication-date-2026-11-06/`、`data/reviews/media-access-2026-11-06/` 和 `data/reviews/bluesky-public-records-2026-11-06/`。媒体、社交账号、早期及中文研究文献仍需扩充，未宣称穷尽。

交付包 `data/materials-delivery.zip` 包含九列工作簿、64 个被引用的长正文文件、批次/覆盖报告以及 `reports/provenance-index.json`。证据索引逐条对应 219 条正式资料；精确核验记录与历史候选证据版本的数量以包内索引为准。每个交付文件的 SHA-256 与数据库证据记录一致。此前未入表或撤出的记录不混入这份正式证据索引。

批次 140 新增四条公开总统文件全文：1971-07-15 访华邀请电视讲话、1971-11-29 访华日期联合公告、1972-02-27 联合声明、1972-02-17 启程讲话。页面可见日期和结构化日期一致；注释分别证明公开广播、新闻发布或当日发布，未仅凭事件日期入表。4 candidate、4 verified，其他状态为 0。

此次复查全部 51 条既有 APP 文件，补录档案页明确列出的署名（人物/机构名称与引用栏对应），23 条正文修正标题、列表、表格遗漏或原始换行。逐条确认主体全部非空白字符及顺序与保存原始 HTML 一致；原始备份和前后审计保存在 `data/reviews/presidency-body-author-2026-11-06/`，不把编辑注释或引用栏混入正文。140 项测试通过。

现在可重复执行交付校验与打包：

```powershell
.\.venv\Scripts\research-crawler.exe deliver --db data/research.sqlite3 --output data/materials-delivery.zip
```

命令在数据库一致性快照下核对原始证据 SHA-256，生成并逐格回读九列工作簿和 UTF-8 长正文，加入全部批次报告、覆盖统计与证据索引，验证 ZIP 后原子替换目标包。失败时保留旧包。该命令检验已保存文件的一致性，不代替原页日期与完整性人工核验；新入表或重新核验时，系统将字段出处、摘要来源及实际使用的证据 ID 与资料正文原子保存；精确关联记录仅打包本次核验引用的文件。旧记录未保存历史关联，因此纳入其声明元数据 URL 的已核验抓取版本，并明确标记为候选证据版本，不推测历史使用关系。只含正式材料的证据，不附带撤出材料。

批次 141/142 分别尝试纽约时报中文网的 2015 年阿里巴巴收购南华早报报道和 2021 年中国对外形象报道，robots.txt 均禁止正文请求；各 1 candidate、0 verified、1 restricted。未改用其他传输方式绕过限制。

批次 143 核验首篇中文研究全文：2015-11-30《从公共外交的视角看中国国家形象宣传片效果/Assessing the Effect of China's National Publicity Films from the Perspective of Public Diplomacy》，来源 Journal of China and International Relations，作者 Cao Wei; Xia Yuchen（照录发布页），PDF 20 页（印刷页 97—116），正文 23,049 字符。Published、citation_date、DC.Date.issued 一致，未使用 2019 年修改日期；摘要照录期刊页中英原文、关键词取 PDF 原文。论文直接分析美国主流媒体和美国受众，不因仅有美国媒体引文而入表。1 candidate、1 verified。

批次 144 核验英文历史研究全文：2016-08-30 “Perceiving Different Chinas: Paradigm Change in the ‘Personalized Journalism’ of Elite U.S. Journalists, 1976–1989”（Excel 标题照录原页双引号），International Journal of Communication，Yunya Song; Chin-Chuan Lee，20 页（4460—4479），正文 70,227 字符，完整保存为 UTF-8 旁文件。文章 Published 与 citation_date 同为 2016-08-30；DC.Date.issued 的 2016-01-05 对应年度卷页的发布日期，未拿卷日期替代文章日期。全部页面已渲染检查；使用 pdfplumber 版面提取避免 pypdf 的英文词内空格，对每页非空白字符多重集合进行独立 pypdf 核对，无增删字符；保留正文、表格、注释和参考文献，原始 PDF 同包交付。1 candidate、1 verified。

批次 145 核验两篇 1992—2016 年媒体全文：2016-12-29 “Fact check: Does China manipulate its currency?”（Paul Wiseman, Associated Press，5,554 字符）及 2009-06-10 “If China Pulls Away From the Dollar, What Happens to the U.S. Economy?”（原页无署名，作者填“未注明”，1,644 字符）。来源均按实际发布页填写 PBS News。完整文章容器及尾部边界已逐条复核，只排除捐款模块、空段落和装饰图片，保留原始拼写；摘要按正文整理并加规定前缀。2 candidate、2 verified。

上述正文与字段复核日志位于 `data/reviews/aau-public-diplomacy-2015/`、`data/reviews/ijoc-us-journalists-2016/`、`data/reviews/pbs-earlier-trade-20261106/`；原始发现及 Firecrawl 发布页抓取保存于 `research/firecrawl/earlier-media-literature-2026-11-06/`。本轮补上了 1992—2016 年媒体与研究文献的实际全文记录，但更早时期的媒体以及全部四时期的广度仍不足。

批次 146 实际新增三条台海危机公开文件：1955-01-24 “Special Message to the Congress Regarding United States Policy for the Defense of Formosa.”（9,577 字符）；1958-09-11 广播电视讲话 “Radio and Television Report to the American People Regarding the Situation in the Formosa Straits.”（15,697 字符）；1958-09-13 致赫鲁晓夫信 “Letter to Nikita Khrushchev, Chairman, Council of Ministers, U. S. S. R., on the Formosa Situation”（3,982 字符）。署名均照录 Dwight D. Eisenhower；信的注释明确区分 Dated September 12 与 Released September 13，正式表采用后者。3 candidate、3 verified，其余为 0。

本次同时回查 55 条既有 APP 记录的日期注释：1972 年访华行程表（原 id 53）和 1984 年民主党纲领（原 id 169）的原页明确说明原件无日期，档案站用事件起始日/大会起始日代填。两条已从正式库撤出并改为 pending；保存原文、撤出前备份和逐条日志于 `data/reviews/app-undated-and-release-date-20261106/`。这些旧表日期不符合严格发布日期规则，请使用当前更新包。本轮新增 3、撤出 2，唯一正式资料净增 1。

程序现保存 `material_verifications` 与 `material_metadata_evidence`：新的字段出处、摘要类型和精确证据 ID 与正文一同提交；记录失败则整体回滚，复核更新替换旧关联。证据索引区分 `exact` 与 `legacy_candidate_captures`，后续抓到的其他版本不会混入 `exact` 记录。原有记录不自动推测关联。上轮四条资料本轮重新执行原文复核，因此连同三条新资料共 7 条精确关联；其中两篇 PDF 的元数据 ID 均已实际保存。Excel 仍只有九列。日期拒绝规则、迁移、持久化、关联替换、失败回滚与交付测试共 148 项通过。

批次 147 核查 5 页 1949—1972 年公开讲话原文，实际新增两篇：1951-04-11 杜鲁门 “Radio Report to the American People on Korea and on U.S. Policy in the Far East.”（13,773 字符）及 1966-07-12 约翰逊 “Remarks to the American Alumni Council: United States Asian Policy.”（14,270 字符）。两篇均有全国广播说明，对华内容直接相关；原始 HTML 主文非空白字符序列与保存正文一致，摘要依正文整理并加前缀。原页和 robots.txt 均 HTTP 200。杜鲁门 1950 年“真相运动”讲话与肯尼迪 1962 年 VOA 周年讲话只论一般传播使命，缺少直接对华内容，暂作背景候选；肯尼迪 1960 年退伍军人大会讲话虽涉华，但来源正文句中有长横线缺口，无法确认完整，保留 pending。另从保存的检索结果登记 2 次既有材料重复发现，只增加重复计数，不新增资料行或伪称重新抓取。批次统计 7 candidate、4 verified（其中 2 条是既有资料）、3 pending、2 duplicate、0 restricted/unprocessed；正式表只净增 2 行。日志见 `data/reviews/early-public-communication-20261106/review.json`。

批次 148 新增五篇 1992—2016 年 PBS News 原文：2009-06-02 “Leader Profile: Student Activist Wang Dan”（PBS News Hour，2,311 字符）；2015-11-10 “Chinese hackers could face U.S. criminal charges says DOJ official”（Tami Abdollah, Associated Press，3,405 字符）；2015-04-01 “Obama creates first sanctions program against cybercriminals”（Ken Dilanian, Associated Press，4,419 字符）；2015-07-25 “Data breach may help Chinese government identify U.S. spies”（Kenzi Abou-Sabe，2,701 字符）；2016-05-13 “China has reclaimed 3,200 acres in South China Sea, Pentagon says”（Lolita C. Baldor, Associated Press，4,496 字符）。来源按实际发布机构 PBS News 填写，不把它们声称为 apnews.com 直接抓取。五个原页及 robots.txt 均 HTTP 200；摘要照录来源提供的 meta description，关键词依正文提取。批次为 5 candidate、5 verified，pending/restricted/duplicate/unprocessed 均为 0。

上述五篇正文已逐条审阅，只有对应 URL、日期、标题、署名和完整正文 SHA-256 全部一致时，适配器才接受无贡献者结尾的页面；正文变化仍须重新审阅。正文提取保留引述框和其后未包在段落标签中的文字，并保留换行产生的词间分隔；列表结构出现无法消费的非标准文本时保持 pending。推荐链接、募款模块排除，原始拼写和重复出现的原文引述保留，不作事实纠正。一次 Firecrawl 传输失败及一次成功重试均保存；成功的原始 HTML 与 Scrapy 取得的同篇正文指纹一致。另回查既有五篇 PBS 资料，原 id 218 的正文在两个链接后多插入的逗号前空格已按原始 DOM 修正（4,552 → 4,550 字符），摘要、来源及日期等不变。此后 8 篇当前适配器支持的正式 PBS 正文重解析均与数据库一致，另两篇先前人工核验版式仍需人工审阅。全部 165 项测试及 Scrapy 检查通过。审阅、来源比较和更正记录见 `data/reviews/pbs-pre2017-china-discourse-20261106/`。

批次 149—151 各新增一篇研究全文：2007-07-11 “U.S. and NATO Apologies for Chinese Embassy Bombing: A Categorical Analysis”（Dexin Tian，International Journal of Communication，17 页，61,756 字符）；2019-01-31《作为一种跨国挑战的“中国挑战”: 对当代美中关系的启示 / The “China” Challenge as Transnational Challenge: Implications for Contemporary U.S.-China Relations》（Chengxin Pan，Journal of China and International Relations，16 页，39,527 字符）；2019-12-01 “The Competitive Strategy and Adjustment of the US Trump Administration's China Policy/竞争战略与美国特朗普政府对华政策调整”（Tang Yongsheng; Li Wei; Shen Zhixiong，同刊，12 页，22,344 字符）。标题和作者照录期刊发布页，保留与 PDF 标点、冠词或作者汉字写法的来源差异说明，不自行改题或猜姓名。

三篇共 45 页均已渲染检查；正文保留原语种、原始顺序、注释及参考文献，仅去除明确的重复页眉和页码，并逐页以独立提取器核对非空白字符。摘要照录来源，中文关键词采用 PDF 原文。文章 Published 与 DC.Date.created 一致；DC.Date.issued 则与卷期页日期一致，故采用文章明确发布日期，未以卷期日期或 2808 的不完整引用年份 2018 代替。3579 的引文页码元数据为 49—63，但实际链接 PDF 完整页码为 64—75，该元数据未作正文完整性依据。原 PDF、发布页及卷期页均随包保存。批次 149—151 各为 1 candidate、1 verified，其余为 0。

批次 153/154 新增两篇 VOA 原始页面全文：2009-02-18 “China Erred at Tiananmen: Bao Tong”（VOA，1,618 字符）和 2019-06-04 “China Blacks Out Tiananmen Coverage in Massive Media Lockdown”（VOA News，6,854 字符）。2013 年同题材页面已在库，按原链接识别为一次重复发现，仅更新计数。Scrapy 遵守 robots.txt，目标页与 robots.txt 均 HTTP 200；页面原始 HTML 与 Firecrawl 辅助页面抓取均已留证。2009 年页面可见时间对应 2 月 18 日美东时间，虽然 UTC JSON-LD 日期、URL 日期和正文 dateline 落在 2 月 19 日，正式表采用可见发布日期。2019 年页面 H1 比 og:title/JSON-LD headline 多“Massive”；在 JSON-LD URL 与原页链接一致且分享标题与 JSON-LD 相符时，照录页面 H1。正文保留全部文章段落及 VOA 对华普通话广播时长信息，排除独立图片说明/嵌入和明确的公关联系方式、记者贡献行。批次 153 最终 2 候选（1 新增、1 已有材料重复，重复发现计 1）；批次 154 为 1 候选（1 新增）；待核验/受限为 0。审计见 `data/reviews/voa-china-broadcasts-20261106/`。

批次 155 复核三份 1972—1991 年总统公开资料：1989-06-05 “The President's News Conference”（George Bush，19,093 字符）和 1990-06-04 “Statement on the Anniversary of the Suppression of the Demonstrations at Tiananmen Square”（George Bush，2,671 字符）已在库中；本批各重新核验一次，未增加资料行。新增 1989-11-30 “Memorandum of Disapproval for the Bill Providing Emergency Chinese Immigration Relief”（George Bush，4,779 字符）。页面可见日期与机器可读日期一致；61、14、5 个正文块重新解析后逐字符等于入库正文。原始页面和 robots.txt 均 HTTP 200，未用搜索摘要代替全文。3 candidate、3 verified（1 新增、2 既有）、2 duplicate，其余状态为 0。逐条日志见 `data/reviews/presidential-public-statements-1989-1990-20261106/`；该批增加历史时期覆盖，但不代表该时期资料已完整。

批次 156 新增 5 篇总统档案原文：1979-01-29 邓小平欢迎仪式讲话（6,165 字符）、1979-01-30 会谈后记者问答（1,795 字符）、1979-02-01 联合新闻公报（3,243 字符）、1984-04-30《美中文化交流协定文本》（8,069 字符）及里根复旦大学讲话（19,798 字符）。协议明确涉及美国之音和北京广播电台互访、交换节目材料与广播人员。本批 141 个有序正文块逐块复提，结果逐字符等于入库正文；页面可见发布日期与机器日期一致。5 candidate、5 verified、0 pending/restricted/duplicate/unprocessed。到目前 1972—1991 时期共有 20 条政府全文，媒体和广播范围仍需继续检索。详细记录见 `data/reviews/deng-visit-and-cultural-exchange-1979-1984-20261107/`。

批次 157 新增 2 篇 VOA 原始报道：2009-06-03 “Cambodian Photographer Holds Tiananmen Exhibition”（Im Sothearith, VOA Khmer，英文原文1,838字符）和 2016-06-04 “Hong Kong Struggles to Keep Memory of Tiananmen Massacre Alive”（Joyce Lau，5,214字符）。均直接抓取原页面、采用可见发布日期并核实正文完整；均属 1992—2016 时期。两条候选、两条 verified，其他状态为0。AP 检索只得到 2019 年图片集，没有作为新闻正文入库。该批补充的是对 1989 事件后续纪念的报道，不是同期报道，因此 1972—1991 媒体空缺仍在。复核见 `data/reviews/voa-english-history-of-tiananmen-20261107/`。

批次 152 从已保存检索结果确认既有论文 OJS article/galley 1311/1066 实际重复出现 3 次；唯一 ID 对应同一篇已核验全文，仅更新重复计数，不增加正文行或声称重新下载。该批为 1 candidate、1 verified（既有）、3 duplicate，其余为 0。复核与交付审计见 `data/reviews/historical-discourse-literature-20261106/`。本轮累计新增 3 篇全文，其中 2 篇中文；总量 198，覆盖仍不充分，目标继续。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

项目依赖声明包含 Scrapy 和 openpyxl。本工作区当前虚拟环境已安装 Scrapy 2.19.0 与 openpyxl 3.1.5；新环境按上面的命令安装即可。

## 检索与候选 URL

按时期和来源类别生成查询式。计划覆盖指定媒体、政府机构、智库、新媒体账号和研究文献的中英文名称，将事件词翻译为中英文，并分别用中英文主题词组扩展。主题词组以 OR 组合，避免把所有来源、事件和主题词展开成上千条查询；查询标签唯一标识来源、事件和语种：

```powershell
.\.venv\Scripts\research-crawler.exe plan --period 2017-2025 --category government --output data/queries-2017-2025-government.csv
```

查询式是检索线索。使用官方目录、站内检索或获准的搜索服务查找原始发布页后，把候选链接整理成 UTF-8 CSV。CSV 不应把搜索摘要写入正文：

```csv
url,period,source_category,query_label,platform_id
https://www.whitehouse.gov/fact-sheets/2025/02/fact-sheet-president-donald-j-trump-imposes-tariffs-on-imports-from-canada-mexico-and-china/,2017-2025,government,trade-war,
```

候选 CSV 只承载链接和发现上下文，不构成已取得全文的依据。导入候选状态库：

```powershell
.\.venv\Scripts\research-crawler.exe import-candidates --csv data/candidates.csv --db data/research.sqlite3
```

## 抓取

抓取一个公开页面：

```powershell
.\.venv\Scripts\research-crawler.exe crawl --url https://www.whitehouse.gov/fact-sheets/2025/02/fact-sheet-president-donald-j-trump-imposes-tariffs-on-imports-from-canada-mexico-and-china/ --period 2017-2025 --category government --query-label trade-war --db data/research.sqlite3 --evidence-dir data/evidence
```

批量处理候选 CSV：

```powershell
.\.venv\Scripts\research-crawler.exe crawl-candidates --csv data/candidates.csv --db data/research.sqlite3 --evidence-dir data/evidence
```

对已有材料执行本地历史来源重验证（只读取数据库中已保存的原始证据，不发起网络请求）：

```powershell
.\.venv\Scripts\research-crawler.exe revalidate --db data/research.sqlite3 --output data/reviews/legacy-revalidation-20261107.json
```

只有当前适配器逐字段重解析结果与原记录完全一致的材料才会补建精确来源快照；不一致或无法重现的记录继续保留为 legacy，并写入报告。

如需对已抓取但仍 pending 的候选执行离线重放，追加 `--include-pending`。该模式只读取已有来源证据，不重新访问网站；只有证据哈希未变、正文与原页面匹配、元数据和精确日期通过现有验证器的记录才会晋级，其余候选保留 pending 并在 JSON 报告中附上来源链接和失败原因：

```powershell
.\.venv\Scripts\research-crawler.exe revalidate --db data/research.sqlite3 --output data/reviews/offline-pending-revalidation.json --include-pending
```

生成四时期 × 五类来源覆盖矩阵及无候选缺口清单：

```powershell
.\.venv\Scripts\research-crawler.exe coverage-audit --db data/research.sqlite3 --output data/reviews/coverage-audit-20261107.json
```

Scrapy 遵守 robots.txt，默认同一网域并发为 1、请求延迟 1 秒并启用 AutoThrottle。401、402、403 和明确付费墙信号会被标记为受限；系统不登录、不注入 Cookie、不绕过付费墙或其他访问控制。Scrapy 的解析器只为已实现的来源版型提供字段；没有可靠匹配的页面会留在待核验状态。

当前内置并完成真实页面全文试采的来源适配器包括白宫事实清单、美国国务院 2021-2025 归档讲话页、AP News 一类文章页、VOA News 一类文章页、Harry S. Truman Library 公共文件页、美国国务院 FRUS 文档页、The American Presidency Project 文档页和官方 PDF 报告。PDF 适配器保留原始 PDF 字节证据，按页提取文本；必须核实封面题名、印刷发布日期和发布机构，且每页都有文本层，扫描页或缺字段时保持待核验。AP 适配器只对 `apnews.com` 的已观察版式启用：标题、署名和发布日期须在页面可见，且正文必须位于单一 `.RichTextStoryBody` 容器；只取正文容器的直接段落，排除广告节点和外围页面模板。VOA 适配器要求页面 H1 与 NewsArticle 结构化标题一致、结构化作者若存在须与可见署名一致、`time[pubdate]` 与结构化发布日期同日；页面未标注作者时使用“未注明”。只取 `#article-content > .wsw` 的 dateline、正文段落、段标题和列表，排除媒体嵌入内容及作者简介。FRUS 适配器保留指定 TEI 文档区域的原始证据；文档 dateline 只能证明成文日期，该版式缺乏独立发布日期，因此不生成正式记录。Presidency Project 适配器只对已观察到的 `.node.node-documents` 版式启用，要求单一文档标题、可见日期与结构化日期一致、正文容器完整，并排除独立的档案注释。其他媒体仍须通过通用 JSON-LD 适配器的严格核验：来源 `articleBody` 必须与页面 `itemprop="articleBody"` 正文完全一致、标题一致且访问属性未标记为付费；该通用格式目前只通过离线 fixture 验证，尚未逐站点实测。通用政府页面适配器只接受明示的 `article[data-full-text="true"]` 模板。

另外，Brookings、CSIS、National Security Archive 和众议院外交事务委员会均有已实测的专用版式适配器。委员会听证页面以同一页面的 `article:published_time` 作为发布时间，不把听证举行日期当作发布日；链接的官方逐字稿 PDF 另行核验，页面未显示精确出版日期时仍留在 pending。

2009—2017 State.gov 旧版归档讲话页也有专用适配器。已核实两篇 2016 年原文：Daniel R. Russel 在 “China's Growing Pains” Conference 的讲话（2016-04-22，18,451 字符）和国务卿 John Kerry 的 “S&ED Opening Session Remarks”（2016-06-06，47,368 字符）。两页 Scrapy 原站响应均为 HTTP 200 技术故障页；对同一原 URL 的 Firecrawl `rawHtml` 元数据核对通过后，按页面 `#date_long`、`#page-title`、`#top-meta .officials-name` 和唯一 `#centerblock` 正文区域解析。白宫旧档案 `obamawhitehouse.archives.gov` 也使用独立适配器，读取 Press Secretary 来源栏、可见日期、标题和 `field-name-field-forall-body` 原文区域；讲话内 `<br>` 分隔的段落顺序保留，导航与分享区不进入正文。完整 Firecrawl captures、scrape IDs 和原始 HTML 证据已保存；Markdown/摘要未作为正文。

美国国务院 2021-2025 归档讲话页适配器通过公开页面版式和离线 fixture 核验。页面 `https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/` 经 Scrapy 请求返回 HTTP 200，但正文为 “Technical Difficulties”；Firecrawl 获取原页面 `rawHtml` 后，经同一适配器核对来源、日期、标题、作者和完整正文，1/1 verified，正文 10,031 字符。随后对 2023 年 Blinken 在 Johns Hopkins SAIS 的讲话和 2023 International Religious Freedom Report Rollout 两页进行直接 Scrapy 请求，均返回技术故障 HTML；对各自原始 URL 用 Firecrawl 获取原始 HTML，核对来源 URL、最终 URL 和 HTTP 状态元数据后，再由同一适配器解析来源页日期、署名和完整正文，该批次 2/2 verified。两篇正文分别为 36,722 和 14,839 字符，前者外置为 UTF-8 sidecar。另一个 2024-01-11 国务院记者会原始页面经 Scrapy 同样返回故障 HTML；Firecrawl 获取的原始 HTML 经适配器核对标题、发言人 Matthew Miller、发布日期和完整 39,701 字符记录后，单条批次 verified。该适配器覆盖了 `.classic-block-wrapper` 与文章 `.entry-content` 两种已观察版式；后者排除视频播放器、标题/署名元数据和标签模块。Firecrawl 的 Markdown、摘要和搜索片段均未作为正文。

AP News 适配器以 Firecrawl 取得的两个 2018 年 AP 页面实测：`https://apnews.com/article/8473860b573d4d0198d8bf19c319b69f` 的原始 HTML 含可见标题、AP 署名、发布时间和 `.RichTextStoryBody` 正文，导入结果为候选 1 条、已核实全文 1 条、待核验 0 条；导出的九列工作簿 1 条记录，正文 2,701 字符，与 SQLite 正文一致，证据 HTML 哈希一致。`https://apnews.com/article/73e5e5aa7be2408892e9904d642d2137` 的捕获页没有可核验的正文容器，登记为待核验候选，未把描述元数据或搜索摘要作为正文。另有 3 条关于华为限制和关税的 AP 原始页经 Scrapy 直接请求均返回 HTTP 403，已登记为 restricted，报告记录状态码，未改用其他抓取路径。该实测只覆盖 AP 的已观察版式和这些页面。纽约时报、美联社其他版式、CNN、路透社、Brookings/CSIS 以外的智库、其他政府来源、社交平台和研究文献尚无已实测的专用适配器；相关来源仍属未覆盖或待核验，不声称已经覆盖。

Brookings 适配器已用五篇公开文章实测，均返回 HTTP 200，来源页结构化数据与标题、作者区署名顺序和发布日期相符：`https://www.brookings.edu/articles/more-pain-than-gain-how-the-us-china-trade-war-hurt-america/`（2020-08-07，14,509 字符）、`https://www.brookings.edu/articles/what-have-we-learned-from-the-trade-war-with-china/`（2019-11-25，1,094 字符）、`https://www.brookings.edu/articles/developing-a-mutually-beneficial-us-china-economic-relationship/`（2019-02-28，7,522 字符）、`https://www.brookings.edu/articles/chinese-perspectives-on-trade-and-the-economic-tension-with-the-us/`（2019-06-24，1,009 字符）和 `https://www.brookings.edu/articles/the-us-china-economic-relationship-a-comprehensive-approach/`（2019-02-28，14,766 字符）。正文按 `wysiwyg-block` 段落/标题顺序提取，并排除推荐内容、作者简介、机构声明和页脚；作者优先照录来源页 Authors 区，结构化 creator 次之。五篇均已核实全文并进入累计工作簿。适配器目前仅覆盖 Brookings 已观察到的这一页面版式，不代表已覆盖其他 Brookings 页面类型或其他智库。

CSIS 适配器已用两篇公开原文实测：`https://www.csis.org/analysis/understanding-temporary-de-escalation-us-china-trade-war`（2025-05-13，7,239 字符）和 `https://www.csis.org/analysis/competition-confrontation-china-major-shift-us-policy`（2020-08-03，106,842 字符）均返回 HTTP 200。按主列 `text-block`/`quote-block` 顺序保留正文段落、标题和引文，排除下载区、嵌入播放器、相关内容和作者简介；长文以 UTF-8 sidecar 随工作簿交付。两篇均已核实全文。该适配器目前只覆盖 CSIS 已观察到的文章版式。

National Security Archive 适配器已覆盖 2019 年 Tiananmen 30 周年专题页和四种旧版 briefing book 页面：2019-06-04 专题页正文 2,294 字符；1999-06-01 Tiananmen briefing book 正文 60,757 字符；2001-06-04 “The U.S. \"Tiananmen Papers\"” 正文 27,550 字符；2003-12-11 Nixon briefing book 正文 25,928 字符；2004-12-21 Nixon 外交 briefing book 正文 14,819 字符。旧版页面声明 ISO-8859-1、实际使用 Windows-1252 标点；适配器按原始字节解码，保留分节、引文、文件条目和独立脚注。五条均直接通过 Scrapy 访问并保留原始 HTML 证据。2002 年 Beijing-Washington back-channel 页面可访问，但页面未显示可核实到年月日的发布日期，保留为 pending。RAND 两条公开报告页面直接请求返回 HTTP 403，登记为受限候选，没有使用其他方式获取正文。

众议院外交事务委员会公开听证页面已直接试采并核实：标题为 “Subcommittee Hearing: U.S. Responses to China's Foreign Influence Operations”，页面发布元数据为 2018-03-15，正文 1,653 字符；页面另显示的 2018-03-21 是听证日期，未用作“时间”。委员会页链接的官方 60 页听证逐字稿 PDF 已保留原始文件证据，但 PDF 未显示可核实的精确出版日期，保持 pending。相应 Congress.gov 文字路径被 robots.txt 禁止，目标页未被请求，记录为未处理。

VOA News 英文页通过 Scrapy 直接访问，robots.txt 允许且响应 HTTP 200。页面的可见 H1、结构化署名、`time[pubdate]` 和 NewsArticle 出版日期相互核验，新闻正文位于 `#article-content > .wsw`；只保存 dateline 与正文段落/标题/列表，排除图片说明和作者简介。2017—2025 时期已采集 7 篇较新报道：5 篇 2019 年贸易报道、1 篇 2020 年 COVID-19 信息争议报道、1 篇 2023 年芯片限制报道；其中最新的三篇来自批次 49，3/3 verified，正文分别为 2,335、2,365 和 6,643 字符。1992—2016 时期已采集 8 篇历史 VOA 报道：5 篇围绕 WTO 入世（批次 3/3、2/2 verified），3 篇围绕中美关系正常化及尼克松访华（批次 3/3 verified）。这些旧档案页面发布日期多显示为 2009 年，因此“时间”按来源页面显示的发布日期登记，标题中的 1972、2001 或 2004 是原始报道/事件日期信息；UTC 与本地时间跨日时按实际时间戳校验，并保留页面显示日期。

1949—1972 时期已核实 Truman Library 1952 年演讲、9 份 FRUS 文件，以及 The American Presidency Project 的 4 份材料：1958-09-04 国务卿台海声明、尼克松访华期间的行程纪要、第三年度外交政策报告和 1972 年 1 月的总统访谈。FRUS 文件包括 1949 年国务院贸易政策文件、1951 年台湾相关情报信件、1955 年总统致国会消息和致丘吉尔信件、1958—1960 年 VOA 短波干扰与台湾海峡公开表态材料、1963 年 USIA 对机构员工备忘录和 1972 年 USIA 局长备忘录。1955 年台海危机批次 3/3 verified；Presidency Project 页面经新增版式适配器核实标题、可见及结构化日期一致和完整正文，未明确列出作者的声明按规则填写“未注明”。尼克松访华批次 3/3 verified，来源页分别显示 1972-01-02、1972-02-09 和 1972-02-17；超长年度报告与访谈正文已按规则外置 UTF-8 文件。1958—1960 批次为 3/3 verified，1960 年代广播政策批次为 2/3 verified；其中一篇 Editorial Note 未显示发布日期或文档日期，未将正文提及的会议日期用作“时间”。1977—1980 正常化沟通批次有 3 份国务院文件，涵盖备忘录、backchannel message 和电报，3/3 verified；1982 年另核实一份 FRUS 对华政策备忘录。另有一份原文日期为 1946 年的候选因早于研究范围而排除，一条目前返回 HTTP 404 的原始链接仍待核验。
1949—1972 时期已核实 Truman Library 1952 年演讲、11 份 FRUS 文件，以及 The American Presidency Project 的 7 份材料：1950 年三份关于朝鲜局势的公开声明/记者会/广播电视讲话、1958-09-04 国务卿台海声明、尼克松访华期间的行程纪要、第三年度外交政策报告和 1972 年 1 月的总统访谈。FRUS 文件包括 1949 年国务院贸易政策文件、1951 年台湾相关情报信件、1951 年 3 月政策规划人员备忘录、1952 年 5 月 10/5 Panel 简报、1955 年总统致国会消息和致丘吉尔信件、1958—1960 年 VOA 短波干扰与台湾海峡公开表态材料、1963 年 USIA 对机构员工备忘录和 1972 年 USIA 局长备忘录。批次 58 两条早期情报/信息政策原件均通过 FRUS 页面核验：d59 的附录涉及 VOA 广播、政治战与公众支持；d108 记录 NSC 监督框架中的中国 covert 项目。批次 59 的总统档案页公开材料 3/3 verified，来源日期分别为 1950-06-27、1950-06-29 和 1950-07-19，未标单独作者的页面按规则填写“未注明”。1955 年台海危机批次 3/3 verified；Presidency Project 页面经新增版式适配器核实标题、可见及结构化日期一致和完整正文，未明确列出作者的声明按规则填写“未注明”。尼克松访华批次 3/3 verified，来源页分别显示 1972-01-02、1972-02-09 和 1972-02-17；超长年度报告与访谈正文已按规则外置 UTF-8 文件。1958—1960 批次为 3/3 verified，1960 年代广播政策批次为 2/3 verified；其中一篇 Editorial Note 未显示发布日期或文档日期，未将正文提及的会议日期用作“时间”。1977—1980 正常化沟通批次有 3 份国务院文件，涵盖备忘录、backchannel message 和电报，3/3 verified；1982 年另核实一份 FRUS 对华政策备忘录。另有一份原文日期为 1946 年的候选因早于研究范围而排除，一条目前返回 HTTP 404 的原始链接仍待核验。

1972—1991 时期新增 1989—1990 年布什政府公开材料批次：The American Presidency Project 的 1989-06-05 总统记者会和 1990-06-04 天安门事件周年声明均通过原始页面全文核验，2/2 verified。日期来自页面可见日期与结构化日期的一致值；页面未标注单独作者时填写“未注明”。

1992—2016 时期新增 2011 年美中战略与经济对话国务院讲话批次：三份 Hillary Rodham Clinton 讲话的来源页均因 Scrapy 响应技术困难页而未被当作正文；Firecrawl 对同一公开原始链接返回的完整 rawHtml 经现有国务院旧站适配器核验，HTTP 200、原始/最终 URL 匹配且保留 scrape ID。来源页面日期为 2011-05-09（两份）和 2011-05-10（一份），批次 3/3 verified。

2017—2025 智库批次新增 3 条唯一资料：两篇 Brookings 对中美竞争及美国对台政策的分析，以及 CSIS 对美国对华政策转变的报告；另核验一篇 Brookings 关于蓬佩奥讲话的评论。4/4 候选 verified，其中 CSIS 原始链接在既有批次中重复出现 1 次，原唯一记录的“重复计数”加 1，未重复添加 Excel 行。

研究文献批次新增一篇 PubMed Central 开放全文论文：Yanni Zhang 等人发表于 *Journal of Psycholinguistic Research* 的 “Comparative Study of Chinese and American Media Reports on the COVID-19 and Expressions of Social Responsibility: A Critical Discourse Analysis”，来源页出版日期 2021-09-09。PMC 原始全文页返回 HTTP 200；专用版式适配器核对页面题名、期刊引文日期与结构化日期、五位作者、摘要和关键词，只保存完整文章主体，排除摘要/关键词重复、参考文献、声明和页面模板。正文 50,899 字符，已核验全文。另有一篇 2023 年 Nature 论文请求返回 HTTP 406，以及一篇 2015 年期刊仓储页返回 HTTP 403；两者均保留为未取得全文的候选，未使用搜索片段或镜像替代。

USTR 2018—2020 年三条 Section 301/Phase One 页面候选中，2018 新闻页所链接的官方 PDF 已作为独立原始文件 URL 直接抓取并核验：封面题名、机构和印刷日期 2018-03-22 相符，215 页均有可提取文本，原始 PDF 字节和 SHA-256 已保存。正文 780,179 字符，超出 Excel 单元格限制，工作簿写相对路径并配套 UTF-8 全文文件；原 HTML 链接页仍单独保留为 pending。另两页虽有正文但来源页未显示可核实的完整发布日期，也保留为 pending。2024 年 USTR 四年审查批次新增 4 条候选：直接链接的官方最终报告 PDF 已核验封面题名、机构、印刷日期 2024-05-14 和 187 页完整文本；正文 466,089 字符，已另存 UTF-8 全文文件。相关 3 条 USTR 新闻页没有来源可见的完整发布日期，继续列为 pending。1949—1972 FRUS/VOA 检索新增 1 条线索；原始链接请求返回 302 且未提供正文，记录为 pending，未将搜索片段视作原文。1979 和 1989 年 NYT 四条原始页均因 `robots.txt` 拒绝而未发出目标页请求，报告已记录阻止原因；CNN 两条 2018 候选及 Reuters 两条 2025 候选也因 robots 规则未处理，未使用 Firecrawl 绕过。RAND 两条候选直接请求均返回 HTTP 403，已登记为 restricted。批次 50 的 3 条台海危机档案候选（两份 FRUS 文件及一份 Presidency Project 1958 年国务卿声明）、批次 51 的 3 条尼克松访华材料、批次 52 的 2 条布什政府公开材料、批次 53 的 3 条美中战略与经济对话讲话和批次 54 的 4 条智库材料均通过全文核验；批次 54 有 1 次 CSIS 同链接重复发现，重复计数已加到原记录。批次 55 的 2023 Nature 学术论文返回 HTTP 406，批次 56 的 2015 期刊仓储论文返回 HTTP 403，均未进入已取得全文表。批次 57 的 PMC 开放论文 1/1 verified；批次 58 的两条 FRUS 信息政策/对华政策原件 2/2 verified；批次 59 的三份 Truman 政府对韩公开材料 3/3 verified。批次 60 再次发现一条已核实的 2018 AP 原文链接，但当前 Scrapy 请求收到 HTTP 403；本次仅登记重复发现并更新原记录重复计数，没有覆盖既有已核实正文。批次 61 新增两份 1949—1950 FRUS 候选，其中 1950-06-02 文件全文已核实，1949 页面虽返回 HTTP 200 但元数据/全文核验未通过，继续 pending。主库 `data/research.sqlite3` 当前登记 102 条候选，其中 71 条候选状态为已核实全文、15 条 pending（包括 HTTP 406 但未判定为访问控制受限的来源）、7 条受限（均 HTTP 403）、9 条尚未处理；累计主工作簿 `data/materials.xlsx` 按唯一来源链接保留 70 条资料行，超长正文另存于相邻 `_bodies/` 文件夹并以相对路径引用。纽约时报、CNN、路透社可合法取得的具体全文、已实测适配器之外的媒体/智库版式、社交平台和更多中英文研究文献仍未充分覆盖，不声称已经覆盖。

## 授权全文导入

通过学校图书馆等授权取得全文后，先将材料候选写入数据库，再准备 manifest JSON。manifest 必须逐字段说明元数据对应的原始来源链接；授权说明和完整性确认均为必填：

```json
{
  "candidate_id": 1,
  "source": "Journal name",
  "time": "2020-02-03",
  "author": "Author name",
  "title": "Article title",
  "abstract": "",
  "keywords": "China; media",
  "source_url": "https://publisher.example/article",
  "authorization_note": "Full text provided by the researcher from university library access.",
  "completeness_confirmed": true,
  "abstract_origin": "none",
  "field_sources": {
    "source": "https://publisher.example/article",
    "time": "https://publisher.example/article",
    "author": "https://publisher.example/article",
    "title": "https://publisher.example/article"
  }
}
```

```powershell
.\.venv\Scripts\research-crawler.exe import-authorized --manifest data/authorized/material.json --file data/authorized/material.txt --db data/research.sqlite3
```

授权说明由使用者提供；程序不会自行判定用户授权范围。源文件按 UTF-8 原样读取并记录哈希和路径。

## 导入 Firecrawl 原始 HTML

当配置的 Firecrawl 工具能访问某个公开原始页面、而本机 Scrapy 不能直接取到页面时，可用 Firecrawl 对已知原始 URL 执行一次 `scrape`，请求 `rawHtml` 格式，并把完整工具结果（保留 `structuredContent`、`rawHtml` 和 `metadata`）保存为 UTF-8 JSON。不要把 Markdown、summary、highlights 或搜索结果作为正文导入。捕获文件至少应保留 `rawHtml` 及 Firecrawl 返回的 `metadata.sourceURL`、`metadata.url`、`metadata.statusCode`、`metadata.scrapeId`。如果结果包含 `success` 或 `error` 字段，也须原样保留。

```powershell
.\.venv\Scripts\research-crawler.exe import-firecrawl `
  --capture data/captures/state-remarks.json `
  --url https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/ `
  --period 2017-2025 `
  --category government `
  --query-label state-dept-remarks-economic-coercion `
  --db data/research.sqlite3 `
  --evidence-dir data/evidence
```

导入器只接受 Firecrawl 原始 HTML 字段；若工具结果显式报告失败则拒绝，否则要求来源 URL 和最终 URL 均与候选 URL 一致，并核验 HTTP 状态码及 scrape ID。随后通过现有来源适配器和同一核验管线。原始 HTML 按 UTF-8 保存并记录 SHA-256、抓取方式和 scrape ID。缺少专用版式、日期或完整正文核验的内容继续标记待核验，不会写入正式 Excel。此命令导入已保存的 Firecrawl 工具结果；Firecrawl 检索仍由配置的 MCP 工具执行。

对于公开 PDF，必须先由 Scrapy 按 `robots.txt` 抓取并保存真实 PDF 响应。若发布页只能从 Firecrawl raw HTML 核验，可用 `import-firecrawl-pdf` 将该 HTML 与数据库中同一候选的 PDF 证据配对；导入器会核对来源页链接、标题、发布日期、机构、PDF 首页和所有页面的可提取文本。HTTP 200 但响应内容不是 PDF、或只有转换后的 Markdown/HTML 提取结果时，候选仍为 pending。

## 报告与导出

```powershell
.\.venv\Scripts\research-crawler.exe report --db data/research.sqlite3 --batch-id 1
.\.venv\Scripts\research-crawler.exe export --db data/research.sqlite3 --output data/materials.xlsx
```

工作簿严格只有九列：来源、时间、作者、标题、摘要、关键词、正文、来源链接、重复计数。超过 Excel 单元格长度的正文完整保存至工作簿同目录下的 `<工作簿名>_bodies/`，正文单元格写相对路径。批次报告分列候选、已核实全文、受限、待核验、未处理和重复数量，并列出未取得全文的候选。

## 覆盖范围

截至批次 87，资料库登记 172 条候选：120 条全文已核实、29 条待核验、10 条受限、13 条未处理；工作簿含 117 条唯一来源链接。批次 87 检索 VOA News 2023—2025 年有关台湾选举舆论、美国芯片政策与台美半导体投资的 5 个原始页面。4 篇核验通过：2023-09-28 台湾选举与信息叙事报道（5,255 字符）、2024-04-25 美光芯片投资报道（4,058 字符）、2024-12-02 中国芯片出口管制报道（1,240 字符）和 2025-03-06 台积电美国投资报道（5,734 字符）。页面及 robots.txt 均返回 HTTP 200；日期、作者、标题和正文按 VOA 页面结构核验，4 条摘要以“据正文整理：”开头。另一页面为视频对象，仅有 VideoObject 元数据，无可核验的完整文章正文或文字稿，保留 pending。批次统计 5 候选、4 verified、1 pending、0 restricted/duplicate/unprocessed。

截至批次 88，资料库登记 177 条候选：125 条全文已核实、29 条待核验、10 条受限、13 条未处理；工作簿含 122 条唯一来源链接。批次 88 检索 PMC 上 5 篇 2022—2023 年美国/英语媒体对华形象与中美新闻话语研究，涉及经济新闻语篇、公共卫生报道、美国—中国疫情历史类比、英语媒体对华报道及疫情身份叙事。5 个出版方原文页面及 robots.txt 均 HTTP 200，由 PMC 适配器核实来源、日期、作者、标题和完整主体原文，正文约 29,727—56,693 字符。出版方摘要予以照录；缺少关键词字段的一篇仅据摘要整理主题词。批次统计 5 候选、5 verified、0 pending/restricted/duplicate/unprocessed。累计工作簿 122 行通过九列、唯一链接、字段和正文/长文文件一致性审计；28 篇超单元格限制的正文均通过 UTF-8 侧文件逐字核对。

截至批次 89，资料库登记 183 条候选：131 条全文已核实、29 条待核验、10 条受限、13 条未处理；工作簿含 128 条唯一来源链接。批次 89 检索美国总统档案项目站 1993 年和 2000 年的对华最惠国待遇与永久正常贸易关系原始文件 6 篇，包括克林顿声明、行政令、与江泽民会谈后记者问答、参议院表决回应及世界贸易组织政策讲话。Scrapy 检查 robots.txt 后抓取六个原始页面，目标页与 robots.txt 均 HTTP 200；逐篇核对标题、发布日期、未注明作者及完整正文。来源未提供摘要和关键词，故摘要按正文整理并以“据正文整理：”开头，关键词取自正文。批次统计 6 候选、6 verified、0 pending/restricted/duplicate/unprocessed。累计工作簿 128 条唯一材料、28 个 UTF-8 长文侧文件，通过九列、元数据和正文一致性审计。本批反映的是总统档案项目可检索页面，不代表同期官方材料的完整覆盖。

截至批次 90，资料库登记 189 条候选：137 条全文已核实、29 条待核验、10 条受限、13 条未处理；工作簿含 134 条唯一来源链接。批次 90 检索美国总统档案项目站 2001—2008 年布什政府有关中国、WTO、亚太安全与对华外交的 6 篇文件，包括总统声明、演讲及问答、副总统复旦大学讲话、胡锦涛会谈记录和亚洲政策事实清单。Scrapy 遵守 robots.txt；robots.txt 与六个原始页面均 HTTP 200，现有适配器核验发布日期、标题、未注明作者及完整正文。来源未提供摘要和关键词，按正文整理摘要并加“据正文整理：”前缀，关键词根据正文。批次统计 6 候选、6 verified、0 pending/restricted/duplicate/unprocessed。累计工作簿 134 条唯一材料、30 个 UTF-8 长文侧文件，九列、元数据和正文均与数据库匹配。本批覆盖限于所检索总统档案项目页面。

批次 91 检索奥巴马政府 2013—2016 年白宫档案中有关习近平会晤、中美气候声明和亚太政策的 6 个候选页面。目标页可经 Firecrawl 以原始 HTML 获取（HTTP 200，sourceURL 与 final URL 完全匹配）；Scrapy 请求返回 HTTP 200，robots.txt 返回 HTTP 404。为旧 Drupal 页面新增专用适配器，逐条核对 Press Secretary 来源栏、可见发布日期、标题和完整正文；原页未署名的作者记为“未注明”。6 篇均通过管线核验，摘要和关键词据正文整理，未使用搜索摘要。批次统计 6 候选、6 verified、0 pending/restricted/duplicate/unprocessed。

批次 92 检索旧版国务院档案中希拉里·克林顿 2011—2012 年关于亚太政策、中美战略与经济对话及对华关系的 8 个候选页面。robots.txt HTTP 200；Scrapy 对 8 个 URL 均收到同一份“Technical Difficulties”页面，故未作正文使用。对同 URL 使用 Firecrawl `rawHtml` 后，经页面适配器验证元数据和完整原文，8 条均 verified。检查发现播放器脚本与界面文本嵌套于旧站正文容器；按原始 HTML 的顶层段落重建了本批 8 条正文，并清理旧库另一条同类 2016 年讲话的模板文本。来源无摘要的 8 篇均按正文整理并加“据正文整理：”前缀。批次 92 统计 8 候选、8 verified、0 pending/restricted/duplicate/unprocessed。

累计截至批次 92 为 203 条候选、151 条已核实、29 条待核验、10 条受限、13 条未处理；工作簿有 148 条唯一全文记录、34 个 UTF-8 长文侧文件，通过字段和正文逐项一致性审计。

批次 93 检索众议院外交事务委员会 2024 年台湾关系法听证页面。Firecrawl 原始 HTML 核对页面发布字段为 2024-04-24（页面修订时间为 2025-06-02）；随后 Scrapy 在 robots.txt 允许下抓取原始页，robots.txt 和目标页均 HTTP 200。页面正文是听证活动目录而非发言逐字稿，完整可见主体共 199 字符，按该委员会页面材料单独收录，摘要据正文整理。批次统计 1 候选、1 verified、0 pending/restricted/duplicate/unprocessed。

批次 94 检索到同场听证的 GovInfo 官方 PDF 逐字稿。Scrapy 遵守 robots.txt，原始 PDF 返回 HTTP 200；文件 42 页，其中 40 页可提取文本、2 页未提取到文字。封面可见听证日期和题名，但 PDF 元数据没有出版日期，且现有适配器不能确认空白页内容与出版元数据，因此保留 pending，不进入 Excel。批次 95 核对 GovInfo 按官方 URL 规则提供的 HTML 版逐字稿，robots.txt 和原始页均 HTTP 200；当前适配器未能验证其完整正文及来源页面出版日期，保留 pending。两批均未使用搜索摘要补正文。累计截至批次 95 为 206 条候选、152 条已核实、31 条待核验、10 条受限、13 条未处理；工作簿有 149 条唯一全文记录、34 个 UTF-8 长文侧文件。

批次 96 抓取该听证在 GovInfo 的官方详情页（robots.txt 和页面均 HTTP 200）。页面列出 “Held Date: May 1, 2024”，并未在已观察字段中提供文档发布日期；该日期不能代替发表日期，故详情页只作为待核验元数据线索。批次 97—98 扩展到 GovInfo 2011—2024 年中国相关听证全文页：2011 年对华公共外交、2017 年美台关系、2023 年中国“一带一路”外交与非洲竞争、2023 年反制中国强制性“一带一路”外交、2024 年中共政治战等 5 个候选。Scrapy 在 robots.txt 允许后抓取全部原始 HTML，robots.txt 和五个目标页均 HTTP 200；页面保存为原始证据，但当前适配器未能严谨确认这些 HTML 听证稿的完整正文及对应元数据，故 5 条均 pending，不进入 Excel。搜索结果仅用于定位原始页面，未用作正文或字段来源。累计截至批次 98 为 212 条候选、152 条已核实、37 条待核验、10 条受限、13 条未处理；工作簿有 149 条唯一全文记录、34 篇长正文由 UTF-8 侧文件保存。

批次 99 检索 PMC 上 7 篇美国对华媒体传播、政治精英话语与中国形象研究。robots.txt 与 7 个原始出版方页面均 HTTP 200；4 篇新增唯一全文通过 PMCFulTextArticleAdapter 核验：2017-06-02 “War or Peace? How the Subjective Perception of Great Power Interdependence Shapes Preemptive Defensive Aggression”（65,960 字符）、2022-11-14 “The moral filter of patriotic prejudice: How Americans view Chinese in the COVID-19 era”、2023-01-16 “US foreign policy elites and the great rejuvenation of the ideological China threat: The role of rhetoric and the ideologization of geopolitical threats”（61,350 字符）和 2023-05-11 “A Second Cold War? Explaining Changes in the American Discourse on China: Evidence from the Presidential Debates (1960–2020)”（65,177 字符）。已有两篇 PMC 全文作为重复发现各计 1；另一篇研究日本网络新闻的新冠涉华报道，主题与美国对华传播范围不符，保留 pending、不纳入正式表。批次 99 统计 7 候选、6 verified、1 pending、2 duplicate discoveries、0 restricted/unprocessed。发现相同原始 URL 在历史记录无平台 ID、新候选带平台 ID时生成了不同身份键，造成两组重复材料行；修复存储身份解析并增加回归测试，合并两组重复行，保留所有候选和抓取证据，SQLite 变更前备份为 `data/research-before-pmc-dedupe.sqlite3`。新增 PMC 正文结构测试并扩展适配器，以从含 “Significance” 和 “Abstract” 两段摘要布局中明确选择论文摘要。累计截至批次 99 为 219 条候选、158 条已核实、38 条待核验、10 条受限、13 条未处理；工作簿有 153 条唯一全文记录，37 篇长正文由 UTF-8 侧文件保存。当前工作簿字段及正文逐行与数据库匹配；侧文件目录另保留 1 个未被当前工作簿引用的历史导出文件。

批次 100 回到 1972—1991 年媒体来源空白，Firecrawl 搜索仅用于定位四篇《纽约时报》1989 年天安门相关原始文章页，其中一篇搜索结果已在旧候选集中，未重复登记。对新增的 4 个 URL 启动 Scrapy 后，robots.txt 对四页均返回禁止规则，目标页面未被请求；全部保留为未处理候选，不标记为受限全文，也未使用搜索摘要补正文。批次统计 4 候选、0 verified/pending/restricted/duplicate、4 unprocessed。累计截至批次 100 为 223 条候选、158 条已核实、38 条待核验、10 条受限、17 条未处理；工作簿仍为 153 条唯一全文记录。该批记录明确了当前 robots.txt 边界，不代表其他《纽约时报》页面或授权访问均不可用。

批次 101 检索 1992—2016 年智库来源，发现 Brookings 的 Fu-Kuo Liu 2008-06-11 研究页面 “Asian Regionalism, Strategic Evolution, and U.S. Policy in Asia: Some Prospects for Cross-Strait Development”。Scrapy 遵守 robots.txt，robots.txt 与原始页面均 HTTP 200。首次适配误把仅含 Introduction 的页面节选（1,854 字符）标为全文；复核原始 HTML 发现页面有 “See More” 展开控件、独立 PDF 下载链接，不能证明浏览器响应包含完整论文。新增回归测试和适配器完整性门槛后重抓，候选改为 pending；错误材料行已从数据库和 Excel 移除，旧证据核验标记已校正，原始 HTML 及两次抓取证据保留，数据库变更前备份为 `data/research-before-brookings-excerpt-correction.sqlite3`。批次统计 1 候选、0 verified、1 pending、0 restricted/duplicate/unprocessed。累计截至批次 101 为 224 条候选、158 条已核实、39 条待核验、10 条受限、17 条未处理；工作簿 153 条唯一全文记录。完整论文 PDF 可从原页面的公开下载链接继续单独核验，但未把页面简介或搜索摘要代替全文。

批次 102 抓取上述 Brookings 页面公开链接的 PDF 原文。robots.txt、关联发布页和 PDF 均 HTTP 200；原始 PDF（32 页）已保存，所有页面都有可提取文本。PDF 封面题名、作者和机构与关联发布页吻合，封面日期为 “June 2008”；精确发布日期 2008-06-11、作者 Fu-Kuo Liu、标题和来源来自关联 Brookings 页面。为此给候选 CSV 增加可选 `metadata_url`，Spider 先抓落地页再抓 PDF，数据库分别保存 PDF 正文证据与落地页元数据证据；只有两者均允许访问、字段来源 URL 对应同一候选的成功证据、且 PDF 所有页面都有文本及首页书目信息匹配时才验证。首次仅用 PDF 的候选保持 pending；配对核验后 117,142 字符完整全文通过并纳入 Excel，正文存为 UTF-8 长文侧文件。批次最终统计 1 候选、1 verified、0 pending/restricted/duplicate/unprocessed。累计截至批次 102 为 225 条候选、159 条已核实、39 条待核验、10 条受限、17 条未处理；工作簿 154 条唯一全文记录。

批次 103 扩展 CSIS 2023—2025 年对华政策材料，发现 6 个原始 URL。CSIS 页面版式中，2 个报告页只提供摘要/目录并链接完整 PDF；新增报告型页面元数据适配及 PDF/落地页配对验证，要求 PDF 所有页面有文本，封面题名和作者可在 PDF 中对应，正文含 CSIS 发布标识，且落地页标题、作者、发布日期与 PDF 链接吻合。两份 PDF 均从 CSIS 页面直接公开链接由 Scrapy 获取，HTTP 200：2025-01-15 Ryan Hass、Ryan McElveen、Lily McElwee 的 “Advancing U.S.-China Coordination amid Strategic Competition: An Emerging Playbook”（10 页、43,913 字符）；2024-02-21 Sujai Shivakumar、Charles Wessner、Thomas Howell 的 “Balancing the Ledger: Export Controls on U.S. Chip Technology to China”（13 页、42,850 字符）。另有 Scott Kennedy 2024-01-03 的 CSIS 评论，以及 Kari A. Bingen 2023-03-09 的国会证词通过原始 HTML 正文核验。2 个报告落地页本身没有完整正文，仍为 pending；对应独立 PDF URL 已分别作为全文记录。批次统计 6 候选、4 verified、2 pending、0 restricted/duplicate/unprocessed。累计截至批次 103 为 231 条候选、163 条已核实、41 条待核验、10 条受限、17 条未处理；工作簿 158 条唯一全文记录、40 个 UTF-8 正文侧文件，九列和全文逐项对照 SQLite 通过。

批次 104 为补充 1992—2016 年美国媒体中国形象研究文献，登记 3 个期刊原始页面候选：Taylor & Francis 的 Alexander Liss 文章，以及 SAGE 上两篇涉华新闻框架研究。按 Scrapy 的 robots.txt 处理后，三个出版方目标页均返回 HTTP 403；均记录为 restricted，没有调用登录凭据、替代镜像或摘要作为正文，也没有进入全文工作簿。批次统计 3 候选、0 verified/pending/duplicate/unprocessed、3 restricted。累计为 234 条候选、163 条已核实、41 条待核验、13 条受限、17 条未处理；唯一全文资料仍为 158 条。该方向的出版方全文覆盖仍不足，后续只接受出版方公开全文、机构仓储合法公开全文或用户提供的授权全文。

批次 105 扩展 Clinton White House 1997—1999 年对华公开沟通与贸易政策档案。Firecrawl 搜索只用于定位，Scrapy 遵守 robots.txt（HTTP 200）并取得 6 个原始页面（目标页均 HTTP 200）。新增旧版 press-release 表格布局解析和回归测试，按唯一 Press Secretary 发布区、发布栏日期、档案标题及完整正文/页脚边界核验。核实的材料包括：1997-10-24 “REMARKS BY THE PRESIDENT IN ADDRESS ON CHINA AND THE NATIONAL INTEREST”（21,844 字符）；1997-12-16 “152nd Press Conference”（83,880）；1998-11-19 “Town Hall Meeting In Tokyo”（45,188）；1999-04-08 克林顿与朱镕基联合记者会（40,885）；1999-11-24 西雅图 WTO 议程（13,802）；以及 1999-11-08 “REMARKS BY THE PRESIDENT AT ON-LINE TOWN HALL MEETING”（48,391）。最后一页 URL 中的 11-09 与原发布栏的 “Monday, November 8, 1999” 不同，时间字段依规范采用发布栏日期。该批 6/6 verified。批次 105 后数据库有 240 条候选记录和 7 次重复发现（共 247 次 URL 发现），其中 169 verified、41 pending、13 restricted、17 unprocessed；工作簿含 164 条唯一全文记录，长正文继续以 UTF-8 侧文件保存。

批次 106 检索国务院 2009—2017 档案中 2014、2016 年可能涉及中国的两场国务卿公开讲话。Scrapy 遵守 robots.txt（HTTP 200），两个原始 URL 均返回 HTTP 200，但保存的响应正文均为同一份 “Technical Difficulties” 页面，缺少文章标题、发布日期和正文，故 2 条均为 pending，不进入 Excel。另尝试通过 Firecrawl 获取 2016 页面原始 HTML，但该次返回内容未能成功保存为本地捕获文件，因此不作为已核验全文。批次统计 2 候选、0 verified、2 pending、0 restricted/duplicate/unprocessed。累计为 242 条候选记录、7 次重复发现（共 249 次 URL 发现），其中 169 verified、43 pending、13 restricted、17 unprocessed；工作簿仍有 164 条唯一全文记录。该档案站旧页面内容仍未能通过当前抓取路径取得，未用搜索摘录补写。

批次 107 回访批次 99 中一篇先前 pending 的 PMC 论文 “Media framing and expression of anti-China sentiment in COVID-19-related news discourse: An analysis using deep learning methods”。Scrapy 遵守 robots.txt，原始 PMC 页面及 robots.txt 均 HTTP 200；用当前适配器重新抓取并核对出版日期 2022-08-28、作者 Zeyu Lyu 与 Hiroki Takikawa、期刊 Heliyon 和 45,287 字符正文，状态更新为 verified。批次 99 现为 7 verified、0 pending、2 duplicate；新增 1 条唯一材料。随后发现并修复了时期边界校验缺口：发布日期必须落在候选所属的四个研究时期内，新增回归测试覆盖 1946 年材料不得进入 1949—1972 批次。累计为 242 条候选记录、7 次重复发现（249 次 URL 发现），其中 170 verified、42 pending、13 restricted、17 unprocessed。`data/materials.xlsx` 正被其他程序占用，未覆盖；最新 165 条资料导出为 `data/materials-refreshed.xlsx`，对应 45 个 UTF-8 长文文件位于 `data/materials-refreshed_bodies/`，九列、全部字段、正文及唯一链接已与 SQLite 逐项核对。

批次 108 采集 Reagan 总统 1987-08-05 “Memorandum on Acid Imports From China”。Firecrawl 搜索仅用于定位，Scrapy 遵守 robots.txt（HTTP 200），原始页面 HTTP 200；American Presidency Project 适配器核对来源、精确发布日期、标题、未注明作者和 1,774 字符完整正文。该材料进入 1972—1991 / government 批次。批次统计 1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。累计为 243 条候选记录、7 次重复发现（250 次 URL 发现），其中 171 verified、42 pending、13 restricted、17 unprocessed；工作簿已重新导出为 166 条唯一全文记录。

批次 109 补充 1972—1991 年美国政党平台中的对华公开表述，收录 American Presidency Project 的 1984 Democratic Party Platform 和 Republican Party Platform of 1988。Scrapy 遵守 robots.txt，robots.txt 与两个原始页面均 HTTP 200；适配器核对正式发布日期分别为 1984-07-16、1988-08-16，完整正文分别为 237,110 和 232,555 字符。两条均为完整原始文本，未使用搜索摘录补正文。批次统计 2 candidate、2 verified、0 pending/restricted/duplicate/unprocessed。累计为 245 条候选记录、7 次重复发现（252 次 URL 发现），其中 173 verified、42 pending、13 restricted、17 unprocessed；工作簿已导出为 168 条唯一全文记录。

批次 110 首次按搜索线索将两篇美国总统候选人辩论页面放入 1972—1991 批次；原始页面和 robots.txt 均 HTTP 200、正文完整，但页面实际发布日期为 1999-12-06 和 1999-10-22，超出该时期，因此两条按时期校验保留 pending。批次统计 2 candidate、0 verified、2 pending、0 restricted/duplicate/unprocessed。

批次 111 将批次 110 的两条原始 URL 按核实到的 1999 年发布日期纠正到 1992—2016 批次。Scrapy 再次遵守 robots.txt，目标页 HTTP 200；适配器核对标题、日期和完整正文，正文分别为 78,895 和 63,477 字符。两条均 verified；同一 URL 的前次错误时期登记按规则计为 2 次重复发现。累计为 249 条候选记录、9 次重复发现（258 次 URL 发现），其中 175 verified、44 pending、13 restricted、17 unprocessed；工作簿已导出为 170 条唯一全文记录。

批次 112 补充 1992 年共和党平台的对华公开政策文本。Scrapy 遵守 robots.txt，robots.txt 与原始页面均 HTTP 200；American Presidency Project 适配器核对发布日期 1992-08-17、标题和 183,777 字符完整正文。批次统计 1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed。累计为 250 条候选记录、9 次重复发现（259 次 URL 发现），其中 176 verified、44 pending、13 restricted、17 unprocessed；工作簿已导出为 171 条唯一全文记录。

批次 113 检索 Trump White House Archives 中 2019 年 Pence 对华政策公开演讲和一页涉中共意识形态材料。Scrapy 遵守 robots.txt，robots.txt 与两个目标页均 HTTP 200。Pence 演讲页通过来源、发布日期 2019-10-24、标题和 26,628 字符完整正文核验；另一页缺少可确认的完整正文和元数据，保留 pending，不使用搜索摘录或页面外部引用补写。批次统计 2 candidate、1 verified、1 pending、0 restricted/duplicate/unprocessed。累计为 252 条候选记录、9 次重复发现（261 次 URL 发现），其中 177 verified、45 pending、13 restricted、17 unprocessed；工作簿已导出为 172 条唯一全文记录。

批次 114 检索 2023 年国务院公开传播材料：Blinken 在 Freedom House 年度颁奖礼的讲话、与中国副主席韩正会前讲话，以及 6 月 14 日国务院记者会。Scrapy 遵守 robots.txt，但三页目标响应都是同一 “Technical Difficulties” 页面，不能作为原文。随后 Firecrawl 对同一原始发布 URL 返回原始 HTML，保存完整捕获及 sourceURL、最终 URL、HTTP 状态和 scrape ID，并通过国务院页面适配器和同一核验管线处理。前两篇 verified：发布日期 2023-05-09（21,941 字符）及 2023-09-18（2,694 字符）；记者会无法通过完整正文/元数据门槛，继续 pending。批次统计 3 candidate、2 verified、1 pending、0 restricted/duplicate/unprocessed。

批次 115 收录国务院 Global Engagement Center 专题报告页面 “How the People’s Republic of China Seeks to Reshape the Global Information Environment”。Scrapy 遵守 robots.txt，但返回 “Technical Difficulties” HTML；Firecrawl 对同一原始页面提供 raw HTML 捕获，页面可见发布日期 2023-09-28，标题、机构署名、来源和 6,574 字符页面正文通过原适配器与共享核验管线，1/1 verified。页面链接到英文官方 PDF，作为批次 116 独立候选。该 PDF 的 Scrapy 响应虽为 HTTP 200，但内容仍是技术故障 HTML；Firecrawl 报告 64 页 PDF 解析结果，但未提供原始 PDF 字节，因此没有把转换结果当作全文，记录继续 pending。批次 115 为 1 verified；批次 116 为 1 pending。

截至批次 116，资料库登记 257 条候选记录和 9 次重复发现（共 266 次 URL 发现），其中 180 verified、47 pending、13 restricted、17 unprocessed；工作簿含 175 条唯一全文资料，50 个 UTF-8 长正文侧文件通过逐项校验。纽约时报、CNN、路透社可合法取得的具体全文、已实测适配器之外的媒体/智库版式、社交平台和更多中英文研究文献仍未充分覆盖，不声称已经覆盖。

批次 117 收录 2024 年国务院对华公开材料：4 月 24 日国务院记者会（Vedant Patel，正文 42,731 字符）和 10 月 30 日外交现代化讲话（Office of the Spokesperson，正文 7,489 字符）经各自原始 State Department 页面 raw HTML 核验，均 verified。记者会全文超过 Excel 单元格限制，完整保存在 UTF-8 长正文侧文件中。访华行程页虽标题提及 2024 年 4 月 24—26 日，但那是行程日期；原页面未显示精确发布日期，Firecrawl 元数据仅有修改时间，故 pending，不纳入 Excel。批次统计 3 candidate、2 verified、1 pending、0 restricted/duplicate/unprocessed。截至批次 117，资料库有 260 条候选和 9 次重复发现（269 次 URL 发现），其中 182 verified、48 pending、13 restricted、17 unprocessed；工作簿含 177 条唯一全文资料，51 个 UTF-8 长正文侧文件。媒体、社交平台和中英文研究文献仍需扩大覆盖，不声称穷尽。

批次 118 检索 AP News 2024 年中国科技出口管制报道。Scrapy 获取 robots.txt 后请求原始文章页，响应 HTTP 403；按访问限制登记为 restricted，不尝试经 Firecrawl 或其他路径重新抓取，正文未进入 Excel。批次统计 1 candidate、1 restricted、0 verified/pending/duplicate/unprocessed。截至批次 118，资料库有 261 条候选和 9 次重复发现（270 次 URL 发现），其中 182 verified、48 pending、14 restricted、17 unprocessed；工作簿仍含 177 条唯一全文资料和 51 个 UTF-8 长正文侧文件。

批次 119 检索 2022 年美国媒体涉华框架研究。ScienceDirect 原始文章页经 Scrapy 请求返回 HTTP 403，按访问限制登记为 restricted；没有改用抓取服务或摘要代替正文。批次统计 1 candidate、1 restricted、0 verified/pending/duplicate/unprocessed。

批次 120 检查一条看似可能补足 2023 年《纽约时报》中国国家形象研究的 PMC 线索。原始 PMC 页面 HTTP 200，但页面实际是发表于 2026-05-21、DOI 为 10.3389/fpsyg.2026.1825833 的另一篇论文；年份超出范围，且只是引用关系，故保留 pending，不导入 Excel。批次统计 1 candidate、1 pending、0 verified/restricted/duplicate/unprocessed。

批次 55 的 Nature 2023 研究候选随后复核（原始 URL `https://www.nature.com/articles/s41599-023-02052-8`）。Firecrawl 保存的完整 raw HTML 元数据与该 URL 匹配，HTTP 200、抓取 ID `01a1b01c-5d7a-7789-915e-2166f44fd7ea`；页面元数据给出发布日期 2023-09-01、作者 Mei Yang 与 Ziwei Wang、DOI `10.1057/s41599-023-02052-8`。Nature 适配器核对页面标题、作者、日期、期刊、摘要、CC BY 4.0 许可及摘要至参考文献的正文区段，提取 58,418 字符。Scrapy 本轮重抓的 robots.txt 与文章页均返回 HTTP 406，未由其取得新内容；使用此前保存的同一官方 URL Firecrawl raw HTML 捕获完成逐字段核验，记录 retrieval ID 和原始哈希，候选状态由 pending 更新为 verified，正式表新增 1 条。详情见 `data/reviews/nature-nyt-china-discourse-2023-20261107/review.json`。

截至批次 120，资料库登记 263 条候选和 9 次重复发现（共 272 次 URL 发现），其中 182 verified、49 pending、15 restricted、17 unprocessed；工作簿仍含 177 条唯一全文资料和 51 个 UTF-8 长正文侧文件。媒体、新媒体和中英文研究文献覆盖仍不足，不声称穷尽。

批次 121 检索美国对华政策、媒体叙事和公众态度研究，共抓取 5 个开放 PMC 原始页面。3 篇通过来源页元数据、精确发布日期和主文全文核验并纳入 Excel：Jacques deLisle 的 “Foreign Policy through Other Means: Hard Power, Soft Power, and China's Turn to Political Warfare to Influence the United States”（2020-03-04，65,913 字符）；Hsuan-Yu Lin 的 “COVID-19 and American Attitudes toward U.S.-China Disputes”（2021-01-25，52,287 字符）；Wu Xie 的 “Unwitting Agents: Representations of Chinese International Students in US-China Geopolitics”（2023-05-31，42,915 字符）。另两篇虽可公开取得全文，但研究对象分别为加拿大公众和亚洲公众对中国的认知，并非美国对华舆论，故保留原始证据、标记 pending，不纳入正式表。批次统计 5 candidate、3 verified、2 pending、0 restricted/duplicate/unprocessed。

截至批次 121，资料库登记 268 条候选和 9 次重复发现（共 277 次 URL 发现），其中 185 verified、51 pending、15 restricted、17 unprocessed；工作簿含 180 条唯一全文资料和 54 个 UTF-8 长正文侧文件。媒体、新媒体及早期中英文研究文献仍需继续补充，不声称穷尽。

批次 98 的 GovInfo 听证材料复核新增 4 篇 verified 原文：2017-06-15 “RENEWING ASSURANCES: STRENGTHENING U.S.-TAIWAN TIES”（92,109 字符）；2023-04-18 “GREAT POWER COMPETITION IN AFRICA: THE CHINESE COMMUNIST PARTY”（85,856 字符）；2023-06-14 “ASSESSING U.S. EFFORTS TO COUNTER CHINA'S COERCIVE BELT AND ROAD DIPLOMACY”（148,847 字符）；2024-06-26 “DEFENDING AMERICA FROM THE CHINESE COMMUNIST PARTY'S POLITICAL WARFARE PART II”（191,925 字符）。Scrapy 遵守 robots.txt 获取同包 transcript HTML 与 GovInfo 官方详情页；以详情页 `dc.date`、`dc.creator`、`dc.publisher`、`dc.title`、`dc.identifier` 核验书目信息，并从 transcript 唯一 `<pre>` 提取全文、核对封面标题及结束标记。异常装饰线已排除出正式标题；全量原文超过 Excel 单元格上限，按 UTF-8 侧文件交付。批次 97 的 2012 “The Price of Public Diplomacy with China” 页面虽可核对题名和日期，但正文末尾是无法解释的 `\\ts\\` 标记，完整性无法确认，保持 pending。

截至批次 121 及 GovInfo 复核，资料库仍有 268 条候选和 9 次重复发现（277 次 URL 发现），其中 189 verified、47 pending、15 restricted、17 unprocessed；工作簿含 184 条唯一全文资料和 58 个 UTF-8 长正文侧文件。纽约时报、CNN、路透社可合法取得全文、官方社交账号及早期中英文文献仍未充分覆盖，不声称穷尽。

批次 122 补充杜鲁门时期涉华总统记者会。American Presidency Project 的 “The President's News Conference” 发布日期为 1949-10-27（正文 12,973 字符），Harry S. Truman Library 的同名记者会发布页日期为 1950-01-05（正文 19,432 字符）；Scrapy 遵守 robots.txt，页面原文和来源可见日期均经对应适配器核验，2/2 verified。另一候选 “Statement by the President: United States Policy Toward China” 来源页显示发布日期 1945-12-15，早于本研究范围，保留为 pending 并排除出工作簿。批次统计 3 candidate、2 verified、1 pending、0 restricted/duplicate/unprocessed。

同轮复核 FRUS `d173` 候选发现，history.state.gov 当前 Scrapy 响应及同 URL Firecrawl rawHtml 均为 HTTP 200 的 JavaScript 外壳（`history.state.gov 3.0 shell`），不含文档原文；此前状态备注所记 dateline 无法由当前保存证据复核，因此仍为 pending。Firecrawl 响应没有被当作全文。

批次 123 检索 1992—2016 年中英文研究文献，核对北京大学《国际政治研究》范士明《美国媒体敌视中国的原因》。作者、题名、1997 年第 3 期、页码 48—53 和期刊摘要可由北大期刊记录页核实；页面及 PDF 仅提供年/期，没有来源标注的 YYYY-MM-DD 发布日期，故按日期规则保留 pending。期刊站点公开 PDF 为六页扫描件，Firecrawl OCR 输出存在跨页缺段且与版面段落不能完整对应；没有把 OCR 或搜索摘要当作正文，也未将此文纳入 Excel。批次统计 1 candidate、0 verified、1 pending、0 restricted/duplicate/unprocessed。

批次 124 检索 1992—2016 年美国印刷媒体中国形象研究，发现 Yang 与 Liu 的 “The 'China Threat' through the Lens of US Print Media: 1992–2006”。泰勒-弗朗西斯出版社页面搜索线索显示在线发布日期为 2012-04-05；Scrapy 已先获取 robots.txt（HTTP 200），原始文章页返回 HTTP 403，登记为 restricted，不尝试绕过访问限制，也未把出版社之外的搜索摘要用作正文。批次统计 1 candidate、0 verified、0 pending、1 restricted、0 duplicate/unprocessed。

批次 125 补充克林顿政府 1994 年对华最惠国待遇公开材料，共核验 4 份 American Presidency Project 原文：1994-08-09 总统声明（233 字符）、1994-06-02 总统备忘录（844 字符）、1994-08-05 行政政策声明（3,366 字符）和 1994-05-26 总统记者会（21,273 字符）。四个原始页均返回 HTTP 200，来源字段、页面显示日期、作者标注状态、标题及完整正文均通过 Presidency Project 适配器验证；页面未标注个人作者的两份短声明/备忘录按规则记为“未注明”。批次统计 4 candidate、4 verified、0 pending/restricted/duplicate/unprocessed。

批次 126 补充克林顿政府 1996—1999 年对华年度贸易地位公开材料，共核验 5 份 American Presidency Project 原文：1996-06-27 众议院决议后总统声明（974 字符）、1996-06-26 行政政策声明（3,122 字符）、1996-05-31 总统备忘录（849 字符）、1998-06-03 南亚核扩散与中国 MFN 讲话（4,959 字符）和 1999-06-03 延长中国正常贸易关系地位声明（2,228 字符）。五个原始页面均返回 HTTP 200，页面日期、来源、标题、未标注个人作者的状态及完整正文通过适配器核验。批次统计 5 candidate、5 verified、0 pending/restricted/duplicate/unprocessed。

批次 127 补充 1999 年中美 WTO 谈判相关总统公开传播材料，共核验 4 份 American Presidency Project 原文：4 月 8 日中美联合声明（2,376 字符）、9 月 14 日 APEC 峰会及记者问答（5,993 字符）、11 月 15 日驻安卡拉使馆社区讲话（6,010 字符）和 12 月 1 日 WTO 西雅图午餐会讲话（23,762 字符）。四个原始页面均返回 HTTP 200，来源页日期、标题、作者标注和全文通过适配器核验。批次统计 4 candidate、4 verified、0 pending/restricted/duplicate/unprocessed。

批次 128 补充 2000 年 PNTR/WTO 公开材料，抓取 5 个 American Presidency Project 目标页；3 篇通过核验并纳入工作簿：2000-05-19 中国—欧盟 WTO 谈判声明（661 字符）、2000-01-24 致国会领导人信函（9,761 字符）及 2000-03-08 致国会法案咨文（4,298 字符）。另外两页分别返回 HTTP 404，登记为 pending，未以搜索结果文本代替原文。批次统计 5 candidate、3 verified、2 pending、0 restricted/duplicate/unprocessed。

批次 129 补充奥巴马政府 2009—2010 年中美会晤公开材料，共核验 5 份白宫原始页面：2009-04-01 伦敦中美元首会晤讲话（3,200 字符）、2009-09-22 纽约中美元首会晤讲话（2,638 字符）、2009-11-17《美中联合声明》（28,089 字符）、2010-09-23 与温家宝会晤讲话（4,204 字符）和 2010-11-11 与胡锦涛会晤讲话（1,651 字符）。页面日期、原始标题、来源和正文通过适配器核验；新增的 Drupal 旧版结构解析保留段落块，并要求正文显式 END 结尾。原始页面及 Scrapy 证据均为 HTTP 200。批次统计 5 candidate、5 verified、0 pending/restricted/duplicate/unprocessed。

截至批次 129，资料库登记 296 条候选，其中 212 verified、51 pending、16 restricted、17 unprocessed；工作簿含 207 条唯一全文资料和 58 个 UTF-8 长正文侧文件。

批次 130 补充 2011 年白宫公开材料：2011-01-19 奥巴马与胡锦涛共同记者会（35,754 字符）、2011-08-21 拜登四川大学讲话及学生问答（37,869 字符）、2011-11-14 奥巴马记者会（32,127 字符）和 2011-11-19 东盟及东亚峰会背景简报（17,579 字符）。原始 HTML 可见发布日期和发布办公室均经核验；副总统讲话的来源照录为 The White House, Office of the Vice President。三份分段结束的逐字稿要求 END 紧接合法格式结束时间，缺失 END 的回归样例保持未核实。1 月 19 日页面在长段落末尾通过换行标明 END，并非缺失结束标记。各篇摘要以“据正文整理：”开头，关键词取自正文。11 月 12 日视频页未核实完整逐字稿，继续 pending。批次统计 5 candidate、4 verified、1 pending、0 restricted/duplicate/unprocessed。

截至批次 130，数据库有 301 条候选状态记录：216 verified、52 pending、16 restricted、17 unprocessed；另登记 9 次跨批重复发现。工作簿含 211 条唯一全文资料和 60 个 UTF-8 长正文侧文件，全部九列及外置正文逐字段与数据库一致。候选状态记录数与重复发现数属于不同统计口径，不相加当作唯一资料数量。纽约时报、CNN、路透社可合法取得全文、官方社交账号及中英文研究文献仍未充分覆盖，不声称穷尽。

截至批次 86，资料库登记 167 条候选：116 条全文已核实、28 条待核验、10 条受限、13 条未处理；工作簿含 113 条唯一来源链接。批次 86 检索 FRUS 1958—1960 年《中国》卷 XIX 的 5 份台海危机原始文件：1958-08-25 白宫会议备忘录（5,325 字符）、09-04 艾森豪威尔总统会议纪要（2,224 字符）、09-12 致赫鲁晓夫信（4,110 字符）、10-23 美台联合公报（4,438 字符）及 10-24 杜勒斯致英国外交大臣信（5,027 字符）。原站 robots.txt 与目标页均 HTTP 200；保存 HTML 由 FRUS 适配器重解析后，来源、日期、作者、标题及五篇正文均逐字段/逐字符与数据库一致。摘要按正文整理并加前缀，关键词根据正文提取。批次统计 5 候选、5 verified、0 pending/restricted/duplicate/unprocessed；此批仅覆盖检索到的五份材料。

截至批次 85，资料库登记 162 条候选：111 条全文已核实、28 条待核验、10 条受限、13 条未处理；工作簿含 108 条唯一来源链接。批次 85 检索 FRUS《中国》1955—1957 卷 II 的 5 份原始文件。2 篇通过核验：1955-03-16 DCI 局长 Allen W. Dulles 关于台湾国民党方面受颠覆活动影响可能性的备忘录（8,826 字符）；1955-05-24 Dulles 致美国驻印度使馆的台湾停火谈判电报（2,365 字符）。两篇的摘要均以“据正文整理：”开头，关键词来自正文。另 3 篇保留 pending：两页为未显示单一发布日期的 Editorial Note；一份 1955-03-27 联合参谋长备忘录有精确日期，但当前解析器尚不支持其 `27 March, 1955` 格式。该批 Scrapy robots.txt 与五个原始页面均返回 HTTP 200；批次统计 5 候选、2 verified、3 pending、0 restricted/duplicate/unprocessed。

截至批次 84，资料库登记 157 条候选：109 条全文已核实、25 条待核验、10 条受限、13 条未处理；工作簿含 106 条唯一来源链接。批次 84 检索 CNN 与 Reuters 的 2018—2025 年对华贸易报道，共 4 个原始页面。Scrapy 获取两站 robots.txt 后，四个目标路径均被 robots 规则禁止，文章页面未请求，故批次记为 4 条未处理（候选记录保留 `Forbidden by robots.txt` 详情），未标记为已抓取/受限，也未将搜索结果摘要用作正文。

截至批次 83，资料库登记 153 条候选：109 条全文已核实、25 条待核验、10 条受限、9 条未处理；工作簿含 106 条唯一来源链接。批次 83 检索 2017—2025 年 Frontiers 期刊上的美国媒体/对华话语研究三篇：2025 年美国贸易政策话语论文的出版方 PDF 共 13 页，另两篇 2023 年文章为出版方 HTML 原文页。Scrapy 访问 robots.txt 和三个目标页均获 HTTP 200；但当前适配器未能核实来源字段与完整正文，三篇均保留 pending，未纳入 Excel。检索摘要未作为正文。

截至批次 82，资料库登记 150 条候选：109 条全文已核实、22 条待核验、10 条受限、9 条未处理；工作簿含 106 条唯一来源链接。批次 82 检索 2017—2025 年美国媒体中国形象研究文献两个出版方页面：SAGE 出版方页面和 robots.txt 返回 HTTP 403，均按受限登记；未使用搜索片段或摘要作为正文，也未尝试绕过访问限制。批次结果为 2 候选、0 已核实全文、2 受限、0 待核验/重复/未处理，未增加正式 Excel 记录。

截至批次 81，资料库登记 148 条候选：109 条全文已核实、22 条待核验、8 条受限、9 条未处理；工作簿含 106 条唯一来源链接。批次 81 检索 1949—1954 年 FRUS 中国相关公开文件，4/4 篇通过原始页面与 robots.txt HTTP 200、来源/日期/标题/作者元数据及正文区域核验：1949-03-30 驻华大使 Stuart 致国务卿备忘录（10,513 字符）、1952-08-01 心理战略委员会报告（14,707 字符）、1953-02-10 国家安全委员会报告（35,052 字符）和 1953-11-06 NSC 对共产主义中国政策声明（77,696 字符）。四篇正文由保存的原始 HTML 重跑 FRUS 适配器后与数据库逐字符一致；摘要均以“据正文整理：”开头，关键词根据正文填写。新增 4 个候选，0 pending/restricted/duplicate/unprocessed。该批次来自 FRUS 页面搜索线索，不代表早期政府文件或广播资料已穷尽。

截至批次 80，资料库登记 144 条候选：105 条全文已核实、22 条待核验、8 条受限、9 条未处理；工作簿含 102 条唯一来源链接。批次 80 检索 2018—2023 年美国政府对华公开讲话与记者会四个原始页面：Pence 2018-10-04 Hudson 演讲全文（29,542 字符）通过核验；Pompeo 的 2017—2021 State.gov 页面及官方翻译站均返回 “Technical Difficulties”，保留 pending；Blinken 2023-06-19 北京记者会使馆页和 robots.txt 返回 HTTP 403，保留 restricted。Pence 页面及 robots.txt 返回 HTTP 200，适配器按页面唯一标题、日期、正文段落和 `END` 标记核验，缺少终止标记的离线测试不会通过。批次 79 新增 1989 年布什政府对华公开表述四份材料：1989-05-21、06-08、06-27 三场总统记者会（正文 20,526、30,254、39,434 字符）及 06-20 Fitzwater 新闻秘书声明（1,173 字符）。前三篇来源为 American Presidency Project，后者来自 George H.W. Bush Presidential Library and Museum；原始页面与 robots.txt 返回 HTTP 200，核对了页面标题、日期和完整正文。Bush Library 专用适配器以先失败的离线测试验证，只提取页面标题、单一日期和正文容器段落。批次 78 新增卡特政府 1978 年中美建交公开传播材料四篇：12 月 15 日的全国讲话（正文 5,578 字符）、美国声明（1,730 字符）、白宫简报（5,325 字符）和 12 月 30 日总统备忘录（2,541 字符）。原始页面和 robots.txt 均返回 HTTP 200；页面显示日期、标题及正文核验通过。批次 77 检索 FRUS 第 XVIII 卷 1973—1975 年中国卷四篇单篇文件；1973-11-12、1975-07-03、1975-11-20 三篇通过核验，正文分别为 47,468、32,525、48,025 字符，原页和 robots.txt 均返回 HTTP 200。Document 12 的原页日期为 1973-02-17 至 18 日的时间区间，不能确定唯一年月日，因此保留 pending、不进入工作簿。批次 76 检索了 FRUS 第 XVII 卷 1969—1972 年中国卷四篇单篇文档；1972-01-03、1972-02-22、1972-03-09 三篇通过核验，正文分别为 28,491、67,829、6,975 字符，原页和 robots.txt 均返回 HTTP 200。Document 165 的原页面明确标注 `Washington, undated`，没有可用年月日，因此保留 pending、不进入工作簿。批次 75 新增两份 FRUS 对华广播与国际信息活动文件：1953-06-30 总统国际信息活动委员会报告（正文 196,378 字符）与 1953-10-01 提交国家安全委员会的备忘录（42,803 字符）。原始页面和 robots.txt 均返回 HTTP 200，来源、文件日期、题名、作者及文档正文区通过 FRUS 适配器核验。批次 74 新增 VOA 两篇天安门相关公开传播材料：2009-06-02 社论 “Tiananmen, Twenty Years Later”（正文 1,935 字符）和 2013-06-04 新闻 “China Marks 24th Anniversary of Tiananmen Crackdown”（正文 2,225 字符）。原始页面与 robots.txt 均返回 HTTP 200；日期与 JSON-LD 发布时刻对应，标题、机构署名和正文段落均在页面核对。批次 73 核验了 FRUS 1981—1988 年卷 I 三份对华文件：1982-09-22 的 Wolfowitz 备忘录（12,848 字符）已作为重复发现，不另存资料行；1985-05-28 的 Rodman 备忘录（13,241 字符）和 1986-04-22 的 Solomon 备忘录（7,058 字符）是新增唯一记录。三个原始页面及 robots.txt 均返回 HTTP 200，FRUS 适配器验证了来源、文件日期、题名和正文区域。国务院对华专卷 XXVIII（1981—1983）与 XXIX（1984—1988）在检索时标记为 Being Cleared，不作为可访问材料采集。

截至批次 72，资料库登记 117 条候选：83 条全文已核实、18 条待核验、7 条受限、9 条未处理；工作簿含 81 条唯一来源链接。批次 72 新增 Clinton White House Archives 2000-09-14 Joe Lockhart 记者会逐字稿，正文 27,121 字符；原页和 robots.txt 均为 HTTP 200，发布日期取自原始页 `For Immediate Release`，标题、页面署名和 `END 2:00 P.M. EDT` 结尾均核验通过。适配器支持跨行发布声明，并从页面标题照录讲话人姓名为作者。

截至批次 71，资料库登记 116 条候选：82 条全文已核实、18 条待核验、7 条受限、9 条未处理；工作簿含 80 条唯一来源链接。批次 71 新增 Clinton White House Archives 1999-04-07 外交政策演讲逐字稿，正文 26,556 字符。原页面与 robots.txt 返回 HTTP 200；发布日期取自 `For Immediate Release`，标题从页面主标题按页面 `<title>` 词项精确截取，排除会场/地点信息，正文止于页面页脚边界。

截至批次 71，资料库登记 116 条候选：82 条全文已核实、18 条待核验、7 条受限、9 条未处理；工作簿含 80 条唯一来源链接。批次 71 新增 Clinton White House Archives 1999-04-07 外交政策演讲逐字稿，正文 26,556 字符。原页面与 robots.txt 返回 HTTP 200；发布日期取自 `For Immediate Release`，标题从页面主标题按页面 `<title>` 词项精确截取，排除会场/地点信息，正文止于页面页脚边界。

截至批次 70，资料库登记 115 条候选：81 条全文已核实、18 条待核验、7 条受限、9 条未处理；工作簿含 79 条唯一来源链接。批次 70 尝试采集 Reagan Library 的 1984-04-27 对华讲话页面，Scrapy/robots.txt 均返回 HTTP 200，页面有完整讲话原文，但唯一日期字段为讲话日期 `Date: 04/27/1984`，未见独立发布日期。依用户日期规则，该记录保留 pending，未进入工作簿。

截至批次 69，资料库登记 114 条候选：81 条全文已核实、17 条待核验、7 条受限、9 条未处理；工作簿含 79 条唯一来源链接。批次 69 新增三份 FRUS 1977—1980《中国》卷文件：1977-01-08 与 1977-02-08 两份备忘录（正文 25,600、16,614 字符）及 1979-01-11 电报（21,390 字符）；原始页和 robots.txt 均返回 HTTP 200，来源、题名、文件日期和全文通过 FRUS 适配器核验。d191 已在旧批次发现，重复计数增加 1。

截至批次 68，资料库登记 111 条候选：78 条全文已核实、17 条待核验、7 条受限、9 条未处理；工作簿含 77 条唯一来源链接。批次 68 新增 Clinton White House Archives 的 2000-03-08 对华 WTO 资料页，正文 4,887 字符；原页面和 robots.txt 均返回 HTTP 200，日期取自 “For Immediate Release” 栏，全文按唯一 354px 正文列顺序提取，排除两侧导航和页脚，并修正该旧站 Windows-1252 字节的替换字符问题。作者未标注，记录为“未注明”。批次 67 新增该档案的 2000-10-10 对华 PNTR 签署活动逐字稿，正文 28,822 字符；唯一 `<PRE>` 全文以正式 `END 5:31 P.M. EDT` 标记收尾，页面历史提示与页脚未进入正文。批次 66 新增国务院 2022-05-26 Blinken 对华政策讲话，全文 42,410 字符；因批次 65 已发现同一原始 URL，重复计数为 1。Scrapy 对该页面返回技术故障 HTML，Firecrawl 提供的同 URL 原始 HTML 经专用适配器核验后导入；语言切换链接及视频播放器模板已从正文排除。批次 64 新增两篇 PMC 开放研究论文，分别发表于 2022-03-11 和 2020-09-11，正文长度为 48,008 和 75,397 字符，均通过原始页面全文核验。批次 63 的 1951 年 FRUS 会谈备忘录已核实，出版日期为 1951-05-03，正文 23,288 字符；同批另一文档页保留为待核验。批次 62 的 2025 PMC 论文全文 55,493 字符，也已核实并纳入工作簿。PMC 新版 Cloud viewer 适配器从正式主稿选取标题、引文日期和正文容器，排除嵌入的审稿往来子文章；旧版与新版结构均有离线 fixture 测试。

按以下时期分别运行查询计划和来源批次：1949—1972、1972—1991、1992—2016、2017—2025。每批还应按媒体、政府/广播机构、智库/研究机构/非政府组织、新媒体和中英文研究文献划分。系统记录当前实际处理量，不声明绝对穷尽。搜索摘要、目录信息、AI 摘要和引用片段永远不能代替正式表中的原文全文。

现有专用适配器仅覆盖已列明并试采的页面版式，不能代表覆盖同机构全部材料。纽约时报、CNN、路透社、社交平台、研究文献和更多政府/智库版式仍需分批检索；robots.txt、HTTP 403、缺少精确发布日期或不完整正文的页面继续按实际状态报告，不绕过限制，也不以摘要替代原文。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\scrapy.exe check
```
批次 179 通过 Firecrawl 搜索定位 APP 原始记者会页面，经 Scrapy 在 robots.txt 许可下抓取（robots 与页面均 HTTP 200）。来源页显示 1962-06-27、作者 John F. Kennedy、标题 “The President's News Conference”；30,438 字符正文经 APP 适配器核验完整，结尾为记者致谢，台湾海峡段落谈及共产中国、金门、马祖与美国政策。页面无摘要和关键词值，未以搜索摘要补写。1 candidate、1 verified、0 pending/restricted/duplicate/unprocessed；正式表净增 1 条。复核和发现记录见 `data/reviews/kennedy-taiwan-strait-news-conference-1962-20261107/review.json` 与 `research/firecrawl/early-taiwan-strait-news-conference-1962-20261107/search.json`。
批次 180 对 TMG Journal for Media History 的论文 “Transnational Environments and 'Mixed Signals' in Radio Propaganda: The Voice of America, the BBC, and the People’s Republic of China, 1949-1976” 做来源发现。期刊元数据表明发布日期为 2021-12-08，作者 Donald Santacaterina，DOI 10.18146/tmg.778，并标注 CC BY-SA 4.0；但 Scrapy 按 robots.txt 规则在元数据页请求阶段被拒绝，未请求 PDF。Firecrawl 数据只保存为发现/元数据线索，不当作授权全文或正式字段证据；批次 1 candidate、0 verified、1 restricted、0 pending/duplicate/unprocessed，正式表净增 0。记录见 `research/firecrawl/tmg-voa-bbc-china-2021-20261107/publisher-page.json` 和 `data/reviews/tmg-voa-bbc-china-2021-20261107/review.json`。
