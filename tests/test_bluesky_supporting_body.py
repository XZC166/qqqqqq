import json

from research_crawler.items import SourceEvidence
from research_crawler.pipelines import _body_matches_verified_bluesky_response


def test_bluesky_exact_api_body_can_verify_page_expanded_links():
    body = "More details: freedomhouse.org/country/taiw..."
    raw = json.dumps({"posts": [{"record": {"$type": "app.bsky.feed.post", "text": body}}]}).encode()
    evidence = SourceEvidence(
        "https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris=test",
        "2026-11-09T00:00:00Z",
        200,
        "hash",
        metadata_verified=True,
        body_format="json",
    )
    supporting = [{"evidence": evidence, "raw_response": raw}]
    assert _body_matches_verified_bluesky_response(
        body, supporting, evidence.source_url
    )
    assert not _body_matches_verified_bluesky_response(
        body + " changed", supporting, evidence.source_url
    )
    assert not _body_matches_verified_bluesky_response(
        body, supporting, "https://other.example/"
    )
