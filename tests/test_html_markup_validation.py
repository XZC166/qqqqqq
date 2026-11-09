from dataclasses import replace
import pytest
from research_crawler.items import SourceEvidence, VerifiedMaterial
from research_crawler.validation import validate_material, ValidationError


def check_body(body):
    url = 'https://example.org/article'
    material = VerifiedMaterial('Example Journal', '2020-05-01', 'A. Author',
                                'China policy', 'Publisher abstract', 'China', body, url)
    evidence = SourceEvidence(url, '2026-11-10T00:00:00Z', 200, 'synthetic-hash',
                              body_complete=True, metadata_verified=True)
    fields = {key: url for key in ('source', 'time', 'author', 'title', 'abstract', 'keywords')}
    return validate_material(material, evidence, fields)


@pytest.mark.parametrize('body', [
    'Citation: <Recent Developments in China Policy>, Example Journal.',
    'Citation: <US-China relations and public opinion>, Example Press.',
    'Citation: <Chinese Public Opinion on the South China Sea>, Example Review.',
])
def test_literal_angle_quoted_titles_are_preserved_verbatim(body):
    assert check_body(body).body == body


@pytest.mark.parametrize('body', [
    '<p>China policy.</p>', '<SPAN class="body">China policy.</SPAN>',
    '<custom-widget data-id="x">China policy.',
    'China policy.</custom-widget>', '<custom-widget />',
])
def test_actual_html_or_xml_markup_is_still_rejected(body):
    with pytest.raises(ValidationError, match='HTML markup'):
        check_body(body)
