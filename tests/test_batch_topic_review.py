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
