"""Gemini (Generative Language API) client for ``GeminiAdapter``.

Structured output uses ``generationConfig.responseMimeType = application/json`` with
``responseJsonSchema``. The key travels in the ``x-goog-api-key`` header, never in the URL, so it
cannot appear in a logged URL.
"""
from __future__ import annotations

import urllib.parse

from .errors import ProviderError
from .messages import gemini_parts, provider_schema, split_messages
from .transport import HttpTransport

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
BLOCKED_FINISH = {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "IMAGE_SAFETY", "LANGUAGE"}


class GeminiClient:
    provider = "google"

    def __init__(self, api_key: str, *, transport: HttpTransport | None = None, max_output_tokens: int = 32768,
                 base_url: str = BASE_URL, temperature: float | None = None):
        if not api_key:
            raise ProviderError("config", "GEMINI_API_KEY is not set", provider=self.provider)
        self._key = api_key
        self.transport = transport or HttpTransport()
        self.max_output_tokens = max_output_tokens
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.last_model = None

    def _headers(self):
        return {"x-goog-api-key": self._key}

    def generate(self, *, model, messages, schema=None):
        system, conversation = split_messages(messages, provider=self.provider)
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": gemini_parts(m["content"])}
                    for m in conversation]
        config = {"maxOutputTokens": self.max_output_tokens}
        if self.temperature is not None:
            config["temperature"] = self.temperature
        if schema is not None:
            config["responseMimeType"] = "application/json"
            config["responseJsonSchema"] = provider_schema(schema, self.provider)
        body = {"contents": contents, "generationConfig": config}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        name = model if model.startswith("models/") else "models/" + model
        url = f"{self.base_url}/{urllib.parse.quote(name, safe='/.-_')}:generateContent"
        raw = self.transport.request_json("POST", url, self._headers(), body, provider=self.provider, secrets=(self._key,))
        return self.parse(raw, model)

    def parse(self, raw, model=None):
        self.last_model = raw.get("modelVersion") or model
        meta = raw.get("usageMetadata") or {}
        thoughts = int(meta.get("thoughtsTokenCount") or 0)
        normalized = {
            "input_tokens": int(meta.get("promptTokenCount") or 0),
            "output_tokens": int(meta.get("candidatesTokenCount") or 0) + thoughts,
            "cached_input_tokens": int(meta.get("cachedContentTokenCount") or 0),
            "reasoning_tokens": thoughts,
        }
        blocked = (raw.get("promptFeedback") or {}).get("blockReason")
        if blocked:
            raise ProviderError("refusal", f"prompt blocked: {blocked}", provider=self.provider)
        candidates = raw.get("candidates")
        if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
            raise ProviderError("malformed", "no candidates", provider=self.provider)
        candidate = candidates[0]
        finish = candidate.get("finishReason") or "unknown"
        if finish == "MAX_TOKENS":
            raise ProviderError("truncated", f"output reached maxOutputTokens={self.max_output_tokens}", provider=self.provider)
        if finish in BLOCKED_FINISH:
            raise ProviderError("refusal", f"finish reason {finish}", provider=self.provider)
        parts = (candidate.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought"))
        if not text.strip():
            raise ProviderError("malformed", "empty text content", provider=self.provider)
        return {"content": text, "usage": normalized, "finish_reason": finish, "model": self.last_model}

    def list_models(self):
        names, token = [], ""
        for _ in range(10):
            url = self.base_url + "/models?pageSize=1000" + (f"&pageToken={urllib.parse.quote(token)}" if token else "")
            raw = self.transport.request_json("GET", url, self._headers(), provider=self.provider, secrets=(self._key,))
            for m in raw.get("models", []):
                if isinstance(m, dict) and "generateContent" in (m.get("supportedGenerationMethods") or []):
                    names.append(str(m.get("name", "")).removeprefix("models/"))
            token = raw.get("nextPageToken") or ""
            if not token:
                break
        return sorted(n for n in names if n)
