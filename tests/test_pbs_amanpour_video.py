import hashlib
from pathlib import Path

from scrapy.http import HtmlResponse

from research_crawler.items import MaterialCandidate
from research_crawler.spiders.government import GovernmentArticleAdapter


URL = "https://www.pbs.org/video/august-9-2024-unvdxv/"
TITLE = "Amanpour and Company | August 9, 2024 | Season 2024"
DATE = "2024-08-09"
BODY_SHA256 = "4c2923118e5f00b8b0d06d2adb19df3f938368958f2b4078cb748d6ec13e24d9"
FIXTURE = Path(__file__).parent / "fixtures" / "pbs_amanpour_chips_2024.html"


def _extract(raw: bytes):
    candidate = MaterialCandidate(URL, "2017-2025", "media", "pbs-amanpour-chips-2024")
    return GovernmentArticleAdapter().extract(
        HtmlResponse(url=URL, body=raw, encoding="utf-8"), candidate
    )


def test_pbs_amanpour_episode_promotes_exact_complete_transcript():
    result = _extract(FIXTURE.read_bytes())

    assert result["material"] is not None
    material = result["material"]
    assert material.source == "PBS"
    assert material.time == DATE
    assert material.author == "未注明"
    assert material.title == TITLE
    assert material.abstract.startswith("据正文整理：")
    assert "中国军民融合" in material.abstract
    assert "先进芯片" in material.abstract
    assert material.body.endswith(">> [MUSIC]")
    assert hashlib.sha256(material.body.encode()).hexdigest() == BODY_SHA256


def test_pbs_amanpour_episode_rejects_changed_transcript():
    raw = FIXTURE.read_bytes().replace(
        b"THANK YOU SO MUCH FOR WATCHING", b"ALTERED TRANSCRIPT", 1
    )

    assert _extract(raw)["material"] is None
