from scrapy.http import HtmlResponse, Request
import pytest
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter

PKG = 'WCPD-1996-02-12'
GRANULE = PKG + '-Pg100'
URL = f'https://www.govinfo.gov/content/pkg/{PKG}/html/{GRANULE}.htm'
META = f'https://www.govinfo.gov/app/details/{PKG}/{GRANULE}'
PUBLISHER = 'Office of the Federal Register, National Archives and Records Administration'
TEXT = '''[Weekly Compilation of Presidential Documents Volume 32, Number 6 (Monday, February 12, 1996)]
[Pages 100-101]
[Online from the Government Publishing Office, www.gpo.gov]

<R04>
Remarks on United States Relations With China

 February 7, 1996

    The United States and China must discuss security and diplomatic relations.

[[Page 101]]

    We will continue these diplomatic talks. Thank you.

Note: The President spoke in Washington.
'''


def extract(text=TEXT, metadata_date='1996-02-12', title='32 WCPD 100 Remarks on United States Relations With China', closed=True, metadata_url=META):
    from html import escape
    metadata = HtmlResponse(url=metadata_url, encoding='utf-8', body=(
        f'<meta name="dc.identifier" content="{metadata_url}">'
        f'<meta name="dc.date" content="{metadata_date}">'
        f'<meta name="dc.creator" content="{PUBLISHER}">'
        f'<meta name="dc.publisher" content="{PUBLISHER}">'
        f'<meta name="dc.title" content="{title}">').encode())
    raw = '<html><body><pre>' + escape(text) + ('</pre></body></html>' if closed else '')
    response = HtmlResponse(url=URL, encoding='utf-8', body=raw.encode(), request=Request(URL, meta={'metadata_response': metadata}))
    return GovernmentArticleAdapter().extract(response, MaterialCandidate(URL, '1992-2016', 'government', 'synthetic', metadata_url=META))


def test_weekly_issue_date_is_publication_not_speech_date():
    r = extract()
    assert r['material'] is not None
    assert r['material'].time == '1996-02-12'
    assert r['material'].title == 'Remarks on United States Relations With China'
    assert r['material'].author == PUBLISHER
    assert r['material'].source == PUBLISHER
    assert '<R04>' not in r['material'].body
    assert 'February 7, 1996' in r['material'].body
    assert 'We will continue these diplomatic talks. Thank you.' in r['material'].body
    assert r['supporting_evidence'][0]['evidence'].metadata_verified


@pytest.mark.parametrize('kwargs', [
    {'metadata_date': '1996-02-07'},
    {'title': '32 WCPD 100 Unrelated remarks'},
    {'closed': False},
    {'text': TEXT.replace('[[Page 101]]', '')},
    {'text': TEXT + 'The tape was incomplete and could not be verified.'},
    {'metadata_url': META.replace('Pg100', 'Pg200')},
    {'text': TEXT.replace('[Pages 100-101]', '[Pages 100-102]')},
])
def test_unresolved_compilation_is_held(kwargs):
    assert extract(**kwargs)['material'] is None
