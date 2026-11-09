from research_crawler.batch_review import assess_topic, derived_fields


def post(body, source='CSIS'):
    return dict(body=body, source_category='new_media', title='Institutional post',
                source=source, source_url='https://bsky.app/profile/csis.org/post/example',
                platform_id='at://did:plc:example/app.bsky.feed.post/example')


def test_complete_post_can_link_china_trade_strategy_to_separate_us_response():
    body = ('China is expanding trade and political engagement in overseas supply chains.\n\n'
            'Read about how the U.S. can counter China: https://example.org/report')
    result = assess_topic(post(body))
    assert result['approved']
    passage = result['supporting_passages'][0]
    assert passage['text'] == body[passage['start']:passage['end']] == body
    assert passage['context_kind'] == 'complete short institutional post with separate China-policy and US-policy anchors'
    abstract, keywords = derived_fields(post(body), result)
    assert abstract.startswith('据正文整理：')
    assert all(term.casefold() in body.casefold() for term in keywords.split('; '))


def test_complete_nuclear_post_can_relate_short_paragraphs_and_numbered_lines():
    body = ('China’s nuclear stockpile is growing.\n\n'
            '2019: 300\n2025: 600\n\n'
            'The buildup is bringing China closer to parity with the U.S. and changing the nuclear balance.')
    assert assess_topic(post(body))['approved']


def test_country_only_paragraph_cannot_borrow_unrelated_us_policy_context():
    body = ('China recorded higher retail sales as people bought household clothing.\n\n'
            'The U.S. Congress will discuss a new trade agreement with Canada next week.')
    assert not assess_topic(post(body))['approved']


def test_two_separate_trade_topics_are_not_assumed_to_be_bilateral():
    body = ('China is expanding trade and political engagement in Brazil.\n\n'
            'The U.S. Congress will discuss a new trade agreement with Canada next week.')
    assert not assess_topic(post(body))['approved']


def test_unknown_institution_cannot_use_document_wide_context():
    body = ('China is expanding trade and political engagement in overseas supply chains.\n\n'
            'Read about how the U.S. can counter China: https://example.org/report')
    assert not assess_topic(post(body, source='Unknown source'))['approved']


def test_long_document_cannot_use_short_post_fallback():
    body = ('China is expanding trade and political engagement in overseas supply chains.\n\n'
            + ('Unrelated content. ' * 130) + '\n\n'
            'Read about how the U.S. can counter China: https://example.org/report')
    assert not assess_topic(post(body))['approved']


def test_audio_preview_and_metadata_concerns_stay_outside_fallback():
    body = ('China is expanding trade and political engagement in overseas supply chains.\n\n'
            'The U.S. can counter China. Listen to our podcast.')
    assert not assess_topic(post(body))['approved']
    assert not assess_topic(post(body.replace('Listen to our podcast.', 'Read the report.')),
                            previous_reason='Publication date conflict remains unresolved')['approved']


def test_research_article_does_not_borrow_full_document_keyword_context():
    row = post('China is expanding trade and political engagement in overseas supply chains.\n\n'
               'Read about how the U.S. can counter China: https://example.org/report')
    row.update(source_category='research_literature', title='Comparing American and Chinese media framing')
    assert not assess_topic(row)['approved']
