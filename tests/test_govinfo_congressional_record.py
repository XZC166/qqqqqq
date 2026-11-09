import json
from html import escape
import pytest
from scrapy.http import HtmlResponse, Request
from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter

PKG='CREC-1998-06-15'
G=PKG+'-PgS100-2'
U=f'https://www.govinfo.gov/content/pkg/{PKG}/html/{G}.htm'
M='https://api.govinfo.gov/search?api_key=DEMO_KEY'
TITLE='UNITED STATES RELATIONS WITH CHINA'
TEXT=f'''[Congressional Record Volume 144, Number 80 (Monday, June 15, 1998)]
[Senate]
[Pages S100-S101]
From the Congressional Record Online through the Government Publishing Office [www.gpo.gov]

                 {TITLE}

  Mr. EXAMPLE. Mr. President, the United States must discuss diplomatic relations with China and support peace across the Taiwan Strait.
[[Page S101]]
  I call on Congress to continue this debate about our policy and public diplomacy toward China. This is my final statement.

                          ____________________
'''


def extract(text=TEXT, title=TITLE, date='1998-06-15', granule=G, closed=True):
    r=dict(packageId=PKG,granuleId=granule,title=title,dateIssued=date,governmentAuthor=['Congress'],collectionCode='CREC')
    md=HtmlResponse(url=M,body=json.dumps({'results':[r]}).encode(),encoding='utf8')
    raw='<html><body><pre>'+escape(text)+('</pre></body></html>' if closed else '')
    response=HtmlResponse(url=U,body=raw.encode(),encoding='utf8',request=Request(U,meta={'metadata_response':md}))
    return GovernmentArticleAdapter().extract(response,MaterialCandidate(U,'1992-2016','government','synthetic',metadata_url=M))


def test_record_uses_actual_issue_date_and_full_original_granule():
    r=extract()
    assert r['material'] is not None
    assert r['material'].time=='1998-06-15'
    assert r['material'].title==TITLE
    assert r['material'].author=='Congress'
    assert 'final statement.' in r['material'].body
    assert '[[Page' not in r['material'].body
    assert r['supporting_evidence'][0]['evidence'].metadata_verified


@pytest.mark.parametrize('kwargs',[
    {'title':'UNRELATED TITLE'}, {'date':'1998-06-14'}, {'granule':G+'-wrong'},
    {'closed':False}, {'text':TEXT.replace('____________________','')},
    {'text':TEXT.replace('[[Page S101]]','')},
    {'text':TEXT.replace('[Pages S100-S101]','[Pages S100-S102]')},
])
def test_mismatch_or_unproven_complete_record_is_held(kwargs):
    assert extract(**kwargs)['material'] is None
