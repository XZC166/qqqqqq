# Research Crawler

本项目为学位论文“美国对华舆论传播与话语竞争的历史演变（1949—2025）”生成检索计划、采集允许公开访问的原始页面、保存来源证据、核验全文并导出资料表。

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

## 检索与候选 URL

按时期和来源类别生成查询式：

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

Scrapy 遵守 robots.txt，默认同一网域并发为 1、请求延迟 1 秒并启用 AutoThrottle。401、402、403 和明确付费墙信号会被标记为受限；系统不登录、不注入 Cookie、不绕过付费墙或其他访问控制。Scrapy 的解析器只为已实现的来源版型提供字段；没有可靠匹配的页面会留在待核验状态。

当前内置并完成真实页面全文试采的站点适配器针对白宫事实清单页面。另有通用 JSON-LD 新闻/文章适配器：只有当来源发布的 `articleBody` 与页面 `itemprop="articleBody"` 正文完全一致、标题一致且访问属性未标记为付费时才接收；这个通用格式目前通过离线 fixture 验证，尚未逐站点实测。通用政府页面适配器只接受明示的 `article[data-full-text="true"]` 模板。

另有美国国务院 2021-2025 归档站点讲话页适配器，依据该站公开页面的主内容版式编写并通过离线 fixture 测试。对页面 `https://2021-2025.state.gov/remarks-at-the-asia-society-on-countering-economic-coercion/` 直接使用 Scrapy 时，候选 1 条、已核实全文 0 条、待核验 1 条；保存的 HTTP 200 响应是 “Technical Difficulties” 页面，未将其误收为正文。随后通过 Firecrawl 获取同一页面完整 `rawHtml` 并用 `import-firecrawl` 导入：候选 1 条、已核实全文 1 条、待核验 0 条。导出的工作簿为九列、一条记录；正文 10,031 字符，与 SQLite 正文一致，证据文件与捕获 HTML 的哈希一致。该验证只覆盖这一篇国务院讲话。纽约时报、美联社、CNN、路透社、智库、其他政府来源、社交平台和研究文献尚无已实测的专用适配器；相应材料应留作候选或待核验，不应声称已经覆盖。

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

## 报告与导出

```powershell
.\.venv\Scripts\research-crawler.exe report --db data/research.sqlite3 --batch-id 1
.\.venv\Scripts\research-crawler.exe export --db data/research.sqlite3 --output data/materials.xlsx
```

工作簿严格只有九列：来源、时间、作者、标题、摘要、关键词、正文、来源链接、重复计数。超过 Excel 单元格长度的正文完整保存至工作簿同目录下的 `<工作簿名>_bodies/`，正文单元格写相对路径。批次报告分列候选、已核实全文、受限、待核验、未处理和重复数量，并列出未取得全文的候选。

## 覆盖范围

按以下时期分别运行查询计划和来源批次：1949—1972、1972—1991、1992—2016、2017—2025。每批还应按媒体、政府/广播机构、智库/研究机构/非政府组织、新媒体和中英文研究文献划分。系统记录当前实际处理量，不声明绝对穷尽。搜索摘要、目录信息、AI 摘要和引用片段永远不能代替正式表中的原文全文。

现阶段除白宫事实清单外，其余来源族尚未提供经过实测的适配器；它们应列为未覆盖，而不是声称已经采集。初次验收先使用离线 fixture 测试，再以单页真实公开来源验证，不对媒体或其他来源执行高并发批量请求。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\scrapy.exe check
```
