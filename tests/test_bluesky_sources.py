from research_crawler.spiders.government import BlueskyPostAdapter


def test_bluesky_adapter_supports_new_verified_accounts():
    sources = BlueskyPostAdapter.sources

    assert sources["reuters.com"] == "Reuters"
    assert sources["cnn.com"] == "CNN"
    assert sources["foreignaffairs.com"] == "Foreign Affairs"
    assert sources["chathamhouse.org"] == "Chatham House"
