from datetime import datetime, timezone
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import html
import json
import re
from urllib.parse import unquote, urljoin, urlsplit

import scrapy
from pypdf import PdfReader
from scrapy.http import HtmlResponse, Response

from research_crawler.adapters import SourceAdapter
from research_crawler.items import MaterialCandidate, SourceEvidence, VerifiedMaterial
from research_crawler.policy import AccessDecision, classify_response
from research_crawler.discovery import import_candidate_csv
from research_crawler.reviewed_sources import (
    BUSH41_REVIEWED_METADATA,
    DAN_RATHER_REVIEWED_SCANNED_TRANSCRIPTS,
    FRIENDS_JOURNAL_REVIEWED_ARTICLES,
    DAILY_IOWAN_REVIEWED_ARTICLES,
    CARNEGIE_REVIEWED_ARTICLES,
    CLINTON_WHITEHOUSE_REVIEWED_METADATA,
    CLINTON_WHITEHOUSE_REVIEWED_HASHED_METADATA,
    TRUMP_WHITEHOUSE_REVIEWED_HASHED_METADATA,
    OBAMA_WHITEHOUSE_REVIEWED_METADATA,
    OBAMA_WHITEHOUSE_REVIEWED_STATEMENTS,
    OBAMA_WHITEHOUSE_REVIEWED_VIDEO_TRANSCRIPTS,
    ARCHIVED_STATE_REVIEWED_METADATA,
    BROOKINGS_REVIEWED_PDF_METADATA,
    BROOKINGS_REVIEWED_ABSTRACTS,
    BROOKINGS_REVIEWED_KEYWORDS,
    CSIS_REVIEWED_KEYWORDS,
    CSIS_REVIEWED_PDFS,
    USTR_REVIEWED_METADATA,
    RFA_REVIEWED_KEYWORDS,
    GOVINFO_REVIEWED_METADATA,
    NSARCHIVE_REVIEWED_METADATA,
    STATE_REVIEWED_METADATA,
    PBS_REVIEWED_ARTICLES,
    PBS_REVIEWED_VIDEO_TRANSCRIPTS,
    PBS_REVIEWED_VIDEO_KEYWORDS,
    PBS_REVIEWED_PROGRAM_TRANSCRIPTS,
    PEW_REVIEWED_ARTICLES,
    PUBLIC_MEDIA_REVIEWED_ARTICLES,
    PUBLIC_MEDIA_REVIEWED_DERIVED_ABSTRACTS,
    PUBLIC_MEDIA_REVIEWED_META_TITLES,
    PRESIDENCY_REVIEWED_METADATA,
    PRESIDENCY_REVIEWED_HASHED_METADATA,
    BLUESKY_REVIEWED_HASHED_METADATA,
    PRCLEADER_REVIEWED_ARTICLES,
    RESEARCH_REVIEWED_KEYWORDS,
    SHORENSTEIN_REVIEWED_PDFS,
    VOA_REVIEWED_KEYWORDS,
    TRUMAN_LIBRARY_REVIEWED_METADATA,
    TRUMAN_LIBRARY_REVIEWED_HASHED_METADATA,
    TRUMAN_LIBRARY_VISIBLE_PUBLICATION_DATE_URLS,
)


HTTP_ERROR_STATUSES = tuple(range(400, 600))


def _pdf_has_page_images(pages) -> bool:
    if not pages:
        return False
    image_pages = 0
    for page in pages:
        try:
            image_pages += bool(page.images)
        except Exception:
            return True
    return image_pages * 5 >= len(pages) * 4


def _reviewed_research_keywords(source_url: str, body: str) -> str:
    reviewed = RESEARCH_REVIEWED_KEYWORDS.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1]
    return ""


def _reviewed_brookings_keywords(source_url: str, body: str) -> str:
    # Brookings JSON-LD keywords include taxonomy/program and format tags.
    # Do not treat that field as article themes without a body review.
    reviewed = BROOKINGS_REVIEWED_KEYWORDS.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1]
    return ""


def _reviewed_brookings_abstract(source_url: str, body: str) -> str:
    reviewed = BROOKINGS_REVIEWED_ABSTRACTS.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1]
    return ""


def _reviewed_csis_keywords(source_url: str, body: str) -> str:
    reviewed = CSIS_REVIEWED_KEYWORDS.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1]
    return ""


def _reviewed_ustr_metadata(source_url: str, body: str) -> tuple[str, str]:
    reviewed = USTR_REVIEWED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return "", ""


def _reviewed_rfa_keywords(source_url: str, body: str) -> str:
    reviewed = RFA_REVIEWED_KEYWORDS.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1]
    return ""


def _reviewed_govinfo_metadata(source_url: str, body: str) -> tuple[str, str]:
    reviewed = GOVINFO_REVIEWED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return "", ""


def _reviewed_nsarchive_metadata(source_url: str, body: str) -> tuple[str, str]:
    reviewed = NSARCHIVE_REVIEWED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return "", ""


def _nsarchive_metadata_fields(
    source_url: str, body: str, abstract: str, keywords: str
) -> tuple[str, str, str, str]:
    reviewed_abstract, reviewed_keywords = _reviewed_nsarchive_metadata(source_url, body)
    publisher_abstract = bool(abstract)
    publisher_keywords = bool(keywords)
    abstract = abstract or reviewed_abstract
    keywords = keywords or reviewed_keywords
    return (
        abstract,
        keywords,
        "publisher" if publisher_abstract else "derived" if abstract else "none",
        "publisher" if publisher_keywords else "derived" if keywords else "none",
    )


def _reviewed_clinton_metadata(source_url: str, body: str):
    reviewed = CLINTON_WHITEHOUSE_REVIEWED_HASHED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return CLINTON_WHITEHOUSE_REVIEWED_METADATA.get(source_url)


def _reviewed_presidency_metadata(source_url: str, body: str):
    reviewed = PRESIDENCY_REVIEWED_HASHED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return PRESIDENCY_REVIEWED_METADATA.get(source_url)


def _reviewed_bluesky_metadata(source_url: str, body: str) -> tuple[str, str]:
    reviewed = BLUESKY_REVIEWED_HASHED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return "", ""


def _derive_bluesky_metadata(body: str) -> tuple[str, str]:
    protected = body.replace("U.S.", "U<dot>S<dot>").replace("A.I.", "A<dot>I<dot>")
    first_sentence = re.split(r"(?<=[.!?])\s+", protected.strip(), maxsplit=1)[0]
    first_sentence = first_sentence.replace("U<dot>S<dot>", "U.S.").replace("A<dot>I<dot>", "A.I.")
    if len(first_sentence) > 220:
        first_sentence = first_sentence[:220].rsplit(" ", 1)[0]
    abstract = f"据正文整理：{first_sentence}" if first_sentence else ""
    terms = (
        ("U.S.-China", r"\bU\.S\.-China\b"),
        ("United States", r"\bUnited States\b|\bU\.S\.(?!-)(?=\W|$)"),
        ("China", r"\bChina\b"),
        ("Chinese", r"\bChinese\b"),
        ("Taiwan", r"\bTaiwan(?:ese)?\b"),
        ("Hong Kong", r"\bHong Kong\b"),
        ("Xinjiang", r"\bXinjiang\b"),
        ("Beijing", r"\bBeijing\b"),
        ("trade war", r"\btrade war\b"),
        ("tariffs", r"\btariffs?\b"),
        ("technology", r"\btechnolog(?:y|ical)\b"),
        ("artificial intelligence", r"\b(?:artificial intelligence|A\.I\.|AI)\b"),
        ("military", r"\bmilitary\b"),
        ("democracy", r"\bdemocrac(?:y|ies)\b"),
        ("public opinion", r"\bpublic opinion\b"),
        ("propaganda", r"\bpropaganda\b"),
        ("information operations", r"\binformation operations\b"),
        ("disinformation", r"\bdisinformation\b"),
        ("misinformation", r"\bmisinformation\b"),
        ("semiconductors", r"\bsemiconductor\w*\b"),
        ("TikTok", r"\bTikTok\b"),
    )
    keywords = [label for label, pattern in terms if re.search(pattern, body, re.I)]
    return abstract, "; ".join(keywords)


def _bluesky_post_text_matches(
    page_text: str, body: str, record: dict, external_url: str = "", page_links=()
) -> bool:
    if page_text == body or bool(external_url and page_text == body + "\n" + external_url):
        return True
    facets = record.get("facets", [])
    linked_urls = {
        feature.get("uri")
        for facet in facets if isinstance(facet, dict)
        for feature in facet.get("features", []) if isinstance(feature, dict)
        if feature.get("$type") == "app.bsky.richtext.facet#link"
    }
    links_confirmed = linked_urls.issubset(set(page_links)) or all(
        url in page_text for url in linked_urls
    )
    if not linked_urls or not links_confirmed:
        return False
    url_pattern = re.compile(r"https?://\S+|(?:[\w-]+\.)+[a-z]{2,}/\S*", re.I)
    comparable_body = re.sub(r"\s+", " ", url_pattern.sub("", body)).strip()
    comparable_page = re.sub(r"\s+", " ", url_pattern.sub("", page_text)).strip()
    return comparable_body == comparable_page


def _reviewed_truman_library_metadata(source_url: str, body: str):
    reviewed = TRUMAN_LIBRARY_REVIEWED_HASHED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return TRUMAN_LIBRARY_REVIEWED_METADATA.get(source_url, ("", ""))


def _reviewed_trump_whitehouse_metadata(source_url: str, body: str):
    reviewed = TRUMP_WHITEHOUSE_REVIEWED_HASHED_METADATA.get(source_url)
    if reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]:
        return reviewed[1], reviewed[2]
    return "", ""


def _csis_pdf_body(page_texts: list[str], pages) -> str:
    if not page_texts:
        return ""

    # CSIS's first-page content stream places the two-column article before its cover.
    # Use embedded text coordinates only for the cover/title block and retain the
    # publisher's original left-then-right extraction order for the article columns.
    first_page = pages[0]
    positioned = []
    first_page.extract_text(visitor_text=lambda text, cm, tm, font, size: positioned.append(
        (tm[5], tm[4], text)
    ) if text.strip() and 380 < tm[5] < 700 and 25 <= tm[4] <= 580 else None)
    positioned.sort(key=lambda item: (-round(item[0] * 2) / 2, item[1]))
    lines = []
    line_y = None
    fragments = []
    for y, _, text in positioned:
        current_y = round(y * 2) / 2
        if line_y is not None and current_y != line_y:
            lines.append(" ".join(fragment.strip() for fragment in fragments if fragment.strip()))
            fragments = []
        line_y = current_y
        fragments.append(text)
    if fragments:
        lines.append(" ".join(fragment.strip() for fragment in fragments if fragment.strip()))

    first_stream_body = page_texts[0].split("THE ISSUE", 1)[0].strip()
    if not lines or not first_stream_body.startswith("PART I:"):
        cleaned_pages = [
            re.sub(r"(?m)^\s*CSIS BRIEFS\s*\|\s*WWW\.CSIS\.ORG\s*\|\s*\d+\s*$\n?", "", text).strip()
            for text in page_texts
        ]
        return "\n\n".join(text for text in cleaned_pages if text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in lines if line.strip()]
    header = "\n".join(lines)
    first_page_body = f"{header}\n\n{first_stream_body}"
    remaining = []
    for text in page_texts[1:]:
        cleaned = re.sub(
            r"(?m)^\s*CSIS BRIEFS\s*\|\s*WWW\.CSIS\.ORG\s*\|\s*\d+\s*$\n?", "", text
        )
        remaining.append(cleaned.strip())
    return "\n\n".join([first_page_body, *remaining])


class CiaoConferenceAdapter:
    source_url = "https://ciaotest.cc.columbia.edu/conf/aac02/aac02f.html"

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW or response.url != self.source_url:
            return {"decision": decision, "evidence": evidence, "material": None}

        resources = response.css("div.resources")
        if len(resources) != 1:
            return {"decision": decision, "evidence": evidence, "material": None}
        blocks = resources.xpath("./*")
        title = _normalized_text(blocks[0].xpath(".//text()").getall()) if blocks else ""
        header = blocks[1] if len(blocks) > 1 else None
        author = " and ".join(
            _normalized_text([name]) for name in header.xpath("./p[1]//a/text()").getall()
        ) if header is not None else ""
        source = _normalized_text(
            header.xpath("./p[2]//a/text()").getall()
        ) if header is not None else ""

        body_parts = []
        started = False
        for block in blocks[2:]:
            text = _normalized_text(block.xpath(".//text()").getall())
            if not started:
                if text == "Preface":
                    started = True
                    body_parts.append(text)
                continue
            if block.root.tag.casefold() == "ul":
                list_items = [
                    _normalized_text(item.xpath(".//text()").getall())
                    for item in block.xpath("./li")
                ]
                body_parts.extend(item for item in list_items if item)
            elif text:
                body_parts.append(text)
        body = "\n\n".join(body_parts)

        text_before_body = "\n".join(
            _normalized_text(block.xpath(".//text()").getall()) for block in blocks[:12]
        )
        year_match = re.search(r"On March 19, (\d{4}),", text_before_body)
        report_produced = re.search(
            r"On March 22, following their discussions, the participants produced this report",
            text_before_body,
            flags=re.IGNORECASE,
        )
        published_on = f"{year_match.group(1)}-03-22" if year_match and report_produced else ""
        complete = bool(
            title == "The China Factor"
            and author == "Winston Lord and William H. Sullivan"
            and source == "American Assembly at Columbia University"
            and published_on == "1981-03-22"
            and body.startswith("Preface\n\n")
            and "Final Report of the Fifty-Ninth American Assembly" in body
            and "Participants of the Fifty-Ninth American Assembly" in body
            and "J. OWEN ZURHELLEN, JR." in body
            and body.rstrip().endswith("Legend * Discussion Leader ** Rapporteur")
        )
        evidence = replace(
            evidence,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
            original_page_verified=complete,
        )
        material = None
        result = {"decision": decision, "evidence": evidence, "material": material}
        if complete:
            material = VerifiedMaterial(
                source=source,
                time=published_on,
                author=author,
                title=title,
                abstract=(
                    "据正文整理：大会报告讨论美国与中华人民共和国关系正常化后的政策选择、"
                    "安全合作、台湾、经济关系及美国公众讨论中的双边关系。"
                ),
                keywords=(
                    "U.S.-China relations; normalization; China policy; public discussion; "
                    "security cooperation; Taiwan"
                ),
                body=body,
                source_url=response.url,
            )
            result["material"] = material
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title", "abstract", "keywords")
            }
            result["abstract_origin"] = "derived"
            result["keywords_origin"] = "derived"
        return result


class ReviewedPublicMediaAdapter:
    """Promote only exact public-media pages with reviewed metadata and body hashes."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        fetched_at = datetime.now(timezone.utc).isoformat()
        digest = sha256(response.body).hexdigest()
        evidence = SourceEvidence(response.url, fetched_at, response.status, digest)
        reviewed = PUBLIC_MEDIA_REVIEWED_ARTICLES.get(response.url)
        if decision is not AccessDecision.ALLOW or reviewed is None:
            return {"decision": decision, "evidence": evidence, "material": None}

        (
            period, source, author, published_on, title, page_kind, expected_length,
            expected_hash, publisher_abstract, keywords, *body_shape,
        ) = reviewed
        expected_body_paragraphs = int(body_shape[0]) if body_shape else None
        expected_total_paragraphs = int(body_shape[1]) if len(body_shape) > 1 else None
        if candidate.period != period or candidate.source_category != "media":
            return {"decision": decision, "evidence": evidence, "material": None}

        meta_title = response.css('meta[property="og:title"]::attr(content)').getall()
        published_meta = response.css(
            'meta[property="article:published_time"]::attr(content)'
        ).getall()
        h1 = [_normalized_text(node.xpath(".//text()").getall()) for node in response.css("h1")]
        document_title = _normalized_text(response.xpath("string(//title)").getall())

        if page_kind in {"time", "time_clean", "time_ads", "time_updated"}:
            containers = response.css("article")
            source_matches = (
                response.css('meta[property="og:site_name"]::attr(content)').getall()
                == ["TIME"]
            )
            author_matches = response.css(
                'meta[name="author"]::attr(content)'
            ).getall() == [author]
            date_values = response.css("time::attr(datetime)").getall()
            schema_matches = (
                len(date_values) >= 2 and (
                    all(value.startswith(published_on) for value in date_values)
                    if page_kind != "time_updated"
                    else any(value.startswith(published_on) for value in date_values)
                )
            )
            visible_title_matches = h1 == [title]
        elif page_kind == "abc_archive":
            containers = response.css(".article-body")
            program = response.css(
                'meta[property="og:site_name"]::attr(content)'
            ).get()
            source_matches = response.css(
                'meta[property="og:site_name"]::attr(content)'
            ).getall() == [program] and program in {"The World Today", "PM", "Lateline"}
            intro = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in response.css("article > p")
            ]
            author_matches = sum(
                (
                    line.startswith("Broadcast ")
                    and line.endswith(f"Reporter: {author}")
                )
                or line.startswith(f"{author} reported this story on ")
                for line in intro
            ) == 1
            schema_matches = len(intro) == 3
            publisher_name = "ABC News" if program == "Lateline" else "ABC listen"
            visible_title_matches = (
                document_title == f"{title} - {program} Archive - {publisher_name}"
            )
        elif page_kind == "abc_news_nested":
            containers = response.css(
                '#content > article > div > div > div[class*="Article_main"]'
            )
            source_matches = document_title == f"{title} - ABC News"
            paragraphs_in_article = containers[0].css("p") if len(containers) == 1 else []
            paragraph_texts = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in paragraphs_in_article
            ]
            expected_footer = "See more ABC coverage in your search results"
            visible_bylines = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in response.css('[class*="Byline_byline"]')
            ]
            if page_kind == "abc_news_nested":
                author_matches = (
                    len(paragraph_texts) == expected_total_paragraphs
                    and paragraph_texts[-1] == expected_footer
                    and all(value == f"By {author}" for value in visible_bylines)
                    and (
                        paragraph_texts[expected_body_paragraphs] == author
                        or (
                            paragraph_texts[expected_body_paragraphs].startswith(f"{author} is ")
                            and bool(visible_bylines)
                        )
                    )
                )
            article_times = response.css("time::attr(datetime)").getall()
            visible_time_texts = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in response.css("time")[:3]
            ]
            parsed_date = datetime.strptime(published_on, "%Y-%m-%d")
            visible_date = f"{parsed_date.day} {parsed_date:%b %Y}"
            schema_matches = (
                len(article_times) >= 3
                and len(set(article_times[:3])) == 1
                and all(visible_date in value for value in visible_time_texts)
            )
            visible_title_matches = h1 == [title]
        elif page_kind == "guardian":
            containers = response.css(".article-body-commercial-selector")
            source_matches = (
                response.css('meta[property="og:site_name"]::attr(content)').getall()
                == ["the Guardian"]
            )
            author_matches = response.css(
                'meta[property="article:author"]::attr(content)'
            ).getall() == [author]
            schema_matches = True
            visible_title_matches = h1 == [title]
        elif page_kind == "guardian_byline":
            containers = response.css(".article-body-commercial-selector")
            source_matches = (
                response.css('meta[property="og:site_name"]::attr(content)').getall()
                == ["the Guardian"]
            )
            author_meta = response.css(
                'meta[property="article:author"]::attr(content)'
            ).getall()
            visible_authors = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in response.css('a[rel="author"]')
            ]
            author_matches = (
                author_meta == [author]
                or bool(visible_authors and all(name == author for name in visible_authors))
            )
            schema_matches = True
            visible_title_matches = h1 == [title]
        elif page_kind == "abc_worldtoday":
            containers = response.css(".article-body")
            source_matches = response.css(
                'meta[property="og:site_name"]::attr(content)'
            ).getall() == ["The World Today"]
            attribution = " ".join(response.xpath("//body//text()").getall())
            author_matches = bool(
                re.search(
                    rf"{re.escape(author)} reported this story on Wednesday, June 4, 2014",
                    _normalized_text([attribution]),
                )
            )
            schema_matches = True
            visible_title_matches = (
                document_title == f"{title} - The World Today Archive - ABC listen"
            )
        else:
            containers = response.css("#transcript")
            source_matches = True
            bylines = response.xpath(
                '//*[contains(translate(@class, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "byline")]'
            )
            author_matches = bylines and [
                _normalized_text(node.xpath(".//text()").getall())
                for node in bylines
            ] == [author, author]
            posted = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in response.css("time")
                if _normalized_text(node.xpath(".//text()").getall())
                == "Tue 4 Jun 2019 at 6:31am"
            ]
            schema_matches = len(posted) == 3
            visible_title_matches = h1 == ["VIDEO: " + title]

        paragraphs = containers[0].css("p") if len(containers) == 1 else []
        paragraph_count_matches = (
            expected_total_paragraphs is None
            or len(paragraphs) == expected_total_paragraphs
        )
        if page_kind in {"time_clean", "time_ads"}:
            paragraphs = [
                node for node in paragraphs
                if _normalized_text(node.xpath(".//text()").getall())
                and not (
                    page_kind == "time_ads"
                    and _normalized_text(node.xpath(".//text()").getall()) == "Advertisement"
                )
            ]
        body_paragraphs = (
            paragraphs[:expected_body_paragraphs]
            if expected_body_paragraphs is not None
            else paragraphs
        )
        body = "\n\n".join(
            text for node in body_paragraphs
            if (text := _normalized_text(node.xpath(".//text()").getall()))
        )
        body_hash = sha256(body.encode("utf-8")).hexdigest()
        if page_kind in {"time", "time_clean", "time_ads", "time_updated"}:
            publication_matches = schema_matches
            if page_kind == "time_updated":
                published_dates = response.xpath(
                    '//span[starts-with(normalize-space(.), "Published:")]//time/@datetime'
                ).getall()
                publication_matches = bool(
                    len(published_dates) == 2
                    and all(value.startswith(published_on) for value in published_dates)
                    and schema_matches
                )
        elif page_kind == "abc_news_nested":
            publication_matches = bool(
                len(published_meta) == 1
                and len(article_times) >= 3
                and len(set(article_times[:3])) == 1
                and published_meta[0].startswith(article_times[0][:10])
            )
        else:
            publication_matches = bool(
                len(published_meta) == 1
                and published_meta[0].startswith(published_on)
            ) if page_kind != "abc_fourcorners" else True
        abstract = publisher_abstract or PUBLIC_MEDIA_REVIEWED_DERIVED_ABSTRACTS.get(
            response.url, ""
        )
        expected_meta_title = PUBLIC_MEDIA_REVIEWED_META_TITLES.get(response.url, title)
        complete = bool(
            len(meta_title) == 1
            and meta_title[0] == expected_meta_title
            and visible_title_matches
            and document_title
            and source_matches
            and author_matches
            and schema_matches
            and publication_matches
            and len(containers) == 1
            and paragraph_count_matches
            and len(body_paragraphs) == (expected_body_paragraphs or len(paragraphs))
            and paragraphs
            and body
            and len(body) == int(expected_length)
            and body_hash == expected_hash
        )
        if not complete:
            return {"decision": decision, "evidence": evidence, "material": None}

        material = VerifiedMaterial(
            source=source,
            time=published_on,
            author=author,
            title=title,
            abstract=abstract,
            keywords=keywords,
            body=body,
            source_url=response.url,
        )
        evidence = SourceEvidence(
            response.url,
            fetched_at,
            response.status,
            digest,
            body_complete=True,
            metadata_verified=True,
            body_format="source_text",
            original_page_verified=True,
        )
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": {name: response.url for name in (
                "source", "time", "author", "title", "abstract", "keywords"
            )},
            "abstract_origin": "publisher" if publisher_abstract else "derived",
            "keywords_origin": "derived",
        }


class GovernmentArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        content_type = response.headers.get(b"Content-Type", b"").decode("latin-1").casefold()
        if "application/pdf" in content_type or response.url.casefold().endswith(".pdf"):
            if (urlsplit(response.url).hostname or "").lower() == "www.gao.gov":
                return GAOPDFDocumentAdapter().extract(response, candidate)
            if response.url in FRIENDS_JOURNAL_REVIEWED_ARTICLES:
                return ReviewedIssueArticlePDFAdapter(
                    FRIENDS_JOURNAL_REVIEWED_ARTICLES
                ).extract(response, candidate)
            if response.url in DAILY_IOWAN_REVIEWED_ARTICLES:
                return ReviewedIssueArticlePDFAdapter(
                    DAILY_IOWAN_REVIEWED_ARTICLES
                ).extract(response, candidate)
            metadata_response = response.meta.get("metadata_response")
            source_parts = urlsplit(response.url)
            if (
                (source_parts.hostname or "").lower() == "ccsenet.org"
                and "/journal/index.php/ells/article/download/" in source_parts.path
            ):
                return CcseJournalPDFDocumentAdapter().extract(response, candidate)
            if candidate.metadata_url and metadata_response is not None:
                metadata_host = (urlsplit(candidate.metadata_url).hostname or "").lower()
                if metadata_host == "www.jstage.jst.go.jp" or metadata_host.endswith(".jstage.jst.go.jp"):
                    return JStagePDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                if metadata_host == "danratherjournalist.org":
                    return ReviewedScannedTranscriptPDFAdapter(
                        DAN_RATHER_REVIEWED_SCANNED_TRANSCRIPTS
                    ).extract(response, candidate, metadata_response)
                if metadata_host == "ijoc.org":
                    return IJocPDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                if (urlsplit(candidate.metadata_url).hostname or "").lower() == "2021-2025.state.gov":
                    return StateDepartmentReportPDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                if (urlsplit(candidate.metadata_url).hostname or "").lower().endswith("csis.org"):
                    return CSISPDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                if (urlsplit(candidate.metadata_url).hostname or "").lower().endswith("shorensteincenter.org"):
                    return ShorensteinPDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                if "open journal systems" in " ".join(
                    metadata_response.css("meta[name='generator']::attr(content)").getall()
                ).casefold():
                    return OjsJournalPDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                if metadata_response.css("meta[name='bepress_citation_title']"):
                    return BepressRepositoryPDFDocumentAdapter().extract(
                        response, candidate, metadata_response
                    )
                return BrookingsPDFDocumentAdapter().extract(
                    response, candidate, metadata_response
                )
            return PDFDocumentAdapter().extract(response, candidate)
        hostname = (urlsplit(response.url).hostname or "").lower()
        if response.url in PUBLIC_MEDIA_REVIEWED_ARTICLES:
            return ReviewedPublicMediaAdapter().extract(response, candidate)
        if hostname == "api.parliament.uk" and response.url.startswith(
            "https://api.parliament.uk/historic-hansard/"
        ):
            return HistoricHansardAdapter().extract(response, candidate)
        if hostname == "ciaotest.cc.columbia.edu":
            return CiaoConferenceAdapter().extract(response, candidate)
        if hostname == "bsky.app":
            return BlueskyPostAdapter().extract(response, candidate, response.meta.get("metadata_response"))
        if hostname == "nature.com" or hostname.endswith(".nature.com"):
            return NatureResearchArticleAdapter().extract(response, candidate)
        if hostname == "www.govinfo.gov" and candidate.metadata_url:
            return GovInfoHearingAdapter().extract(
                response, candidate, response.meta.get("metadata_response")
            )
        if hostname == "trumpwhitehouse.archives.gov":
            return TrumpWhiteHouseStatementAdapter().extract(response, candidate)
        if hostname == "obamawhitehouse.archives.gov":
            if response.css("#video-info") and response.css("#transcript"):
                return ObamaWhiteHouseVideoTranscriptAdapter().extract(response, candidate)
            return ObamaWhiteHouseArchiveAdapter().extract(response, candidate)
        if hostname == "whitehouse.gov" or hostname.endswith(".whitehouse.gov"):
            return WhiteHouseFactSheetAdapter().extract(response, candidate)
        if hostname == "www.prcleader.org" and response.url in PRCLEADER_REVIEWED_ARTICLES:
            return PRCLeadershipMonitorArticleAdapter().extract(response, candidate)
        if hostname == "carnegieendowment.org" and response.url in CARNEGIE_REVIEWED_ARTICLES:
            return CarnegieResearchArticleAdapter().extract(response, candidate)
        if hostname == "brookings.edu" or hostname.endswith(".brookings.edu"):
            return BrookingsArticleAdapter().extract(response, candidate)
        if hostname == "pewresearch.org" or hostname.endswith(".pewresearch.org"):
            return PewResearchArticleAdapter().extract(response, candidate)
        if hostname == "csis.org" or hostname.endswith(".csis.org"):
            return CSISArticleAdapter().extract(response, candidate)
        if hostname == "foreignaffairs.house.gov" or hostname.endswith(".foreignaffairs.house.gov"):
            return HouseForeignAffairsHearingAdapter().extract(response, candidate)
        if hostname in {"nsarchive.gwu.edu", "nsarchive2.gwu.edu"} or hostname.endswith(".nsarchive.gwu.edu"):
            return NationalSecurityArchiveAdapter().extract(response, candidate)
        if hostname == "apnews.com" or hostname.endswith(".apnews.com"):
            return APNewsArticleAdapter().extract(response, candidate)
        if hostname == "rfa.org" or hostname.endswith(".rfa.org"):
            return RFAArticleAdapter().extract(response, candidate)
        if (
            hostname in {"pbs.org", "www.pbs.org"}
            and response.url in PBS_REVIEWED_PROGRAM_TRANSCRIPTS
        ):
            return PBSProgramTranscriptAdapter().extract(response, candidate)
        if (
            hostname in {"pbs.org", "www.pbs.org"}
            and response.url in PBS_REVIEWED_VIDEO_TRANSCRIPTS
        ):
            return PBSVideoTranscriptAdapter().extract(response, candidate)
        if hostname in {"pbs.org", "www.pbs.org"} and urlsplit(response.url).path.startswith("/newshour/"):
            return PBSNewsArticleAdapter().extract(response, candidate)
        if (
            hostname == "www.pbs.org"
            and urlsplit(response.url).path == "/wgbh/pages/frontline/tankman/etc/transcript.html"
        ):
            return FrontlineTankManTranscriptAdapter().extract(response, candidate)
        if (
            hostname == "voanews.com"
            or hostname.endswith(".voanews.com")
            or hostname == "insidevoa.com"
            or hostname.endswith(".insidevoa.com")
            or hostname == "editorials.voa.gov"
        ):
            return VOANewsArticleAdapter().extract(response, candidate)
        if hostname == "trumanlibrary.gov" or hostname.endswith(".trumanlibrary.gov"):
            return TrumanLibraryPublicPaperAdapter().extract(response, candidate)
        if hostname == "bush41library.gov" or hostname.endswith(".bush41library.gov"):
            return BushLibraryPublicPaperAdapter().extract(response, candidate)
        if hostname == "presidency.ucsb.edu" or hostname.endswith(".presidency.ucsb.edu"):
            return PresidencyProjectDocumentAdapter().extract(response, candidate)
        if hostname == "clintonwhitehouse4.archives.gov":
            return ClintonWhiteHouseArchiveAdapter().extract(response, candidate)
        if hostname == "clintonwhitehouse6.archives.gov":
            return ClintonWhiteHouse6ArchiveAdapter().extract(response, candidate)
        if hostname == "pmc.ncbi.nlm.nih.gov" or hostname.endswith(".pmc.ncbi.nlm.nih.gov"):
            return PMCFulTextArticleAdapter().extract(response, candidate)
        if hostname == "history.state.gov" or hostname.endswith(".history.state.gov"):
            return FRUSDocumentAdapter().extract(response, candidate)
        if hostname == "worldjpn.net" and response.url == WorldJPNAchesonSpeechAdapter.source_url:
            return WorldJPNAchesonSpeechAdapter().extract(
                response, candidate, response.meta.get("metadata_response")
            )
        if hostname == "2009-2017.state.gov":
            return ArchivedStateDepartmentRemarksAdapter().extract(response, candidate)
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
            name: response.url for name in ("source", "time", "author", "title")
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


class HouseForeignAffairsHearingAdapter:
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

        articles = response.css("article.node.evo-hearing.evo-hearing--full")
        title_nodes = response.css("h1")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        document_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        publication_stamp = response.css(
            "meta[property='article:published_time']::attr(content)"
        ).get(default="").strip()
        publication_date = _publication_date("", publication_stamp)
        body_nodes = articles.css(".evo-hearing__body")
        witness_nodes = articles.css(".evo-hearing__field-evo-witnesses")
        title_matches = document_title == f"{title} | {source}"
        metadata_verified = bool(
            title
            and source
            and publication_date
            and title_matches
            and len(articles) == 1
            and len(body_nodes) == 1
            and len(witness_nodes) == 1
        )
        # This layout is the hearing announcement and witness/download directory.
        # Neither its introductory quotation nor the witness list is the transcript.
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=False,
            metadata_verified=metadata_verified,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": None}
        if metadata_verified:
            result["source_metadata"] = {
                "source": source, "time": publication_date, "author": "未注明", "title": title,
            }
        return result


class GAOPDFDocumentAdapter:
    """Extract a public GAO report only when its cover identifies the report."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        digest = sha256(response.body).hexdigest()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status_code=response.status,
            content_sha256=digest,
            body_format="pdf_text",
        )
        decision = classify_response(response.url, response.status)
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}
        if (urlsplit(response.url).hostname or "").lower() != "www.gao.gov":
            return {"decision": decision, "evidence": evidence, "material": None}

        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            pages = list(reader.pages)
            page_texts = [page.extract_text() or "" for page in pages]
        except Exception:
            return {"decision": decision, "evidence": evidence, "material": None}

        first_page = page_texts[0] if page_texts else ""
        report_number = re.search(r"(?im)^\s*GAO\s*/\s*ID\s*-\s*82\s*-\s*37\s*$", first_page)
        title = "The Voice of America Should Address Existing Problems To Ensure High Performance"
        title_present = bool(re.search(
            r"(?is)The Voice Of America Should Address Existing Problems\s+To Ensure High Performance",
            first_page,
        ))
        date_match = re.search(
            r"(?im)^\s*JULY\s+29,\s+1982\s*$", first_page
        )
        body = "\n\n".join(text.strip() for text in page_texts if text.strip())
        complete = bool(
            pages
            and all(text.strip() for text in page_texts)
            and _pdf_has_page_images(pages) is False
            and re.search(r"(?i)UNITED STATES GENERAL ACCOUNTING OFFICE", first_page)
            and report_number
            and title_present
            and date_match
            and body
        )
        if not complete:
            return {"decision": decision, "evidence": evidence, "material": None}

        material = VerifiedMaterial(
            source="United States General Accounting Office",
            time="1982-07-29",
            author="未注明",
            title=title,
            abstract="",
            keywords="",
            body=body,
            source_url=response.url,
        )
        evidence = replace(evidence, body_complete=True, metadata_verified=True)
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": {name: response.url for name in ("source", "time", "author", "title")},
            "abstract_origin": "none",
        }


class PDFDocumentAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_format="pdf_text",
        )
        decision = classify_response(response.url, response.status)
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            return {"decision": decision, "evidence": evidence, "material": None}

        metadata = reader.metadata
        first_page = page_texts[0] if page_texts else ""
        title = _pdf_metadata_text(getattr(metadata, "title", None))
        if title.casefold() in {"untitled", "unknown", "none"}:
            title = ""
        author = _pdf_metadata_text(getattr(metadata, "author", None)) or "未注明"
        if author.casefold() in {"anonymous", "unknown", "none"}:
            author = "未注明"
        lines = [line.strip() for line in first_page.splitlines() if line.strip()]
        source_index = next(
            (
                index
                for index, line in enumerate(lines)
                if re.fullmatch(
                    r"(?i)office\s+of\s+the\s+united\s+states\s+trade\s+representative",
                    line,
                )
            ),
            None,
        )
        source = (
            "Office of the United States Trade Representative"
            if source_index is not None
            else ""
        )
        date_match = re.search(
            r"(?im)^\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\.?\s*$",
            first_page,
        )
        try:
            publication_date = datetime.strptime(
                date_match.group(0).strip().rstrip("."), "%B %d, %Y"
            ).date().isoformat()
        except (AttributeError, ValueError):
            publication_date = ""
        if not title and date_match and source_index is not None:
            date_line = next(
                (index for index, line in enumerate(lines) if date_match.group(0).strip() in line),
                None,
            )
            title_lines = lines[source_index + 1 : date_line] if date_line is not None else []
            title_lines = [
                line
                for line in title_lines
                if not re.fullmatch(r"(?i)executive office of the president", line)
            ]
            title = _normalized_text(title_lines)

        body = "\n\n".join(text.strip() for text in page_texts if text.strip())
        complete = bool(
            title
            and source
            and publication_date
            and page_texts
            and all(text.strip() for text in page_texts)
            and body
        )
        if not complete:
            return {"decision": decision, "evidence": evidence, "material": None}

        material = VerifiedMaterial(
            source=source,
            time=publication_date,
            author=author,
            title=title,
            abstract="",
            keywords="",
            body=body,
            source_url=response.url,
        )
        abstract, keywords = _reviewed_ustr_metadata(response.url, body)
        material = replace(material, abstract=abstract, keywords=keywords)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=True,
            metadata_verified=True,
            body_format="pdf_text",
        )
        field_sources = {
            name: response.url for name in ("source", "time", "author", "title")
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
            "abstract_origin": "derived" if abstract else "none",
        }


class ShorensteinPDFDocumentAdapter:
    """Verify a Shorenstein Center landing page paired with its exact PDF."""

    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        digest = sha256(response.body).hexdigest()
        decision = classify_response(response.url, response.status)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status_code=response.status,
            content_sha256=digest,
            body_format="pdf_text",
        )
        spec = SHORENSTEIN_REVIEWED_PDFS.get(response.url)
        if spec is None or candidate.metadata_url != spec["metadata_url"]:
            return {"decision": decision, "evidence": evidence, "material": None}
        if decision is not AccessDecision.ALLOW or metadata_response.status < 200 or metadata_response.status >= 300:
            return {"decision": decision, "evidence": evidence, "material": None}

        page_title = _normalized_text(metadata_response.css("h1.header2-title::text").getall())
        page_date = metadata_response.css("time[datetime]::attr(datetime)").get() or ""
        page_abstract = metadata_response.xpath(
            "string((//div[contains(@class, 'body1')]//div[contains(@class, 'wizzy')]/p)[1])"
        ).get() or ""
        page_abstract = _normalized_text([page_abstract])
        linked_pdf = {
            urljoin(metadata_response.url, href)
            for href in metadata_response.css("a[href]::attr(href)").getall()
            if href.lower().split("?", 1)[0].endswith(".pdf")
        }
        metadata_verified = bool(
            metadata_response.url == spec["metadata_url"]
            and page_title == spec["title"]
            and page_date == spec["published_on"]
            and page_abstract == spec["abstract"]
            and response.url in linked_pdf
        )

        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            pages = list(reader.pages)
            page_texts = [page.extract_text() or "" for page in pages]
        except Exception:
            pages = []
            page_texts = []
        scan_like = _pdf_has_page_images(pages)
        reviewed_body = str(spec.get("reviewed_body", ""))
        body = (
            reviewed_body
            if scan_like and reviewed_body
            else "\n\n".join(text.strip() for text in page_texts if text.strip())
        )
        body_verified = bool(
            digest == spec["pdf_sha256"]
            and pages
            and (reviewed_body if scan_like else page_texts)
            and (scan_like or all(text.strip() for text in page_texts))
            and sha256(body.encode("utf-8")).hexdigest() == spec["body_sha256"]
        )
        verified = metadata_verified and body_verified
        evidence = replace(
            evidence,
            body_complete=body_verified,
            metadata_verified=metadata_verified,
            body_format="pdf_reviewed_transcript" if scan_like and reviewed_body else (
                "pdf_ocr_text" if scan_like else "pdf_text"
            ),
            original_page_verified=verified,
        )
        result = {"decision": decision, "evidence": evidence, "material": None}
        if verified:
            result["material"] = VerifiedMaterial(
                source=spec["publisher"],
                time=spec["published_on"],
                author=spec["author"],
                title=spec["title"],
                abstract=spec["abstract"],
                keywords=spec["keywords"],
                body=body,
                source_url=response.url,
            )
            result["field_sources"] = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title", "abstract", "keywords")
            }
            result["field_sources"]["body"] = response.url
            result["abstract_origin"] = "publisher"
            result["supporting_evidence"] = [{
                "decision": AccessDecision.ALLOW,
                "evidence": SourceEvidence(
                    source_url=metadata_response.url,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    status_code=metadata_response.status,
                    content_sha256=sha256(metadata_response.body).hexdigest(),
                    metadata_verified=True,
                    original_page_verified=True,
                    body_format="source_text",
                ),
                "raw_response": metadata_response.body,
            }]
        return result


class ReviewedIssueArticlePDFAdapter:
    """Extract one reviewed article from a public issue-level PDF."""

    def __init__(self, reviewed_sources: dict[str, dict[str, object]]):
        self.reviewed_sources = reviewed_sources

    @staticmethod
    def _page_text(page, column: dict[str, object] | None = None) -> str:
        if column:
            fragments: list[tuple[float, float, str]] = []

            def visitor(text, _cm, tm, _font_dict, _font_size):
                value = text.replace("\u00ad", "")
                if not value.strip():
                    return
                x = float(tm[4])
                y = float(tm[5])
                if (
                    float(column["x_min"]) <= x <= float(column["x_max"])
                    and float(column["y_min"]) <= y <= float(column["y_max"])
                ):
                    fragments.append((round(y, 2), x, value))

            page.extract_text(visitor_text=visitor)
            lines: list[str] = []
            for y in sorted({fragment[0] for fragment in fragments}, reverse=True):
                line = "".join(
                    fragment[2].replace("\n", "")
                    for fragment in sorted(
                        (item for item in fragments if item[0] == y),
                        key=lambda item: item[1],
                    )
                ).strip()
                if line:
                    lines.append(line)
            return "\n".join(lines)
        text = page.extract_text() or ""
        text = text.replace("\u00ad", "")
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        digest = sha256(response.body).hexdigest()
        decision = classify_response(response.url, response.status)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status_code=response.status,
            content_sha256=digest,
            body_format="pdf_text",
        )
        spec = self.reviewed_sources.get(response.url)
        if spec is not None and "variants" in spec:
            variants = spec.get("variants")
            spec = (
                variants.get(candidate.platform_id)
                if isinstance(variants, dict) and candidate.platform_id
                else None
            )
        if (
            spec is None
            or decision is not AccessDecision.ALLOW
            or response.url != candidate.source_url
            or not response.body.startswith(b"%PDF-")
            or digest != spec.get("pdf_sha256")
        ):
            return {"decision": decision, "evidence": evidence, "material": None}
        try:
            pages = PdfReader(BytesIO(response.body), strict=True).pages
            page_numbers = [int(value) for value in spec["pages"]]
            if not page_numbers or min(page_numbers) < 1 or max(page_numbers) > len(pages):
                raise ValueError("reviewed page range is outside the PDF")
            scan_like = _pdf_has_page_images(pages)
            reviewed_body = str(spec.get("reviewed_body") or "")
            if scan_like and not reviewed_body:
                evidence = replace(evidence, body_format="pdf_ocr_text")
                return {"decision": decision, "evidence": evidence, "material": None}
            page_text = "\n".join(
                self._page_text(pages[number - 1], spec.get("column"))
                for number in page_numbers
            )
        except Exception:
            return {"decision": decision, "evidence": evidence, "material": None}
        start = str(spec["body_start"])
        end = str(spec["body_end"])
        boundary_start = str(spec.get("boundary_start") or start)
        boundary_end = str(spec.get("boundary_end") or end)
        start_index = page_text.find(boundary_start)
        end_index = (
            page_text.find(boundary_end, start_index + len(boundary_start))
            if start_index >= 0
            else -1
        )
        extracted_body = (
            page_text[start_index:end_index].strip()
            if start_index >= 0 and end_index >= 0
            else ""
        )
        body = str(spec.get("reviewed_body") or extracted_body)
        if spec.get("reviewed_body") and (
            not body.startswith(start) or body.find(end) >= 0
        ):
            body = ""
        verified = bool(body) and sha256(body.encode("utf-8")).hexdigest() == spec.get("body_sha256")
        evidence = replace(
            evidence,
            body_complete=verified,
            metadata_verified=verified,
            body_format="pdf_reviewed_transcript" if scan_like and spec.get("reviewed_body") else (
                "pdf_ocr_text" if scan_like else "pdf_text"
            ),
            original_page_verified=verified,
        )
        if not verified:
            return {"decision": decision, "evidence": evidence, "material": None}
        material = VerifiedMaterial(
            source=str(spec["publisher"]),
            time=str(spec["published_on"]),
            author=str(spec["author"]),
            title=str(spec["title"]),
            abstract=str(spec.get("abstract") or f"据正文整理：{body[:180]}"),
            keywords=str(spec.get("keywords") or "China; United States; public opinion; media discourse"),
            body=body,
            source_url=response.url,
        )
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": {name: response.url for name in ("source", "time", "author", "title", "abstract", "keywords")},
            "abstract_origin": (
                "derived"
                if material.abstract.startswith("据正文整理：")
                else "publisher" if spec.get("abstract") else "derived"
            ),
        }


class GovInfoHearingAdapter:
    package_pattern = re.compile(r"/content/pkg/(CHRG-[^/]+)/html/", re.IGNORECASE)

    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response | None,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_decision = classify_response(response.url, response.status, response.text)
        body_digest = sha256(response.body).hexdigest()
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=body_digest,
        )
        if metadata_response is None:
            return {"decision": body_decision, "evidence": body_evidence, "material": None}

        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        package_match = self.package_pattern.search(response.url)
        metadata_parts = urlsplit(metadata_response.url)
        metadata_package = re.search(
            r"/app/details/(CHRG-[^/]+)/", metadata_parts.path, re.IGNORECASE
        )
        detail_url = metadata_response.css(
            "meta[name='dc.identifier']::attr(content)"
        ).get(default="").strip()
        metadata_title = metadata_response.css(
            "meta[name='dc.title']::attr(content)"
        ).get(default="").strip()
        creator_values = [
            _normalized_text([value])
            for value in metadata_response.css("meta[name='dc.creator']::attr(content)").getall()
            if _normalized_text([value])
        ]
        publisher = metadata_response.css(
            "meta[name='dc.publisher']::attr(content)"
        ).get(default="").strip()
        date_value = metadata_response.css(
            "meta[name='dc.date']::attr(content)"
        ).getall()
        publication_date = _publication_date("", date_value[0]) if len(date_value) == 1 else ""

        pre_nodes = response.css("body > pre")
        raw_document = pre_nodes[0].xpath("string(.)").get(default="") if len(pre_nodes) == 1 else ""
        document_lines = raw_document.strip().splitlines()
        publisher_marker = "[From the U.S. Government Publishing Office]"
        marker_index = next(
            (index for index, line in enumerate(document_lines) if line.strip() == publisher_marker),
            None,
        )
        separator_index = next(
            (
                index
                for index, line in enumerate(document_lines)
                if re.fullmatch(r"\s*={5,}\s*", line)
            ),
            None,
        )
        title = (
            _normalized_text(
                line
                for line in document_lines[marker_index + 1 : separator_index]
                if not re.fullmatch(r"\s*_+\s*", line)
            )
            if marker_index is not None and separator_index is not None
            else ""
        )
        published_title = re.sub(
            r"^Serial No\.\s*.*?\s-\s*", "", metadata_title, flags=re.IGNORECASE
        ).strip()
        published_title = re.sub(r"\s*\(House Hearing\)\s*$", "", published_title, flags=re.IGNORECASE)
        detail_url_matches = unquote(detail_url) == metadata_response.url
        metadata_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and metadata_response.url == candidate.metadata_url
            and metadata_parts.hostname == "www.govinfo.gov"
            and package_match
            and metadata_package
            and package_match.group(1).casefold() == metadata_package.group(1).casefold()
            and detail_url_matches
            and publisher in {
                "U.S. Government Publishing Office",
                "U.S. Government Printing Office",
            }
            and metadata_title
            and title
            and _metadata_match_key(title) == _metadata_match_key(published_title)
            and publication_date
            and len(date_value) == 1
            and response.url == candidate.source_url
        )
        trailing_lines = [line.strip() for line in document_lines if line.strip()]
        completion_marker = bool(
            trailing_lines
            and (
                trailing_lines[-1].casefold() == "[all]"
                or re.search(
                    r"\[Whereupon,.*(?:adjourned|recessed).*\]$",
                    trailing_lines[-1],
                    flags=re.IGNORECASE,
                )
                or trailing_lines[-1].casefold()
                == "[graphic(s) not available in tiff format]"
            )
        )
        complete = bool(
            body_decision is AccessDecision.ALLOW
            and len(pre_nodes) == 1
            and document_lines
            and document_lines[0].startswith("[House Hearing,")
            and publisher_marker in {line.strip() for line in document_lines}
            and title
            and completion_marker
        )
        body = "\n".join(document_lines)
        if trailing_lines and trailing_lines[-1].casefold() == "[all]":
            body = re.sub(r"(?:\r?\n)?\s*\[all\]\s*$", "", body, flags=re.IGNORECASE)
        reviewed_abstract, reviewed_keywords = _reviewed_govinfo_metadata(response.url, body)

        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=metadata_matches,
        )
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=body_digest,
            body_complete=complete,
            body_format="source_text",
        )
        material = None
        field_sources = {}
        if metadata_matches and complete:
            material = VerifiedMaterial(
                source=publisher,
                time=publication_date,
                author="; ".join(creator_values) or "未注明",
                title=title,
                abstract=reviewed_abstract,
                keywords=reviewed_keywords,
                body=body,
                source_url=response.url,
            )
            field_sources = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if reviewed_abstract:
                field_sources["abstract"] = response.url
            if reviewed_keywords:
                field_sources["keywords"] = response.url
        return {
            "decision": body_decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "derived" if reviewed_abstract else "none",
            "keywords_origin": "derived" if reviewed_keywords else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class StateDepartmentReportPDFDocumentAdapter:
    source_name = "United States Department of State"

    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        is_pdf = response.body.lstrip().startswith(b"%PDF-")
        body_decision = classify_response(
            response.url, response.status,
            "" if is_pdf else response.body.decode("utf-8", errors="replace"),
        )
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        title_nodes = metadata_response.css(
            "main.nav__main-content article .featured-content__headline"
        )
        title = (
            _normalized_text(title_nodes.xpath(".//text()").getall())
            if len(title_nodes) == 1
            else ""
        )
        published_on = _publication_date(
            _normalized_text(
                metadata_response.css(
                    "main.nav__main-content article .article-meta__publish-date"
                ).xpath(".//text()").getall()
            ),
            "",
        )
        authors = list(dict.fromkeys(
            value
            for node in metadata_response.css(
                "main.nav__main-content article .article-meta__author-bureau"
            )
            if (value := _normalized_text(node.xpath(".//text()").getall()))
        ))
        author = ", ".join(authors) or "未注明"
        source = metadata_response.css(
            "meta[property='og:site_name']::attr(content)"
        ).get(default="").strip()
        pdf_urls = [
            urljoin(metadata_response.url, href)
            for href in metadata_response.css(
                "main.nav__main-content article .entry-content a[href]::attr(href)"
            ).getall()
            if re.search(r"\.pdf(?:\?|$)", href, flags=re.IGNORECASE)
        ]
        page_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and metadata_response.url == candidate.metadata_url
            and (urlsplit(metadata_response.url).hostname or "").lower()
            == "2021-2025.state.gov"
            and source == self.source_name
            and len(title_nodes) == 1
            and title
            and published_on
            and response.url == candidate.source_url
            and response.url in pdf_urls
        )
        page_texts = []
        if is_pdf and body_decision is AccessDecision.ALLOW:
            try:
                reader = PdfReader(BytesIO(response.body), strict=True)
                page_texts = [page.extract_text() or "" for page in reader.pages]
            except Exception:
                page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        first_page_key = _metadata_match_key(first_page)
        title_key = _metadata_match_key(title)
        complete = bool(
            body_decision is AccessDecision.ALLOW
            and page_texts
            and all(text.strip() for text in page_texts)
            and title_key
            and title_key in first_page_key
            and "global engagement center" in first_page.casefold()
        )
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=False,
            body_format="pdf_text" if is_pdf else "source_text",
        )
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=page_matches,
        )
        material = None
        field_sources = {}
        abstract = metadata_response.css(
            "meta[property='og:description']::attr(content)"
        ).get(default="").strip()
        keywords = "; ".join(dict.fromkeys(
            value
            for node in metadata_response.css(
                "main.nav__main-content article .related-tags__pills a"
            )
            if (value := _normalized_text(node.xpath(".//text()").getall()))
        ))
        if page_matches and complete:
            material = VerifiedMaterial(
                source=source,
                time=published_on,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body="\n\n".join(text.strip() for text in page_texts),
                source_url=response.url,
            )
            field_sources = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if abstract:
                field_sources["abstract"] = metadata_response.url
            if keywords:
                field_sources["keywords"] = metadata_response.url
        return {
            "decision": body_decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if material and abstract else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class IJocPDFDocumentAdapter:
    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_decision = classify_response(response.url, response.status)
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        title = _normalized_text(metadata_response.css("h1.page_title::text").getall())
        citation_title = metadata_response.css(
            "meta[name='citation_title']::attr(content)"
        ).get(default="").strip()
        citation_title = _normalized_text([citation_title])
        citation_date = metadata_response.css(
            "meta[name='citation_date']::attr(content)"
        ).get(default="").strip()
        visible_date = _normalized_text(
            metadata_response.css(".item.published .value").xpath(".//text()").getall()
        )
        try:
            visible_published = datetime.strptime(visible_date, "%Y-%m-%d").date().isoformat()
            structured_published = datetime.strptime(citation_date, "%Y/%m/%d").date().isoformat()
        except ValueError:
            visible_published = structured_published = ""
        authors = list(dict.fromkeys(
            value
            for node in metadata_response.css(".item.authors .name")
            if (value := _normalized_text(node.xpath(".//text()").getall()))
        ))
        citation_authors = [
            value.strip()
            for value in metadata_response.css("meta[name='citation_author']::attr(content)").getall()
            if value.strip()
        ]
        author = "; ".join(authors) if authors else "未注明"
        journal = metadata_response.css(
            "meta[name='citation_journal_title']::attr(content)"
        ).get(default="").strip()
        pdf_url = metadata_response.css(
            "meta[name='citation_pdf_url']::attr(content)"
        ).get(default="").strip()
        abstract = metadata_response.css(
            "meta[name='citation_abstract']::attr(content)"
        ).get(default="").strip()
        keywords = "; ".join(dict.fromkeys(
            value.strip()
            for value in metadata_response.css(
                "meta[name='citation_keywords']::attr(content)"
            ).getall()
            if value.strip()
        ))
        requested_pdf_urls = {
            response.url,
            *response.request.meta.get("redirect_urls", []),
        }
        metadata_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and metadata_response.url == candidate.metadata_url
            and (urlsplit(metadata_response.url).hostname or "").lower() == "ijoc.org"
            and title
            and title == citation_title
            and visible_published
            and visible_published == structured_published
            and authors
            and authors == citation_authors
            and journal == "International Journal of Communication"
            and candidate.source_url in requested_pdf_urls
            and pdf_url == candidate.source_url
        )
        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            reader = None
            page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        first_page_key = _metadata_match_key(first_page)
        article_title = title.split("|", 1)[-1].strip()
        complete = bool(
            body_decision is AccessDecision.ALLOW
            and page_texts
            and all(text.strip() for text in page_texts)
            and journal.casefold() in first_page.casefold()
            and _metadata_match_key(article_title) in first_page_key
            and all(_metadata_match_key(name) in first_page_key for name in authors)
        )
        body_evidence = SourceEvidence(
            source_url=candidate.source_url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=False,
            body_format="pdf_text",
        )
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=metadata_matches,
        )
        material = None
        field_sources = {}
        publisher_keywords = bool(keywords)
        if metadata_matches and complete:
            body = "\n\n".join(text.strip() for text in page_texts)
            if not keywords:
                keywords = _reviewed_research_keywords(response.url, body)
            material = VerifiedMaterial(
                source=journal,
                time=visible_published,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=candidate.source_url,
            )
            field_sources = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if abstract:
                field_sources["abstract"] = metadata_response.url
            if keywords:
                field_sources["keywords"] = metadata_response.url if publisher_keywords else response.url
        return {
            "decision": body_decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if material and abstract else "none",
            "keywords_origin": "publisher" if publisher_keywords else "derived" if material and keywords else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class OjsJournalPDFDocumentAdapter:
    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_decision = classify_response(response.url, response.status)
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        title_nodes = metadata_response.css("h1.page_title")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        citation_title = metadata_response.css(
            "meta[name='citation_title']::attr(content)"
        ).get(default="").strip()
        author_nodes = metadata_response.css(".item.authors .name")
        visible_authors = list(dict.fromkeys(
            value for node in author_nodes
            if (value := _normalized_text(node.xpath(".//text()").getall()))
        ))
        citation_authors = list(dict.fromkeys(
            value.strip()
            for value in metadata_response.css(
                "meta[name='citation_author']::attr(content)"
            ).getall()
            if value.strip()
        ))
        published_visible = _normalized_text(
            metadata_response.css(".item.published .value").xpath(".//text()").getall()
        )
        citation_date = metadata_response.css(
            "meta[name='citation_date']::attr(content)"
        ).get(default="").strip()
        try:
            visible_date = datetime.strptime(published_visible, "%Y-%m-%d").date().isoformat()
            structured_date = datetime.strptime(citation_date, "%Y/%m/%d").date().isoformat()
        except ValueError:
            visible_date = structured_date = ""
        journal = metadata_response.css(
            "meta[name='citation_journal_title']::attr(content)"
        ).get(default="").strip()
        generator = metadata_response.css("meta[name='generator']::attr(content)").get(default="")
        pdf_url = metadata_response.css(
            "meta[name='citation_pdf_url']::attr(content)"
        ).get(default="").strip()
        visible_pdf_urls = {
            urljoin(metadata_response.url, href)
            for href in metadata_response.css("a.obj_galley_link.pdf::attr(href)").getall()
        }
        citation_parts = urlsplit(pdf_url)
        citation_path = citation_parts.path.replace("/article/view/", "/article/download/")
        visible_pdf_matches = any(
            urlsplit(value).netloc.casefold() == citation_parts.netloc.casefold()
            and urlsplit(value).path.replace("/article/view/", "/article/download/") == citation_path
            for value in visible_pdf_urls
        )
        rights = [
            value.strip().casefold()
            for value in metadata_response.css("meta[name='DC.Rights']::attr(content)").getall()
        ]
        has_open_license = any(
            "creativecommons.org/licenses/" in value for value in rights
        )
        metadata_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and metadata_response.url == candidate.metadata_url
            and "open journal systems" in generator.casefold()
            and title
            and title == citation_title
            and visible_date
            and visible_date == structured_date
            and visible_authors
            and visible_authors == citation_authors
            and journal
            and pdf_url == response.url == candidate.source_url
            and visible_pdf_matches
            and has_open_license
        )
        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        article_title = title.split("=", 1)[-1].strip() if "=" in title else title
        first_page_key = _metadata_match_key(first_page)
        complete = bool(
            body_decision is AccessDecision.ALLOW
            and page_texts
            and all(text.strip() for text in page_texts)
            and _metadata_match_key(article_title) in first_page_key
            and all(_metadata_match_key(author) in first_page_key for author in citation_authors)
            and _metadata_match_key(journal) in first_page_key
        )
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=False,
            body_format="pdf_text",
        )
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=metadata_matches,
        )
        abstract = metadata_response.css(
            "meta[name='citation_abstract']::attr(content)"
        ).get(default="").strip()
        keywords = "; ".join(dict.fromkeys(
            value.strip()
            for value in metadata_response.css(
                "meta[name='citation_keywords']::attr(content)"
            ).getall()
            if value.strip()
        ))
        material = None
        field_sources = {}
        if metadata_matches and complete:
            material = VerifiedMaterial(
                source=journal,
                time=visible_date,
                author="; ".join(visible_authors),
                title=title,
                abstract=abstract,
                keywords=keywords,
                body="\n\n".join(text.strip() for text in page_texts),
                source_url=response.url,
            )
            field_sources = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if abstract:
                field_sources["abstract"] = metadata_response.url
            if keywords:
                field_sources["keywords"] = metadata_response.url
        return {
            "decision": body_decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if material and abstract else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class JStagePDFDocumentAdapter:
    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: HtmlResponse,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_decision = classify_response(response.url, response.status)
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        journal = metadata_response.css(
            "meta[name='citation_journal_title']::attr(content)"
        ).get(default="").strip()
        publisher = metadata_response.css(
            "meta[name='citation_publisher']::attr(content)"
        ).get(default="").strip()
        primary_title = _normalized_text(
            metadata_response.css(".global-article-title").xpath(".//text()").getall()
        )
        subtitle = _normalized_text(
            metadata_response.css(".global-article-inner-title").xpath(".//text()").getall()
        )
        title = metadata_response.css(
            "meta[name='citation_title']::attr(content)"
        ).get(default="").strip()
        visible_title = " ".join(part for part in (primary_title, subtitle) if part)
        authors = list(dict.fromkeys(
            _normalized_text(node.xpath(".//text()").getall())
            for node in metadata_response.css(".global-authors-name-tags > a span")
            if _normalized_text(node.xpath(".//text()").getall())
        ))
        citation_authors = list(dict.fromkeys(
            value.strip()
            for value in metadata_response.css(
                "meta[name='citation_author']::attr(content)"
            ).getall()
            if value.strip()
        ))
        citation_date = metadata_response.css(
            "meta[name='citation_publication_date']::attr(content)"
        ).get(default="").strip()
        page_date = metadata_response.css(
            "meta[name='publication_date']::attr(content)"
        ).get(default="").strip()
        try:
            publication_date = datetime.strptime(citation_date, "%Y/%m/%d").date().isoformat()
            visible_publication_date = datetime.strptime(page_date, "%Y/%m/%d").date().isoformat()
        except ValueError:
            publication_date = visible_publication_date = ""
        doi = metadata_response.css(
            "meta[name='citation_doi']::attr(content)"
        ).get(default="").strip().removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        candidate_doi = (candidate.platform_id or "").strip().removeprefix(
            "https://doi.org/"
        ).removeprefix("http://doi.org/")
        citation_pdf_url = metadata_response.css(
            "meta[name='citation_pdf_url']::attr(content)"
        ).get(default="").strip()
        citation_pdf_url = urljoin(metadata_response.url, citation_pdf_url)
        visible_pdf_urls = {
            urljoin(metadata_response.url, href)
            for href in metadata_response.css("a.thirdlevel-pdf-btn::attr(href)").getall()
        }
        abstract_nodes = metadata_response.css("#article-overiew-abstract-wrap .global-para-14")
        abstract = _normalized_text(abstract_nodes.xpath(".//text()").getall()) if len(abstract_nodes) == 1 else ""

        def pdf_key(value: str) -> tuple[str, str, str]:
            parts = urlsplit(value)
            path = parts.path.removesuffix("/-char/en").rstrip("/")
            return parts.scheme.casefold(), parts.netloc.casefold(), path

        expected_pdf = pdf_key(citation_pdf_url)
        pdf_matches = bool(
            expected_pdf[0] == "https"
            and expected_pdf[1].endswith("jstage.jst.go.jp")
            and expected_pdf[2].endswith("/_pdf")
            and pdf_key(response.url) == expected_pdf
            and pdf_key(candidate.source_url) == expected_pdf
            and any(pdf_key(value) == expected_pdf for value in visible_pdf_urls)
        )
        metadata_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and metadata_response.url == candidate.metadata_url
            and (urlsplit(metadata_response.url).hostname or "").casefold().endswith("jstage.jst.go.jp")
            and journal
            and publisher
            and title
            and visible_title == title
            and authors
            and authors == citation_authors
            and publication_date
            and publication_date == visible_publication_date
            and doi
            and candidate_doi == doi
            and pdf_matches
        )

        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        first_page_key = _metadata_match_key(first_page)
        complete = bool(
            body_decision is AccessDecision.ALLOW
            and page_texts
            and all(text.strip() for text in page_texts)
            and _metadata_match_key(title) in first_page_key
            and all(_metadata_match_key(author) in first_page_key for author in authors)
            and _metadata_match_key(journal) in first_page_key
        )
        body = "\n\n".join(text.strip() for text in page_texts if text.strip())
        keyword_terms = (
            "U.S.-China relations",
            "China-U.S. relations",
            "foreign policy",
            "public opinion",
            "normalization",
            "Taiwan",
        )
        body_key = _metadata_match_key(body)
        keywords = "; ".join(
            term for term in keyword_terms if _metadata_match_key(term) in body_key
        )
        source = f"{journal} ({publisher})" if journal and publisher else ""
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=metadata_matches,
        )
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            body_format="pdf_text",
            original_page_verified=metadata_matches,
        )
        material = None
        field_sources = {}
        if metadata_matches and complete:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author="; ".join(authors),
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=metadata_response.url,
            )
            field_sources = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if abstract:
                field_sources["abstract"] = metadata_response.url
            if keywords:
                field_sources["keywords"] = "body"
        decision = (
            body_decision
            if body_decision is not AccessDecision.ALLOW
            else metadata_decision
        )
        return {
            "decision": decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if material and abstract else "none",
            "keywords_origin": "derived" if material and keywords else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class CcseJournalPDFDocumentAdapter:
    source_host = "ccsenet.org"
    expected_page_numbers = list(range(16, 31))

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_format="pdf_text",
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}
        parts = urlsplit(response.url)
        if (
            response.url != candidate.source_url
            or (parts.hostname or "").lower() != self.source_host
            or "/journal/index.php/ells/article/download/" not in parts.path
        ):
            return {"decision": decision, "evidence": evidence, "material": None}

        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            page_texts = []
        first_page = page_texts[0] if page_texts else ""
        lines = [line.strip() for line in first_page.splitlines() if line.strip()]
        publisher_index = next(
            (i for i, line in enumerate(lines)
             if line.casefold() == "published by canadian center of science and education"),
            None,
        )
        author_index = next(
            (i for i, line in enumerate(lines)
             if i > (publisher_index if publisher_index is not None else -1)
             and " & " in line),
            None,
        )
        journal = lines[0].split(";", 1)[0].strip() if lines else ""
        title_lines = []
        if publisher_index is not None and author_index is not None:
            title_lines = [
                line for line in lines[publisher_index + 1:author_index]
                if not re.fullmatch(r"\d+", line)
            ]
        title = _normalized_text(title_lines)
        raw_author_line = lines[author_index] if author_index is not None else ""
        author_parts = [
            _normalized_text([part])
            for group in re.sub(r"(?<=[A-Za-z])\d+\b", "", raw_author_line).split("&")
            for part in group.split(",")
        ]
        authors = [author for author in author_parts if author]

        metadata_text = re.sub(
            r"(?<![A-Za-z])(?:[A-Za-z]\s+){2,}[A-Za-z](?![A-Za-z])",
            lambda match: re.sub(r"\s+", "", match.group()),
            first_page,
        )
        metadata_text = re.sub(r"(?<=\d)\s+(?=\d)", "", metadata_text)
        date_match = re.search(
            r"(?i)Online\s*Published\s*:\s*([A-Z][a-z]+\s+\d{1,2}\s*,\s*\d{4})",
            metadata_text,
        )
        try:
            publication_date = datetime.strptime(
                re.sub(r"\s*,\s*", ", ", date_match.group(1)), "%B %d, %Y"
            ).date().isoformat() if date_match else ""
        except ValueError:
            publication_date = ""
        doi_match = re.search(r"(?im)^\s*doi\s*:\s*(10\.\d{4,9}/[^\s]+)", first_page)
        doi = doi_match.group(1).rstrip(".,;") if doi_match else ""
        abstract_match = re.search(r"(?ms)^Abstract\s*\n(.*?)^Keywords\s*:", first_page)
        abstract = _normalized_text(abstract_match.group(1).splitlines()) if abstract_match else ""
        keywords_match = re.search(
            r"(?ms)^Keywords\s*:\s*(.*?)^\s*1\.\s*Introduction\s*$", first_page
        )
        keywords = _normalized_text(keywords_match.group(1).splitlines()) if keywords_match else ""

        page_numbers = []
        for page_text in page_texts:
            numbers = [
                int(line.strip()) for line in page_text.splitlines()
                if re.fullmatch(r"\s*\d{2}\s*", line)
            ]
            page_numbers.append(numbers[0] if len(numbers) == 1 else None)
        all_text = "\n\n".join(text.strip() for text in page_texts)
        license_present = bool(re.search(
            r"(?i)creativecommons\.org/licenses/by/4\.0/?", all_text
        ))
        complete = bool(
            page_texts and all(text.strip() for text in page_texts)
            and len(page_texts) == len(self.expected_page_numbers)
            and page_numbers == self.expected_page_numbers
            and publisher_index is not None and author_index is not None
            and journal == "English Language and Literature Studies"
            and title and len(authors) == 3 and publication_date
            and doi == "10.5539/ells.v15n3p16"
            and abstract and keywords and license_present and all_text
        )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=complete,
            body_format="pdf_text",
        )
        material = None
        result = {"decision": decision, "evidence": evidence, "material": None}
        if complete:
            material = VerifiedMaterial(
                source=journal,
                time=publication_date,
                author="; ".join(authors),
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=all_text,
                source_url=response.url,
            )
            result.update({
                "material": material,
                "field_sources": {
                    name: response.url
                    for name in ("source", "time", "author", "title", "abstract", "keywords")
                },
                "abstract_origin": "publisher",
            })
        return result


class BepressRepositoryPDFDocumentAdapter:
    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_decision = classify_response(response.url, response.status)
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        title = metadata_response.css(
            'meta[name="bepress_citation_title"]::attr(content)'
        ).get(default="").strip()
        displayed_title = metadata_response.css(
            'meta[itemprop="name"]::attr(content)'
        ).get(default="").strip()
        author = metadata_response.css('meta[name="author"]::attr(content)').get(default="").strip()
        bepress_authors = [
            value.strip()
            for value in metadata_response.css(
                'meta[name="bepress_citation_author"]::attr(content)'
            ).getall()
            if value.strip()
        ]
        online_date = metadata_response.css(
            'meta[name="bepress_citation_online_date"]::attr(content)'
        ).get(default="").strip()
        try:
            publication_date = datetime.strptime(online_date, "%Y/%m/%d").date().isoformat()
        except ValueError:
            publication_date = ""
        pdf_url = metadata_response.css(
            'meta[name="bepress_citation_pdf_url"]::attr(content)'
        ).get(default="").strip()
        abstract = metadata_response.css('meta[name="description"]::attr(content)').get(default="").strip()
        keywords = metadata_response.css('meta[name="keywords"]::attr(content)').get(default="").strip()
        site_name = metadata_response.css('meta[property="og:site_name"]::attr(content)').get(default="").strip()
        institution = metadata_response.css("#logo a::attr(title)").get(default="").strip()
        source = f"{site_name} ({institution})" if site_name and institution else site_name
        author_tokens = [token.casefold() for token in re.findall(r"[\w'-]+", author)]
        bepress_author_matches = any(
            [token.casefold() for token in re.findall(r"[\w'-]+", value)]
            in (author_tokens, list(reversed(author_tokens)))
            for value in bepress_authors
        )
        metadata_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and metadata_response.url == candidate.metadata_url
            and (urlsplit(metadata_response.url).hostname or "").lower() == "opensiuc.lib.siu.edu"
            and title and displayed_title == title and author
            and bepress_author_matches
            and publication_date
            and pdf_url == response.url == candidate.source_url
            and source
        )
        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        first_page_key = _metadata_match_key(first_page)
        complete = bool(
            body_decision is AccessDecision.ALLOW
            and page_texts
            and all(text.strip() for text in page_texts)
            and _metadata_match_key(title) in first_page_key
            and _metadata_match_key(author) in first_page_key
        )
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=False,
            body_format="pdf_text",
        )
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=metadata_matches,
        )
        material = None
        fields = {}
        if metadata_matches and complete:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body="\n\n".join(text.strip() for text in page_texts),
                source_url=response.url,
            )
            fields = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if abstract:
                fields["abstract"] = metadata_response.url
            if keywords:
                fields["keywords"] = metadata_response.url
        return {
            "decision": body_decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": fields,
            "abstract_origin": "publisher" if material and abstract else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class BrookingsPDFDocumentAdapter:
    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        body_digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status)
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=body_digest,
            body_format="pdf_text",
        )
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        metadata_article = _find_jsonld_article(metadata_response)
        title = _normalized_text(metadata_response.css("h1::text").getall())
        structured_title = _normalized_text(
            [str(metadata_article.get("headline", ""))] if metadata_article else []
        )
        source = metadata_response.css(
            "meta[property='og:site_name']::attr(content)"
        ).get(default="").strip()
        published_on = _publication_date(
            "", str(metadata_article.get("datePublished", "")) if metadata_article else ""
        )
        authors = list(dict.fromkeys(
            name
            for node in metadata_response.css(".byo-block.authors span.name")
            if (name := _normalized_text(node.xpath(".//text()").getall()))
        ))
        if not authors and metadata_article:
            structured_authors = metadata_article.get("creator") or metadata_article.get("author") or []
            if not isinstance(structured_authors, list):
                structured_authors = [structured_authors]
            authors = list(dict.fromkeys(
                name for value in structured_authors if (name := _jsonld_name(value))
            ))
        author = ", ".join(authors) or "未注明"
        abstract = metadata_response.css(
            "meta[name='description']::attr(content)"
        ).get(default="").strip()
        metadata_valid = bool(
            metadata_decision is AccessDecision.ALLOW
            and source == "Brookings"
            and title
            and title == structured_title
            and published_on
            and metadata_response.url == candidate.metadata_url
            and response.url in {
                urljoin(metadata_response.url, href)
                for href in metadata_response.css("a[href]::attr(href)").getall()
            }
        )
        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        first_page_folded = first_page.casefold()
        body = "\n\n".join(text.strip() for text in page_texts)
        keywords = _reviewed_brookings_keywords(response.url, body)
        reviewed = BROOKINGS_REVIEWED_PDF_METADATA.get(response.url)
        reviewed_title = bool(
            reviewed
            and reviewed["metadata_url"] == metadata_response.url
            and reviewed["page_title"] == title
            and reviewed["published_on"] == published_on
            and reviewed["pdf_sha256"] == body_digest
            and reviewed["body_sha256"] == sha256(body.encode("utf-8")).hexdigest()
            and _metadata_match_key(reviewed["title"]) in _metadata_match_key(first_page)
        )
        if reviewed_title:
            title = reviewed["title"]
        title_key = _metadata_match_key(title)
        author_matches = author == "未注明" or all(
            _metadata_match_key(name) in _metadata_match_key(first_page)
            for name in authors
        )
        pdf_complete = bool(
            decision is AccessDecision.ALLOW
            and len(page_texts) > 0
            and all(text.strip() for text in page_texts)
            and ("brookings institution" in first_page_folded or reviewed_title)
            and title_key
            and title_key in _metadata_match_key(first_page)
            and author_matches
        )
        body_evidence = replace(
            body_evidence,
            body_complete=pdf_complete,
            metadata_verified=False,
        )
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            body_complete=False,
            metadata_verified=metadata_valid,
        )
        material = None
        field_sources = {}
        if metadata_valid and pdf_complete:
            material = VerifiedMaterial(
                source="Brookings",
                time=published_on,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
            field_sources = {
                name: metadata_response.url
                for name in ("source", "time", "author", "title")
            }
            if reviewed_title:
                field_sources["title"] = reviewed.get("title_source", response.url)
            if abstract:
                field_sources["abstract"] = metadata_response.url
            if keywords:
                field_sources["keywords"] = response.url
        return {
            "decision": decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "publisher" if abstract else "none",
            "keywords_origin": "derived" if keywords else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


class CSISPDFDocumentAdapter:
    source_name = "Center for Strategic and International Studies (CSIS)"

    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response,
    ) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_digest = sha256(response.body).hexdigest()
        decision = classify_response(response.url, response.status)
        body_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=body_digest,
            body_format="pdf_text",
        )
        metadata_decision = classify_response(
            metadata_response.url, metadata_response.status, metadata_response.text
        )
        title_nodes = metadata_response.css("h1")
        title = (
            _normalized_text(title_nodes.xpath(".//text()").getall())
            if len(title_nodes) == 1
            else ""
        )
        document_title = _normalized_text(
            [metadata_response.xpath("string(//head/title)").get(default="")]
        )
        content = metadata_response.css(
            "#block-ts-csis-content .layout--columns-report .column--second, "
            "#block-ts-csis-content .layout--columns-article .column--first"
        )
        byline = _normalized_text(content.css(".byline-block").xpath(".//text()").getall())
        author_match = re.search(
            r"(?:Commentary|Analysis|Brief|Report|Congressional Testimony)\s+by\s+(.+?)\s+Published\s+",
            byline,
            flags=re.IGNORECASE,
        )
        date_match = re.search(
            r"Published\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            byline,
            flags=re.IGNORECASE,
        )
        authors = (
            [_normalized_text([part]) for part in re.split(r"\s*,\s*|\s+and\s+", author_match.group(1))]
            if author_match
            else []
        )
        authors = [name for name in authors if name]
        author = ", ".join(authors)
        publication_date = _publication_date(date_match.group(1) if date_match else "", "")
        keywords = ""
        abstract = metadata_response.css(
            "meta[name='description']::attr(content)"
        ).get(default="").strip()
        pdf_url = next(
            (
                href
                for href in metadata_response.css(".downloads-block a[href]::attr(href)").getall()
                if re.search(r"\.pdf(?:\?|$)", href, flags=re.IGNORECASE)
            ),
            None,
        )
        page_matches = bool(
            metadata_decision is AccessDecision.ALLOW
            and (urlsplit(metadata_response.url).hostname or "").lower().endswith("csis.org")
            and metadata_response.url == candidate.metadata_url
            and title
            and title == document_title
            and len(content) == 1
            and authors
            and publication_date
            and pdf_url
            and urljoin(metadata_response.url, pdf_url) == response.url
        )
        try:
            reader = PdfReader(BytesIO(response.body), strict=True)
            page_texts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            page_texts = []
        first_page = _normalized_text(page_texts[0].splitlines()) if page_texts else ""
        first_page_key = _metadata_match_key(first_page)
        body = _csis_pdf_body(page_texts, reader.pages) if page_texts else ""
        complete_pdf_text = "\n".join(page_texts)
        complete_pdf_text_folded = complete_pdf_text.casefold()
        pdf_complete = bool(
            decision is AccessDecision.ALLOW
            and page_texts
            and all(text.strip() for text in page_texts)
            and (
                "center for strategic and international studies" in complete_pdf_text_folded
                or ("csis" in complete_pdf_text_folded and "www.csis.org" in complete_pdf_text_folded)
            )
            and _metadata_match_key(title)
            and _metadata_match_key(title) in first_page_key
            and all(_metadata_match_key(name) in first_page_key for name in authors)
            and (
                response.url not in CSIS_REVIEWED_PDFS
                or CSIS_REVIEWED_PDFS[response.url] == (body_digest, len(page_texts))
            )
        )
        body_evidence = replace(body_evidence, body_complete=pdf_complete)
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=fetched_at,
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=page_matches,
        )
        material = None
        fields = {}
        if page_matches and pdf_complete:
            material = VerifiedMaterial(
                source=self.source_name,
                time=publication_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
            keywords = _reviewed_csis_keywords(response.url, body)
            material = replace(material, keywords=keywords)
            fields = {name: metadata_response.url for name in ("source", "time", "author", "title")}
            if abstract:
                fields["abstract"] = metadata_response.url
            if keywords:
                fields["keywords"] = response.url
        return {
            "decision": decision,
            "evidence": body_evidence,
            "material": material,
            "field_sources": fields,
            "abstract_origin": "publisher" if abstract else "none",
            "keywords_origin": "derived" if material and material.keywords else "none",
            "supporting_evidence": [{
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            }],
        }


def _metadata_match_key(value: str) -> str:
    return "".join(character.casefold() for character in value if character.isalnum())


class APNewsArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        headings = response.css("h1")
        title = _normalized_text(headings[0].xpath(".//text()").getall()) if len(headings) == 1 else ""
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        author_text = _normalized_text(response.css(".Page-authors").xpath(".//text()").getall())
        author = re.sub(r"^By\s+", "", author_text, flags=re.IGNORECASE).strip()
        byline = _normalized_text(response.css(".Page-byline-info").xpath(".//text()").getall())
        visible_date = re.search(
            r"Published\s+\d{1,2}:\d{2}\s+[AP]M\s+[A-Z]{2,5},\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            byline,
        )
        try:
            publication_date = datetime.strptime(visible_date.group(1), "%B %d, %Y").date().isoformat()
        except (AttributeError, ValueError):
            publication_date = ""

        body_containers = response.css(".RichTextStoryBody")
        paragraphs = []
        if len(body_containers) == 1:
            paragraphs = [
                _normalized_text(paragraph.xpath(".//text()").getall())
                for paragraph in body_containers.xpath("./p")
            ]
        body = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        raw_keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        keywords = "; ".join(part.strip() for part in raw_keywords.split(",") if part.strip())
        complete = bool(source == "AP News" and title and publication_date and body_containers and body)
        if any(marker in body.casefold() for marker in ("continue reading", "subscribe to read", "read more")):
            complete = False

        material = None
        if complete:
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
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = "publisher" if abstract else "none"
            result["keywords_origin"] = "derived" if raw_keywords else "none"
        return result


class BlueskyPostAdapter:
    """Public post HTML cross-checked against the documented public getPosts API."""

    sources = {
        "apnews.com": "The Associated Press",
        "nytimes.com": "The New York Times",
        "nytopinion.nytimes.com": "The New York Times",
        "freedomhouse.bsky.social": "Freedom House",
        "csis.org": "CSIS",
        "poqjournal.bsky.social": "Public Opinion Quarterly",
        "pewresearch.org": "Pew Research Center",
        "brookings.edu": "Brookings Institution",
        "cfr.org": "Council on Foreign Relations",
        "rand.org": "RAND",
        "reuters.com": "Reuters",
        "cnn.com": "CNN",
        "foreignaffairs.com": "Foreign Affairs",
        "chathamhouse.org": "Chatham House",
        "pbs.org": "PBS",
        "npr.org": "NPR",
        "foreignpolicy.com": "Foreign Policy",
        "theguardian.com": "The Guardian",
        "washingtonpost.com": "The Washington Post",
        "lawfaremedia.org": "Lawfare",
        "carnegieendowment.org": "Carnegie Endowment",
        "theconversation.com": "The Conversation",
        "politico.com": "Politico",
        "thediplomat.com": "The Diplomat",
        "scmp.com": "South China Morning Post",
        "axios.com": "Axios",
        "economist.com": "The Economist",
        "usip.org": "U.S. Institute of Peace",
        "wilsoncenter.org": "The Wilson Center",
        "hrw.org": "Human Rights Watch",
        "amnesty.org": "Amnesty International",
        "justsecurity.org": "Just Security",
        "gallup.com": "Gallup",
        "state-department.bsky.social": "U.S. Department of State",
        "deptofdefense.bsky.social": "U.S. Department of Defense",
        "whitehouse.bsky.social": "The White House",
        "financialtimes.com": "Financial Times",
        "scmpnews.bsky.social": "South China Morning Post",
        "scmp.com": "South China Morning Post",
        "chinadaily.bsky.social": "China Daily",
        "peoplesdaily.bsky.social": "People's Daily, China",
        "hrwchinese.bsky.social": "Human Rights Watch Chinese",
        "radiofreeasiapr.bsky.social": "Radio Free Asia",
        "ununiversity.bsky.social": "United Nations University",
        "globalcompact.bsky.social": "United Nations Global Compact",
        "ecfr.eu": "European Council on Foreign Relations",
        "dgap.org": "German Council on Foreign Relations",
    }

    def extract(self, response: Response, candidate: MaterialCandidate, metadata_response: Response | None) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(response.url, fetched_at, response.status, sha256(response.body).hexdigest())
        result = {"decision": decision, "evidence": evidence, "material": None}
        if decision is not AccessDecision.ALLOW or metadata_response is None:
            return result
        metadata_decision = classify_response(metadata_response.url, metadata_response.status, metadata_response.text)
        if metadata_decision is not AccessDecision.ALLOW:
            return result
        from urllib.parse import parse_qs
        parts = urlsplit(response.url)
        path = re.fullmatch(r"/profile/([^/]+)/post/([^/]+)", parts.path)
        if not path or path.group(1) not in self.sources:
            return result
        handle, key = path.groups()
        api_parts = urlsplit(metadata_response.url)
        try:
            posts = json.loads(metadata_response.text)["posts"]
            post = posts[0] if len(posts) == 1 else {}
            record = post.get("record", {})
            author = post.get("author", {})
        except (KeyError, ValueError, TypeError, IndexError, AttributeError):
            return result
        if not isinstance(record, dict) or not isinstance(author, dict):
            return result
        summary = response.css("#bsky_post_summary")
        did = summary.css("#bsky_did::text").get(default="")
        expected_uri = f"at://{did}/app.bsky.feed.post/{key}"
        page_text_nodes = summary.css("#bsky_post_text")
        page_text = page_text_nodes.xpath("string(.)").get(default="") if len(page_text_nodes) == 1 else ""
        body = record.get("text", "")
        embed = record.get("embed", {})
        external = embed.get("external", {}) if isinstance(embed, dict) else {}
        external_url = external.get("uri", "") if isinstance(external, dict) else ""
        page_links = page_text_nodes.css("a::attr(href)").getall() if len(page_text_nodes) == 1 else []
        page_matches = isinstance(body, str) and _bluesky_post_text_matches(
            page_text, body, record, external_url, page_links
        )
        title = response.css("head > title::text").get(default="")
        indexed_at = summary.css("#bsky_post_indexedat::text").get(default="")
        published_meta = response.css('meta[property="article:published_time"]::attr(content)').get(default="")
        created_at = record.get("createdAt", "")
        publication_date = _publication_date("", created_at) if isinstance(created_at, str) else ""
        complete = bool(
            response.url == candidate.source_url and metadata_response.url == candidate.metadata_url
            and api_parts.scheme == "https" and api_parts.hostname == "public.api.bsky.app"
            and api_parts.path == "/xrpc/app.bsky.feed.getPosts"
            and parse_qs(api_parts.query) == {"uris": [expected_uri]}
            and len(summary) == 1 and did.startswith("did:")
            and post.get("uri") == expected_uri
            and candidate.platform_id == expected_uri
            and response.css('meta[name="at:canonical"]::attr(content)').get() == expected_uri
            and author.get("did") == did and author.get("handle") == handle
            and summary.css("#bsky_handle::text").get() == handle
            and author.get("displayName") == summary.css("#bsky_display_name::text").get()
            and record.get("$type") == "app.bsky.feed.post"
            and body and page_matches and title == f"@{handle} on Bluesky"
            and publication_date and publication_date == _publication_date("", published_meta)
            and published_meta == indexed_at == post.get("indexedAt")
        )
        evidence = replace(evidence, body_complete=complete, metadata_verified=complete, body_format="source_text")
        result["evidence"] = evidence
        if not complete:
            return result
        abstract, keywords = _reviewed_bluesky_metadata(response.url, body)
        if not abstract or not keywords:
            abstract, keywords = _derive_bluesky_metadata(body)
        result["material"] = VerifiedMaterial(
            self.sources[handle], publication_date, author["displayName"], title,
            abstract, keywords, body, response.url,
        )
        result["field_sources"] = {"source": response.url, "title": response.url,
                                    "author": metadata_response.url, "time": metadata_response.url}
        if abstract:
            result["field_sources"]["abstract"] = response.url
        if keywords:
            result["field_sources"]["keywords"] = response.url
        result["abstract_origin"] = "derived" if abstract else "none"
        result["keywords_origin"] = "derived" if keywords else "none"
        result["supporting_evidence"] = [{
            "decision": metadata_decision,
            "evidence": SourceEvidence(metadata_response.url, fetched_at, metadata_response.status,
                                       sha256(metadata_response.body).hexdigest(), metadata_verified=True, body_format="json"),
            "raw_response": metadata_response.body,
        }]
        return result


def _pbs_inline_text(node) -> str:
    fragments = [
        fragment.root if isinstance(fragment.root, str) else "\n"
        for fragment in node.xpath(".//text() | .//br")
    ]
    return _normalized_text(["".join(fragments)])


class PBSNewsArticleAdapter:
    """Observed PBS bodies with a closing credit or an exact reviewed snapshot."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(response.url, fetched_at, response.status, digest)
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        title_nodes = response.css('h1.post__title[itemprop="headline"]')
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        metadata_title = response.css('meta[property="og:title"]::attr(content)').get(default="").strip()
        source = response.css('meta[property="og:site_name"]::attr(content)').get(default="").strip()
        dates = response.css('time.post__date[itemprop="datePublished"]')
        visible_date = _normalized_text(dates.xpath(".//text()").getall()) if len(dates) == 1 else ""
        visible_match = re.search(r"\b[A-Z][a-z]{2} \d{1,2}, \d{4}\b", visible_date)
        try:
            publication_date = datetime.strptime(visible_match.group(0), "%b %d, %Y").date().isoformat()
        except (AttributeError, ValueError):
            publication_date = ""
        date_content = dates[0].attrib.get("content", "") if len(dates) == 1 else ""
        published_meta = response.css('meta[property="article:published_time"]::attr(content)').getall()
        bylines = response.css(".post__byline--side")
        authors = list(dict.fromkeys(
            _normalized_text(node.xpath(".//text()").getall())
            for node in bylines.css(".post__byline-name-unhyphenated")
        ))
        body_nodes = response.css('article[itemprop="articleBody"] > .body-text')
        parts = []
        body_supported = True
        end_boundary = False
        if len(body_nodes) == 1:
            children = body_nodes.xpath("./*")
            leading_text = _normalized_text([body_nodes[0].root.text or ""])
            if leading_text:
                parts.append(leading_text)
            if children:
                end_boundary = "inline-invite-type__funding" in children[-1].attrib.get("class", "").split()
            for node in children:
                classes = node.attrib.get("class", "").split()
                if "inline-invite-type__funding" in classes:
                    if (node.root.tail or "").strip():
                        body_supported = False
                    continue
                # Concatenate inline fragments before whitespace normalization;
                # joining fragments with spaces alters linked punctuation/words.
                text = _pbs_inline_text(node)
                tag = node.root.tag.lower()
                recommendation = tag == "p" and text.startswith(("READ MORE:", "WATCH:", "WATCH MORE:", "MORE:")) and node.xpath("./a")
                if text and not recommendation:
                    if tag not in {"p", "h2", "h3", "blockquote", "pullquote", "ul", "ol"}:
                        body_supported = False
                    elif tag in {"ul", "ol"}:
                        items = node.xpath("./li")
                        if ((node.root.text or "").strip()
                                or node.xpath("./*[not(self::li)]")
                                or any((li.root.tail or "").strip() for li in items)):
                            body_supported = False
                        parts.extend(_pbs_inline_text(li) for li in items)
                    else:
                        parts.append(text)
                # Some legacy articles place substantive text after a pullquote
                # directly in its tail, outside a paragraph element.
                tail = _normalized_text([node.root.tail or ""])
                if tail:
                    parts.append(tail)
        body = "\n\n".join(part for part in parts if part)
        closing_credit = bool(re.search(r"contributed to this report(?: from [^.]+)?\.$", parts[-1])) if parts else False
        author = "; ".join(authors) or "未注明"
        reviewed_snapshot = PBS_REVIEWED_ARTICLES.get(response.url) == (
            publication_date, title, author, sha256(body.encode("utf-8")).hexdigest()
        )
        complete = bool(
            source == "PBS News" and title and title == metadata_title
            and publication_date and len(dates) == 1
            and publication_date == _publication_date("", date_content)
            and len(published_meta) == 1 and published_meta[0] == date_content
            and len(bylines) == 1 and len(body_nodes) == 1
            and body and body_supported and (closing_credit or reviewed_snapshot) and end_boundary
        )
        abstract = response.css('meta[name="description"]::attr(content)').get(default="").strip()
        material = VerifiedMaterial(
            source, publication_date, author, title,
            abstract, "", body, response.url,
        ) if complete else None
        evidence = SourceEvidence(
            response.url, fetched_at, response.status, digest,
            body_complete=complete, metadata_verified=complete, body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {name: response.url for name in ("source", "time", "author", "title")}
            if abstract:
                result["field_sources"]["abstract"] = response.url
            result["abstract_origin"] = "publisher" if abstract else "none"
        return result


class PBSVideoTranscriptAdapter:
    """Extract an exact, source-reviewed PBS NewsHour video transcript page."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(response.url, fetched_at, response.status, digest)
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        reviewed = PBS_REVIEWED_VIDEO_TRANSCRIPTS.get(response.url)
        if reviewed is None:
            return {"decision": decision, "evidence": evidence, "material": None}

        title_nodes = response.css("h1.video-single__title")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        metadata_title = response.css('meta[property="og:title"]::attr(content)').getall()
        source = response.css('meta[property="og:site_name"]::attr(content)').getall()
        visible_time = _normalized_text(
            response.css(".video-single__hero-info").xpath(".//text()").getall()
        )
        visible_match = re.search(r"\b([A-Z][a-z]{2} \d{1,2}, \d{4})\b", visible_time)
        try:
            visible_date = datetime.strptime(visible_match.group(1), "%b %d, %Y").date().isoformat()
        except (AttributeError, ValueError):
            visible_date = ""
        published_values = response.css('meta[property="article:published_time"]::attr(content)').getall()
        structured = _find_jsonld_article(response)
        structured_date = _publication_date(
            "", str(structured.get("datePublished", "")) if structured else ""
        )
        transcript_nodes = response.css(".video-transcript.body-text")
        blocks = []
        supported = len(transcript_nodes) == 1
        if supported:
            children = transcript_nodes[0].xpath("./*")
            supported = bool(children) and all(node.root.tag.lower() == "p" for node in children)
            if supported:
                blocks = [
                    _normalized_text(node.xpath(".//text()").getall())
                    for node in children
                ]
                if blocks and not blocks[-1]:
                    blocks.pop()
                supported = all(blocks)
        body = "\n\n".join(blocks)
        body_hash = sha256(body.encode("utf-8")).hexdigest()
        abstract_values = response.css('meta[name="description"]::attr(content)').getall()
        keyword_values = response.css('meta[name="news_keywords"]::attr(content)').getall()
        authors = list(dict.fromkeys(
            _normalized_text(node.xpath(".//text()").getall())
            for node in response.css(".post__byline-name-unhyphenated")
        ))
        author = "; ".join(authors) or "未注明"
        complete = bool(
            len(metadata_title) == 1
            and len(source) == 1
            and source[0] == "PBS News"
            and title == metadata_title[0] == reviewed[1]
            and visible_date == structured_date == reviewed[0]
            and len(published_values) == 1
            and _publication_date("", published_values[0]) == reviewed[0]
            and structured is not None
            and structured.get("headline") == reviewed[1]
            and len(transcript_nodes) == 1
            and supported
            and len(body) == reviewed[2]
            and body_hash == reviewed[3]
            and bool(blocks)
            and blocks[-1] == reviewed[4]
            and author == reviewed[5]
        )
        if not complete:
            return {"decision": decision, "evidence": evidence, "material": None}

        abstract = abstract_values[0].strip() if len(abstract_values) == 1 else ""
        keywords = PBS_REVIEWED_VIDEO_KEYWORDS.get(response.url) or (
            keyword_values[0].strip() if len(keyword_values) == 1 else ""
        )
        material = VerifiedMaterial(
            source=source[0],
            time=reviewed[0],
            author=reviewed[5],
            title=reviewed[1],
            abstract=abstract,
            keywords=keywords,
            body=body,
            source_url=response.url,
        )
        evidence = SourceEvidence(
            response.url,
            fetched_at,
            response.status,
            digest,
            body_complete=True,
            metadata_verified=True,
            body_format="source_text",
        )
        field_sources = {name: response.url for name in ("source", "time", "author", "title")}
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


class PBSProgramTranscriptAdapter:
    """Verify an individually reviewed PBS program page and its full transcript."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(response.url, fetched_at, response.status, digest)
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        reviewed = PBS_REVIEWED_PROGRAM_TRANSCRIPTS.get(response.url)
        if reviewed is None:
            return {"decision": decision, "evidence": evidence, "material": None}

        expected_date, expected_title, expected_length, expected_hash, final_marker, abstract, keywords = reviewed
        title_values = response.css('meta[property="og:title"]::attr(content)').getall()
        document_titles = response.css("title::text").getall()
        structured_nodes = []
        for raw in response.css('script[type="application/ld+json"]::text').getall():
            try:
                value = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and value.get("@type") == "TVEpisode":
                structured_nodes.append(value)
        structured = structured_nodes[0] if len(structured_nodes) == 1 else {}
        visible_dates = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in response.css("h1")
        ]
        parsed_date = datetime.strptime(expected_date, "%Y-%m-%d").date()
        expected_visible_date = f"{parsed_date.strftime('%B')} {parsed_date.day}, {parsed_date.year}"
        transcript_nodes = response.css('div[class*="transcript_text"]')
        blocks = []
        supported = len(transcript_nodes) == 1
        if supported:
            children = transcript_nodes[0].xpath("./*")
            supported = bool(children) and all(node.root.tag.lower() == "p" for node in children)
            if supported:
                blocks = [
                    _normalized_text(node.xpath(".//text()").getall())
                    for node in children
                ]
                supported = all(blocks)
        body = "\n\n".join(blocks)
        body_hash = sha256(body.encode("utf-8")).hexdigest()
        complete = bool(
            len(title_values) == 1
            and title_values[0] == expected_title
            and len(document_titles) == 1
            and _normalized_text(document_titles) == f"{expected_title} | PBS"
            and len(structured_nodes) == 1
            and structured.get("url") == response.url
            and structured.get("datePublished") == expected_date
            and structured.get("name") == expected_visible_date
            and visible_dates == [expected_visible_date, expected_visible_date]
            and len(transcript_nodes) == 1
            and supported
            and len(body) == expected_length
            and body_hash == expected_hash
            and body.endswith(final_marker)
            and "CHINA" in body.upper()
            and "TAIWAN" in body.upper()
        )
        if not complete:
            return {"decision": decision, "evidence": evidence, "material": None}

        material = VerifiedMaterial(
            source="PBS",
            time=expected_date,
            author="未注明",
            title=expected_title,
            abstract=abstract,
            keywords=keywords,
            body=body,
            source_url=response.url,
        )
        evidence = SourceEvidence(
            response.url,
            fetched_at,
            response.status,
            digest,
            body_complete=True,
            metadata_verified=True,
            body_format="source_text",
        )
        field_sources = {name: response.url for name in ("source", "time", "title")}
        field_sources["abstract"] = response.url
        field_sources["keywords"] = response.url
        field_sources["author"] = response.url
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": field_sources,
            "abstract_origin": "derived",
        }


class FrontlineTankManTranscriptAdapter:
    """Extract the published transcript body from FRONTLINE's legacy Tank Man page."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status, response.text)
        paragraphs = response.css("div.mainarea div.stdbody p")
        texts = [_normalized_text(node.xpath(".//text()").getall()) for node in paragraphs]
        air_dates = [text for text in texts if text.startswith("Air date:")]
        writer_credits = [
            text for text in texts
            if text == "Written, produced and directed by Antony Thomas"
        ]
        posted = _normalized_text(response.css("b.global_date::text").getall())
        posted_match = re.fullmatch(r"(?i)posted ([A-Z][a-z]{2})\. (\d{1,2}), (\d{4})", posted)
        try:
            posted_date = datetime.strptime(
                f"{posted_match.group(1)}. {posted_match.group(2)}, {posted_match.group(3)}",
                "%b. %d, %Y",
            ).date().isoformat()
        except (AttributeError, ValueError):
            posted_date = ""
        air_match = re.fullmatch(r"Air date: ([A-Z][a-z]+ \d{1,2}, \d{4})", air_dates[0]) if len(air_dates) == 1 else None
        try:
            air_date = datetime.strptime(air_match.group(1), "%B %d, %Y").date().isoformat()
        except (AttributeError, ValueError):
            air_date = ""
        title_nodes = [text for text in texts if text == "THE TANK MAN"]
        title_meta = response.css("title::text").get(default="")
        author_meta = response.css('meta[name="author"]::attr(content)').get(default="").strip()
        start_index = next(
            (i + 1 for i, text in enumerate(texts)
             if text == "Written, produced and directed by Antony Thomas"),
            None,
        )
        end_index = next(
            (i for i, text in enumerate(texts)
             if i > (start_index or -1) and text == "The Tank Man"),
            None,
        )
        body_parts = texts[start_index:end_index] if start_index is not None and end_index is not None else []
        body_parts = [part for part in body_parts if part]
        body = "\n\n".join(body_parts)
        complete = bool(
            decision is AccessDecision.ALLOW
            and response.url == candidate.source_url
            and len(paragraphs) >= 5
            and len(air_dates) == 1 and air_date and posted_date == air_date
            and len(writer_credits) == 1 and title_nodes
            and title_meta == "Transcript | The Tank Man | FRONTLINE | PBS"
            and author_meta == "FRONTLINE"
            and start_index is not None and end_index is not None
            and body_parts and body_parts[0].startswith("ANNOUNCER:")
            and body_parts[-1].startswith("Prof. XIAO QIANG:")
            and all(part for part in body_parts)
        )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source="FRONTLINE (WGBH/PBS)",
                time=air_date,
                author="Antony Thomas",
                title="THE TANK MAN",
                abstract=("据正文整理：节目通过天安门现场报道者、研究者及相关人士的叙述，"
                          "回顾1989年抗议与镇压，并讨论媒体自由、信息审查及坦克人形象的传播。"),
                keywords="Tiananmen Square; media freedom; information censorship; Tank Man",
                body=body,
                source_url=response.url,
            )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title", "abstract", "keywords")
            }
            result["abstract_origin"] = "derived"
        return result


class CarnegieResearchArticleAdapter:
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
        spec = CARNEGIE_REVIEWED_ARTICLES.get(response.url)
        if decision is not AccessDecision.ALLOW or spec is None:
            return {"decision": decision, "evidence": evidence, "material": None}

        hero_sections = response.xpath(
            "//main/section[contains(concat(' ', normalize-space(@class), ' '), ' bg-grey/60 ')]"
        )
        hero = hero_sections[0] if len(hero_sections) == 1 else None
        title = _normalized_text(hero.css("h2").xpath(".//text()").getall()) if hero else ""
        citation_title = response.css("meta[name='citation_title']::attr(content)").get(default="").strip()
        structured = _find_jsonld_article(response)
        structured_title = _normalized_text([str(structured.get("headline", ""))]) if structured else ""
        author_line_nodes = hero.xpath(".//span[normalize-space(.)='By']/parent::*") if hero else []
        author_line = _normalized_text(author_line_nodes.xpath(".//text()").getall()) if len(author_line_nodes) == 1 else ""
        author = re.sub(r"\s+,", ",", author_line.removeprefix("By ")) if author_line.startswith("By ") else ""
        visible_date_text = " ".join(hero.xpath(".//text()").getall()) if hero else ""
        visible_date_match = re.search(
            r"Published on\s+([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})", visible_date_text
        )
        try:
            visible_date = datetime.strptime(visible_date_match.group(1), "%b %d, %Y").date().isoformat()
        except (AttributeError, ValueError):
            visible_date = ""
        structured_date = str(structured.get("datePublished", "")) if structured else ""
        try:
            structured_day = datetime.strptime(structured_date, "%b %d, %Y").date().isoformat()
        except ValueError:
            structured_day = ""
        citation_date = response.css("meta[name='citation_publication_date']::attr(content)").get(default="").strip()
        citation_day = _publication_date("", citation_date)
        structured_author_value = structured.get("author") if structured else None
        structured_authors = (
            [_jsonld_name(value) for value in structured_author_value]
            if isinstance(structured_author_value, list)
            else [_jsonld_name(structured_author_value)] if structured_author_value else []
        )
        visible_authors = [name.strip() for name in author.split(",") if name.strip()]

        body_sections = []
        for section in response.xpath(
            "//main//section[contains(concat(' ', normalize-space(@class), ' '), ' order-1 ')]"
        ):
            nodes = section.xpath(
                ".//*[self::h3 or self::h4 or self::h5 or self::p or self::li[not(.//p)]]"
            )
            headings = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in nodes if node.root.tag.lower() in {"h3", "h4", "h5"}
            ]
            if not headings or headings[0].casefold().startswith("about the authors"):
                continue
            parts = []
            for node in nodes:
                text = _normalized_text(node.xpath(".//text()").getall()).replace("\u200b", "").strip()
                if not text:
                    continue
                if node.root.tag.lower() in {"h3", "h4", "h5"} and text.casefold().startswith("about the author"):
                    break
                parts.append(text)
            if parts:
                body_sections.append(parts)
        body_parts = [part for section in body_sections for part in section]
        body = "\n\n".join(body_parts)
        body_digest = sha256(body.encode("utf-8")).hexdigest()
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        complete = bool(
            hero
            and title == str(spec["title"])
            and citation_title == title
            and structured_title == title
            and source == "Carnegie Endowment for International Peace"
            and author == str(spec["authors"])
            and len(visible_authors) == len(structured_authors)
            and set(visible_authors) == set(structured_authors)
            and visible_date == str(spec["published_on"])
            and structured_date == str(spec["structured_date"])
            and structured_day == visible_date
            and citation_date == str(spec["citation_date"])
            and citation_day == visible_date
            and abstract == str(spec["abstract"])
            and len(body_sections) == int(spec["body_sections"])
            and len(body_parts) == int(spec["body_blocks"])
            and body_parts[0].startswith(str(spec["first_body_prefix"]))
            and body_parts[-1].startswith(str(spec["last_body_prefix"]))
            and body_digest == str(spec["body_sha256"])
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=source,
                time=visible_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=str(spec["keywords"]),
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title", "abstract")
            }
            result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = "publisher"
        return result


class PRCLeadershipMonitorArticleAdapter:
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
        spec = PRCLEADER_REVIEWED_ARTICLES.get(response.url)
        if decision is not AccessDecision.ALLOW or spec is None:
            return {"decision": decision, "evidence": evidence, "material": None}

        expected_title = str(spec["title"])
        articles = [
            article
            for article in response.css("article")
            if _normalized_text(article.css("h1").xpath(".//text()").getall()) == expected_title
        ]
        article = articles[0] if len(articles) == 1 else None
        title = _normalized_text(article.css("h1").xpath(".//text()").getall()) if article else ""
        structured = _find_jsonld_article(response)
        structured_title = _normalized_text([str(structured.get("headline", ""))]) if structured else ""
        structured_author = _jsonld_name((structured.get("author") or "")) if structured else ""
        structured_date = str(structured.get("datePublished", "")) if structured else ""
        page_title = response.css("meta[property='og:title']::attr(content)").get(default="").strip()
        site_name = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        author = _normalized_text(article.css("[data-hook='user-name']").xpath(".//text()").getall()) if article else ""
        visible_date = _normalized_text(article.css("[data-hook='time-ago']").xpath(".//text()").getall()) if article else ""
        try:
            publication_date = datetime.strptime(visible_date, "%b %d, %Y").date().isoformat()
        except ValueError:
            publication_date = ""

        body_sections = []
        if article:
            for section in article.css("section"):
                paragraphs = section.css("p")
                normalized = [
                    _normalized_text(node.xpath(".//text()").getall()).replace("\u200b", "").strip()
                    for node in paragraphs
                ]
                body_parts = [part for part in normalized if part]
                if body_parts and body_parts[0].startswith(str(spec["first_body_prefix"])):
                    if body_parts[-1].casefold().startswith("photo credit:"):
                        body_parts.pop()
                    body_sections.append(body_parts)
        body_parts = body_sections[0] if len(body_sections) == 1 else []
        body = "\n\n".join(body_parts)
        body_digest = sha256(body.encode("utf-8")).hexdigest()
        complete = bool(
            article
            and title == expected_title
            and structured_title == expected_title
            and page_title == expected_title + " | China Leadership Monitor"
            and site_name == "China Leadership"
            and author == str(spec["author"])
            and structured_author == author
            and publication_date == str(spec["published_on"])
            and structured_date == str(spec["structured_date"])
            and len(body_parts) == int(spec["body_paragraphs"])
            and body_parts[0].startswith(str(spec["first_body_prefix"]))
            and body_parts[-1].startswith(str(spec["last_body_prefix"]))
            and body_digest == str(spec["body_sha256"])
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source="China Leadership Monitor",
                time=publication_date,
                author=author,
                title=title,
                abstract=str(spec["abstract"]),
                keywords=str(spec["keywords"]),
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            result["field_sources"].update({"abstract": response.url, "keywords": response.url})
            result["abstract_origin"] = "derived"
        return result


class BrookingsArticleAdapter:
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
        title = _normalized_text(response.css("h1").xpath(".//text()").getall())
        structured_title = _normalized_text(
            [html.unescape(str(article.get("headline", "")))]
        ) if article else ""
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        publication_date = _publication_date(
            "", str(article.get("datePublished", "")) if article else ""
        )
        visible_authors = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in response.css(".byo-block.authors span.name")
        ]
        visible_authors = list(dict.fromkeys(name for name in visible_authors if name))
        if visible_authors:
            author = ", ".join(visible_authors)
        else:
            author_value = (article.get("creator") or article.get("author") or "") if article else ""
            if isinstance(author_value, list):
                author = ", ".join(name for name in (_jsonld_name(value) for value in author_value) if name)
            else:
                author = _jsonld_name(author_value)

        blocks = response.css(
            ".byo-blocks.article-content > .byo-block.wysiwyg-block:not(.medium):not(.border-t):not(.archived)"
        )
        body_parts = []
        footnote_parts = []
        footnotes_seen = False
        structure_valid = True
        article_roots = response.css(".byo-blocks.article-content")
        if len(article_roots) != 1 or article_roots[0].xpath("./text()[normalize-space()]"):
            structure_valid = False
        for sibling in article_roots.xpath("./*"):
            classes = set(sibling.attrib.get("class", "").split())
            if sibling.root.tag.lower() == "aside" and "sidebar" in classes:
                continue
            if "footnotes" in classes:
                footnotes_seen = True
                if footnote_parts:
                    structure_valid = False
                source_notes = []
                expected_text = []
                for section in sibling.css(".accordion > .accordion-item"):
                    headings = section.css("a .h3")
                    content = section.css(":scope > .accordion-content")
                    if len(headings) != 1 or len(content) != 1:
                        structure_valid = False
                        continue
                    heading = _normalized_text(headings[0].xpath(".//text()").getall())
                    nodes = content[0].xpath(".//*[self::p or self::li[not(.//p)] or self::h2 or self::h3]")
                    texts = [_normalized_text(n.xpath(".//text()").getall()) for n in nodes]
                    if (not texts or _normalized_text(texts) != _normalized_text(content[0].xpath(".//text()").getall())
                            or content[0].xpath(".//table|.//img|.//iframe|.//video|.//audio|.//object")):
                        structure_valid = False
                    footnote_parts.extend([heading, *texts])
                    expected_text.extend([heading, *texts])
                    source_notes.extend(texts)
                if not source_notes:
                    structure_valid = False
                for tooltip in sibling.css("[role='tooltip']"):
                    tooltip_text = _normalized_text(tooltip.xpath(".//text()").getall())
                    expected_text.append(tooltip_text)
                    if tooltip_text not in source_notes:
                        structure_valid = False
                if (_normalized_text(expected_text) != _normalized_text(sibling.xpath(".//text()").getall())
                        or sibling.xpath(".//table|.//img|.//iframe|.//video|.//audio|.//object")):
                    structure_valid = False
                continue
            if "wysiwyg-block" in classes or classes & {"authors", "related-content"}:
                if footnotes_seen and "wysiwyg-block" in classes and not classes & {"medium", "border-t", "archived"}:
                    structure_valid = False
                continue
            if (_normalized_text(sibling.xpath(".//text()").getall())
                    or sibling.xpath(".//table|.//img|.//iframe|.//video|.//audio|.//svg|.//object")):
                structure_valid = False
        for block in blocks:
            nodes = block.xpath(
                ".//*[self::p or self::h2 or self::h3 or self::li[not(.//p)] "
                "or self::blockquote[not(.//p)] "
                "or self::strong[ancestor::div[contains(@class,'editors-note')]]]"
            )
            parts = [
                text
                for node in nodes
                if (text := _normalized_text(node.xpath(".//text()").getall()))
            ]
            if (_normalized_text(parts) != _normalized_text(block.xpath(".//text()").getall())
                    or block.xpath(".//table|.//img|.//iframe|.//object|.//video|.//script|.//svg")):
                structure_valid = False
            body_parts.extend(parts)
        body_parts.extend(footnote_parts)
        body = "\n\n".join(body_parts)
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        publisher_abstract = bool(abstract)
        reviewed_abstract = _reviewed_brookings_abstract(response.url, body)
        abstract = abstract or reviewed_abstract
        keywords = _reviewed_brookings_keywords(response.url, body)

        has_expansion_control = bool(response.css(".show-more-btn"))
        has_download = any(
            "download" in _normalized_text(node.xpath(".//text()").getall()).casefold()
            for node in response.css("a")
        )

        complete = bool(
            source == "Brookings"
            and title
            and title == structured_title
            and publication_date
            and author
            and blocks
            and body
            and structure_valid
            and not (has_expansion_control and has_download)
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = (
                "publisher" if publisher_abstract else "derived" if reviewed_abstract else "none"
            )
            result["keywords_origin"] = "derived" if keywords else "none"
        return result


class CSISArticleAdapter:
    source_name = "Center for Strategic and International Studies (CSIS)"

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

        title_nodes = response.css("h1")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        document_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        column = response.css("#block-ts-csis-content .layout--columns-article .column--first")
        byline = _normalized_text(column.css(".byline-block").xpath(".//text()").getall())
        author_match = re.search(
            r"(?:Commentary|Analysis|Brief|Report|Congressional Testimony)\s+by\s+(.+?)(?:\s+Published\s+|$)",
            byline,
            flags=re.IGNORECASE,
        )
        date_match = re.search(
            r"Published\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            byline,
            flags=re.IGNORECASE,
        )
        author = _normalized_text([author_match.group(1)]) if author_match else ""
        publication_date = _publication_date(date_match.group(1) if date_match else "", "")

        blocks = column.xpath(
            "./div[contains(concat(' ',normalize-space(@class),' '),' text-block ') "
            "or contains(concat(' ',normalize-space(@class),' '),' quote-block ') "
            "or contains(concat(' ',normalize-space(@class),' '),' block--migrated-content ')]"
        )
        body_parts = []
        body_finished = False
        migrated_structure_valid = True
        has_migrated = any("block--migrated-content" in b.attrib.get("class", "").split() for b in blocks)
        if has_migrated:
            known_blocks = {"article-hero-block", "byline-block", "downloads-block", "text-block", "quote-block", "block--migrated-content", "content-footer-block"}
            for sibling in column.xpath("./*"):
                if not (set(sibling.attrib.get("class", "").split()) & known_blocks):
                    if (_normalized_text(sibling.xpath(".//text()").getall())
                            or sibling.xpath(".//table|.//img|.//iframe|.//video|.//audio|.//svg|.//object")):
                        migrated_structure_valid = False
        for block_index, block in enumerate(blocks):
            migrated = "block--migrated-content" in block.attrib.get("class", "").split()
            containers = block.css(".wysiwyg-wrapper") or block.css("blockquote")
            if migrated and len(containers) != 1:
                migrated_structure_valid = False
            if has_migrated and _normalized_text(block.xpath(".//text()").getall()) != _normalized_text([
                _normalized_text(n.xpath(".//text()").getall()) for n in containers
            ]):
                migrated_structure_valid = False
            if has_migrated and block.xpath(".//table|.//img|.//iframe|.//object|.//script|.//svg|.//video|.//audio|.//embed|.//canvas"):
                migrated_structure_valid = False
            for container in containers:
                nodes = container.xpath(
                    ".//*[self::p or self::h2 or self::h3 or self::h4 "
                    "or self::li[not(.//p)] or self::blockquote[not(.//p)]]"
                )
                if has_migrated:
                    # A migrated preview with a separate report download is not
                    # evidence that the page includes the report in full.
                    if column.css(".downloads-block a[href]"):
                        migrated_structure_valid = False
                    consumed = [_normalized_text(node.xpath(".//text()").getall()) for node in nodes]
                    if (_normalized_text(consumed) != _normalized_text(container.xpath(".//text()").getall())
                            or container.xpath(".//table|.//img|.//iframe|.//object|.//script|.//svg|.//video|.//audio|.//embed|.//canvas")):
                        migrated_structure_valid = False
                    for position, text in enumerate(consumed):
                        if _is_csis_author_bio(text, author) and any(consumed[position + 1:]):
                            migrated_structure_valid = False
                for node in nodes:
                    text = _normalized_text(node.xpath(".//text()").getall())
                    if not text:
                        continue
                    if re.match(r"^For additional .+ studies see:?$", text, flags=re.IGNORECASE):
                        if has_migrated:
                            migrated_structure_valid = False
                        body_finished = True
                        break
                    if node.root.tag.lower() == "p" and _is_csis_author_bio(text, author):
                        if has_migrated and any(_normalized_text(b.xpath(".//text()").getall()) for b in blocks[block_index + 1:]):
                            migrated_structure_valid = False
                        body_finished = True
                        break
                    body_parts.append(text)
                if body_finished:
                    break
            if body_finished:
                break
        body = "\n\n".join(body_parts)
        raw_keywords = _reviewed_csis_keywords(response.url, body)
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()

        complete = bool(
            title
            and title == document_title
            and len(column) == 1
            and author
            and publication_date
            and blocks
            and body
            and migrated_structure_valid
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=self.source_name,
                time=publication_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=raw_keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if raw_keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = "publisher" if abstract else "none"
            result["keywords_origin"] = "derived" if raw_keywords else "none"
        return result

class NationalSecurityArchiveAdapter:
    source_name = "National Security Archive"

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

        if (urlsplit(response.url).hostname or "").lower() == "nsarchive2.gwu.edu":
            return self._extract_legacy(response, decision, evidence)

        title_nodes = response.css("h1")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        document_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        title_matches = document_title == f"{title} | National Security Archive"
        date_nodes = response.css("time[datetime]::attr(datetime)").getall()
        date_text = date_nodes[0] if len(date_nodes) == 1 else ""
        publication_date = _publication_date("", date_text)
        body_nodes = response.css(
            "#block-nsarchive-mainpagecontent .field--name-body.field__item"
        )
        body_parts = []
        if len(body_nodes) == 1:
            body_parts = [
                text
                for node in body_nodes.xpath(
                    ".//*[self::p or self::h2 or self::h3 or self::h4 "
                    "or self::li[not(.//p)] or self::blockquote[not(.//p)]]"
                )
                if (text := _normalized_text(node.xpath(".//text()").getall()))
            ]
        body = "\n\n".join(body_parts)
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        raw_keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        abstract, raw_keywords, abstract_origin, keywords_origin = _nsarchive_metadata_fields(
            response.url, body, abstract, raw_keywords
        )
        complete = bool(title and title_matches and publication_date and body_nodes and body)

        material = None
        if complete:
            material = VerifiedMaterial(
                source=self.source_name,
                time=publication_date,
                author="未注明",
                title=title,
                abstract=abstract,
                keywords=raw_keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            result["field_sources"]["author"] = response.url
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if raw_keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = abstract_origin
            result["keywords_origin"] = keywords_origin
        return result

    def _extract_legacy(
        self,
        response: Response,
        decision: AccessDecision,
        initial_evidence: SourceEvidence,
    ) -> dict:
        # This legacy site declares ISO-8859-1 but serves Windows-1252 punctuation.
        response = response.replace(encoding="cp1252")
        title_nodes = response.css("h1")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        document_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        page_text = _normalized_text(response.css("#content").xpath(".//text()").getall())
        date_match = re.search(
            r"Published\s*[\-–—]\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            page_text,
            flags=re.IGNORECASE,
        )
        publication_date = _publication_date(date_match.group(1) if date_match else "", "")
        article_nodes = response.css("#article")
        if not article_nodes:
            return self._extract_legacy_table_layout(response, initial_evidence)
        body_parts = []
        if len(article_nodes) == 1:
            nodes = article_nodes.xpath(
                ".//*[self::p or self::h2 or self::h3 or self::h4 or self::center "
                "or self::blockquote[not(.//p)] or self::li[not(.//p)] "
                "or self::sup[not(ancestor::p)]]"
            )
            body_parts = [
                text
                for node in nodes
                if (text := _normalized_text(node.xpath(".//text()").getall()))
            ]
        body = "\n\n".join(body_parts)
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        if abstract == title:
            abstract = ""
        raw_keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        abstract, raw_keywords, abstract_origin, keywords_origin = _nsarchive_metadata_fields(
            response.url, body, abstract, raw_keywords
        )
        complete = bool(
            title
            and document_title == title
            and publication_date
            and len(article_nodes) == 1
            and body
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=self.source_name,
                time=publication_date,
                author="未注明",
                title=title,
                abstract=abstract,
                keywords=raw_keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=initial_evidence.fetched_at,
            status_code=response.status,
            content_sha256=initial_evidence.content_sha256,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if raw_keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = abstract_origin
            result["keywords_origin"] = keywords_origin
        return result

    def _extract_legacy_table_layout(
        self,
        response: Response,
        initial_evidence: SourceEvidence,
    ) -> dict:
        page_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        paragraphs = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in response.css("body table p")
        ]
        paragraphs = [text for text in paragraphs if text]
        title = next(
            (
                text
                for text in paragraphs
                if text == page_title or text.startswith(page_title + " ")
            ),
            paragraphs[0] if paragraphs else "",
        )
        author_match = next(
            (
                match
                for text in paragraphs
                if (match := re.match(r"(?:by|edited by)\s+(.+)", text, flags=re.IGNORECASE))
            ),
            None,
        )
        author = author_match.group(1).strip() if author_match else ""
        source_index = next(
            (
                i
                for i, text in enumerate(paragraphs)
                if "National Security Archive Electronic Briefing Book" in text
            ),
            -1,
        )
        header_text = " ".join(paragraphs[: source_index + 5]) if source_index >= 0 else ""
        date_match = re.search(
            r"Posted\s*[\-–—]\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            header_text,
            flags=re.IGNORECASE,
        )
        if date_match is None:
            date_match = next(
                (
                    match
                    for text in paragraphs[: source_index + 5]
                    if (match := re.fullmatch(r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text))
                ),
                None,
            )
        publication_date = _publication_date(date_match.group(1) if date_match else "", "")
        source_label = any(
            "National Security Archive Electronic Briefing Book" in text
            for text in paragraphs
        )
        quote_nodes = response.xpath("//blockquote[.//p and not(ancestor::blockquote)]")
        body_parts = []
        if len(quote_nodes) == 1:
            body_parts = [
                text
                for node in quote_nodes.xpath(
                    ".//*[self::p or self::h2 or self::h3 or self::h4 or self::li[not(.//p)]]"
                )
                if (text := _normalized_text(node.xpath(".//text()").getall()))
            ]
        body = "\n\n".join(body_parts)
        abstract, raw_keywords, abstract_origin, keywords_origin = _nsarchive_metadata_fields(
            response.url, body, "", ""
        )
        complete = bool(
            page_title
            and (title == page_title or title.startswith(page_title + " "))
            and author
            and publication_date
            and source_label
            and len(quote_nodes) == 1
            and body
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=self.source_name,
                time=publication_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=raw_keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=initial_evidence.fetched_at,
            status_code=response.status,
            content_sha256=initial_evidence.content_sha256,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {
            "decision": AccessDecision.ALLOW,
            "evidence": evidence,
            "material": material,
        }
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if raw_keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = abstract_origin
            result["keywords_origin"] = keywords_origin
        return result


class RFAArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        site_names = response.css("meta[property='og:site_name']::attr(content)").getall()
        titles = response.css("h1").xpath(".//text()").getall()
        structured_titles = response.css("meta[property='og:title']::attr(content)").getall()
        date_nodes = response.css("time.c-date.b-rfa-date[datetime]")
        sections = response.css("section.b-rfa-right-rail-article__main")
        articles = sections.css("article.b-article-body") if len(sections) == 1 else []

        source = _normalized_text(site_names) if len(site_names) == 1 else ""
        title = _normalized_text(titles)
        structured_title = _normalized_text(structured_titles)
        visible_date = _normalized_text(date_nodes[0].xpath(".//text()").getall()) if len(date_nodes) == 1 else ""
        structured_date = date_nodes[0].attrib.get("datetime", "").strip() if len(date_nodes) == 1 else ""
        publication_date = _publication_date(visible_date, "")
        structured_publication_date = _publication_date("", structured_date)
        dates_match = publication_date == structured_publication_date or _rfa_utc_rollover(
            publication_date, structured_date
        )

        body_blocks = []
        if len(articles) == 1:
            for node in articles[0].xpath("./*"):
                tag = node.root.tag.lower()
                if tag in {"p", "h2", "h3", "blockquote"}:
                    value = _normalized_text(node.xpath(".//text()").getall())
                    if value:
                        body_blocks.append(value)
                elif tag in {"ul", "ol"}:
                    body_blocks.extend(
                        value for value in (
                            _normalized_text(item.xpath(".//text()").getall())
                            for item in node.xpath("./li")
                        ) if value
                    )

        author = ""
        author_nodes = response.css("meta[name='author']::attr(content)").getall()
        if len(author_nodes) == 1:
            author = _normalized_text(author_nodes)
        else:
            byline_nodes = response.css(".b-byline__names::text, .c-attribution::text").getall()
            if len(byline_nodes) == 1:
                author = re.sub(r"^By\s+", "", _normalized_text(byline_nodes), flags=re.IGNORECASE)
        if not author and body_blocks:
            byline_match = re.fullmatch(
                r"Reported by\s+(.+?)(?:\.)?", body_blocks[-1], flags=re.IGNORECASE
            )
            if byline_match:
                author = byline_match.group(1).strip()
                body_blocks.pop()

        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        raw_keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        keywords = "; ".join(part.strip() for part in raw_keywords.split(",") if part.strip())
        body = "\n\n".join(body_blocks)
        reviewed_keywords = _reviewed_rfa_keywords(response.url, body)
        publisher_keywords = bool(keywords)
        keywords = keywords or reviewed_keywords
        complete = bool(
            source == "Radio Free Asia"
            and title
            and title == structured_title
            and publication_date
            and dates_match
            and len(sections) == 1
            and len(articles) == 1
            and body
        )
        material = None
        if complete:
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
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = "publisher" if abstract else "none"
            result["keywords_origin"] = "publisher" if publisher_keywords else "derived" if keywords else "none"
        return result


class VOANewsArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        article = _find_jsonld_article(response)
        headings = response.css("h1")
        page_title = _normalized_text(headings[0].xpath(".//text()").getall()) if len(headings) == 1 else ""
        headline = _normalized_text([str(article.get("headline", ""))]) if article else ""
        if not article or not headline or not page_title:
            return {"decision": decision, "evidence": evidence, "material": None}
        if headline != page_title:
            structured_url = str(article.get("url", "")).strip()
            social_title = _normalized_text(
                response.css("meta[property='og:title']::attr(content)").getall()
            )
            if structured_url != response.url or social_title != headline:
                return {"decision": decision, "evidence": evidence, "material": None}

        publisher = article.get("publisher") or {}
        if isinstance(publisher, list):
            publisher = publisher[0] if publisher else {}
        source = _normalized_text([str(publisher.get("name", ""))]) if isinstance(publisher, dict) else ""
        author_value = article.get("author") or ""
        if isinstance(author_value, list):
            author = ", ".join(name for name in (_jsonld_name(value) for value in author_value) if name)
            author_descriptions = [str(value.get("description", "")).strip() for value in author_value if isinstance(value, dict)]
        else:
            author = _jsonld_name(author_value)
            author_descriptions = [str(author_value.get("description", "")).strip()] if isinstance(author_value, dict) else []
        visible_author = _normalized_text(response.css(".authors-highlights").xpath(".//text()").getall())
        if author and visible_author and author not in visible_author:
            return {"decision": decision, "evidence": evidence, "material": None}

        published_times = response.css("time[pubdate][datetime]")
        visible_times = response.css("time[datetime]")
        if len(published_times) == 1:
            visible_datetime = published_times[0].attrib.get("datetime", "").strip()
        elif not published_times and len(visible_times) == 1:
            visible_datetime = visible_times[0].attrib.get("datetime", "").strip()
        else:
            visible_datetime = ""
        publication_date = _publication_date("", visible_datetime)
        structured_datetime = str(article.get("datePublished", ""))
        if not publication_date or not _same_publication_instant(visible_datetime, structured_datetime):
            publication_date = ""

        body_containers = response.css("#article-content > .wsw")
        if not body_containers:
            body_containers = response.css(".article-body > .container.wsw")
        body_blocks = []
        dateline_blocks = set()
        if len(body_containers) == 1:
            for block in body_containers.xpath("./*"):
                tag = block.root.tag.lower()
                classes = block.attrib.get("class", "").split()
                if tag == "span" and "dateline" in classes:
                    value = _normalized_text(block.xpath(".//text()").getall())
                    dateline_blocks.add(value)
                elif tag in {"p", "h2", "h3", "blockquote"}:
                    value = _normalized_text(block.xpath(".//text()").getall())
                elif tag in {"ul", "ol"}:
                    items = [_normalized_text(item.xpath(".//text()").getall()) for item in block.xpath("./li")]
                    value = "\n".join(f"• {item}" for item in items if item)
                else:
                    continue
                if (
                    value.startswith("For more information, please call VOA Public Relations at ")
                    or value.endswith(" contributed to this report.")
                ):
                    continue
                if value and value not in author_descriptions:
                    body_blocks.append(value)
            if not body_blocks:
                body_blocks = _voa_br_separated_body(
                    body_containers[0].root, set(author_descriptions)
                )
        body = "\n\n".join(body_blocks)
        substantive_blocks = [block for block in body_blocks if block not in dateline_blocks]
        if not substantive_blocks:
            body_blocks = _voa_br_separated_body(
                body_containers[0].root, set(author_descriptions)
            ) if len(body_containers) == 1 else []
            body = "\n\n".join(body_blocks)
            substantive_blocks = [block for block in body_blocks if block not in dateline_blocks]
        abstract = str(article.get("description", "")).strip()
        if not abstract:
            abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        abstract_origin = "publisher" if abstract else "none"
        if not abstract:
            abstract = _pmc_derived_abstract("\n\n".join(substantive_blocks))
            if abstract:
                abstract_origin = "derived"
        raw_keywords = response.css("meta[name='keywords']::attr(content)").get(default="").strip()
        keyword_parts = [part.strip() for part in raw_keywords.split(",") if part.strip()]
        keyword_parts = [
            part for part in keyword_parts
            if part.casefold() not in {"lessons of the day", "as it is"}
        ]
        keywords = VOA_REVIEWED_KEYWORDS.get(response.url) or "; ".join(keyword_parts)
        if not keywords:
            keywords = _voa_derived_keywords(page_title, body)
        complete = bool(
            source
            and page_title
            and publication_date
            and len(body_containers) == 1
            and body
            and substantive_blocks
        )

        material = None
        if complete:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author=author or "未注明",
                title=page_title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if abstract:
                result["field_sources"]["abstract"] = response.url
            if keywords:
                result["field_sources"]["keywords"] = response.url
            result["abstract_origin"] = abstract_origin
        return result


def _voa_br_separated_body(root, author_descriptions: set[str]) -> list[str]:
    blocks = []
    parts = []
    excluded_classes = {"wsw__embed", "vjs-player", "video-js", "content-sharing"}

    def flush() -> None:
        value = _normalized_text(parts)
        if value and value != "<!-- IMAGE -->" and value not in author_descriptions:
            blocks.append(value)
        parts.clear()

    def visit(node, is_root: bool = False) -> None:
        tag = node.tag.lower() if isinstance(node.tag, str) else ""
        classes = set(node.attrib.get("class", "").split())
        if classes.intersection(excluded_classes):
            flush()
            return
        is_block = tag in {"p", "h2", "h3", "blockquote", "li"}
        if is_block and not is_root:
            flush()
        if node.text:
            parts.append(node.text)
        for child in node:
            child_tag = child.tag.lower() if isinstance(child.tag, str) else ""
            if child_tag == "br":
                flush()
            else:
                visit(child)
            if child.tail:
                parts.append(child.tail)
        if is_block and not is_root:
            flush()

    visit(root, is_root=True)
    flush()
    return blocks


def _voa_derived_keywords(title: str, body: str) -> str:
    source_text = f"{title}\n{body}".casefold()
    phrases = (
        "United States-China relations", "U.S.-China relations", "public diplomacy",
        "public opinion", "media coverage", "media framing", "international broadcasting",
        "strategic communication", "information operations", "influence operations",
        "information warfare", "social media", "disinformation", "misinformation",
        "propaganda", "artificial intelligence", "export controls", "trade dispute",
        "trade war", "Chinese products", "tariffs", "semiconductors", "chips", "election",
        "China", "United States", "Taiwan", "Hong Kong",
        "Xinjiang", "Tiananmen",
    )
    return "; ".join(phrase for phrase in phrases if phrase.casefold() in source_text)


class TrumanLibraryPublicPaperAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        titles = [
            _normalized_text(heading.xpath(".//text()").getall())
            for heading in response.css("h1")
        ]
        titles = [value for value in titles if value]
        title = titles[0] if len(titles) == 1 else ""
        body_containers = response.css(
            "article.node--type-official-document .field--name-body"
        )
        if not body_containers:
            body_containers = response.css(".node__content > .field--name-body")
        body_blocks = _br_separated_paragraphs(body_containers[0]) if len(body_containers) == 1 else []
        publication_fields = response.css(
            ".field--name-field-publication-date, time[itemprop='datePublished']"
        )
        publication_value = ""
        if len(publication_fields) == 1:
            publication_value = (
                publication_fields[0].attrib.get("datetime")
                or _normalized_text(publication_fields[0].xpath(".//text()").getall())
            )
        if not publication_value:
            publication_value = (
                response.css("meta[property='article:published_time']::attr(content)").get()
                or response.css("meta[itemprop='datePublished']::attr(content)").get()
                or ""
            )
        publication_date = _publication_date("", publication_value)
        if (
            not publication_date
            and body_blocks
            and response.url in TRUMAN_LIBRARY_VISIBLE_PUBLICATION_DATE_URLS
        ):
            visible_date = body_blocks[0]
            publication_date = _publication_date(visible_date, "")
            if publication_date:
                body_blocks = body_blocks[1:]

        footer_text = _normalized_text(response.css("footer").xpath(".//text()").getall())
        source = (
            "Harry S. Truman Library & Museum"
            if "Harry S. Truman Library & Museum" in footer_text
            else ""
        )
        body = "\n\n".join(body_blocks)
        complete = bool(source and title and publication_date and body_containers and body)
        material = None
        if complete:
            abstract, keywords = _reviewed_truman_library_metadata(response.url, body)
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author="未注明",
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url
                for name in ("source", "time", "author", "title", "abstract", "keywords")
            }
            result["abstract_origin"] = "derived" if material.abstract else "none"
        return result


class BushLibraryPublicPaperAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        articles = response.css("article.node--type-public-papers")
        title_nodes = response.css("h1.page-title")
        date_nodes = articles.css(".field--name-field-public-papers-date .field__item") if len(articles) == 1 else []
        body_nodes = articles.css(".field--name-body") if len(articles) == 1 else []
        title = _normalized_text(title_nodes[0].xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        visible_date = _normalized_text(date_nodes[0].xpath(".//text()").getall()) if len(date_nodes) == 1 else ""
        try:
            publication_date = datetime.strptime(visible_date, "%m/%d/%Y").date().isoformat()
        except ValueError:
            publication_date = ""
        body_blocks = [
            _normalized_text(paragraph.xpath(".//text()").getall())
            for paragraph in body_nodes[0].css(":scope > p")
        ] if len(body_nodes) == 1 else []
        body = "\n\n".join(block for block in body_blocks if block)
        page_title = _normalized_text(response.css("head > title::text").getall())
        source = page_title.rpartition(" | ")[2]
        reviewed_metadata = BUSH41_REVIEWED_METADATA.get(response.url)
        abstract, keywords = reviewed_metadata or ("", "")
        complete = bool(
            source == "George H.W. Bush Presidential Library and Museum"
            and title
            and publication_date
            and len(articles) == len(title_nodes) == len(date_nodes) == len(body_nodes) == 1
            and body_blocks
            and all(body_blocks)
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author="未注明",
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if reviewed_metadata:
                result["field_sources"].update({"abstract": response.url, "keywords": response.url})
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result


class TrumpWhiteHouseStatementAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        title_nodes = response.css("h1")
        date_nodes = response.css("time")
        body_containers = response.css(".page-content__content.editor")
        title = _normalized_text(title_nodes[0].xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        visible_date = _normalized_text(date_nodes[0].xpath(".//text()").getall()) if len(date_nodes) == 1 else ""
        publication_date = _publication_date(visible_date, "")
        body_blocks = [
            _normalized_text(paragraph.xpath(".//text()").getall())
            for paragraph in body_containers[0].xpath("./p")
        ] if len(body_containers) == 1 else []
        body = "\n\n".join(block for block in body_blocks if block)
        page_title = _normalized_text(response.css("head > title::text").getall())
        source = re.split(r"\s+[–-]\s+", page_title)[-1]
        complete = bool(
            source == "The White House"
            and title
            and publication_date
            and len(title_nodes) == len(date_nodes) == len(body_containers) == 1
            and body_blocks
            and all(body_blocks)
            and "END" in body_blocks
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author="未注明",
                title=title,
                abstract="",
                keywords="",
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            reviewed_abstract, reviewed_keywords = _reviewed_trump_whitehouse_metadata(
                response.url, body
            )
            if reviewed_abstract and reviewed_keywords:
                material = replace(material, abstract=reviewed_abstract, keywords=reviewed_keywords)
                result["material"] = material
                result["field_sources"].update({"abstract": response.url, "keywords": response.url})
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result


class HistoricHansardAdapter:
    """Whole published debate section; reject unhandled structures/subsections."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        from copy import deepcopy
        from parsel import Selector

        decision = classify_response(response.url, response.status, response.text)
        evidence = SourceEvidence(
            response.url, datetime.now(timezone.utc).isoformat(), response.status,
            sha256(response.body).hexdigest(),
        )
        result = {"decision": decision, "evidence": evidence, "material": None}
        if decision is not AccessDecision.ALLOW or candidate.source_category != "government":
            return result
        roots = response.css("div#content")
        headings = [_normalized_text(n.xpath(".//text()").getall()) for n in response.css("h1")]
        title = headings[0] if len(headings) == 1 else ""
        citations = roots[0].css(":scope > cite.section") if len(roots) == 1 else []
        citation = _normalized_text(citations[0].xpath(".//text()").getall()) if len(citations) == 1 else ""
        date_match = re.match(r"^(?:HC|HL) Deb (\d{2} [A-Za-z]+ \d{4}) vol ", citation)
        try:
            day = datetime.strptime(date_match.group(1), "%d %B %Y") if date_match else None
        except ValueError:
            day = None
        path_match = re.fullmatch(
            r"/historic-hansard/(?:commons|lords|written-answers|written-statements)/(\d{4})/([a-z]{3})/(\d{2})/[^/]+/?",
            urlsplit(response.url).path,
        )
        page_title = _normalized_text(response.xpath("string(//title)").getall())
        date_valid = bool(
            day and path_match
            and path_match.groups() == (day.strftime("%Y"), day.strftime("%b").lower(), day.strftime("%d"))
            and page_title == f"{title} (Hansard, {day.day} {day:%B %Y})"
        )
        source_valid = response.css("meta::attr(author)").getall() == ["UK Parliament"]
        blocks = []
        structure_valid = len(roots) == 1
        contributions = []
        inline_tags = {"a", "em", "strong", "b", "i", "u", "s", "sup", "sub", "span", "br", "small", "abbr", "cite", "q"}

        def cleaned(node):
            cloned = deepcopy(node.root)
            for link in cloned.xpath('.//a[contains(concat(" ",normalize-space(@class)," ")," permalink ")]'):
                link.drop_tree()
            return Selector(root=cloned)

        def paragraph_text(node):
            if any(child.root.tag.lower() not in inline_tags for child in node.xpath(".//*")):
                return None
            return _normalized_text(node.xpath(".//text()").getall())

        if len(roots) == 1:
            if roots[0].xpath("./text()[normalize-space()]"):
                structure_valid = False
            for node in roots[0].xpath("./*"):
                tag, attrs = node.root.tag.lower(), node.attrib
                classes = attrs.get("class", "").split()
                if tag == "cite" and "section" in classes:
                    continue
                if tag == "a" and "permalink" in classes:
                    continue
                if tag == "div" and attrs.get("id") == "section-navigation":
                    continue
                if tag == "ol" and "xoxo" in classes and not node.xpath("./*") and not _normalized_text(node.xpath(".//text()").getall()):
                    continue
                if tag == "p" and "procedural" in classes:
                    text = paragraph_text(cleaned(node))
                    if text is None:
                        structure_valid = False
                    elif text:
                        blocks.append(text)
                    continue
                if tag != "div" or "member_contribution" not in classes:
                    structure_valid = False
                    continue
                contributions.append(node)
                quotes = node.xpath('./blockquote[contains(concat(" ",normalize-space(@class)," ")," contribution_text ")]')
                if len(quotes) != 1 or node.xpath("./text()[normalize-space()]"):
                    structure_valid = False
                    continue
                for sibling in node.xpath("./*"):
                    if sibling.root is quotes[0].root:
                        continue
                    if sibling.root.tag.lower() == "a" and not sibling.xpath("./*") and not _normalized_text(sibling.xpath(".//text()").getall()):
                        continue
                    structure_valid = False
                quote = cleaned(quotes[0])
                authors = quote.css(":scope > cite.member.author")
                if len(authors) != 1 or quote.xpath("./text()[normalize-space()]"):
                    structure_valid = False
                header = []
                paragraph_count = 0
                for part in quote.xpath("./*"):
                    part_tag, part_classes = part.root.tag.lower(), part.attrib.get("class", "").split()
                    if (part_tag == "cite" and "member" in part_classes) or (part_tag == "span" and ({"question_no", "member_constituency"} & set(part_classes))):
                        if paragraph_count:
                            structure_valid = False
                        text = paragraph_text(part)
                        if text is None:
                            structure_valid = False
                        elif text:
                            header.append(text)
                    elif part_tag == "p":
                        if header:
                            blocks.append(" ".join(header))
                            header = []
                        text = paragraph_text(part)
                        if text is None or not text:
                            structure_valid = False
                        else:
                            blocks.append(text)
                            paragraph_count += 1
                    else:
                        structure_valid = False
                if header or not paragraph_count:
                    structure_valid = False
        body = "\n\n".join(block for block in blocks if block)
        complete = bool(source_valid and title and date_valid and structure_valid and contributions and body)
        if not complete:
            return result
        # The Hansard citation, URL and title establish a sitting date, not
        # independently the publication day. Historic daily parts were normally
        # published the following morning. Do not infer a date or promote this
        # extracted text until exact publication evidence is available.
        result.update({
            "evidence": replace(evidence, body_complete=True, metadata_verified=False, original_page_verified=True),
            "extracted_body": body,
            "pending_reason": "Exact publication date unverified; Hansard sitting date is not publication evidence.",
        })
        return result


class FRUSDocumentAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        containers = response.css("#content-container > .content > .tei-div3")
        title_nodes = containers.css(":scope > .tei-head7") if len(containers) == 1 else []
        title = _frus_node_text(title_nodes[0]) if len(title_nodes) == 1 else ""
        footer_text = _normalized_text(response.css("footer").xpath(".//text()").getall())
        logo_alts = {value.strip() for value in response.css("img::attr(alt)").getall()}
        source = (
            "Office of the Historian, U.S. Department of State"
            if "Office of the Historian" in logo_alts
            and "United States Department of State" in footer_text
            else ""
        )
        body_blocks = _frus_document_blocks(containers[0]) if len(containers) == 1 else []
        body = "\n\n".join(body_blocks)
        # FRUS datelines establish when the historical document was written,
        # not when it was published. This layout has no independently verified
        # exact publication date, so preserve evidence without promoting a row.
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=bool(source and title and body),
            metadata_verified=False,
            body_format="source_text",
        )
        return {"decision": decision, "evidence": evidence, "material": None}


class WorldJPNAchesonSpeechAdapter:
    source_url = "https://worldjpn.net/documents/texts/docs/19500112.S1E.html"
    metadata_url = "https://history.state.gov/historicaldocuments/frus1950v03/d572"
    final_sentence = (
        "It is not a decision which a friend or even an enemy from the outside can decide for them."
    )

    def extract(
        self,
        response: Response,
        candidate: MaterialCandidate,
        metadata_response: Response | None,
    ) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        fetched_at = datetime.now(timezone.utc).isoformat()
        body_digest = sha256(response.body).hexdigest()
        base_evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=body_digest,
            body_format="source_text",
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": base_evidence, "material": None}

        children = response.css("body > *")
        values = [(_normalized_text(node.xpath(".//text()").getall()), node) for node in children]
        title_values = [value.removeprefix("[Title]").strip() for value, _ in values if value.startswith("[Title]")]
        source_values = [value.removeprefix("[Source]").strip() for value, _ in values if value.startswith("[Source]")]
        full_text_markers = [node for value, node in values if value == "[Full text]"]

        title_label = title_values[0] if len(title_values) == 1 else ""
        title_match = re.fullmatch(
            r"Secretary of State (Dean G\. Acheson)'s speech, (Crisis in Asia - An Examination of U\.S\. Policy)",
            title_label,
        )
        title = title_match.group(2) if title_match else ""
        author = title_match.group(1) if title_match else ""
        source_citation = source_values[0] if len(source_values) == 1 else ""
        issue_date_match = re.fullmatch(
            r"Department of State Bulletin, XXII, No\.?\s*551\s*\(January 23, 1950\),\s*pp\.?\s*111-118\.",
            source_citation,
            flags=re.IGNORECASE,
        )
        publication_date = "1950-01-23" if issue_date_match else ""

        body_nodes = full_text_markers[0].xpath("following-sibling::p") if len(full_text_markers) == 1 else []
        body_blocks = [
            _normalized_text(node.xpath(".//text()").getall()) for node in body_nodes
        ]
        body = "\n\n".join(block for block in body_blocks if block)

        metadata_text = ""
        metadata_decision = None
        metadata_verified = False
        if metadata_response is not None:
            metadata_decision = classify_response(
                metadata_response.url, metadata_response.status, metadata_response.text
            )
            metadata_text = _normalized_text(
                metadata_response.css("#content-container").xpath(".//text()").getall()
                or metadata_response.css("body").xpath(".//text()").getall()
            )
            metadata_verified = bool(
                metadata_decision is AccessDecision.ALLOW
                and metadata_response.url == candidate.metadata_url == self.metadata_url
                and (urlsplit(metadata_response.url).hostname or "").lower() == "history.state.gov"
                and all(term in metadata_text.casefold() for term in (
                    "acheson", "national press club", "january 12, 1950",
                    "department of state bulletin", "january 23, 1950", "111",
                ))
            )

        complete = bool(
            response.url == candidate.source_url == self.source_url
            and title and author and issue_date_match
            and len(title_values) == len(source_values) == len(full_text_markers) == 1
            and len(body_blocks) >= 70
            and len(body) >= 30000
            and body.endswith(self.final_sentence)
        )
        material = None
        result = {
            "decision": decision,
            "evidence": replace(
                base_evidence,
                body_complete=complete,
                metadata_verified=False,
            ),
            "material": None,
            "supporting_evidence": [],
        }
        if metadata_response is not None:
            result["supporting_evidence"].append({
                "evidence": SourceEvidence(
                    source_url=metadata_response.url,
                    fetched_at=fetched_at,
                    status_code=metadata_response.status,
                    content_sha256=sha256(metadata_response.body).hexdigest(),
                    metadata_verified=metadata_verified,
                    body_format="source_text",
                ),
                "raw_response": metadata_response.body,
                "decision": metadata_decision,
            })

        if complete and metadata_verified:
            material = VerifiedMaterial(
                source="U.S. Department of State",
                time=publication_date,
                author=author,
                title=title,
                abstract=(
                    "据正文整理：演讲讨论美国与亚洲各国人民的关系、美国对亚洲的政策、"
                    "中国局势、共产主义、太平洋安全及美国援助的限度。"
                ),
                keywords="Asia policy; China; public opinion; press; radio; Pacific security",
                body=body,
                source_url=response.url,
            )
            result.update({
                "material": material,
                "field_sources": {
                    "source": metadata_response.url,
                    "time": metadata_response.url,
                    "author": response.url,
                    "title": response.url,
                    "abstract": response.url,
                    "keywords": response.url,
                },
                "abstract_origin": "derived",
            })
        return result


class PresidencyProjectDocumentAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        documents = response.css(".node.node-documents.view-mode-full")
        titles = documents.css(".field-ds-doc-title") if len(documents) == 1 else []
        date_nodes = (
            documents.css(".field-docs-start-date-time .date-display-single")
            if len(documents) == 1
            else []
        )
        body_nodes = documents.css(".field-docs-content") if len(documents) == 1 else []
        title = _normalized_text(titles[0].xpath(".//text()").getall()) if len(titles) == 1 else ""
        visible_date = _normalized_text(date_nodes[0].xpath(".//text()").getall()) if len(date_nodes) == 1 else ""
        structured_date = date_nodes[0].attrib.get("content", "").strip() if len(date_nodes) == 1 else ""
        visible_publication_date = _publication_date(visible_date, "")
        structured_publication_date = _publication_date("", structured_date)
        publication_date = visible_publication_date
        notes = _normalized_text(documents.css(".field-docs-footnote").xpath(".//text()").getall()) if len(documents) == 1 else ""
        date_valid = bool(publication_date and publication_date == structured_publication_date)
        if re.search(r"(?:this document|original document) is undated", notes, flags=re.I):
            date_valid = False
        release_pairs = re.findall(
            r"Released\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})\.\s+Dated\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            notes,
        )
        if release_pairs:
            released_dates = {_publication_date(released, "") for released, _ in release_pairs}
            dated_dates = {_publication_date(dated, "") for _, dated in release_pairs}
            if (len(released_dates) != 1 or not all(released_dates)
                    or dated_dates != {visible_publication_date}
                    or min(released_dates) < visible_publication_date):
                date_valid = False
            else:
                publication_date = next(iter(released_dates))
        body_parts = _presidency_body_blocks(body_nodes[0]) if len(body_nodes) == 1 else None
        body = "\n\n".join(part for part in (body_parts or []) if part)
        body_structure_valid = body_parts is not None
        author_nodes = documents.css(".field-docs-person .diet-title a") if len(documents) == 1 else []
        citation = _normalized_text(documents.css(".ucsbapp_citation").xpath(".//text()").getall()) if len(documents) == 1 else ""
        author = _normalized_text(author_nodes[0].xpath(".//text()").getall()) if len(author_nodes) == 1 else ""
        if not author or not citation.startswith(author + ", "):
            author = "未注明"
        page_title = _normalized_text(response.xpath("//title/text()").getall())
        complete = bool(
            title
            and publication_date
            and date_valid
            and len(documents) == len(titles) == len(date_nodes) == len(body_nodes) == 1
            and body
            and body_structure_valid
            and page_title.endswith(" | The American Presidency Project")
        )
        material = None
        if complete:
            reviewed_metadata = _reviewed_presidency_metadata(response.url, body)
            abstract = reviewed_metadata[0] if reviewed_metadata else _presidency_derived_abstract(body)
            keywords = reviewed_metadata[1] if reviewed_metadata else _presidency_derived_keywords(body)
            material = VerifiedMaterial(
                source="The American Presidency Project",
                time=publication_date,
                author=author,
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if reviewed_metadata:
                result["field_sources"].update(
                    {name: response.url for name in ("abstract", "keywords")}
                )
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "derived" if abstract else "none"
                if abstract:
                    result["field_sources"]["abstract"] = response.url
                if keywords:
                    result["field_sources"]["keywords"] = response.url
                    result["keywords_origin"] = "derived"
        return result


def _presidency_paragraph_text(paragraph) -> str:
    from copy import deepcopy

    node = deepcopy(paragraph.root)
    for br in node.iter("br"):
        br.text = "\n"
    for child in node.iter("p"):
        if child is not node:
            child.text = "\n\n" + (child.text or "")
            child.tail = "\n\n" + (child.tail or "")
    text = "".join(node.itertext())
    return "\n".join(" ".join(line.split()) for line in text.split("\n")).strip()


def _presidency_body_blocks(container) -> list[str] | None:
    if container.xpath("./text()[normalize-space()] | .//script | .//iframe | .//img | .//object"):
        return None
    blocks = []
    inline = {"a", "b", "strong", "i", "em", "u", "br", "span", "sup", "sub", "font"}
    for node in container.xpath("./*"):
        tag = node.root.tag.lower()
        if tag in {"p", "h2", "h3", "h4", "h5", "h6", "center"}:
            if any(child.root.tag.lower() not in inline for child in node.xpath(".//*")):
                return None
            blocks.append(_presidency_paragraph_text(node))
        elif tag in {"ul", "ol"}:
            if node.xpath("./*[not(self::li)] | ./text()[normalize-space()]"):
                return None
            for entry in node.xpath("./li"):
                if any(child.root.tag.lower() not in inline for child in entry.xpath(".//*")):
                    return None
                blocks.append(_presidency_paragraph_text(entry))
        elif tag == "table":
            if any(child.root.tag.lower() not in inline | {"p", "tr", "tbody", "thead", "tfoot", "td", "th"}
                   for child in node.xpath(".//*")):
                return None
            for row in node.xpath("./tr | ./tbody/tr | ./thead/tr | ./tfoot/tr"):
                values = []
                for cell in row.xpath("./td | ./th"):
                    if any(child.root.tag.lower() not in inline | {"p"} for child in cell.xpath(".//*")):
                        return None
                    values.append(_presidency_paragraph_text(cell))
                if values:
                    blocks.append("\t".join(values))
            if not node.xpath("./tr | ./tbody/tr | ./thead/tr | ./tfoot/tr"):
                return None
        else:
            return None
    return blocks


def _presidency_derived_keywords(body: str) -> str:
    terms = (
        "China", "Chinese", "Taiwan", "Formosa", "Peking", "Beijing",
        "Taiwan Strait", "Sino-American", "people's republic of China",
        "public opinion", "public diplomacy", "international broadcasting",
        "Voice of America", "propaganda", "psychological warfare",
        "political warfare", "information operations", "strategic communication",
        "foreign policy", "Korean War", "Tiananmen", "Hong Kong", "Xinjiang",
    )
    body_folded = body.casefold()
    return "; ".join(term for term in terms if term.casefold() in body_folded)


def _presidency_derived_abstract(body: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]
    summary = " ".join(paragraphs[:2])
    if len(summary) > 420:
        summary = summary[:420].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"据正文整理：{summary}" if summary else ""


class PMCFulTextArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        main_nodes = response.css("main#main-content")
        cloud_articles = main_nodes.css("article[lang]:not(.sub-article)") if len(main_nodes) == 1 else []
        content_root = cloud_articles[0] if len(cloud_articles) == 1 else (
            main_nodes[0] if len(main_nodes) == 1 and not cloud_articles else None
        )
        title_nodes = content_root.css("h1") if content_root is not None else []
        citation_nodes = content_root.css(".pmc-layout__citation") if content_root is not None else []
        body_nodes = content_root.css("section.body.main-article-body") if content_root is not None else []
        abstract_sections = content_root.css("section.abstract") if content_root is not None else []
        labeled_abstracts = [
            section
            for section in abstract_sections
            if _normalized_text(
                section.xpath("./h2[1]//text() | ./h3[1]//text()").getall()
            ).casefold() == "abstract"
        ]
        abstract_nodes = labeled_abstracts if len(labeled_abstracts) == 1 else (
            abstract_sections if len(abstract_sections) == 1 and not labeled_abstracts else []
        )
        keyword_nodes = content_root.css("section.kwd-group") if content_root is not None else []

        citation_title = response.css("meta[name='citation_title']::attr(content)").getall()
        journal = response.css("meta[name='citation_journal_title']::attr(content)").getall()
        authors = [
            _normalized_text([value])
            for value in response.css("meta[name='citation_author']::attr(content)").getall()
            if _normalized_text([value])
        ]
        publication_values = response.css("meta[name='citation_publication_date']::attr(content)").getall()
        metadata_title = _normalized_text(citation_title)
        title_candidates = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in title_nodes
        ]
        title = next(
            (
                normalized
                for visible in title_candidates
                if (normalized := re.sub(r"\s*[☆*†‡§]+\s*$", "", visible)) == metadata_title
            ),
            title_candidates[0] if title_candidates else "",
        )
        journal_title = _normalized_text(journal)
        citation_date_text = _normalized_text(citation_nodes[0].xpath(".//text()").getall()) if citation_nodes else ""
        visible_date_match = re.search(r"\b(?:19|20)\d{2}\s+[A-Z][a-z]{2,8}\s+\d{1,2}\b", citation_date_text)
        visible_date = _pmc_publication_date(visible_date_match.group(0)) if visible_date_match else ""
        metadata_date = _pmc_publication_date(publication_values[0]) if len(publication_values) == 1 else ""

        abstract = "\n\n".join(
            text
            for paragraph in abstract_nodes[0].css("p")
            if not paragraph.xpath(
                "ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' kwd-group ')]"
            )
            if (text := _normalized_text(paragraph.xpath(".//text()").getall()))
        ) if len(abstract_nodes) == 1 else ""
        keyword_text = _normalized_text(keyword_nodes[0].xpath(".//text()").getall()) if len(keyword_nodes) == 1 else ""
        keyword_text = re.sub(r"^Keywords?\s*:\s*", "", keyword_text, flags=re.IGNORECASE)
        keywords = "; ".join(
            value.strip() for value in re.split(r"[,;]", keyword_text) if value.strip()
        )
        body = "\n\n".join(_pmc_body_blocks(content_root, body_nodes[0])) if len(body_nodes) == 1 else ""
        body_text = body_nodes[0].xpath(".//text()").getall() if len(body_nodes) == 1 else []
        body_tokens = re.findall(r"\w+", _normalized_text(body_text), flags=re.UNICODE)
        relevance_text = " ".join((title, abstract, keywords, body)).casefold()
        body_mentions_china = any(
            term in relevance_text
            for term in ("china", "chinese", "taiwan", "tiananmen", "hong kong", "xinjiang", "tibet")
        )
        topical_terms = (
            "media", "discourse", "propaganda", "public opinion", "public diplomacy",
            "soft power", "national image", "country image", "foreign policy",
            "international relations", "rhetoric", "narrative", "perception",
            "communication", "influence", "journalism", "news", "strategic",
            "information", "threat", "representation", "framing", "social media",
        )
        body_mentions_topic = any(term in relevance_text for term in topical_terms)
        topic_relevance_verified = body_mentions_china and body_mentions_topic
        publisher_keywords = bool(keywords)
        if not keywords:
            keywords = _reviewed_research_keywords(response.url, body)
        if not keywords:
            keywords = _pmc_derived_keywords(title, abstract, body)
        abstract_origin = "publisher" if abstract else "none"
        if not abstract:
            abstract = _pmc_derived_abstract(body)
            abstract_origin = "derived" if abstract else "none"
        complete = bool(
            title
            and title == metadata_title
            and journal_title
            and authors
            and metadata_date
            and metadata_date == visible_date
            and body
            and content_root is not None
            and title_nodes
            and citation_nodes
            and len(body_nodes) == 1
            and len(abstract_nodes) <= 1
            and len(keyword_nodes) <= 1
            and topic_relevance_verified
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source=journal_title,
                time=metadata_date,
                author=", ".join(authors),
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url
                for name in ("source", "time", "author", "title", "abstract", "keywords")
                if name != "abstract" or abstract
                if name != "keywords" or keywords
            }
            result["abstract_origin"] = abstract_origin
            result["keywords_origin"] = "publisher" if publisher_keywords else "derived" if keywords else "none"
        return result


class NatureResearchArticleAdapter:
    """Extract Nature research articles from their observed full-text layout."""

    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        fetched_at = datetime.now(timezone.utc).isoformat()
        decision = classify_response(response.url, response.status, response.text)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        title = response.css('meta[name="citation_title"]::attr(content)').get(default="").strip()
        visible_title = _normalized_text(
            response.css("h1.c-article-title").xpath(".//text()").getall()
        )
        journal = response.css(
            'meta[name="citation_journal_title"]::attr(content)'
        ).get(default="").strip()
        doi = response.css('meta[name="citation_doi"]::attr(content)').get(default="").strip()
        abstract = response.css('meta[name="description"]::attr(content)').get(default="").strip()
        abstract_sections = response.css(
            'div.c-article-body > section[aria-labelledby="Abs1"]'
        )
        abstract_visible = _normalized_text(
            abstract_sections.css(".c-article-section__content p").xpath(".//text()").getall()
        ) if len(abstract_sections) == 1 else ""

        published_dates = []
        for node in response.css("li.c-article-identifiers__item"):
            label = _normalized_text(node.xpath(".//text()").getall())
            if re.match(r"(?i)^published\s*:", label):
                published_dates.extend(node.css("time::attr(datetime)").getall())
        publication_date = ""
        if len(published_dates) == 1:
            try:
                publication_date = datetime.strptime(
                    published_dates[0], "%Y-%m-%d"
                ).date().isoformat()
            except ValueError:
                pass

        visible_authors = [
            _normalized_text(node.xpath(".//text()" ).getall())
            for node in response.css('ul[data-test="authors-list"] a[data-test="author-name"]')
        ]
        citation_authors = response.css(
            'meta[name="citation_author"]::attr(content)'
        ).getall()
        author_match = bool(visible_authors) and len(visible_authors) == len(citation_authors)
        for visible, cited in zip(visible_authors, citation_authors):
            visible_tokens = [token.casefold() for token in re.findall(r"[\w'-]+", visible)]
            cited_tokens = [token.casefold() for token in re.findall(r"[\w'-]+", cited)]
            if visible_tokens != list(reversed(cited_tokens)):
                author_match = False
                break

        main_content = response.css("div.c-article-body > div.main-content")
        references = response.css('div.c-article-body section[aria-labelledby="Bib1"]')
        introductions = response.css('div.c-article-body section[data-title="Introduction"]')
        back_matter = response.css(
            "div.c-article-body > div.u-mt-32 > "
            "section[data-title='Data availability'], "
            "div.c-article-body > div.u-mt-32 > section[aria-labelledby='Bib1']"
        )
        body_blocks = []
        roots = [*abstract_sections, *main_content]
        if main_content and len(main_content.css('section[aria-labelledby="Bib1"]')) == 0:
            roots.extend(back_matter)
        for root in roots:
            for block in root.xpath(
                ".//h2 | .//h3 | .//h4 | .//p | .//li[not(.//p)] | "
                ".//td[not(.//p)] | .//th[not(.//p)] | .//figcaption | "
                ".//blockquote[not(.//p)]"
            ):
                text = _normalized_text(block.xpath(".//text()").getall())
                if text:
                    body_blocks.append(text)
        body = "\n\n".join(body_blocks)
        license_urls = response.css('a[rel="license"]::attr(href)').getall()
        rights_text = _normalized_text(
            response.css('section[data-title="Rights and permissions"]').xpath(".//text()").getall()
        )
        open_license = any(
            "creativecommons.org/licenses/by/4.0" in value.casefold()
            for value in license_urls
        ) and "creative commons attribution 4.0 international license" in rights_text.casefold()
        complete = bool(
            response.url == candidate.source_url
            and (urlsplit(response.url).hostname or "").lower() in {"nature.com", "www.nature.com"}
            and title and visible_title == _normalized_text([title])
            and journal and doi and abstract and abstract_visible == _normalized_text([abstract])
            and publication_date and author_match and len(abstract_sections) == 1
            and len(main_content) == 1 and len(references) == 1 and len(introductions) == 1
            and body and open_license
        )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=sha256(response.body).hexdigest(),
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        material = None
        result = {"decision": decision, "evidence": evidence, "material": None}
        if complete:
            keywords = _reviewed_research_keywords(response.url, body)
            material = VerifiedMaterial(
                source=journal,
                time=publication_date,
                author="; ".join(visible_authors),
                title=title,
                abstract=abstract,
                keywords=keywords,
                body=body,
                source_url=response.url,
            )
            result.update({
                "material": material,
                "field_sources": {
                    name: response.url
                    for name in ("source", "time", "author", "title", "abstract")
                },
                "abstract_origin": "publisher",
                "keywords_origin": "derived" if keywords else "none",
            })
            if keywords:
                result["field_sources"]["keywords"] = response.url
        return result


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


def _pew_inline_text(node) -> str:
    values = node.xpath(
        ".//text()[not(ancestor::button) and not(ancestor::svg) and not(ancestor::*[@hidden])]"
    ).getall()
    return " ".join("".join(values).split())


def _pew_body_text(content) -> tuple[str, bool]:
    body_parts = []
    supported_structure = True
    for node in content.xpath("./*"):
        tag = node.root.tag.lower()
        if tag in {"p", "h2", "h3", "h4", "blockquote"}:
            text = _pew_inline_text(node)
            if text.startswith(("Related:", "For more on")) and node.xpath(".//a"):
                continue
            if text:
                body_parts.append(text)
        elif tag in {"ul", "ol"}:
            items = [_pew_inline_text(item) for item in node.xpath("./li")]
            if any(items):
                body_parts.append("\n".join(item for item in items if item))
        elif tag == "figure":
            caption = _pew_inline_text(node.css("figcaption"))
            if caption:
                body_parts.append(caption)
        elif tag == "details":
            details_parts = [
                _pew_inline_text(item)
                for item in node.xpath("./summary | .//p | .//h2 | .//h3 | .//li")
            ]
            body_parts.extend(part for part in details_parts if part)
        elif tag == "div":
            classes = set(node.attrib.get("class", "").split())
            if "wp-block-prc-block-collapsible" in classes:
                title_nodes = node.xpath(
                    "./div[contains(@class, 'wp-block-prc-block-collapsible__title')]/div[1]"
                )
                content_nodes = node.xpath(
                    "./div[contains(@class, 'wp-block-prc-block-collapsible__content')]"
                )
                children = node.xpath("./*")
                text_blocks = content_nodes[0].xpath("./*") if len(content_nodes) == 1 else []
                if (
                    len(children) != 2
                    or len(title_nodes) != 1
                    or len(content_nodes) != 1
                    or not text_blocks
                    or any(block.root.tag.lower() != "p" for block in text_blocks)
                ):
                    supported_structure = False
                    continue
                heading = _pew_inline_text(title_nodes[0])
                paragraphs = [_pew_inline_text(block) for block in text_blocks]
                body_parts.extend(part for part in [heading, *paragraphs] if part)
            elif "wp-block-group" in classes and "is-style-callout" in classes:
                children = node.xpath("./*")
                if (
                    len(children) < 2
                    or children[0].root.tag.lower() not in {"h2", "h3", "h4"}
                    or children[0].root.tag.lower() != "h4"
                    or any(child.root.tag.lower() != "p" for child in children[1:])
                ):
                    supported_structure = False
                    continue
                body_parts.extend(text for text in (_pew_inline_text(child) for child in children) if text)
            elif "wp-block-group" in classes:
                blockquotes = node.xpath("./blockquote")
                children = node.xpath("./*")
                quote_blocks = blockquotes[0].xpath("./*") if len(blockquotes) == 1 else []
                if (
                    len(children) != 1
                    or len(blockquotes) != 1
                    or not quote_blocks
                    or any(block.root.tag.lower() not in {"p", "cite"} for block in quote_blocks)
                ):
                    supported_structure = False
                    continue
                body_parts.extend(
                    text for text in (_pew_inline_text(block) for block in quote_blocks) if text
                )
            else:
                text = _pew_inline_text(node)
                if not text.startswith(("Guide to this report", "Report Materials")):
                    supported_structure = False
        else:
            supported_structure = False
    return "\n\n".join(body_parts), supported_structure


class PewResearchArticleAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        article = _find_jsonld_article(response)
        content = response.css(".entry-content.wp-block-post-content")
        title = _normalized_text(response.css("h1").xpath(".//text()").getall())
        visible_title = response.css("meta[property='og:title']::attr(content)").get(default="").strip()
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        visible_dates = response.css("article.wp-block-group time")
        visible_date = (
            _normalized_text(visible_dates[0].xpath(".//text()").getall())
            if len(visible_dates) == 1 else ""
        )
        structured_dates = response.css("meta[property='article:published_time']::attr(content)").getall()
        publication_date = _publication_date(visible_date, str(article.get("datePublished", "")) if article else "")
        authors = list(dict.fromkeys(
            _normalized_text(node.xpath(".//text()").getall())
            for node in response.css("div[class*='bylines-display'] a")
        ))
        author = ", ".join(value for value in authors if value)
        structured_authors = article.get("author", []) if article else []
        if isinstance(structured_authors, dict):
            structured_authors = [structured_authors]
        author_names = [
            _jsonld_name(value) for value in structured_authors
        ] if isinstance(structured_authors, list) else []
        publisher = article.get("publisher", {}) if article else {}
        if isinstance(publisher, list):
            publisher = publisher[0] if publisher else {}
        structured_source = _jsonld_name(publisher) if isinstance(publisher, dict) else ""
        abstract = response.css("meta[name='description']::attr(content)").get(default="").strip()
        body, supported_structure = (
            _pew_body_text(content[0]) if len(content) == 1 else ("", False)
        )
        reviewed = PEW_REVIEWED_ARTICLES.get(response.url)
        body_hash = sha256(body.encode("utf-8")).hexdigest()
        metadata_match = bool(
            reviewed
            and reviewed[:4] == (publication_date, title, author, body_hash)
            and reviewed[4]
        )
        complete = bool(
            response.url == candidate.source_url
            and source == structured_source == "Pew Research Center"
            and title
            and title == visible_title
            and len(visible_dates) == len(structured_dates) == 1
            and publication_date
            and author
            and authors == author_names
            and abstract
            and body
            and supported_structure
            and metadata_match
        )
        evidence = replace(
            evidence,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        if not complete:
            return {"decision": decision, "evidence": evidence, "material": None}

        material = VerifiedMaterial(
            source=source,
            time=publication_date,
            author=author,
            title=title,
            abstract=abstract,
            keywords=reviewed[4],
            body=body,
            source_url=response.url,
        )
        return {
            "decision": decision,
            "evidence": evidence,
            "material": material,
            "field_sources": {
                "source": response.url,
                "time": response.url,
                "author": response.url,
                "title": response.url,
                "abstract": response.url,
                "keywords": "body",
            },
            "abstract_origin": "publisher",
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
        publisher_abstract = bool(abstract)
        reviewed_abstract, reviewed_keywords = _reviewed_trump_whitehouse_metadata(
            response.url, body
        )
        abstract = abstract or reviewed_abstract
        keywords = keywords or reviewed_keywords
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
            abstract_origin = (
                "publisher" if publisher_abstract else "derived" if reviewed_abstract else "none"
            )
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


class ObamaWhiteHouseVideoTranscriptAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        title_nodes = response.css("#video-info h1[property='dc:title'], #video-info h1")
        title = _normalized_text(title_nodes[0].xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        notes = _normalized_text(response.css("#video-info .notes").xpath(".//text()").getall())
        visible_date = _normalized_text(
            response.css("#video-info .date-display-single").xpath(".//text()").getall()
        )
        if not visible_date:
            date_match = re.search(
                r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
                notes,
            )
            visible_date = date_match.group(0) if date_match else ""
        publication_date = _publication_date(visible_date, "")

        transcript = response.css("#transcript")
        body_blocks = []
        if len(transcript) == 1:
            for node in transcript.xpath("./*"):
                classes = set(node.root.attrib.get("class", "").split())
                if node.root.tag.lower() == "h2" or "more" in classes:
                    continue
                value = _normalized_text(node.xpath(".//text()").getall())
                if value:
                    body_blocks.append(value)
        body = "\n\n".join(body_blocks)
        reviewed = OBAMA_WHITEHOUSE_REVIEWED_VIDEO_TRANSCRIPTS.get(response.url)
        reviewed_body = reviewed and sha256(body.encode("utf-8")).hexdigest() == reviewed[0]
        complete = bool(
            response.css("meta[property='og:site_name']::attr(content)").get(default="").strip() == "The White House"
            and title
            and publication_date
            and len(transcript) == 1
            and body
            and reviewed
            and reviewed_body
            and publication_date == reviewed[3]
            and title == reviewed[4]
        )
        material = None
        if complete:
            material = VerifiedMaterial(
                source="The White House",
                time=publication_date,
                author="未注明",
                title=title,
                abstract=reviewed[1],
                keywords=reviewed[2],
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title", "abstract", "keywords")
            }
            result["abstract_origin"] = "derived"
            result["keywords_origin"] = "derived"
        return result


class ObamaWhiteHouseArchiveAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        decision = classify_response(response.url, response.status, response.text)
        digest = sha256(response.body).hexdigest()
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        content_start = response.css("#content-start")
        title_nodes = content_start.css("h1") if len(content_start) == 1 else []
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        source_header = _normalized_text(
            content_start.css(".press-article-heading").xpath(".//text()").getall()
        )
        source_site = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        source = (
            "The White House, Office of the Vice President"
            if "Office of the Vice President" in source_header
            else "The White House, Office of the Press Secretary"
        )
        date_nodes = content_start.css(".press-article-date") if len(content_start) == 1 else []
        visible_date = _normalized_text(date_nodes.xpath(".//text()").getall()) if len(date_nodes) == 1 else ""
        publication_date = _publication_date(visible_date, "")

        body_nodes = (
            content_start.css(".field-name-field-forall-body .field-items > .field-item")
            if len(content_start) == 1
            else []
        )
        body_parts = []
        if len(body_nodes) == 1:
            legacy_content = body_nodes.css(".legacy-content")
            if len(legacy_content) == 1:
                body_parts = [
                    text
                    for text in (
                        _normalized_text(node.xpath(".//text()").getall())
                        for node in legacy_content.css(".legacy-para")
                    )
                    if text
                ]
            standard_blocks = body_nodes.xpath(
                "./p | ./h2 | ./h3 | ./h4 | ./blockquote | ./ul/li | ./ol/li"
            )
            if standard_blocks:
                for node in standard_blocks:
                    if node.root.tag.lower() == "p":
                        body_parts.extend(_obama_archive_paragraphs(node))
                    else:
                        text = _normalized_text(node.xpath(".//text()").getall())
                        if text:
                            body_parts.append(text)
            elif not legacy_content:
                body_parts = [
                    text
                    for text in (
                        _normalized_text(node.xpath(".//text()").getall())
                        for node in body_nodes.xpath("./div")
                    )
                    if text
                ]
        body = "\n\n".join(body_parts)
        terminal_block = body_parts[-1] if body_parts else ""
        transcript_ending = bool(
            terminal_block == "END"
            or terminal_block.startswith("END ")
            or (
                len(body_parts) >= 2
                and body_parts[-2] == "END"
                and re.fullmatch(r"\d{1,2}:\d{2} [AP]\.M\. (?:[A-Z]{2,5}|\(Local\))", terminal_block)
            )
        )
        reviewed_statement = OBAMA_WHITEHOUSE_REVIEWED_STATEMENTS.get(response.url)
        statement_complete = reviewed_statement == (
            publication_date, title, sha256(body.encode("utf-8")).hexdigest()
        )
        body_metadata = _normalized_text(body_nodes.xpath(".//text()").getall()) if body_nodes else ""
        source_verified = (
            source_site.casefold() == "whitehouse.gov"
            and "The White House" in source_header
            and (
                "Office of the Press Secretary" in source_header
                or "Office of the Vice President" in source_header
                or "Office of the Press" in body_metadata
            )
        )
        complete = bool(
            source_verified
            and title
            and publication_date
            and len(date_nodes) == 1
            and len(body_nodes) == 1
            and body
            and (transcript_ending or statement_complete)
        )
        material = None
        if complete:
            reviewed_metadata = OBAMA_WHITEHOUSE_REVIEWED_METADATA.get(response.url)
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author="未注明",
                title=title,
                abstract=reviewed_metadata[0] if reviewed_metadata else "",
                keywords=reviewed_metadata[1] if reviewed_metadata else "",
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if reviewed_metadata:
                result["field_sources"].update(
                    {name: response.url for name in ("abstract", "keywords")}
                )
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result


def _obama_archive_paragraphs(node) -> list[str]:
    children = node.xpath("./node()")
    if not any(len(child.xpath("self::br")) for child in children):
        text = _normalized_text(node.xpath(".//text()").getall())
        return [text] if text else []

    paragraphs = []
    current = []
    for child in children:
        if len(child.xpath("self::br")):
            text = _normalized_text(current)
            if text:
                paragraphs.append(text)
            current = []
        else:
            value = child.get() if isinstance(child.root, str) else child.xpath("string(.)").get(default="")
            current.append(value)
    text = _normalized_text(current)
    if text:
        paragraphs.append(text)
    return paragraphs


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
        title = _normalized_text(article.css(".featured-content__headline").xpath(".//text()").getall())
        visible_date = _normalized_text(article.css(".article-meta__publish-date").xpath(".//text()").getall())
        publication_date = _publication_date(visible_date, "")
        author_text = _normalized_text(article.css(".article-meta__author-bureau").xpath(".//text()").getall())
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        body_container = content.css(".classic-block-wrapper")
        transcript_layout = not body_container and bool(article and content)
        if transcript_layout:
            body_container = content
        body_blocks = []
        if body_container:
            for block in body_container.xpath(".//p | .//h2 | .//h3 | .//blockquote | .//ul | .//ol"):
                if block.xpath(
                    "ancestor-or-self::*[contains(@class, 'vjs-') "
                    "or contains(@class, 'video-js') "
                    "or contains(@class, 'article-meta') "
                    "or contains(@class, 'featured-content') "
                    "or contains(@class, 'wp-block-tags-block') "
                    "or contains(@class, 'related-tags') "
                    "or self::p[a[contains(@href, '/translations/')]]]"
                ):
                    continue
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
        # Report landing pages expose an executive summary and link to the report.
        # The linked document, rather than this excerpt, must pass full-text review.
        summary_landing_page = bool(
            body_blocks
            and body_blocks[0].casefold() == "executive summary"
            and any(part.casefold() == "download the report" for part in body_blocks)
            and content.css("a[href]").xpath(
                "@href[contains(translate(., 'PDF', 'pdf'), '.pdf')]"
            )
        )
        if summary_landing_page:
            complete = False
        material = None
        result = {"decision": decision, "material": None}
        if complete and source:
            reviewed = STATE_REVIEWED_METADATA.get(response.url)
            if reviewed and reviewed[0] != sha256(body.encode("utf-8")).hexdigest():
                reviewed = None
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author=author_text or "未注明",
                title=title,
                abstract=reviewed[1] if reviewed else "",
                keywords=reviewed[2] if reviewed else "",
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
            if reviewed:
                result["field_sources"].update(
                    {name: response.url for name in ("abstract", "keywords")}
                )
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result


class ClintonWhiteHouseArchiveAdapter:
    def extract(self, response: Response, candidate: MaterialCandidate) -> dict:
        source_digest = sha256(response.body).hexdigest()
        if "\ufffd" in response.text:
            try:
                response.body.decode("utf-8")
            except UnicodeDecodeError:
                decoded = response.body.decode("utf-8", errors="surrogateescape")
                repaired = "".join(
                    bytes((ord(character) - 0xDC00,)).decode("windows-1252", errors="replace")
                    if 0xDC80 <= ord(character) <= 0xDCFF
                    else character
                    for character in decoded
                )
                response = HtmlResponse(
                    url=response.url,
                    request=response.request,
                    body=repaired.encode("utf-8"),
                    encoding="utf-8",
                    status=response.status,
                    headers=response.headers,
                )
        decision = classify_response(response.url, response.status, response.text)
        digest = source_digest
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=False,
            metadata_verified=False,
        )
        if decision is not AccessDecision.ALLOW:
            return {"decision": decision, "evidence": evidence, "material": None}

        if "/textonly/WH/New/" in response.url:
            return self._extract_textonly_document(response, decision, digest, fetched_at)

        transcripts = response.css("pre")
        if not transcripts:
            return self._extract_briefing_page(response, decision, digest, fetched_at)
        title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        visible_title = _normalized_text(response.css("body > center b::text").getall())
        body = transcripts.xpath("string(.)").get(default="") if len(transcripts) == 1 else ""
        body = "\n".join(
            line.strip() for line in body.replace("\r\n", "\n").replace("\r", "\n").splitlines()
        ).strip()
        release_match = re.search(
            r"For\s+Immediate\s+Release\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            body,
            flags=re.IGNORECASE,
        )
        publication_date = _publication_date(release_match.group(1), "") if release_match else ""
        complete = bool(
            len(transcripts) == 1
            and title
            and title == visible_title
            and publication_date
            and "THE WHITE HOUSE" in body
            and "Office of the Press Secretary" in body
            and re.search(r"\bEND\s+\d{1,2}:\d{2}\s+[AP]\.M\.\s+EDT\s*$", body)
        )
        material = None
        if complete:
            reviewed_metadata = _reviewed_clinton_metadata(response.url, body)
            briefing_author = re.fullmatch(
                r"Press Briefing by (.+?)\s+\(\d{1,2}/\d{1,2}/\d{2,4}\)", title
            )
            material = VerifiedMaterial(
                source="The White House, Office of the Press Secretary",
                time=publication_date,
                author=briefing_author.group(1) if briefing_author else "未注明",
                title=title,
                abstract=reviewed_metadata[0] if reviewed_metadata else "",
                keywords=reviewed_metadata[1] if reviewed_metadata else "",
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if reviewed_metadata:
                result["field_sources"].update(
                    {name: response.url for name in ("abstract", "keywords")}
                )
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result

    def _extract_briefing_page(self, response, decision, digest, fetched_at) -> dict:
        columns = response.xpath("//td[@width='354']")
        content = columns[0] if len(columns) == 1 else None
        page_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        headline_candidates = []
        if content is not None:
            for node in content.css("center"):
                value = _clinton_visible_title(page_title, node)
                if value:
                    headline_candidates.append(value)
        headline = headline_candidates[0] if len(headline_candidates) == 1 else ""
        is_work_page = "/WH/Work/" in response.url
        if is_work_page and content is not None:
            work_headlines = [
                _normalized_text(node.xpath(".//text()").getall())
                for node in content.xpath(".//font[@size='4']//b")
            ]
            work_headlines = [value for value in work_headlines if value]
            headline = work_headlines[0] if len(work_headlines) == 1 else ""
        if response.url == "https://clintonwhitehouse4.archives.gov/WH/New/html/20000308_2.html":
            headline = "The U.S.-China WTO Agreement Will Help Promote Reform, Accountability, and Openness in China"
        if not headline and page_title and content is not None:
            headline = page_title
        source_header = _normalized_text(content.xpath(".//h3//text()").getall()) if content is not None else ""
        release_date = ""
        if content is not None:
            for table in content.xpath(".//table"):
                cells = [
                    _normalized_text(cell.xpath(".//text()").getall())
                    for cell in table.xpath(".//td")
                ]
                if any(value == "For Immediate Release" for value in cells):
                    dates = [
                        match.group(0)
                        for value in cells
                        for match in re.finditer(
                            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
                            value,
                            flags=re.IGNORECASE,
                        )
                    ]
                    dates = list(dict.fromkeys(dates))
                    if len(dates) == 1:
                        release_date = dates[0]
                    break
        publication_date = _publication_date(release_date, "")

        if is_work_page:
            masthead = _normalized_text(response.xpath("//body/table[1]//text()").getall())
            visible_dates = list(dict.fromkeys(re.findall(
                r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
                masthead,
                flags=re.IGNORECASE,
            )))
            publication_date = _publication_date(visible_dates[0], "") if len(visible_dates) == 1 else ""

        body_parts = []
        footer_seen = False
        if content is not None:
            for node in content.xpath(".//p | .//li"):
                if node.root.tag.lower() == "p" and node.xpath("ancestor::li"):
                    continue
                value = _normalized_text(node.xpath(".//text()").getall())
                if not value:
                    continue
                if is_work_page and node.xpath(".//font[@size='4']"):
                    continue
                if value.startswith(("President and First Lady", "Privacy Statement")):
                    footer_seen = True
                    break
                body_parts.append(value)
        body = "\n\n".join(body_parts)
        source = "The White House" if is_work_page else "The White House, Office of the Press Secretary"
        source_valid = (
            "THE WHITE HOUSE" in _normalized_text(response.xpath("//body//text()").getall()).upper()
            if is_work_page
            else "Office of the Press Secretary" in source_header
        )
        complete = bool(
            content is not None
            and headline
            and source_valid
            and publication_date
            and body
            and footer_seen
        )
        material = None
        if complete:
            reviewed_metadata = _reviewed_clinton_metadata(response.url, body)
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author="未注明",
                title=headline,
                abstract=reviewed_metadata[0] if reviewed_metadata else "",
                keywords=reviewed_metadata[1] if reviewed_metadata else "",
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if reviewed_metadata:
                result["field_sources"].update(
                    {name: response.url for name in ("abstract", "keywords")}
                )
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result

    def _extract_textonly_document(self, response, decision, digest, fetched_at) -> dict:
        blocks = response.xpath("//blockquote")
        block = blocks[0] if len(blocks) == 1 else None
        block_text = _normalized_text(block.xpath(".//text()").getall()) if block is not None else ""
        office = "Office of the Press Secretary" in block_text
        release_match = re.search(
            r"For\s+Immediate\s+Release\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            block_text,
            flags=re.IGNORECASE,
        )
        publication_date = _publication_date(release_match.group(1), "") if release_match else ""
        center_texts = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in (block.xpath(".//center") if block is not None else [])
        ]
        title_candidates = []
        for value in center_texts:
            press_availability = re.search(
                r"(PRESS AVAILABILITY BY PRESIDENT CLINTON AND PRESIDENT JIANG)\b",
                value,
                re.I,
            )
            photo_opportunity = re.search(
                r"(REMARKS BY PRESIDENT CLINTON AND PRESIDENT JIANG ZEMIN IN PHOTO OPPORTUNITY)\b",
                value,
                re.I,
            )
            china_address = re.search(
                r"(REMARKS BY THE PRESIDENT IN ADDRESS ON CHINA AND THE NATIONAL INTEREST)\b",
                value,
                re.I,
            )
            match = press_availability or photo_opportunity or china_address
            if match:
                title_candidates.append(match.group(1))
        title = title_candidates[0] if len(title_candidates) == 1 else ""

        paragraphs = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in (block.xpath(".//p") if block is not None else [])
        ]
        paragraphs = [value for value in paragraphs if value]
        time_index = next((index for index, value in enumerate(paragraphs) if re.fullmatch(
            r"\d{1,2}:\d{2}\s+[AP]\.M\.\s*\(L\)", value, re.I
        )), None)
        is_1997_china_address = response.url == (
            "https://clintonwhitehouse4.archives.gov/textonly/WH/New/html/19971024-3863.html"
        )
        body_parts = (
            paragraphs[time_index + 1:]
            if time_index is not None
            else paragraphs if is_1997_china_address else []
        )
        body = "\n\n".join(body_parts)
        complete = bool(
            block is not None
            and office
            and publication_date
            and title
            and body
            and (
                time_index is not None
                or (
                    is_1997_china_address
                    and body.startswith("THE PRESIDENT:")
                    and body.endswith("Thank you very much. (Applause.)")
                )
            )
        )
        metadata = _reviewed_clinton_metadata(response.url, body) if complete else None
        material = VerifiedMaterial(
            source="The White House, Office of the Press Secretary",
            time=publication_date,
            author="未注明",
            title=title,
            abstract=metadata[0] if metadata else "",
            keywords=metadata[1] if metadata else "",
            body=body,
            source_url=response.url,
        ) if complete else None
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if metadata:
                result["field_sources"].update({name: response.url for name in ("abstract", "keywords")})
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result


class ClintonWhiteHouse6ArchiveAdapter:
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
        metadata_response = response.meta.get("metadata_response")
        if decision is not AccessDecision.ALLOW or metadata_response is None:
            return {"decision": decision, "evidence": evidence, "material": None}

        metadata_text = _normalized_text(metadata_response.xpath("//body//text()").getall())
        date_match = re.search(
            r"\bDate:\s*\w{3},\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\b",
            metadata_text,
            flags=re.IGNORECASE,
        )
        subject_match = re.search(r"\bSubject:\s*(.+?)(?=\s+Keywords:|\s+Message-Id:|$)", metadata_text, re.I)
        publication_date = (
            _publication_date(f"{date_match.group(2)} {date_match.group(1)}, {date_match.group(3)}", "")
            if date_match else ""
        )
        title = subject_match.group(1).strip() if subject_match else ""
        source_text = _normalized_text(response.xpath("//body//text()").getall())
        source_verified = "THE WHITE HOUSE" in source_text and "Office of the Press Secretary" in source_text
        metadata_verified = bool(
            metadata_response.url == candidate.metadata_url
            and metadata_response.status == 200
            and "From: The White House" in metadata_text
            and publication_date
            and title
        )
        time_markers = [
            index for index, node in enumerate(response.xpath("//body/p"))
            if re.fullmatch(r"\d{1,2}:\d{2}\s+[AP]\.M\.\s+EDT", _normalized_text(node.xpath(".//text()").getall()), re.I)
        ]
        end_markers = [
            index for index, node in enumerate(response.xpath("//body/p"))
            if re.fullmatch(r"END\s*\d{1,2}:\d{2}\s+[AP]\.M\.\s+EDT", _normalized_text(node.xpath(".//text()").getall()), re.I)
        ]
        paragraphs = response.xpath("//body/p")
        body_parts = []
        body_complete = False
        if len(time_markers) == 1 and len(end_markers) == 1 and end_markers[0] > time_markers[0]:
            for node in paragraphs[time_markers[0] + 1:end_markers[0]]:
                value = _normalized_text(node.xpath(".//text()").getall())
                if value:
                    body_parts.append(value)
            body_complete = bool(body_parts and body_parts[0].startswith("MR. LAKE:"))
        body = "\n\n".join(body_parts)
        complete = bool(source_verified and metadata_verified and body_complete and title)
        reviewed_metadata = _reviewed_clinton_metadata(response.url, body) if complete else None
        material = VerifiedMaterial(
            source="The White House, Office of the Press Secretary",
            time=publication_date,
            author="未注明",
            title=title,
            abstract=reviewed_metadata[0] if reviewed_metadata else "",
            keywords=reviewed_metadata[1] if reviewed_metadata else "",
            body=body,
            source_url=response.url,
        ) if complete else None
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=False,
            body_format="source_text",
        )
        metadata_evidence = SourceEvidence(
            source_url=metadata_response.url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status_code=metadata_response.status,
            content_sha256=sha256(metadata_response.body).hexdigest(),
            metadata_verified=metadata_verified,
            original_page_verified=metadata_verified,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                "source": response.url,
                "time": metadata_response.url,
                "author": response.url,
                "title": metadata_response.url,
                "abstract": "body",
                "keywords": "body",
            }
            result["abstract_origin"] = "derived" if reviewed_metadata else "none"
            result["supporting_evidence"] = [{
                "decision": decision,
                "evidence": metadata_evidence,
                "raw_response": metadata_response.body,
            }]
        return result


class ArchivedStateDepartmentRemarksAdapter:
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

        title_nodes = response.css("#page-title")
        title = _normalized_text(title_nodes.xpath(".//text()").getall()) if len(title_nodes) == 1 else ""
        document_title = _normalized_text([response.xpath("string(//head/title)").get(default="")])
        source = response.css("meta[property='og:site_name']::attr(content)").get(default="").strip()
        date_nodes = response.css("#top-meta #date_long")
        visible_date = _normalized_text(date_nodes.xpath(".//text()").getall()) if len(date_nodes) == 1 else ""
        publication_date = _publication_date(visible_date, "")
        authors = [
            _normalized_text(node.xpath(".//text()").getall())
            for node in response.css("#top-meta .officials-name")
        ]
        authors = [name for name in authors if name]
        author = "; ".join(authors) if authors else "未注明"
        body_nodes = response.css("#centerblock")
        body_parts = []
        if len(body_nodes) == 1:
            body_parts = [
                text
                for node in body_nodes.xpath(
                    ".//*[self::h2 or self::h3 or self::h4 or self::p or self::li or self::blockquote[not(.//p)]]"
                )
                if not node.xpath(
                    "ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' flex-video ')]"
                )
                if (text := _normalized_text(node.xpath(".//text()").getall()))
            ]
        body = "\n\n".join(body_parts)
        complete = bool(
            title
            and document_title == title
            and source
            and publication_date
            and len(body_nodes) == 1
            and body
        )
        material = None
        if complete:
            reviewed_metadata = ARCHIVED_STATE_REVIEWED_METADATA.get(response.url)
            material = VerifiedMaterial(
                source=source,
                time=publication_date,
                author=author,
                title=title,
                abstract=reviewed_metadata[0] if reviewed_metadata else "",
                keywords=reviewed_metadata[1] if reviewed_metadata else "",
                body=body,
                source_url=response.url,
            )
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=fetched_at,
            status_code=response.status,
            content_sha256=digest,
            body_complete=complete,
            metadata_verified=complete,
            body_format="source_text",
        )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: response.url for name in ("source", "time", "author", "title")
            }
            if reviewed_metadata:
                result["field_sources"].update(
                    {name: response.url for name in ("abstract", "keywords")}
                )
                result["abstract_origin"] = "derived"
            else:
                result["abstract_origin"] = "none"
        return result


def _normalized_text(values: list[str]) -> str:
    return " ".join(" ".join(values).split())


def _clinton_title_tokens_match(page_title: str, visible_title: str) -> bool:
    ignored = {"a", "an", "and", "by", "in", "of", "the", "to", "with"}
    page_tokens = {
        token for token in re.findall(r"[a-z0-9]+", page_title.casefold()) if token not in ignored
    }
    visible_tokens = set(re.findall(r"[a-z0-9]+", visible_title.casefold()))
    return bool(page_tokens and page_tokens.issubset(visible_tokens))


def _clinton_visible_title(page_title: str, node) -> str:
    parts = []
    for value in node.xpath(".//text()").getall():
        normalized = _normalized_text([value])
        if not normalized:
            continue
        parts.append(normalized)
        candidate = _normalized_text(parts)
        if _clinton_title_tokens_match(page_title, candidate):
            return candidate
    return ""


def _is_csis_author_bio(text: str, author: str) -> bool:
    if not re.search(
        r"\bat (?:the Center for Strategic and International Studies|CSIS)\b",
        text,
        flags=re.IGNORECASE,
    ):
        return False
    for name in re.split(r"\s*,\s*|\s+and\s+", author, flags=re.IGNORECASE):
        tokens = re.findall(r"[A-Za-z]+", name)
        if len(tokens) < 2:
            continue
        pattern = rf"^{re.escape(tokens[0])}(?:\s+[A-Z]\.?)?\s+{re.escape(tokens[-1])}\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False


def _pdf_metadata_text(value) -> str:
    return " ".join(str(value).split()) if value else ""


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


def _rfa_utc_rollover(visible_date: str, structured_date: str) -> bool:
    try:
        page_date = datetime.fromisoformat(visible_date).date()
        published_at = datetime.fromisoformat(structured_date.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (
        published_at.tzinfo is not None
        and published_at.utcoffset().total_seconds() == 0
        and (published_at.date() - page_date).days == 1
        and published_at.hour < 6
    )


def _publication_date(visible_date: str, structured_date: str) -> str:
    for value in (visible_date, structured_date):
        value = value.strip()
        try:
            return datetime.strptime(value, "%B %d, %Y").date().isoformat()
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%Y.%m.%d").date().isoformat()
        except ValueError:
            pass
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                return datetime.fromisoformat(value).date().isoformat()
            except ValueError:
                pass
        if re.match(r"^\d{4}-\d{2}-\d{2}[T ]", value):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
    return ""


def _pmc_publication_date(value: str) -> str:
    value = value.strip()
    for pattern in ("%Y %b %d", "%Y %B %d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    return ""


def _pmc_note_blocks(note) -> list[str]:
    block_tags = {"p", "li", "blockquote", "caption", "figcaption", "td", "th",
                  "h2", "h3", "h4", "ul", "ol", "table", "tr", "div", "section"}
    blocks, inline = [], []

    def flush():
        text = _normalized_text(inline)
        if text:
            blocks.append(text)
        inline.clear()

    def visit(element):
        if element.text:
            inline.append(element.text)
        for child in element:
            if not isinstance(child.tag, str):
                if child.tail:
                    inline.append(child.tail)
                continue
            boundary = child.tag.lower() in block_tags
            # A leading note label belongs with its first paragraph.
            if boundary and (blocks or not re.fullmatch(r"\d+[a-z]?|[*†‡]+", _normalized_text(inline), re.I)):
                flush()
            visit(child)
            if boundary:
                flush()
            if child.tail:
                inline.append(child.tail)

    visit(note.root)
    flush()
    return blocks


def _pmc_body_blocks(container, main_body=None) -> list[str]:
    block_tags = {"p", "li", "blockquote", "caption", "figcaption", "td", "th"}
    excluded_classes = {
        "abstract", "kwd-group", "ack", "glossary", "ref-list", "fn-group", "app",
        "notes", "associated-data",
    }
    blocks = []
    emitted = set()
    nodes = container.xpath(
        ".//*[self::h2 or self::h3 or self::h4 or self::p or self::li or self::blockquote "
        "or self::caption or self::figcaption or self::td or self::th "
        "or contains(concat(' ', normalize-space(@class), ' '), ' fn ')]"
    )
    for node in nodes:
        ancestors = node.xpath("ancestor::*")
        if "fn" in node.root.attrib.get("class", "").split():
            if any(a.root in emitted for a in ancestors):
                continue
            ancestor_classes = [set(a.root.attrib.get("class", "").split()) for a in ancestors]
            if (not any("fn-group" in classes for classes in ancestor_classes)
                    or any(classes.intersection({"abstract", "ref-list", "associated-data", "sub-article", "fn"})
                           for classes in ancestor_classes)):
                continue
            note_text = _normalized_text(node.xpath(".//text()").getall())
            if re.match(r"^(?:\d+\s*)?Publisher[’']s\s+Note\b", note_text, re.I):
                continue
            blocks.extend(_pmc_note_blocks(node))
            continue
        if main_body is not None and not any(a.root is main_body.root for a in ancestors):
            continue
        if any(
            ancestor.root.tag.lower() in block_tags
            or excluded_classes.intersection(ancestor.root.attrib.get("class", "").split())
            or _normalized_text(
                ancestor.xpath(
                    "./h2[1]//text() | ./h3[1]//text() | ./h4[1]//text()"
                ).getall()
            ).casefold() in {"references", "declarations", "footnotes", "appendix", "appendices"}
            for ancestor in ancestors
        ):
            continue
        text = _normalized_text(node.xpath(".//text()").getall())
        if text:
            blocks.append(text)
            emitted.add(node.root)
    return blocks


def _pmc_derived_keywords(title: str, abstract: str, body: str) -> str:
    source_text = f"{title}\n{abstract}\n{body}".casefold()
    phrases = (
        "United States-China relations", "U.S.-China relations", "Sino-American relations",
        "public diplomacy", "public opinion", "strategic communication", "political warfare",
        "information operations", "influence operations", "critical discourse analysis",
        "media framing", "media coverage", "media representation", "news media",
        "national image", "country image", "soft power", "sharp power", "foreign policy",
        "international broadcasting", "strategic competition", "threat perception",
        "discourse analysis", "social media", "China", "Chinese", "Taiwan", "Tiananmen",
        "Hong Kong", "Xinjiang", "Tibet", "journalism", "media", "discourse", "propaganda",
        "rhetoric", "narrative", "communication", "information", "public health", "COVID-19",
        "trade war", "semiconductors", "artificial intelligence",
    )
    return "; ".join(phrase for phrase in phrases if phrase.casefold() in source_text)[:500]


def _pmc_derived_abstract(body: str, limit: int = 420) -> str:
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", body.strip())
    selected = []
    size = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if len(re.findall(r"\w+", sentence, flags=re.UNICODE)) < 8:
            continue
        if selected and size + len(sentence) + 1 > limit:
            break
        if len(sentence) > limit and not selected:
            sentence = sentence[:limit].rsplit(" ", 1)[0]
        selected.append(sentence)
        size += len(sentence) + 1
        if len(selected) == 2:
            break
    return "据正文整理：" + " ".join(selected) if selected else ""


def _same_publication_instant(visible_datetime: str, structured_datetime: str) -> bool:
    try:
        visible = datetime.fromisoformat(visible_datetime.strip().replace("Z", "+00:00"))
        structured = datetime.fromisoformat(structured_datetime.strip().replace("Z", "+00:00"))
        difference = abs((visible - structured).total_seconds())
    except (TypeError, ValueError):
        return False
    return difference <= 7200


def _br_separated_paragraphs(container) -> list[str]:
    paragraphs = []
    current = []
    breaks = 0
    for node in container.xpath("./node()"):
        if isinstance(node.root, str):
            text = _normalized_text([node.root])
        elif node.root.tag.lower() == "br":
            breaks += 1
            continue
        else:
            text = _normalized_text(node.xpath(".//text()").getall())
        if text:
            if breaks >= 2 and current:
                paragraphs.append(_normalized_text(current))
                current = []
            current.append(text)
            breaks = 0
    if current:
        paragraphs.append(_normalized_text(current))
    return paragraphs


def _frus_document_blocks(container) -> list[str]:
    blocks = []
    for node in container.xpath("./*"):
        tag = node.root.tag.lower()
        classes = node.attrib.get("class", "").split()
        if "tei-note2" in classes:
            continue
        if tag == "section" and "tei-frus_attachment" in classes:
            blocks.extend(_frus_document_blocks(node))
        elif tag == "dl":
            for entry in node.xpath("./dt | ./dd"):
                value = _frus_node_text(entry)
                if value:
                    blocks.append(value)
        elif tag in {"h2", "h3", "h4", "p"} and any(
            value.startswith("tei-head") or value.startswith("tei-p") for value in classes
        ):
            value = _frus_node_text(node)
            if value:
                blocks.append(value)
        elif tag == "div" and ("tei-opener" in classes or "tei-dateline" in classes or "tei-closer" in classes):
            value = _frus_node_text(node)
            if value:
                blocks.append(value)
    return blocks


def _frus_node_text(node) -> str:
    return _frus_normalized_text(
        node.xpath(".//text()[not(ancestor::a[contains(concat(' ', normalize-space(@class), ' '), ' note ')])]").getall()
    )


def _frus_normalized_text(values: list[str]) -> str:
    text = _normalized_text(values)
    text = re.sub(r"\s+([,.;:!?%)\]])", r"\1", text)
    return re.sub(r"([\[(])\s+", r"\1", text)


class ReviewedScannedTranscriptPDFAdapter:
    def __init__(self, reviewed_sources: dict[str, dict[str, object]]):
        self.reviewed_sources = reviewed_sources

    def extract(
        self, response: Response, candidate: MaterialCandidate, metadata_response: Response
    ) -> dict:
        digest = sha256(response.body).hexdigest()
        decision = classify_response(response.url, response.status)
        evidence = SourceEvidence(
            source_url=response.url,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status_code=response.status,
            content_sha256=digest,
        )
        spec = self.reviewed_sources.get(response.url)
        if (
            spec is None
            or decision is not AccessDecision.ALLOW
            or not response.body.startswith(b"%PDF-")
            or response.url != candidate.source_url
            or not candidate.metadata_url
            or metadata_response.url != candidate.metadata_url
            or metadata_response.status != 200
            or digest != spec.get("pdf_sha256")
        ):
            return {"decision": decision, "evidence": evidence, "material": None}

        titles = metadata_response.css("title::text").getall()
        linked_files = []
        for node in metadata_response.css("iframe, object, embed, a"):
            for attr in ("data-src", "src", "data", "href"):
                value = node.attrib.get(attr)
                if value:
                    linked_files.append(urljoin(metadata_response.url, value))
        try:
            page_count = len(PdfReader(BytesIO(response.body)).pages)
        except Exception:
            page_count = 0

        body = str(spec.get("body", ""))
        body_matches = bool(body) and sha256(body.encode("utf-8")).hexdigest() == spec.get(
            "body_sha256"
        )
        page_date_marker = spec.get("page_date_marker")
        verified = bool(
            len(titles) == 1
            and titles[0].strip() == spec.get("page_title")
            and response.url in linked_files
            and page_count == spec.get("pages")
            and body_matches
            and isinstance(page_date_marker, str)
            and page_date_marker in titles[0]
        )
        evidence = replace(
            evidence,
            body_complete=verified,
            metadata_verified=verified,
            body_format="pdf_reviewed_transcript",
            original_page_verified=verified,
        )
        material = None
        if verified:
            material = VerifiedMaterial(
                source=str(spec["publisher"]),
                time=str(spec["published_on"]),
                author=str(spec["author"]),
                title=str(spec["title"]),
                abstract=str(spec["abstract"]),
                keywords=str(spec["keywords"]),
                body=body,
                source_url=response.url,
            )
        result = {"decision": decision, "evidence": evidence, "material": material}
        if material is not None:
            result["field_sources"] = {
                name: metadata_response.url for name in ("source", "time", "author", "title", "abstract", "keywords")
            }
            result["field_sources"]["body"] = response.url
            result["abstract_origin"] = "derived"
            result["supporting_evidence"] = [{
                "decision": AccessDecision.ALLOW,
                "evidence": SourceEvidence(
                    source_url=metadata_response.url,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    status_code=metadata_response.status,
                    content_sha256=sha256(metadata_response.body).hexdigest(),
                    metadata_verified=True,
                    original_page_verified=True,
                    body_format="source_text",
                ),
                "raw_response": metadata_response.body,
            }]
        return result


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
            if candidate.metadata_url:
                yield scrapy.Request(
                    candidate.metadata_url,
                    callback=self.parse_metadata,
                    errback=self.errback,
                    meta={"handle_httpstatus_list": HTTP_ERROR_STATUSES, "candidate": candidate},
                    dont_filter=True,
                )
                continue
            yield scrapy.Request(
                candidate.source_url,
                callback=self.parse,
                errback=self.errback,
                meta={"handle_httpstatus_list": HTTP_ERROR_STATUSES, "candidate": candidate},
                dont_filter=True,
            )

    def start_requests(self):
        for candidate in self.candidates:
            if candidate.metadata_url:
                yield scrapy.Request(
                    candidate.metadata_url,
                    callback=self.parse_metadata,
                    errback=self.errback,
                    meta={"handle_httpstatus_list": HTTP_ERROR_STATUSES, "candidate": candidate},
                    dont_filter=True,
                )
                continue
            yield scrapy.Request(
                candidate.source_url,
                callback=self.parse,
                errback=self.errback,
                meta={"handle_httpstatus_list": HTTP_ERROR_STATUSES, "candidate": candidate},
                dont_filter=True,
            )

    def parse_metadata(self, response: Response):
        candidate = response.meta["candidate"]
        yield scrapy.Request(
            candidate.source_url,
            callback=self.parse,
            errback=self.errback,
            meta={
                "handle_httpstatus_list": HTTP_ERROR_STATUSES,
                "candidate": candidate,
                "metadata_response": response,
            },
            dont_filter=True,
        )

    def errback(self, failure):
        candidate = failure.request.meta["candidate"]
        return {"candidate": candidate, "crawl_error": failure.getErrorMessage()}

    def parse(self, response: Response):
        candidate = response.meta["candidate"]
        if (
            not candidate.metadata_url
            and (urlsplit(response.url).hostname or "").lower() == "www.govinfo.gov"
            and "/content/pkg/CHRG-" in response.url
            and "/html/" in response.url
        ):
            package_match = GovInfoHearingAdapter.package_pattern.search(response.url)
            if package_match:
                metadata_url = (
                    f"https://www.govinfo.gov/app/details/"
                    f"{package_match.group(1)}/{package_match.group(1)}"
                )
                metadata_candidate = replace(candidate, metadata_url=metadata_url)
                yield scrapy.Request(
                    metadata_url,
                    callback=self.parse_govinfo_metadata,
                    errback=self.errback,
                    meta={"handle_httpstatus_list": HTTP_ERROR_STATUSES, "candidate": metadata_candidate,
                          "body_response": response},
                    dont_filter=True,
                )
                return
        result = self.adapter.extract(response, candidate)
        result["candidate"] = candidate
        result["raw_response"] = response.body
        yield result

    def parse_govinfo_metadata(self, response: Response):
        candidate = response.meta["candidate"]
        original_response = response.meta["body_response"]
        request = original_response.request.replace(
            meta={**original_response.meta, "metadata_response": response}
        )
        body_response = HtmlResponse(
            url=original_response.url,
            request=request,
            headers=original_response.headers,
            body=original_response.body,
            encoding=original_response.encoding,
            status=original_response.status,
        )
        result = self.adapter.extract(body_response, candidate)
        result["candidate"] = candidate
        result["raw_response"] = body_response.body
        yield result
