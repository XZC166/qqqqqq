from research_crawler.batch_review import assess_topic, derived_fields


def row(body, category='government', title='Policy statement', source='The American Presidency Project'):
    return dict(body=body, source_category=category, title=title, source=source,
                source_url='https://www.presidency.ucsb.edu/documents/example')


def test_presidential_policy_paragraph_is_preserved_with_offsets():
    body = 'Opening greeting.\n\nThe United States will improve relations with China through diplomatic negotiations and consultations on trade policy.'
    result = assess_topic(row(body))
    assert result['approved']
    span = result['supporting_passages'][0]
    assert body[span['start']:span['end']] == span['text']
    abstract, keywords = derived_fields(row(body), result)
    assert abstract.startswith('据正文整理：')
    assert all(term.casefold() in body.casefold() for term in keywords.split('; '))


def test_biomedical_keywords_do_not_establish_discourse_relevance():
    body = 'China and the United States conducted an international trade study of cell cultures, vaccines and viral proteins.'
    assert not assess_topic(row(body, 'research_literature', 'Nidoviruses of Fish and Crustaceans'))['approved']


def test_bibliography_is_not_topic_evidence():
    body = 'This article studies fish.\n\nReferences\n\nThe United States and China improved diplomatic relations through trade policy.'
    assert not assess_topic(row(body, 'research_literature', 'Fish biology'))['approved']


def test_social_crash_geography_does_not_pass():
    body = 'A United States military helicopter crashed in the South China Sea during a routine flight, officials said in a statement.'
    assert not assess_topic(row(body, 'new_media'))['approved']


def test_social_podcast_preview_is_held():
    body = 'The United States and China are negotiating trade tariffs. Listen to our podcast episode about their diplomatic relations.'
    assert not assess_topic(row(body, 'new_media'))['approved']


def test_article_focused_on_media_comparison_can_pass():
    body = 'This study compares United States and Chinese news coverage, examining how media framing presents trade competition and diplomatic conflict.'
    assert assess_topic(row(body, 'research_literature', 'Comparing American and Chinese news framing'))['approved']


def test_unresolved_previous_date_conflict_is_never_overridden():
    body = 'The United States will improve relations with China through diplomatic negotiations and consultations on trade policy.'
    assert not assess_topic(row(body), previous_reason='Publication date conflict: source says released next day')['approved']


def test_us_pronoun_and_medical_media_title_are_not_us_policy_evidence():
    body = 'Chinese patients told us about their need for better security and peace of mind when discussing their health on social media.'
    assert not assess_topic(row(body, 'research_literature', 'Chinese patients on social media'))['approved']


def test_explicit_partial_transcript_is_never_promoted():
    body = 'The United States will improve relations with China through diplomatic negotiations and consultations on trade policy.'
    assert not assess_topic(row(body, title='Partial Transcript of Presidential Remarks'))['approved']


def official_post(body, source='CSIS'):
    return dict(body=body, source_category='new_media', title='@csis.org on Bluesky',
                source=source, source_url='https://bsky.app/profile/csis.org/post/example',
                platform_id='at://did:plc:example/app.bsky.feed.post/example')


def test_institutional_china_threat_narrative_does_not_require_us_in_every_paragraph():
    body = 'China’s military buildup in the Taiwan Strait raises the danger of a blockade and coercion against Taiwan, according to this assessment.'
    result = assess_topic(official_post(body))
    assert result['approved']
    assert result['supporting_passages'][0]['us_context'] == 'CSIS'
    assert result['supporting_passages'][0]['text'] == body


def test_institutional_control_discourse_can_pass_with_its_explicit_source_context():
    body = 'China uses censorship and propaganda to limit criticism and influence political debate, according to this account of authoritarian repression.'
    assert assess_topic(official_post(body, source='CNN'))['approved']


def test_institutional_source_does_not_make_ordinary_china_news_topical():
    body = 'China recorded higher retail sales this month as customers purchased clothing, electronics and other household goods in stores across the country.'
    assert not assess_topic(official_post(body))['approved']


def test_weak_geographic_reference_is_not_political_discourse():
    body = 'A helicopter crashed in the South China Sea on Tuesday during a training flight; its crew was rescued safely by another military aircraft.'
    assert not assess_topic(official_post(body))['approved']


def test_listen_here_and_named_audio_series_are_kept_outside_transcript_fulltexts():
    body = 'China uses censorship and propaganda to control political discussion. Join Pekingology to discuss authoritarian repression. Listen here: example.org'
    assert not assess_topic(official_post(body))['approved']
