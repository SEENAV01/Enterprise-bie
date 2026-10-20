"""Minimal JSON-over-HTTPS transport (standard library only).

Every failure becomes a ``ProviderError`` with a stable kind. Response bodies quoted in errors
are shortened and redacted, so a provider that echoes part of a wrong key cannot leak it into
logs, annotations or evidence.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from .errors import ProviderError, kind_for_status, redact

MAX_RESPONSE_BYTES = 32 * 1024 * 1024


class HttpTransport:
    def __init__(self, *, timeout: float = 600.0, opener=None):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout
        self._open = opener or urllib.request.urlopen

    def request_json(self, method: str, url: str, headers: dict, body=None, *, provider: str, secrets=()) -> dict:
        if not url.startswith("https://"):
            raise ProviderError("config", "only https endpoints are allowed", provider=provider)
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("content-type", "application/json")
        request.add_header("accept", "application/json")
        for name, value in headers.items():
            request.add_header(name, value)
        try:
            with self._open(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read(4000).decode("utf-8", "replace")
            except Exception:  # pragma: no cover - defensive
                detail = ""
            raise ProviderError(kind_for_status(exc.code), redact(_error_text(detail), secrets),
                                status=exc.code, provider=provider) from None
        except (socket.timeout, TimeoutError) as exc:
            raise ProviderError("timeout", redact(exc, secrets), provider=provider) from None
        except urllib.error.URLError as exc:
            reason = exc.reason
            kind = "timeout" if isinstance(reason, (socket.timeout, TimeoutError)) else "provider_unavailable"
            raise ProviderError(kind, redact(reason, secrets), provider=provider) from None
        except (ConnectionError, OSError) as exc:
            raise ProviderError("provider_unavailable", redact(exc, secrets), provider=provider) from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderError("malformed", "response too large", provider=provider)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise ProviderError("malformed", "response is not JSON", provider=provider) from None
        if not isinstance(value, dict):
            raise ProviderError("malformed", "response is not a JSON object", provider=provider)
        return value


def _error_text(detail: str) -> str:
    """The provider's own error message when the body is JSON, else the first characters."""
    try:
        value = json.loads(detail)
    except ValueError:
        return detail[:300]
    error = value.get("error") if isinstance(value, dict) else None
    if isinstance(error, dict):
        parts = [str(error.get(k)) for k in ("type", "code", "status", "message") if error.get(k)]
        return " | ".join(parts)[:300]
    if isinstance(error, str):
        return error[:300]
    return detail[:300]
