"""Shared message and schema helpers for the provider clients.

BIE messages are ``{"role": "system" | "user" | "assistant", "content": str}``. Each provider
receives the schema keywords it accepts; the gateway always validates the full schema locally.
"""
from __future__ import annotations

from .errors import ProviderError

ROLES = ("system", "user", "assistant")

# Keywords each provider's structured-output mode accepts. Anything else is removed before sending
# (the local validator still enforces it). Anthropic: additionalProperties must be false, no
# length/count/numeric bounds (minItems only 0 or 1). OpenAI strict mode: all properties required,
# additionalProperties false. Gemini responseJsonSchema: a JSON Schema subset with item counts.
_COMMON = {"type", "properties", "required", "items", "enum", "description", "title"}
ALLOWED_KEYWORDS = {
    "anthropic": _COMMON | {"additionalProperties"},
    "openai": _COMMON | {"additionalProperties"},
    "google": _COMMON | {"minItems", "maxItems"},
    "fake": None,
}


def split_messages(messages, *, provider: str):
    """Validate messages; return (system_text, conversation) with system turns joined."""
    if not messages:
        raise ProviderError("config", "messages required", provider=provider)
    system, conversation = [], []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in ROLES or not isinstance(message.get("content"), str):
            raise ProviderError("config", "message must have role and text content", provider=provider)
        if message["role"] == "system":
            if conversation:
                raise ProviderError("config", "system messages must come first", provider=provider)
            system.append(message["content"])
        else:
            conversation.append({"role": message["role"], "content": message["content"]})
    if not conversation or conversation[0]["role"] != "user":
        raise ProviderError("config", "the conversation must start with a user message", provider=provider)
    return "\n\n".join(system), conversation


def provider_schema(schema, provider: str):
    """A copy of ``schema`` with only the keywords ``provider`` accepts."""
    allowed = ALLOWED_KEYWORDS.get(provider)
    if schema is None or allowed is None:
        return schema

    def strip(node):
        if isinstance(node, dict):
            out = {}
            for key, value in node.items():
                if key == "properties" and isinstance(value, dict):
                    out[key] = {name: strip(child) for name, child in value.items()}
                elif key in allowed:
                    out[key] = strip(value) if key == "items" else value
            return out
        return node

    return strip(schema)
