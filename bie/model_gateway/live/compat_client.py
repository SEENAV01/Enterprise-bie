"""OpenAI-compatible Chat Completions client for reseller gateways (first: AICredits, aicredits.in).

Navin pays for Claude and Gemini through AICredits (rupee wallet, UPI). AICredits exposes many
providers' models behind one OpenAI-compatible endpoint (``https://api.aicredits.in/v1``, Bearer
``sk-`` key, model ids such as ``anthropic/claude-opus-5.5``). Source: aicredits.in/docs/api-reference
and aicredits.in/models, read 2026-10-20.

The client plugs into the existing ``ClaudeAdapter`` (``messages_create``) and ``GeminiAdapter``
(``generate``), so the gateway, ledger and blind test treat it like a direct connection; ``via``
records the route. Its documented JSON mode is ``{"type": "json_object"}``, so the schema is always
written into the system message as well; ``json_schema`` is tried first and dropped for good if the
gateway rejects it. ``no_cache`` is always sent: the gateway's own semantic cache must never answer
for the model. The gateway always validates the schema locally.
"""
from __future__ import annotations

import json
import urllib.parse

from .errors import ProviderError, classify
from .messages import chat_parts, split_messages
from .transport import HttpTransport

AICREDITS_BASE_URL = "https://api.aicredits.in/v1"
SCHEMA_INSTRUCTION = ("Reply with one JSON object only, no prose and no code fences. It must match this JSON schema "
                      "exactly (every listed field, no extra fields):\n{schema}")


class OpenAICompatChatClient:
    def __init__(self, api_key: str, *, via: str = "aicredits", base_url: str = AICREDITS_BASE_URL,
                 transport: HttpTransport | None = None, max_tokens: int = 16000, models_url: str | None = None,
                 stream: bool = False):
        if not api_key:
            raise ProviderError("config", f"the {via} API key is not set", provider=via)
        self._key = api_key
        self.via = via
        self.provider = via
        self.base_url = base_url.rstrip("/")
        parts = urllib.parse.urlsplit(self.base_url)
        self.models_url = models_url or f"{parts.scheme}://{parts.netloc}/api/models"
        self.transport = transport or HttpTransport()
        self.max_tokens = max_tokens
        self.schema_mode = "json_schema"
        self.stream = stream
        self.last_model = None

    def _headers(self):
        return {"authorization": "Bearer " + self._key}

    def _body(self, model, messages, schema):
        system, conversation = split_messages(messages, provider=self.via)
        if schema is not None:
            system = (system + "\n\n" if system else "") + SCHEMA_INSTRUCTION.format(schema=json.dumps(schema, ensure_ascii=False))
        chat = ([{"role": "system", "content": system}] if system else []) + [
            {"role": m["role"], "content": chat_parts(m["content"], m["role"])} for m in conversation]
        body = {"model": model, "messages": chat, "max_tokens": self.max_tokens, "no_cache": True}
        if schema is not None:
            body["response_format"] = ({"type": "json_schema", "json_schema": {"name": "bie_output", "schema": schema}}
                                       if self.schema_mode == "json_schema" else {"type": "json_object"})
        return body

    def _send(self, body):
        if not self.stream:
            return self.transport.request_json("POST", self.base_url + "/chat/completions", self._headers(), body,
                                               provider=self.via, secrets=(self._key,))
        body = dict(body, stream=True, stream_options={"include_usage": True})
        texts, refusals, raw = [], [], {"usage": {}}
        finish = None
        for event in self.transport.request_events("POST", self.base_url + "/chat/completions", self._headers(), body,
                                                   provider=self.via, secrets=(self._key,)):
            if isinstance(event.get("error"), dict):
                return {"error": event["error"]}
            raw["model"] = event.get("model") or raw.get("model")
            if event.get("usage"):
                raw["usage"] = event["usage"]
            for choice in event.get("choices") or []:
                delta = choice.get("delta") or {}
                if isinstance(delta.get("content"), str):
                    texts.append(delta["content"])
                if delta.get("refusal"):
                    refusals.append(delta["refusal"])
                finish = choice.get("finish_reason") or finish
        raw["choices"] = [{"message": {"content": "".join(texts), "refusal": "".join(refusals) or None},
                           "finish_reason": finish or "stop"}]
        return raw

    def chat(self, *, model, messages, schema=None):
        try:
            raw = self._send(self._body(model, messages, schema))
        except ProviderError as exc:
            if exc.kind != "bad_request" or schema is None or self.schema_mode != "json_schema":
                raise
            self.schema_mode = "json_object"  # this gateway does not take json_schema; keep the prompt-level schema
            raw = self._send(self._body(model, messages, schema))
        return self.parse(raw)

    # The adapters' method names.
    def messages_create(self, *, model, messages, schema=None):
        return self.chat(model=model, messages=messages, schema=schema)

    def generate(self, *, model, messages, schema=None):
        return self.chat(model=model, messages=messages, schema=schema)

    def responses_create(self, *, model, messages, response_schema=None):
        return self.chat(model=model, messages=messages, schema=response_schema)

    def parse(self, raw):
        if isinstance(raw.get("error"), dict):
            error = raw["error"]
            text = " | ".join(str(error.get(k)) for k in ("type", "code", "message") if error.get(k)) or "error"
            raise ProviderError(classify(None, text), text[:300], provider=self.via)
        self.last_model = raw.get("model")
        usage = raw.get("usage") or {}
        details = usage.get("completion_tokens_details") or {}
        normalized = {
            "input_tokens": int(usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("completion_tokens") or 0),
            "cached_input_tokens": int((usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0),
            "reasoning_tokens": int(details.get("reasoning_tokens") or 0),
        }
        choices = raw.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ProviderError("malformed", "no choices", provider=self.via)
        finish = choices[0].get("finish_reason") or "unknown"
        message = choices[0].get("message") or {}
        if finish == "length":
            raise ProviderError("truncated", f"output reached max_tokens={self.max_tokens}", provider=self.via)
        if finish == "content_filter" or (message.get("refusal") and not message.get("content")):
            raise ProviderError("refusal", str(message.get("refusal") or finish)[:300], provider=self.via)
        content = message.get("content")
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") in (None, "text"))
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("malformed", "empty message content", provider=self.via)
        return {"content": content, "usage": normalized, "finish_reason": finish, "model": self.last_model}

    def list_models(self):
        return [m["id"] for m in self.list_model_details()]

    def list_model_details(self):
        """Every model the gateway lists, with its published prices per 1M tokens.

        AICredits documents ``input_cost_per_1m``/``output_cost_per_1m``; its live list (read 2026-10-22) sends
        ``input_cost_per_token``, ``output_cost_per_token`` and ``cached_input_cost_per_token`` in USD, the same in
        INR (``*_inr``), its ``exchange_rate`` and ``last_updated``. Both forms are read."""
        raw = self.transport.request_json("GET", self.models_url, {}, provider=self.via, secrets=(self._key,))
        rows = []
        for m in raw.get("data", []):
            if not isinstance(m, dict) or not m.get("id"):
                continue
            row = {"id": str(m["id"])}
            for key in ("name", "exchange_rate", "last_updated"):
                if m.get(key) is not None:
                    row[key] = m[key]
            context = m.get("context_window", m.get("context_length"))
            if context is not None:
                row["context_window"] = context
            for currency, suffix in (("usd", ""), ("inr", "_inr")):
                prices = {}
                for kind in ("input", "output", "cached_input"):
                    per_token = m.get(f"{kind}_cost_per_token{suffix}")
                    per_million = m.get(f"{kind}_cost_per_1m{suffix}")
                    if isinstance(per_token, (int, float)):
                        prices[kind] = round(per_token * 1e6, 6)
                    elif isinstance(per_million, (int, float)):
                        prices[kind] = per_million
                if prices:
                    row[f"{currency}_per_1m"] = prices
            if isinstance(m.get("input_modalities"), list):
                row["input_modalities"] = m["input_modalities"]
            rows.append(row)
        return sorted(rows, key=lambda m: m["id"])

    def credits(self):
        """The key's wallet balance as the gateway reports it (``GET /v1/credits``, free, no tokens).

        The response format is not documented beyond "wallet balance in INR", so only numeric fields whose
        name mentions balance, credit, budget or remaining are kept."""
        raw = self.transport.request_json("GET", self.base_url + "/credits", self._headers(), provider=self.via,
                                          secrets=(self._key,))
        found = {}
        def walk(value, prefix=""):
            for name, item in (value.items() if isinstance(value, dict) else ()):
                path = prefix + str(name)
                if isinstance(item, dict):
                    walk(item, path + ".")
                elif isinstance(item, (int, float)) and not isinstance(item, bool) and any(
                        word in path.lower() for word in ("balance", "credit", "budget", "remaining", "inr")):
                    found[path] = item
        walk(raw)
        return found
