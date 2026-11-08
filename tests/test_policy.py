from research_crawler.policy import AccessDecision, classify_response


def test_allows_public_http_success():
    assert classify_response("https://example.org/article", 200) is AccessDecision.ALLOW


def test_rejects_non_http_urls():
    assert classify_response("file:///tmp/article.html", 200) is AccessDecision.REJECT


def test_stops_on_restricted_statuses():
    for status in (401, 402, 403):
        assert classify_response("https://example.org/article", status) is AccessDecision.RESTRICTED


def test_stops_on_paywall_marker_even_with_success_status():
    body = "<h1>Subscribe to continue reading</h1>"
    assert classify_response("https://example.org/article", 200, body) is AccessDecision.RESTRICTED


def test_stops_on_explicit_forbidden_error_page_even_with_success_status():
    body = "<title>Technical Difficulties</title><p>Exception: forbidden</p>"
    assert classify_response("https://example.org/article", 200, body) is AccessDecision.RESTRICTED


def test_stops_on_turnstile_challenge_page_even_with_success_status():
    body = "<title>Verifying connection</title><form id='captcha-form'><div class='cf-turnstile'></div></form>"
    assert classify_response("https://example.org/article", 200, body) is AccessDecision.RESTRICTED


def test_stops_on_browser_verification_page_even_with_success_status():
    body = "<title>Sorry, we can't verify your browser!</title>"
    assert classify_response("https://example.org/article", 200, body) is AccessDecision.RESTRICTED


def test_retries_only_transient_failure_statuses():
    assert classify_response("https://example.org/article", 429) is AccessDecision.RETRY
    assert classify_response("https://example.org/article", 503) is AccessDecision.RETRY
    assert classify_response("https://example.org/article", 404) is AccessDecision.REJECT
