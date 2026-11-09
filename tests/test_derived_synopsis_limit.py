from research_crawler.batch_review import assess_topic, derived_fields


def test_unbroken_long_policy_sentence_does_not_overflow_excel_summary():
    body = 'The United States and China discuss trade policy ' + 'and diplomatic negotiations ' * 2000 + '.'
    row = dict(body=body, source_category='government', title='Policy statement',
               source='Congress', source_url='https://example.org/document')
    assessment = assess_topic(row)
    assert assessment['approved']
    abstract, keywords = derived_fields(row, assessment)
    assert abstract.startswith('据正文整理：')
    assert len(abstract.encode('utf-16-le')) // 2 < 2000
    assert keywords
    assert all(term.casefold() in body.casefold() for term in keywords.split('; '))
