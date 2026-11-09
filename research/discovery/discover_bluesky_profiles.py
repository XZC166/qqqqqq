"""Discover public, topic-matched text posts from official institutional feeds."""

import argparse
import csv
import json
import re
import time
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE = "https://public.api.bsky.app/xrpc"
USER_AGENT = "research-crawler/0.1 (academic public-source discovery)"
FEED_HANDLES = {
    "nytimes.com": "The New York Times",
    "nytopinion.nytimes.com": "The New York Times Opinion",
    "apnews.com": "The Associated Press",
    "csis.org": "CSIS",
    "pewresearch.org": "Pew Research Center",
    "brookings.edu": "Brookings Institution",
    "cfr.org": "Council on Foreign Relations",
    "rand.org": "RAND",
    "reuters.com": "Reuters",
    "cnn.com": "CNN",
    "foreignaffairs.com": "Foreign Affairs",
    "chathamhouse.org": "Chatham House",
    "pbs.org": "PBS",
    "npr.org": "NPR",
    "foreignpolicy.com": "Foreign Policy",
    "theguardian.com": "The Guardian",
    "washingtonpost.com": "The Washington Post",
}
TOPIC_PATTERN = re.compile(
    r"\b(?:china|chinese|taiwan(?:ese)?|hong kong|xinjiang|tibet|beijing|peking|"
    r"tiananmen|sino[- ]american|u\.?s\.?[- ]china|south china sea|trade war|"
    r"tariffs?|semiconduct\w*|chips?|artificial intelligence|public diplomacy|"
    r"propaganda|disinformation|misinformation|influence operations|information operations|"
    r"strategic communication)\b",
    re.I,
)


def _contains_video(value) -> bool:
    if isinstance(value, dict):
        type_name = str(value.get("$type", "")).casefold()
        if "embed.video" in type_name or type_name.endswith("#video"):
            return True
        return any(_contains_video(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_video(child) for child in value)
    return False


def build_candidate(handle: str, post: dict) -> dict | None:
    author = post.get("author") or {}
    record = post.get("record") or {}
    uri = post.get("uri", "")
    text = record.get("text", "")
    created_at = record.get("createdAt", "")
    if (
        handle not in FEED_HANDLES
        or author.get("handle") != handle
        or record.get("$type") != "app.bsky.feed.post"
        or not uri.startswith("at://")
        or not isinstance(text, str)
        or not TOPIC_PATTERN.search(text)
        or _contains_video(post.get("embed"))
        or _contains_video(record.get("embed"))
    ):
        return None
    try:
        published = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
    except (AttributeError, ValueError):
        return None
    if not date(2017, 1, 1) <= published <= date(2025, 12, 31):
        return None
    rkey = uri.rsplit("/", 1)[-1]
    metadata_url = f"{API_BASE}/app.bsky.feed.getPosts?{urlencode({'uris': uri})}"
    return {
        "url": f"https://bsky.app/profile/{handle}/post/{rkey}",
        "period": "2017-2025",
        "source_category": "new_media",
        "query_label": f"bsky-timeline-{handle.replace('.', '-')}-2023-2025",
        "platform_id": uri,
        "metadata_url": metadata_url,
    }


def _get_json(endpoint: str, params: dict, timeout: int = 25) -> dict:
    url = f"{API_BASE}/{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise URLError(f"HTTP {response.status}")
        return json.load(response)


def discover(
    output: Path,
    *,
    max_pages_per_account: int = 60,
    delay: float = 0.25,
    handles: list[str] | None = None,
) -> dict:
    if not 1 <= max_pages_per_account <= 250:
        raise ValueError("max pages per account must be between 1 and 250")
    if delay < 0.2:
        raise ValueError("delay must be at least 0.2 seconds")

    selected_handles = handles or list(FEED_HANDLES)
    if any(handle not in FEED_HANDLES for handle in selected_handles):
        raise ValueError("all handles must be in the verified institutional account list")

    candidates = {}
    accounts = {}
    for handle in selected_handles:
        stats = {"profile_verified": False, "pages": 0, "posts_scanned": 0,
                 "video_posts_skipped": 0, "candidates": 0, "oldest_post": None,
                 "page_limit_reached": False, "error": None}
        accounts[handle] = stats
        try:
            profile = _get_json("app.bsky.actor.getProfile", {"actor": handle})
            stats["profile_verified"] = profile.get("handle") == handle and bool(profile.get("did"))
            if not stats["profile_verified"]:
                stats["error"] = "profile response did not confirm requested handle"
                continue
            cursor = None
            for _ in range(max_pages_per_account):
                params = {"actor": handle, "limit": 100}
                if cursor:
                    params["cursor"] = cursor
                payload = _get_json("app.bsky.feed.getAuthorFeed", params)
                feed = payload.get("feed", [])
                stats["pages"] += 1
                stats["posts_scanned"] += len(feed)
                if stats["pages"] % 10 == 0:
                    print(
                        f"{handle}: pages={stats['pages']} posts={stats['posts_scanned']} "
                        f"candidates={len(candidates)}",
                        flush=True,
                    )
                post_dates = []
                for entry in feed:
                    post = entry.get("post", {})
                    record = post.get("record") or {}
                    stamp = record.get("createdAt", "")
                    if stamp:
                        post_dates.append(stamp)
                    if _contains_video(post.get("embed")) or _contains_video(record.get("embed")):
                        stats["video_posts_skipped"] += 1
                    candidate = build_candidate(handle, post)
                    if candidate:
                        candidates.setdefault(candidate["platform_id"], candidate)
                if post_dates:
                    stats["oldest_post"] = min(post_dates)
                    oldest = min(datetime.fromisoformat(value.replace("Z", "+00:00")).date()
                                 for value in post_dates)
                    if oldest < date(2017, 1, 1):
                        break
                cursor = payload.get("cursor")
                if not cursor or not feed:
                    break
                time.sleep(delay)
            else:
                stats["page_limit_reached"] = True
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, KeyError, TypeError) as exc:
            stats["error"] = f"{type(exc).__name__}: {exc}"
        stats["candidates"] = sum(
            row["query_label"].startswith(f"bsky-timeline-{handle.replace('.', '-')}-")
            for row in candidates.values()
        )
        time.sleep(delay)

    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ("url", "period", "source_category", "query_label", "platform_id", "metadata_url")
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates.values())
    report = {
        "source": "Bluesky public AppView API: getAuthorFeed and getProfile",
        "window": ["2017-01-01", "2025-12-31"],
        "accounts": accounts,
        "candidate_urls": len(candidates),
        "candidate_csv": str(output),
        "note": "Discovery metadata only. Candidate posts must pass original-page and getPosts body/date/author checks before formal export; video posts are skipped.",
    }
    output.with_suffix(".json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-pages-per-account", type=int, default=60)
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--handles", nargs="+", choices=tuple(FEED_HANDLES))
    args = parser.parse_args()
    print(json.dumps(discover(
        args.output,
        max_pages_per_account=args.max_pages_per_account,
        delay=args.delay,
        handles=args.handles,
    ), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
