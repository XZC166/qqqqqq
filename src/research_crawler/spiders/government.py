from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from urllib.parse import urlsplit

import scrapy
from scrapy.http import Response

from research_crawler.adapters import SourceAdapter
from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.policy import AccessDecision, classify_response
from research_crawler.discovery import import_candidate_csv


class GovernmentArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        hostname = (urlsplit(response.url).hostname or "").lower()
        if hostname == "whitehouse.gov" or hostname.endswith(".whitehouse.gov"):
            return WhiteHouseFactSheetAdapter().extract(response, candidate)
        if hostname == "2021-2025.state.gov":
            state_result = StateDepartmentRemarksAdapter().extract(response, candidate)
            if state_result["material"] is not None or state_result["decision"] is AccessDecision.RESTRICTED:
                return state_result

        structured = JsonLdArticleAdapter().extract(response, candidate)
        if structured["material"] is not None or structured["decision"] is AccessDecision.RESTRICTED:
            return structured

        body_text = response.text
        decision = classify_response(response.url, response.status, body_text)
        digest = sha256(response.body).hexdigest()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status_code=response.status,
            content_sha256=digest,
            body_complete=False,
            metadata_verified=False,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        article = response.css("article[data-full-text='true']")
        title = " ".join(article.css("h1::text").getall()).strip()
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        visible_date = _normalized_text(article.css("time").xpath(".//text()").getall())
        structured_date = (
            response.css("meta[property='article:published_time']::attr(content)").get()
            or article.css("time[datetime]::attr(datetime)").get()
            or ""
        ).strip()
        publication_date = _publication_date(visible_date, structured_date)
        author = response.css("meta[name='author']::attr(content)").get(default="").strip()
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        paragraphs = [
            " ".join(paragraph.xpath(".//text()").getall()).strip()
            for paragraph in article.css(".article-body p")
        ]
        body = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
        complete_marker = article.attrib.get("data-full-text", "").casefold() == "true"

        if not (source and title and publication_date and body and complete_marker):
            return {"decision": decision, "evidence": evidence, "material": None}

        material = VerifiedMaterial(
            source=source,
            time=publication_date,
            author=author or "未注明",
            title=title,
            abstract=abstract,
            keywords=keywords,
            body=body,
            source_url=response.url,
        )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=evidence.fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete_marker,
            metadata_verified=True,
            body_format="source_text",
        )
        field_sources = {
            "source": response.url,
            "time": response.url,
            "author": response.url,
            "title": response.url,
        }
        if abstract:
            field_sources["abstract"] = response.url
        if keywords:
            field_sources["keywords"] = response.url
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if abstract else "none",
        }


class JsonLdArticleAdapter:
    article_types = {
        "article",
        "newsarticle",
        "report",
        "blogposting",
        "socialmediaposting",
    }

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status, response.text)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        article = _find_jsonld_article(response)
        if article is None:
            return {"decision": decision, "evidence": evidence, "material": None}
        if str(article.get("isAccessibleForFree", "true")).casefold() == "false":
            return {
                "decision": AccessDecision.RESTRICTED,
                "evidence": evidence,
                "material": None,
            }

        headline = _normalized_text([str(article.get("headline", ""))])
        page_title = _normalized_text(response.css("article h1").xpath(".//text()").getall())
        body = str(article.get("articleBody", "")).strip()
        body_node = response.css("[itemprop='articleBody']")
        visible_body = _normalized_text(body_node.xpath(".//text()").getall())
        if not body or not headline or headline != page_title or _normalized_text([body]) != visible_body:
            return {"decision": decision, "evidence": evidence, "material": None}

        publisher = article.get("publisher") or {}
        if isinstance(publisher, list):
            publisher = publisher[0] if publisher else {}
        source = _normalized_text([str(publisher.get("name", ""))]) if isinstance(publisher, dict) else ""
        date_text = _normalized_text(response.css("article time").xpath(".//text()").getall())
        publication_date = _publication_date(date_text, str(article.get("datePublished", "")))
        if not source or not publication_date:
            return {"decision": decision, "evidence": evidence, "material": None}

        author_value = article.get("author") or ""
        if isinstance(author_value, list):
            authors = [_jsonld_name(value) for value in author_value]
            author = ", ".join(name for name in authors if name)
        else:
            author = _jsonld_name(author_value)
        abstract = str(article.get("description", "")).strip()
        raw_keywords = article.get("keywords", "")
        if isinstance(raw_keywords, list):
            keywords = "; ".join(str(value).strip() for value in raw_keywords if str(value).strip())
        else:
            keywords = str(raw_keywords).strip()

        material = VerifiedMaterial(
            source=source,
            time=publication_date,
            author=author or "未注明",
            title=headline,
            abstract=abstract,
            keywords=keywords,
            body=body,
            source_url=response.url,
        )
        field_sources = {
            name: response.url for name in ("source", "time", "author", "title")
        }
        if abstract:
            field_sources["abstract"] = response.url
        if keywords:
            field_sources["keywords"] = response.url
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=True,
            metadata_verified=True,
            body_format="source_text",
        )
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if abstract else "none",
        }


class WhiteHouseFactSheetAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        if decision is not AccessDecision.ALLOW:
            return {
                "decision": decision,
                "evidence": SourceEvidence(
                    response.url, fetched_at, response.status, digest
                ),
                "material": None,
            }

        content = response.css("main .entry-content")
        topper = content.css(".wp-block-whitehouse-topper")
        title = _normalized_text(topper.css("h1").xpath(".//text()").getall())
        visible_date = _normalized_text(topper.css("time").xpath(".//text()").getall())
        try:
            published_on = datetime.strptime(visible_date, "%B %d, %Y").date().isoformat()
        except ValueError:
            published_on = ""

        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        body_blocks = []
        for block in content.xpath("./*"):
            if "wp-block-whitehouse-topper" in block.attrib.get("class", ""):
                continue
            tag = block.root.tag.lower()
            if tag in {"ul", "ol"}:
                items = [
                    _normalized_text(item.xpath(".//text()").getall())
                    for item in block.xpath("./li")
                ]
                list_text = "\n".join(f"• {item}" for item in items if item)
                if list_text:
                    body_blocks.append(list_text)
            elif tag in {"p", "h2", "h3", "blockquote"}:
                text = _normalized_text(block.xpath(".//text()").getall())
                if text:
                    body_blocks.append(text)
        body = "\n\n".join(body_blocks)
        complete = bool(title and visible_date and body and content and topper)
        lowered_body = body.casefold()
        if any(marker in lowered_body for marker in ("continue reading", "subscribe to read", "read more")):
            complete = False

        material = None
        field_sources = {}
        abstract_origin = "none"
        metadata_verified = False
        if source and title and published_on and body and complete:
            material = VerifiedMaterial(
                source=source,
                time=published_on,
                author="未注明",
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
            field_sources = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                field_sources["abstract"] = response.url
            if keywords:
                field_sources["keywords"] = response.url
            abstract_origin = "publisher" if abstract else "none"
            metadata_verified = True

        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=metadata_verified,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = field_sources
            result["abstract_origin"] = abstract_origin
        return result


class StateDepartmentRemarksAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        if decision is not AccessDecision.ALLOW:
            return {
                "decision": decision,
                "evidence": SourceEvidence(response.url, fetched_at, response.status, digest),
                "material": None,
            }

        article = response.css("main.nav__main-content article")
        content = article.css(".entry-content")
        title = _normalized_text(content.css(".featured-content__headline").xpath(".//text()").getall())
        visible_date = _normalized_text(content.css(".article-meta__publish-date").xpath(".//text()").getall())
        publication_date = _publication_date(visible_date, "")
        author_text = _normalized_text(content.css(".article-meta__author-bureau").xpath(".//text()").getall())
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        body_container = content.css(".classic-block-wrapper")
        body_blocks = []
        if body_container:
            for block in body_container.xpath(".//p | .//h2 | .//h3 | .//blockquote | .//ul | .//ol"):
                tag = block.root.tag.lower()
                if tag in {"ul", "ol"}:
                    items = [
                        _normalized_text(item.xpath(".//text()").getall())
                        for item in block.xpath("./li")
                    ]
                    value = "\n".join(f"• {item}" for item in items if item)
                else:
                    value = _normalized_text(block.xpath(".//text()").getall())
                if value:
                    body_blocks.append(value)
        body = "\n\n".join(body_blocks)
        complete = bool(article and content and body_container and title and publication_date and body)
        material = None
        result = {"decision": decision, "material": None}
        if complete and source:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author=author_text or "未注明",
                title=title,
                abstract="",
                keywords="",
                body=body,
                source_url=response.url,
            )
            result["material"] = material
        result["evidence"] = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete and material is not None,
            metadata_verified=material is not None,
            body_format="source_text",
        )
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            result["abstract_origin"] = "none"
        return result


def _normalized_text(values: list[str]) -> str:
    return " ".join(" ".join(values).split())


def _find_jsonld_article(response: Response) -> dict | None:
    for script in response.css("script[type='application/ld+json']::text").getall():
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            graph = node.get("@graph", [])
            nodes_to_check = [node, *(graph if isinstance(graph, list) else [])]
            for candidate in nodes_to_check:
                if not isinstance(candidate, dict):
                    continue
                types = candidate.get("@type", [])
                if isinstance(types, str):
                    types = [types]
                if any(str(value).casefold() in JsonLdArticleAdapter.article_types for value in types):
                    return candidate
    return None


def _jsonld_name(value) -> str:
    if isinstance(value, dict):
        return _normalized_text([str(value.get("name", ""))])
    return _normalized_text([str(value)]) if value else ""


def _publication_date(visible_date: str, structured_date: str) -> str:
    for value in (visible_date, structured_date):
        value = value.strip()
        try:
            return datetime.strptime(value, "%B %d, %Y").date().isoformat()
        except ValueError:
            pass
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                return datetime.fromisoformat(value).date().isoformat()
            except ValueError:
                pass
        if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
    return ""


class GovernmentSpider(scrapy.Spider):
    name = "government"

    def __init__(
        self,
        url: str | None = None,
        period: str | None = None,
        source_category: str = "government",
        query_label: str = "manual",
        candidates_csv: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.url = url
        self.period = period
        self.source_category = source_category
        self.query_label = query_label
        self.candidates_csv = candidates_csv
        if url and not period:
            raise ValueError("period is required when a URL is supplied")
        self.candidates = import_candidate_csv(candidates_csv) if candidates_csv else []
        if url:
            self.candidates = [
                MaterialCandidate(url, period, source_category, query_label)
            ]
        self.adapter: SourceAdapter = GovernmentArticleAdapter()

    async def start(self):
        for candidate in self.candidates:
            yield scrapy.Request(
                candidate.source_url,
                callback=self.parse,
                meta={"handle_httpstatus_all": True, "candidate": candidate},
                dont_filter=True,
            )

    def start_requests(self):
        for candidate in self.candidates:
            yield scrapy.Request(
                candidate.source_url,
                callback=self.parse,
                meta={"handle_httpstatus_all": True, "candidate": candidate},
                dont_filter=True,
            )

    def parse(self, response: Response):
        candidate = response.meta["candidate"]
        result = self.adapter.extract(response, candidate)
        result["candidate"] = candidate
        result["raw_response"] = response.body
        yield result
