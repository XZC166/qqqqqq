import importlib.util
from pathlib import Path


script_path = Path(__file__).resolve().parents[1] / "research" / "discovery" / "discover_bluesky_profiles.py"
spec = importlib.util.spec_from_file_location("bluesky_profile_discovery", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_bluesky_discovery_keeps_relevant_text_posts_and_skips_video_and_out_of_range():
    post = {
        "uri": "at://did:plc:test/app.bsky.feed.post/abc",
        "author": {"handle": "nytimes.com"},
        "record": {
            "$type": "app.bsky.feed.post",
            "createdAt": "2025-08-01T10:00:00.000Z",
            "text": "U.S.-China technology competition is shaping policy.",
        },
        "embed": {},
    }

    candidate = module.build_candidate("nytimes.com", post)

    assert candidate["period"] == "2017-2025"
    assert candidate["source_category"] == "new_media"
    assert candidate["platform_id"] == post["uri"]
    assert candidate["url"].endswith("/post/abc")
    assert candidate["metadata_url"].startswith(
        "https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris="
    )
    assert module.build_candidate(
        "nytimes.com",
        {**post, "embed": {"$type": "app.bsky.embed.video"}},
    ) is None
    assert module.build_candidate(
        "nytimes.com",
        {**post, "record": {**post["record"], "createdAt": "2026-01-01T00:00:00Z"}},
    ) is None


def test_bluesky_discovery_rejects_reposts_from_an_official_timeline():
    post = {
        "uri": "at://did:plc:other/app.bsky.feed.post/abc",
        "author": {"handle": "other.example"},
        "record": {
            "$type": "app.bsky.feed.post",
            "createdAt": "2025-08-01T10:00:00Z",
            "text": "China and Taiwan update.",
        },
        "embed": {},
    }

    assert module.build_candidate("nytimes.com", post) is None


def test_bluesky_discovery_includes_verified_media_and_policy_accounts():
    assert module.FEED_HANDLES["reuters.com"] == "Reuters"
    assert module.FEED_HANDLES["cnn.com"] == "CNN"
    assert module.FEED_HANDLES["foreignaffairs.com"] == "Foreign Affairs"
    assert module.FEED_HANDLES["chathamhouse.org"] == "Chatham House"
