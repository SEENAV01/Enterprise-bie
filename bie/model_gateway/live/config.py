"""Build live or fake routes from environment variables.

Keys: ``ANTHROPIC_API_KEY``, ``OPENAI_API_KEY``, ``GEMINI_API_KEY`` (``GOOGLE_API_KEY`` is accepted
too). Models: ``BIE_ANTHROPIC_MODEL``, ``BIE_OPENAI_MODEL``, ``BIE_GEMINI_MODEL``, else the
defaults below. A provider without a key is reported as not configured; it is never faked
silently. The fake routes are used only when asked for explicitly.
"""
from __future__ import annotations

import os

from ..claude_adapter import ClaudeAdapter
from ..gemini_adapter import GeminiAdapter
from ..gpt_adapter import GPTAdapter
from .anthropic_client import AnthropicClient
from .fake_client import FakeProviderClient
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient
from .transport import HttpTransport

PROVIDERS = ("anthropic", "openai", "google")
KEY_ENV = {"anthropic": ("ANTHROPIC_API_KEY",), "openai": ("OPENAI_API_KEY",), "google": ("GEMINI_API_KEY", "GOOGLE_API_KEY")}
MODEL_ENV = {"anthropic": "BIE_ANTHROPIC_MODEL", "openai": "BIE_OPENAI_MODEL", "google": "BIE_GEMINI_MODEL"}
# Defaults are each provider's flagship as far as public sources showed on 2026-10-20. The probe
# run (tools/run_blind_test.py --mode probe) lists the models each key can really use; change a
# default only after that list confirms the name.
DEFAULT_MODELS = {"anthropic": "claude-opus-5-5", "openai": "gpt-6.1-sol", "google": "gemini-3.1-pro"}
ADAPTERS = {"anthropic": ClaudeAdapter, "openai": GPTAdapter, "google": GeminiAdapter}


def key_for(provider: str, env=None) -> str:
    env = os.environ if env is None else env
    for name in KEY_ENV[provider]:
        value = (env.get(name) or "").strip()
        if value:
            return value
    return ""


def model_for(provider: str, env=None) -> str:
    env = os.environ if env is None else env
    return (env.get(MODEL_ENV[provider]) or "").strip() or DEFAULT_MODELS[provider]


def make_client(provider: str, key: str, *, timeout: float = 600.0):
    transport = HttpTransport(timeout=timeout)
    if provider == "anthropic":
        return AnthropicClient(key, transport=transport)
    if provider == "openai":
        return OpenAIClient(key, transport=transport)
    if provider == "google":
        return GeminiClient(key, transport=transport)
    raise ValueError("unknown provider " + repr(provider))


def build_routes(providers=PROVIDERS, *, env=None, fake=False, fake_scripts=None, timeout: float = 600.0):
    """Return (routes, not_configured): adapters keyed by provider, and providers without a key."""
    routes, missing = {}, []
    for provider in providers:
        if provider not in PROVIDERS:
            raise ValueError("unknown provider " + repr(provider))
        model = model_for(provider, env)
        if fake:
            client = FakeProviderClient(provider, script=(fake_scripts or {}).get(provider, ()))
        else:
            key = key_for(provider, env)
            if not key:
                missing.append(provider)
                continue
            client = make_client(provider, key, timeout=timeout)
        routes[provider] = ADAPTERS[provider](client, model)
    return routes, missing
