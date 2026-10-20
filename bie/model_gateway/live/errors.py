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
})


class ProviderError(RuntimeError):
    """A failed provider call. ``kind`` decides whether a retry is allowed."""

    def __init__(self, kind: str, message: str = "", *, status: int | None = None, provider: str | None = None):
        if kind not in KINDS:
            raise ValueError("unknown provider error kind: " + str(kind))
        self.kind = kind
        self.status = status
        self.provider = provider
        self.message = message[:600]
        super().__init__(f"{provider or 'provider'}:{kind}" + (f":{status}" if status else "") + (f": {self.message}" if self.message else ""))

    @property
    def retryable(self) -> bool:
        return self.kind in RETRYABLE_KINDS


def kind_for_status(status: int) -> str:
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
