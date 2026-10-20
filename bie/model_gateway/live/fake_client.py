"""Deterministic fake provider client: offline, repeatable, schema-shaped output.

It implements the client methods of all three adapters (``messages_create``,
``responses_create``, ``generate``), so tests drive the real adapter → gateway → validation →
ledger path without network or keys. Fake output proves execution, never teaching quality.

``script`` injects behaviour per call, in order: a ``ProviderError`` kind such as
``"rate_limit"`` raises that error; ``"invalid"`` returns JSON that breaks the schema;
``"garbage"`` returns text that is not JSON; ``"ok"`` (or an exhausted script) returns valid output.
"""
from __future__ import annotations

import hashlib
import json

from .errors import KINDS, ProviderError
from .messages import split_messages


def sample(schema, seed: str, path: str = "$"):
    """A value that satisfies ``schema``, derived only from ``seed`` and the path."""
    schema = schema or {}
    digest = hashlib.sha256((seed + "\0" + path).encode()).hexdigest()
    if "enum" in schema:
        options = list(schema["enum"])
        return options[int(digest[:8], 16) % len(options)]
    kind = schema.get("type")
    if kind == "object":
        return {name: sample(child, seed, f"{path}.{name}") for name, child in (schema.get("properties") or {}).items()}
    if kind == "array":
        low = int(schema.get("minItems", 1))
        high = int(schema.get("maxItems", max(low, 2)))
        count = max(low, min(high, max(low, 2)))
        return [sample(schema.get("items") or {}, seed, f"{path}[{i}]") for i in range(count)]
    if kind == "integer":
        if path.endswith("_number") and "[" in path:
            return int(path.rsplit("[", 1)[1].split("]", 1)[0]) + 1  # sequence numbers count 1, 2, 3 ...
        return 1 + int(digest[:4], 16) % 3
    if kind == "number":
        return round((int(digest[:4], 16) % 1000) / 10, 1)
    if kind == "boolean":
        return int(digest[:2], 16) % 2 == 0
    text = f"Fake {path.rsplit('.', 1)[-1]} {digest[:8]}"
    return text.ljust(int(schema.get("minLength", 0)), ".")


class FakeProviderClient:
    def __init__(self, provider: str = "fake", *, script=(), usage=(1200, 800)):
        for step in script:
            if step not in KINDS and step not in ("ok", "invalid", "garbage"):
                raise ValueError("unknown fake script step: " + str(step))
        self.provider = provider
        self.script = list(script)
        self.usage = usage
        self.calls = []
        self.last_model = None

    def _respond(self, model, messages, schema):
        split_messages(messages, provider=self.provider)
        self.calls.append({"model": model, "messages": [dict(m) for m in messages], "schema": schema})
        step = self.script.pop(0) if self.script else "ok"
        if step in KINDS:
            raise ProviderError(step, "scripted fake failure", provider=self.provider)
        self.last_model = f"fake-{model}"
        seed = hashlib.sha256(json.dumps([model, list(messages)], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if step == "garbage":
            content = "I cannot produce JSON right now."
        elif step == "invalid":
            content = json.dumps({"unexpected": True})
        else:
            content = json.dumps(sample(schema, seed) if schema else {"text": "fake " + seed[:8]}, ensure_ascii=False)
        usage = {"input_tokens": self.usage[0], "output_tokens": self.usage[1], "cached_input_tokens": 0, "reasoning_tokens": 0}
        return {"content": content, "usage": usage, "finish_reason": "stop", "model": self.last_model}

    def messages_create(self, *, model, messages, schema=None):
        return self._respond(model, messages, schema)

    def responses_create(self, *, model, messages, response_schema=None):
        return self._respond(model, messages, response_schema)

    def generate(self, *, model, messages, schema=None):
        return self._respond(model, messages, schema)

    def list_models(self):
        return ["fake-large", "fake-small"]
