import pytest
from research_crawler.quality_audit import _app_editorial_risks


def page(note):
    return ('<html><div class="field-docs-footnote">' + note + '</div></html>').encode()


@pytest.mark.parametrize("note", [
    "Vice Premier spoke in Chinese. His response was translated as follows: We welcome cooperation.",
    "Mr. Connally introduced the President as follows: Distinguished guests, welcome.",
    "A portion of these remarks could not be verified because the tape was incomplete.",
    "A complete tape was not available for verification of the content of these remarks.",
])
def test_unseen_speech_or_unverifiable_transcript_is_held(note):
    assert _app_editorial_risks(page(note), "The President's main speech.", "1972-02-28")


@pytest.mark.parametrize("note", [
    "The transcript of the interview was released on January 26.",
    "The text of the letters was released by the Office of the Press Secretary on March 1.",
    "The transcript was released by the Office of Communications on November 3.",
])
def test_explicit_different_release_day_does_not_pass_as_event_day(note):
    risks = _app_editorial_risks(page(note), "The main text.", "1982-02-28")
    assert any("release" in risk.lower() for risk in risks)


def test_same_day_release_and_contextual_note_do_not_create_false_conflict():
    note = "The transcript was released on February 28. The President spoke in the Rose Garden."
    assert _app_editorial_risks(page(note), "Complete China statement.", "1982-02-28") == []


def test_already_preserved_note_is_not_an_omitted_speech():
    note = "The Premier responded as follows: Thank you for this invitation."
    assert _app_editorial_risks(page(note), "Main text. " + note, "1972-02-28") == []


def test_preserved_note_with_original_html_line_break_is_not_falsely_held():
    note = "The Premier responded as follows:<br/>Mr. President, thank you."
    body = "Main text. The Premier responded as follows:\nMr. President, thank you."
    assert _app_editorial_risks(page(note), body, "1972-02-28") == []


def test_notes_without_risk_cues_do_not_block_body():
    assert _app_editorial_risks(page("Note: The President spoke at 10 a.m. in the Rose Garden."), "Full body.", "1972-02-28") == []


@pytest.mark.parametrize("event,visible,note,release", [
    ("1979-01-25", "January 25, 1979", "The transcript of the interview was released on January 26.", "1979-01-26"),
    ("1982-02-28", "February 28, 1982", "The text of the letters was released by the Office of the Press Secretary on March 1.", "1982-03-01"),
    ("1984-04-28", "April 28, 1984", "As printed above, this item follows the text of the White House press release, which was released by the Office of the Press Secretary in Beijing on April 29.", "1984-04-29"),
    ("2025-10-31", "October 31, 2025", "The transcript was released by the Office of Communications on November 3.", "2025-11-03"),
])
def test_adapter_uses_explicit_same_document_text_release_day(event, visible, note, release):
    from pathlib import Path
    from scrapy.http import HtmlResponse
    from research_crawler.items import MaterialCandidate
    from research_crawler.spiders.government import GovernmentArticleAdapter

    raw = (Path(__file__).parent / "fixtures/presidency_statement.html").read_text(encoding="utf-8")
    raw = raw.replace("1958-09-04", event).replace("September 04, 1958", visible)
    raw = raw.replace("Editorial note must not enter the body.", note)
    url = "https://www.presidency.ucsb.edu/documents/synthetic-release"
    period = "2017-2025" if event.startswith("2025") else "1972-1991"
    result = GovernmentArticleAdapter().extract(HtmlResponse(url=url, body=raw.encode(), encoding="utf-8"),
                                               MaterialCandidate(url, period, "government", "test"))
    assert result["material"].time == release
    assert result["material"].body == "Opening statement.\n\nNumbered statement."


def test_signed_topic_approval_cannot_bypass_omitted_app_speech(tmp_path):
    import hashlib
    from dataclasses import replace
    from scrapy.http import HtmlResponse
    from research_crawler.items import MaterialCandidate
    from research_crawler.store import ResearchStore
    from research_crawler.spiders.government import GovernmentArticleAdapter
    from research_crawler.quality_audit import audit_material
    from test_quality_audit import approval

    url = "https://www.presidency.ucsb.edu/documents/synthetic-china-statement"
    raw = b'''<html><head><title>Statement | The American Presidency Project</title></head>
    <body><div class="node node-documents view-mode-full">
    <div class="field-ds-doc-title">China statement</div>
    <div class="field-docs-start-date-time"><span class="date-display-single"
    content="1958-09-04T00:00:00+00:00">September 04, 1958</span></div>
    <div class="field-docs-content"><p>China policy statement.</p></div>
    <div class="field-docs-footnote">The Premier responded as follows: Thank you for inviting me.</div>
    </div></body></html>'''
    candidate = MaterialCandidate(url, "1949-1972", "government", "synthetic-test")
    extracted = GovernmentArticleAdapter().extract(HtmlResponse(url=url, body=raw, encoding="utf-8"), candidate)
    assert "The Premier responded as follows: Thank you for inviting me." in extracted["material"].body
    store = ResearchStore(tmp_path / "audit.sqlite3")
    batch = store.create_batch(candidate.period, candidate.source_category, candidate.query_label)
    cid = store.add_candidate(batch, candidate)
    path = tmp_path / "source.html"
    path.write_bytes(raw)
    evidence = replace(extracted["evidence"], evidence_path=path)
    eid = store.add_evidence(cid, evidence, "allow")
    # A historical database row omitted this second speech despite a signed
    # topical approval. Fresh parsing must recover it; export must hold the row.
    material = replace(extracted["material"], body="China policy statement.",
                       abstract="据正文整理：公开中国政策声明。", keywords="China")
    fields = {key: url for key in ("source", "time", "author", "title", "abstract", "keywords")}
    mid, _ = store.add_verified_material(cid, eid, material, abstract_origin="derived", field_sources=fields)
    result = audit_material(store, mid, approval(store, mid))
    assert result["status"] == "pending"
    assert not result["source_pass"]
    assert "omitted" in result["reason"]
    assert result["checks"]["app_editorial_risks"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == evidence.content_sha256
    store.close()
