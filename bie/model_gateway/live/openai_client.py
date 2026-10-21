"""OpenAI (Responses API) client for ``GPTAdapter``.

Structured output uses ``text.format`` with ``type: json_schema`` and ``strict: true``. Strict
mode needs every object to list all its properties as required and set
``additionalProperties: false``; BIE schemas are written that way.
"""
from __future__ import annotations

from .errors import ProviderError
from .messages import openai_responses_parts, provider_schema, split_messages
from .transport import HttpTransport

BASE_URL = "https://api.openai.com/v1"


class OpenAIClient:
    provider = "openai"

    def __init__(self, api_key: str, *, transport: HttpTransport | None = None, max_output_tokens: int = 32000,
                 base_url: str = BASE_URL, reasoning_effort: str | None = None):
        if not api_key:
            raise ProviderError("config", "OPENAI_API_KEY is not set", provider=self.provider)
        self._key = api_key
        self.transport = transport or HttpTransport()
        self.max_output_tokens = max_output_tokens
        self.base_url = base_url.rstrip("/")
        self.reasoning_effort = reasoning_effort
        self.last_model = None

    def _headers(self):
        return {"authorization": "Bearer " + self._key}

    def responses_create(self, *, model, messages, response_schema=None):
        system, conversation = split_messages(messages, provider=self.provider)
        turns = [{"role": m["role"], "content": openai_responses_parts(m["content"], m["role"])} for m in conversation]
        body = {"model": model, "input": turns, "max_output_tokens": self.max_output_tokens, "store": False}
        if system:
            body["instructions"] = system
        if self.reasoning_effort:
            body["reasoning"] = {"effort": self.reasoning_effort}
        if response_schema is not None:
            body["text"] = {"format": {"type": "json_schema", "name": "bie_output", "strict": True,
                                       "schema": provider_schema(response_schema, self.provider)}}
        raw = self.transport.request_json("POST", self.base_url + "/responses", self._headers(), body,
                                          provider=self.provider, secrets=(self._key,))
        return self.parse(raw)

    def parse(self, raw):
        self.last_model = raw.get("model")
        usage = raw.get("usage") or {}
        normalized = {
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "cached_input_tokens": int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0),
            "reasoning_tokens": int((usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0),
        }
        status = raw.get("status")
        if status == "incomplete":
            reason = (raw.get("incomplete_details") or {}).get("reason") or "incomplete"
            kind = "truncated" if reason == "max_output_tokens" else "refusal"
            raise ProviderError(kind, f"response incomplete: {reason}", provider=self.provider)
        if status == "failed":
            error = raw.get("error") or {}
            raise ProviderError("server_error", str(error.get("message") or "response failed")[:300], provider=self.provider)
        texts, refusals = [], []
        for item in raw.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for part in item.get("content") or []:
                if isinstance(part, dict) and part.get("type") == "output_text":
                    texts.append(part.get("text", ""))
                elif isinstance(part, dict) and part.get("type") == "refusal":
                    refusals.append(part.get("refusal", ""))
        if refusals and not "".join(texts).strip():
            raise ProviderError("refusal", refusals[0][:300], provider=self.provider)
        text = "".join(texts)
        if not text.strip():
            raise ProviderError("malformed", "no output text", provider=self.provider)
        return {"content": text, "usage": normalized, "finish_reason": status or "unknown", "model": self.last_model}

    def list_models(self):
        raw = self.transport.request_json("GET", self.base_url + "/models", self._headers(),
                                          provider=self.provider, secrets=(self._key,))
        return sorted(str(m.get("id")) for m in raw.get("data", []) if isinstance(m, dict) and m.get("id"))
