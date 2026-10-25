"""Provider failures as stable kinds; the retryable kinds match ``retry_policy.RETRYABLE``."""
from __future__ import annotations

import re

RETRYABLE_KINDS = frozenset({"timeout", "rate_limit", "provider_unavailable", "server_error"})
KINDS = RETRYABLE_KINDS | frozenset({
    "auth",          # bad or missing key, no access to the model
    "bad_request",   # the provider rejected the request shape
    "not_found",     # unknown model or endpoint
    "refusal",       # the model declined or a safety block stopped it
    "truncated",     # output hit the token limit
    "malformed",     # the response could not be read
    "schema_invalid",  # valid JSON that does not match the schema after repair
    "config",        # local configuration (missing key, unknown provider)
    "balance",       # the provider or reseller says the wallet, key budget or quota is used up
    "budget",        # BIE's own cost guard stopped the call before it was sent
    "plan_limit",    # a subscription plan's usage window is used up (ChatGPT Pro via Codex); resumable later
})


class ProviderError(RuntimeError):
    """A failed provider call. ``kind`` decides whether a retry is allowed."""

    def __init__(self, kind: str, message: str = "", *, status: int | None = None, provider: str | None = None,
                 usage: dict | None = None, retry_after: float | None = None):
        if kind not in KINDS:
            raise ValueError("unknown provider error kind: " + str(kind))
        self.kind = kind
        # The tokens the provider reports for a call that generated an answer and then failed (truncated, refused,
        # unreadable): such a call is billed, so the gateway records its cost (Task 045d job B2: a review that ran to
        # 32,000 output tokens cost about Rs 44 and the ledger had counted Rs 0).
        self.usage = usage
        # Seconds the provider asks BIE to wait before the next try (Google's RetryInfo on a per-minute quota).
        self.retry_after = retry_after
        self.status = status
        self.provider = provider
        self.message = message[:600]
        super().__init__(f"{provider or 'provider'}:{kind}" + (f":{status}" if status else "") + (f": {self.message}" if self.message else ""))

    @property
    def retryable(self) -> bool:
        return self.kind in RETRYABLE_KINDS


# Wallet, key budget or quota exhausted: retrying cannot help and only adds calls. OpenAI sends 429
# "insufficient_quota"; AICredits sends 402 "insufficient_quota" ("API Key Budget Exceeded",
# "Insufficient Balance"); Anthropic's Messages format names it "billing_error".
_BALANCE_TEXT = re.compile(r"(?i)insufficient[_ ]quota|insufficient[_ ]balance|credit[_ ]balance|billing[_ ]error|"
                           r"budget[_ ]exceeded|no credits remaining|exceeded your current quota")


def kind_for_status(status: int) -> str:
    if status == 402:
        return "balance"
    if status in (401, 403):
        return "auth"
    if status == 404:
        return "not_found"
    if status in (408,):
        return "timeout"
    if status == 429:
        return "rate_limit"
    if status in (503, 529):
        return "provider_unavailable"
    if status >= 500:
        return "server_error"
    return "bad_request"


# Google's free tier (Navin's reviewer key from 25 October 2026) answers every quota with 429 RESOURCE_EXHAUSTED and "You exceeded your current
# quota", the same words as a used-up wallet. Its details name the quota: a per-minute one
# ("GenerateRequestsPerMinutePerProjectPerModel-FreeTier") clears within a minute, so it is a rate limit to wait out
# (RetryInfo "retryDelay": "37s"); a per-day one, or a model the tier does not serve ("limit: 0"), is used up.
_QUOTA_ID = re.compile(r'"quotaId"\s*:\s*"([^"]+)"')
_NO_QUOTA = re.compile(r"limit\s*:\s*0\b")
_RETRY_DELAY = re.compile(r'"retryDelay"\s*:\s*"([0-9]+(?:\.[0-9]+)?)s"|retry in ([0-9]+(?:\.[0-9]+)?)\s*s', re.I)


def per_minute_quota(status: int | None, detail: object = "") -> bool:
    """True for a 429 whose quotas are all per-minute ones that still serve this model."""
    detail = str(detail or "")
    ids = _QUOTA_ID.findall(detail)
    return status == 429 and bool(ids) and all("PerMinute" in i for i in ids) and not _NO_QUOTA.search(detail)


def retry_after(detail: object = "") -> float | None:
    """The wait a provider asks for (Google's RetryInfo or "Please retry in 37.2s"), in seconds."""
    match = _RETRY_DELAY.search(str(detail or ""))
    return float(match.group(1) or match.group(2)) if match else None


def classify(status: int | None, text: object = "", detail: object = "") -> str:
    """The kind for an HTTP status and the provider's error text; balance messages win over the status, except a
    Google per-minute quota (``detail``: the raw error body), which is a rate limit."""
    if per_minute_quota(status, detail):
        return "rate_limit"
    if _BALANCE_TEXT.search(str(text or "")):
        return "balance"
    return kind_for_status(status) if status is not None else "server_error"


_KEY_PATTERNS = (
    re.compile(r"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_\-]{4,}"),
    re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{4,}"),
    re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{6,}"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[A-Za-z0-9._\-]{8,}"),
    re.compile(r"[A-Za-z0-9_\-]*\*{3,}[A-Za-z0-9_\-]*"),  # masked keys such as sk-ab****xyz9
)


def redact(text: object, secrets=()) -> str:
    """Remove keys from text: the exact secrets, key-shaped and masked tokens, and 6+ character pieces of a secret."""
    value = str(text)
    for secret in secrets:
        if secret:
            value = value.replace(secret, "[REDACTED]")
    for pattern in _KEY_PATTERNS:
        if pattern.groups:
            value = pattern.sub(lambda m: m.group(1) + "[REDACTED]", value)
        else:
            value = pattern.sub("[REDACTED]", value)
    for secret in secrets:
        # Providers often echo a prefix or suffix of a wrong key ("sk-abc...xyz").
        if secret and len(secret) >= 12:
            for piece in {secret[:8], secret[-6:]}:
                value = value.replace(piece, "[REDACTED]")
    return value
