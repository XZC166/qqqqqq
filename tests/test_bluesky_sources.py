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


def test_bluesky_adapter_supports_verified_policy_and_media_handles():
    sources = BlueskyPostAdapter.sources
    expected = {
        "lawfaremedia.org": "Lawfare",
        "carnegieendowment.org": "Carnegie Endowment",
        "theconversation.com": "The Conversation",
        "politico.com": "Politico",
        "thediplomat.com": "The Diplomat",
        "scmp.com": "South China Morning Post",
        "axios.com": "Axios",
        "economist.com": "The Economist",
        "usip.org": "U.S. Institute of Peace",
        "wilsoncenter.org": "The Wilson Center",
    }
    for handle, source in expected.items():
        assert sources[handle] == source


def test_bluesky_adapter_supports_verified_rights_and_polling_handles():
    sources = BlueskyPostAdapter.sources
    expected = {
        "hrw.org": "Human Rights Watch",
        "amnesty.org": "Amnesty International",
        "justsecurity.org": "Just Security",
        "gallup.com": "Gallup",
    }
    for handle, source in expected.items():
        assert sources[handle] == source
