from scrapy.http import HtmlResponse
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter

URL='https://obamawhitehouse.archives.gov/the-press-office/2014/01/01/remarks'
PROSE='The United States and China must continue diplomatic negotiations and public discussions about security and peaceful relations. We will continue this work together.'


def extract(extra=''):
    raw=f'''<html><head><meta property="og:site_name" content="whitehouse.gov"></head><body>
    <div id="content-start"><h1>Remarks on China Policy</h1>
    <div class="press-article-heading">The White House Office of the Press Secretary</div>
    <div class="press-article-date">January 1, 2014</div>
    <div class="field-name-field-forall-body"><div class="field-items"><div class="field-item">
    <p>{PROSE}</p>{extra}<p>END</p></div></div></div></div></body></html>'''
    return GovernmentArticleAdapter().extract(HtmlResponse(url=URL,body=raw.encode(),encoding='utf8'),MaterialCandidate(URL,'1992-2016','government','synthetic'))


def test_plain_transcript_accounts_for_all_source_body_text():
    assert extract()['material'].body==PROSE+'\n\nEND'


def test_transcript_with_unhandled_substantive_div_is_not_complete():
    assert extract('<div>An additional paragraph about China policy must not silently disappear.</div>')['material'] is None


def test_transcript_with_unhandled_table_is_not_complete():
    assert extract('<table><tr><td>Additional source text</td></tr></table>')['material'] is None
