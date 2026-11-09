import pytest
from research_crawler.batch_review import assess_topic

BODY='China must protect freedom of expression and human rights. These diplomatic relations and security commitments require continued negotiations and public discussion.'


@pytest.mark.parametrize('source,url',[
 ('The White House, Office of the Press Secretary','https://obamawhitehouse.archives.gov/the-press-office/2014/01/01/statement'),
 ('The White House, Office of the Vice President','https://obamawhitehouse.archives.gov/the-press-office/2014/01/01/remarks'),
 ('Office of the Federal Register, National Archives and Records Administration','https://www.govinfo.gov/content/pkg/WCPD-1996-02-12/html/WCPD-1996-02-12-Pg100.htm'),
 ('U.S. Government Publishing Office','https://www.govinfo.gov/content/pkg/CREC-2018-01-01/html/CREC-2018-01-01-PgS100.htm'),
])
def test_exact_official_source_supplies_us_context_for_substantive_policy(source,url):
    r=assess_topic(dict(source=source,source_url=url,source_category='government',title='Statement',body=BODY))
    assert r['approved']
    assert r['supporting_passages'][0]['text']==BODY


def test_official_origin_does_not_establish_topic_without_policy():
    row=dict(source='The White House, Office of the Press Secretary',source_url='https://obamawhitehouse.archives.gov/the-press-office/2014/01/01/statement',source_category='government',title='Dinner menu',body='Visitors from China enjoyed a dinner with many desserts. The garden was decorated with flowers and the evening ended with music and a photograph.')
    assert not assess_topic(row)['approved']


def test_lookalike_source_on_unrelated_site_does_not_supply_context():
    row=dict(source='The White House, Office of the Press Secretary',source_url='https://example.org/statement',source_category='government',title='Statement',body=BODY)
    assert not assess_topic(row)['approved']
