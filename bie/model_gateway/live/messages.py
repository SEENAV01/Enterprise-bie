"""Shared message and schema helpers for the provider clients.

BIE messages are ``{"role": "system" | "user" | "assistant", "content": str | list}``. A list holds
parts: ``{"type": "text", "text": str}`` or ``{"type": "image", "media_type": "image/png" |
"image/jpeg" | "image/webp", "data": <base64>}``. Images are allowed only in user turns; system
text stays plain. Each client turns parts into its provider's format (``*_parts`` below). Each
provider receives the schema keywords it accepts; the gateway always validates the full schema
locally.
"""
from __future__ import annotations

import base64
import binascii

from .errors import ProviderError

ROLES = ("system", "user", "assistant")
IMAGE_TYPES = ("image/png", "image/jpeg", "image/webp")
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def _check_parts(parts, *, role: str, provider: str):
    if not parts:
        raise ProviderError("config", "message parts must not be empty", provider=provider)
    for part in parts:
        kind = part.get("type") if isinstance(part, dict) else None
        if kind == "text" and isinstance(part.get("text"), str):
            continue
        if kind == "image":
            if role != "user":
                raise ProviderError("config", "images are allowed only in user messages", provider=provider)
            if part.get("media_type") not in IMAGE_TYPES or not isinstance(part.get("data"), str):
                raise ProviderError("config", "image part needs media_type and base64 data", provider=provider)
            try:
                size = len(base64.b64decode(part["data"], validate=True))
            except (binascii.Error, ValueError):
                raise ProviderError("config", "image data is not base64", provider=provider) from None
            if not 0 < size <= MAX_IMAGE_BYTES:
                raise ProviderError("config", "image must be 1 byte to 8 MiB", provider=provider)
            continue
        raise ProviderError("config", "unknown message part", provider=provider)


def text_of(content) -> str:
    """The text of a message, images left out."""
    if isinstance(content, str):
        return content
    return "\n".join(p["text"] for p in content if p.get("type") == "text")


def anthropic_parts(content):
    if isinstance(content, str):
        return content
    return [{"type": "text", "text": p["text"]} if p["type"] == "text" else
            {"type": "image", "source": {"type": "base64", "media_type": p["media_type"], "data": p["data"]}}
            for p in content]


def openai_responses_parts(content, role: str):
    if isinstance(content, str):
        return content
    if role != "user":
        return text_of(content)
    return [{"type": "input_text", "text": p["text"]} if p["type"] == "text" else
            {"type": "input_image", "image_url": f"data:{p['media_type']};base64,{p['data']}"} for p in content]


def gemini_parts(content):
    if isinstance(content, str):
        return [{"text": content}]
    return [{"text": p["text"]} if p["type"] == "text" else {"inlineData": {"mimeType": p["media_type"], "data": p["data"]}}
            for p in content]


def chat_parts(content, role: str):
    """OpenAI Chat Completions format, used by OpenAI-compatible resellers."""
    if isinstance(content, str):
        return content
    if role != "user":
        return text_of(content)
    return [{"type": "text", "text": p["text"]} if p["type"] == "text" else
            {"type": "image_url", "image_url": {"url": f"data:{p['media_type']};base64,{p['data']}"}} for p in content]

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
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(message, dict) or message.get("role") not in ROLES or not isinstance(content, (str, list, tuple)):
            raise ProviderError("config", "message must have role and text content", provider=provider)
        if not isinstance(content, str):
            content = list(content)
            _check_parts(content, role=message["role"], provider=provider)
        if message["role"] == "system":
            if conversation:
                raise ProviderError("config", "system messages must come first", provider=provider)
            if not isinstance(content, str):
                raise ProviderError("config", "system messages must be plain text", provider=provider)
            system.append(content)
        else:
            conversation.append({"role": message["role"], "content": content})
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
