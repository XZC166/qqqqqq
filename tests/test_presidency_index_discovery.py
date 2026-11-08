import importlib.util
from pathlib import Path


script_path = Path(__file__).resolve().parents[1] / "research" / "discovery" / "discover_presidency_index.py"
spec = importlib.util.spec_from_file_location("presidency_index_discovery", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_presidential_index_does_not_match_korea_only_titles():
    assert not module.TOPIC_PATTERN.search(
        "Remarks Following Discussions With President Roh Tae Woo of the Republic of Korea"
    )
    assert module.TOPIC_PATTERN.search("The Korean War and China's intervention")
