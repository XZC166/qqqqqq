"""Synthetic HTML; no publisher full text is redistributed with these tests."""
from hashlib import sha256
from html import escape

import pytest
from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.reviewed_sources import (
    PUBLIC_MEDIA_REVIEWED_ARTICLES,
    PUBLIC_MEDIA_REVIEWED_META_TITLES,
)
from research_crawler.spiders.government import ReviewedPublicMediaAdapter


URLS = (
    "https://time.com/2918689/how-to-hunt-a-chinese-hacker/",
    "https://time.com/4004397/the-china-decade/",
    "https://time.com/4644775/donald-trump-china-trade-cold-war/",
    "https://time.com/5228991/president-trumps-tariff-tussle-with-china-is-just-the-beginning/",
    "https://time.com/5759394/taiwan-election-2020/",
)


@pytest.mark.parametrize("url", URLS)
@pytest.mark.parametrize("changed", (False, True))
def test_reviewed_time_pages_drop_ads_but_require_exact_article(monkeypatch, url, changed):
    record = list(PUBLIC_MEDIA_REVIEWED_ARTICLES[url])
    # Keep the real reviewed extraction mode, replacing only fixture-specific
    # text, lengths and paragraph counts with an explicitly synthetic document.
    body = "Synthetic China policy paragraph.\n\nSynthetic final paragraph."
    record[6:8] = [str(len(body)), sha256(body.encode()).hexdigest()]
    record[10:12] = ["2", "3"]
    monkeypatch.setitem(PUBLIC_MEDIA_REVIEWED_ARTICLES, url, tuple(record))
    title = escape(record[4], quote=True)
    meta_title = escape(PUBLIC_MEDIA_REVIEWED_META_TITLES.get(url, record[4]), quote=True)
    author = escape(record[2], quote=True)
    date = record[3]
    ending = "Changed final paragraph." if changed else "Synthetic final paragraph."
    raw = f'''<html><head><title>Synthetic fixture</title>
        <meta property="og:site_name" content="TIME">
        <meta property="og:title" content="{meta_title}">
        <meta name="author" content="{author}"></head><body>
        <h1>{title}</h1><time datetime="{date}"></time><time datetime="{date}"></time>
        <article><p>Synthetic China policy paragraph.</p>
        <div data-ad-wrapper="true"><p>Advertisement</p></div>
        <p>{ending}</p></article></body></html>'''
    response = HtmlResponse(url, body=raw.encode(), encoding="utf-8")
    candidate = MaterialCandidate(url, record[0], "media", "synthetic-test")
    result = ReviewedPublicMediaAdapter().extract(response, candidate)
    if changed:
        assert result["material"] is None
    else:
        assert result["material"] is not None
        assert result["material"].body == body
        assert result["evidence"].body_complete
