"""Claude (Anthropic Messages API) client for ``ClaudeAdapter``.

Structured output uses ``output_config.format`` (JSON schema; generally available, no beta
header). Source: platform.claude.com/docs/en/build-with-claude/structured-outputs (read 2026-10-20).
"""
from __future__ import annotations

from .errors import ProviderError
from .messages import anthropic_parts, provider_schema, split_messages
from .transport import HttpTransport

API_VERSION = "2023-06-01"
BASE_URL = "https://api.anthropic.com/v1"


class AnthropicClient:
    provider = "anthropic"

    def __init__(self, api_key: str, *, transport: HttpTransport | None = None, max_tokens: int = 16000,
                 base_url: str = BASE_URL, temperature: float | None = None):
        if not api_key:
            raise ProviderError("config", "ANTHROPIC_API_KEY is not set", provider=self.provider)
        self._key = api_key
        self.transport = transport or HttpTransport()
        self.max_tokens = max_tokens
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.last_model = None

    def _headers(self):
        return {"x-api-key": self._key, "anthropic-version": API_VERSION}

    def messages_create(self, *, model, messages, schema=None):
        system, conversation = split_messages(messages, provider=self.provider)
        body = {"model": model, "max_tokens": self.max_tokens,
                "messages": [{"role": m["role"], "content": anthropic_parts(m["content"])} for m in conversation]}
        if system:
            body["system"] = system
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if schema is not None:
            body["output_config"] = {"format": {"type": "json_schema", "schema": provider_schema(schema, self.provider)}}
        raw = self.transport.request_json("POST", self.base_url + "/messages", self._headers(), body,
                                          provider=self.provider, secrets=(self._key,))
        return self.parse(raw)

    def parse(self, raw):
        stop = raw.get("stop_reason")
        self.last_model = raw.get("model")
        usage = raw.get("usage") or {}
        normalized = {
            "input_tokens": int(usage.get("input_tokens") or 0) + int(usage.get("cache_creation_input_tokens") or 0)
            + int(usage.get("cache_read_input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "cached_input_tokens": int(usage.get("cache_read_input_tokens") or 0),
            "reasoning_tokens": 0,
        }
        if stop == "refusal":
            raise ProviderError("refusal", "the model declined the request", provider=self.provider)
        if stop == "max_tokens":
            raise ProviderError("truncated", f"output reached max_tokens={self.max_tokens}", provider=self.provider)
        blocks = raw.get("content")
        if not isinstance(blocks, list):
            raise ProviderError("malformed", "no content blocks", provider=self.provider)
        text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text")
        if not text.strip():
            raise ProviderError("malformed", "empty text content", provider=self.provider)
        return {"content": text, "usage": normalized, "finish_reason": stop or "unknown", "model": self.last_model}

    def list_models(self):
        raw = self.transport.request_json("GET", self.base_url + "/models?limit=100", self._headers(),
                                          provider=self.provider, secrets=(self._key,))
        return sorted(str(m.get("id")) for m in raw.get("data", []) if isinstance(m, dict) and m.get("id"))
