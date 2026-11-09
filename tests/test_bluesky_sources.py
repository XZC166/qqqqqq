from research_crawler.spiders.government import BlueskyPostAdapter


def test_bluesky_adapter_supports_new_verified_accounts():
    sources = BlueskyPostAdapter.sources

    assert sources["reuters.com"] == "Reuters"
    assert sources["cnn.com"] == "CNN"
    assert sources["foreignaffairs.com"] == "Foreign Affairs"
    assert sources["chathamhouse.org"] == "Chatham House"


def test_bluesky_adapter_supports_additional_verified_media_handles():
    sources = BlueskyPostAdapter.sources
    assert sources["pbs.org"] == "PBS"
    assert sources["npr.org"] == "NPR"
    assert sources["foreignpolicy.com"] == "Foreign Policy"
    assert sources["theguardian.com"] == "The Guardian"
    assert sources["washingtonpost.com"] == "The Washington Post"
