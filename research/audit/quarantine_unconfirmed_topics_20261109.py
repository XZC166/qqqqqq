"""Reversible quarantine of unconfirmed topics; never rewrites source text."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/research.sqlite3"
BACKUP = ROOT / "data/backups/pre-topic-quarantine-20261109.sqlite3"
REPORT = ROOT / "data/reviews/topic-quarantine-20261109.json"


def main():
    if REPORT.exists():
        raise SystemExit("Audit already exists; inspect saved report instead of repeating.")
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    if not BACKUP.exists():
        with sqlite3.connect(BACKUP) as b:
            c.backup(b)
    baseline = sqlite3.connect(BACKUP)
    baseline.row_factory = sqlite3.Row
    before = baseline.execute("SELECT count(*) FROM materials").fetchone()[0]
    old_foreign_key_issues = {tuple(r) for r in baseline.execute("PRAGMA foreign_key_check")}
    us = re.compile(r"\b(?:u\.?s\.?|united states|american|washington|trump|biden|congress|white house|state department|pentagon)\b", re.I)
    china = re.compile(r"\b(?:china|chinese|beijing|prc|taiwan|hong kong|xinjiang|tibet)\b", re.I)
    policy = re.compile(r"\b(?:trade|tariff|chip|semiconductor|export control|sanction|diplomac\w*|bilateral|relations|security|military|defen[cs]e|competition|dialogue|talks|meeting|visit|summit|public opinion|image|media|narrative|disinformation|propaganda|human rights|influence|cyber|technology|visa|tiktok|deterrence|alliance|arms|interference|containment)\b", re.I)
    taiwan = re.compile(r"\b(?:taiwan|cross[- ]strait|taiwan strait|lai ching|dpp|taipei|one china|reunification|independence|separatist|external forces|interference)\b", re.I)
    taiwan_context = re.compile(r"\b(?:u\.?s\.?|united states|american|washington|foreign|external forces|independence|separatist|dpp|lai ching|military|defen[cs]e|arms|interference|cross[- ]strait|sovereignty|sovereign|pla|strait thunder|status quo|one china|unification|secession)\b", re.I)
    territory = re.compile(r"\b(?:xinjiang|hong kong|tibet)\b", re.I)
    controversy = re.compile(r"\b(?:u\.?s\.?|united states|western media|western countries|human rights|forced labor|sanction|disinformation|public opinion|image|narrative|propaganda|foreign interference|democracy|freedom of speech|national security law|activist|criticis\w*|accusation|accusations|vilif\w*|bad-mouth\w*)\b", re.I)
    protect = re.compile(r"discours|propagand|diplomac|media|news|framing|narrative|public opinion|politic|foreign polic|relations|soft power|image|influence|information operation|nationalis|racis|xenophob|geopolit|strategic competit|trade war|anti.chin|us.chin|united states|america|percept|attitude|stereotyp|stigma|misinform|disinform|conspirac|communicat|social|information|survey|cultur|govern|secur|Cold War|conflict|trust|democra|authoritar|press|opinion|trade|bilateral", re.I)
    biomedical = re.compile(r"cancer|carcinoma|tumou?r|oncol|protein|genom|molecular|clinical|\bpatients?\b|diabetes|mellitus|rats?\b|\bmice\b|mouse|immun|enzyme|cellular|\bcells?\b|syndrome|biomarker|\bRNA\b|\bDNA\b|microRNA|diagnos|metaboli|meta.analysis|randomized|\bin vitro\b|\bin vivo\b|gene expression|quantum|photocatal|nanoparticle|biochem|nucleic|mutation|bacteri|antibiot|glyco|apoptosis|porcine|hamsters|coronavirus.*spike", re.I)
    withdrawn = []
    for row in baseline.execute("SELECT * FROM materials").fetchall():
        reason = None
        if row["source"] == "China Daily" and row["source_url"].startswith("https://bsky.app/"):
            text = row["body"]
            signal = ((us.search(text) and china.search(text) and policy.search(text))
                      or (taiwan.search(text) and taiwan_context.search(text))
                      or (territory.search(text) and controversy.search(text)))
            if not signal:
                reason = "Topic verification pending: institutional China Daily post lacks a direct supported US-China policy/discourse or Taiwan/Hong Kong/Xinjiang/Tibet controversy signal; China mention alone is insufficient."
        elif "pmc.ncbi.nlm.nih.gov/" in row["source_url"]:
            if biomedical.search(row["title"]) and not protect.search(row["title"]):
                reason = "Topic verification pending: clinical/biomedical or physical-science title with no supported discourse/policy/media signal; title screen is a flag, not a final assertion of irrelevance."
        if reason:
            withdrawn.append({"material_id": row["id"], "identity_key": row["identity_key"], "source": row["source"], "title": row["title"], "source_url": row["source_url"], "published_on": row["published_on"], "body_sha256": hashlib.sha256(row["body"].encode()).hexdigest(), "reason": reason})
    with c:
        for row in withdrawn:
            c.execute("UPDATE candidates SET status='pending',status_detail=? WHERE identity_key=?", (row["reason"], row["identity_key"]))
            c.execute("DELETE FROM materials WHERE id=?", (row["material_id"],))
    after = c.execute("SELECT count(*) FROM materials").fetchone()[0]
    assert before - after == len(withdrawn)
    new_foreign_key_issues = {tuple(r) for r in c.execute("PRAGMA foreign_key_check")}
    assert not new_foreign_key_issues - old_foreign_key_issues
    assert all(c.execute("SELECT count(*) FROM candidates WHERE identity_key=? AND status='pending'", (r["identity_key"],)).fetchone()[0] > 0 for r in withdrawn)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(), "before_material_rows": before,
        "after_material_rows": after, "withdrawn_to_pending": len(withdrawn),
        "china_daily": sum(r["source"] == "China Daily" for r in withdrawn),
        "other_biomedical_flags": sum(r["source"] != "China Daily" for r in withdrawn),
        "preexisting_foreign_key_issues": len(old_foreign_key_issues),
        "new_foreign_key_issues": len(new_foreign_key_issues - old_foreign_key_issues),
        "backup": str(BACKUP.relative_to(ROOT)), "backup_sha256": hashlib.sha256(BACKUP.read_bytes()).hexdigest(),
        "notice": "All source evidence and full bodies survive in the backup and evidence directory. Remaining materials are still a working pool requiring deeper scope/quality review. No claim that retained keyword signals establish final relevance.",
        "withdrawn": withdrawn,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "withdrawn"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
