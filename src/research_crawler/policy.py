from enum import Enum
from urllib.parse import urlsplit


class AccessDecision(Enum):
    ALLOW = "allow"
    RESTRICTED = "restricted"
    RETRY = "retry"
    REJECT = "reject"


_RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}
_RESTRICTED_STATUSES = {401, 402, 403}
_RESTRICTION_MARKERS = (
    "subscribe to continue",
    "subscribe to read",
    "this content is for subscribers",
    "sign in to continue reading",
    "log in to continue reading",
    "purchase access to view",
)


def classify_response(url: str, status_code: int, body_text: str = "") -> AccessDecision:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return AccessDecision.REJECT
    if status_code in _RESTRICTED_STATUSES:
        return AccessDecision.RESTRICTED
    normalized_body = body_text.casefold()
    if any(marker in normalized_body for marker in _RESTRICTION_MARKERS):
        return AccessDecision.RESTRICTED
    if status_code in _RETRYABLE_STATUSES:
        return AccessDecision.RETRY
    if 200 <= status_code < 300:
        return AccessDecision.ALLOW
    return AccessDecision.REJECT
