from scrapy.http import HtmlResponse, Request

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


def test_presidency_project_derives_keywords_only_from_document_text():
    url = "https://www.presidency.ucsb.edu/documents/test"
    html = b"""<!doctype html>
    <html><head><title>Statement | The American Presidency Project</title></head>
    <body><div class="node node-documents view-mode-full">
      <div class="field-ds-doc-title">Statement on Formosa</div>
      <div class="field-docs-start-date-time"><span property="dc:date"
        datatype="xsd:dateTime" content="1958-09-04T00:00:00+00:00"
        class="date-display-single">September 04, 1958</span></div>
      <div class="field-docs-content"><p>China and Formosa Taiwan public diplomacy.</p></div>
      <div class="field-docs-footnote"></div>
    </div></body></html>"""
    response = HtmlResponse(url=url, request=Request(url), body=html, encoding="utf-8")

    result = GovernmentArticleAdapter().extract(
        response, MaterialCandidate(url, "1949-1972", "government", "test")
    )

    assert result["material"].abstract.startswith("据正文整理：China and Formosa Taiwan public diplomacy.")
    assert result["material"].keywords == "China; Taiwan; Formosa; public diplomacy"
    assert result["abstract_origin"] == "derived"
    assert result["field_sources"]["abstract"] == url
    assert result["field_sources"]["keywords"] == url
