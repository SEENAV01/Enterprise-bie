"""Build live or fake routes from environment variables.

Direct keys: ``ANTHROPIC_API_KEY``, ``OPENAI_API_KEY``, ``GEMINI_API_KEY`` (``GOOGLE_API_KEY`` is
accepted too). Reseller key: ``AICREDITS_API_KEY`` (aicredits.in, one OpenAI-compatible endpoint
for many providers' models). Route per provider: ``BIE_<PROVIDER>_VIA`` = ``direct`` or
``aicredits`` forces it; otherwise a direct key wins and the AICredits key is the fallback.
Models: ``BIE_ANTHROPIC_MODEL``, ``BIE_OPENAI_MODEL``, ``BIE_GEMINI_MODEL``, else the route's
default below. A provider without any key is reported as not configured; it is never faked
silently. The fake routes are used only when asked for explicitly.
"""
from __future__ import annotations

import os

from ..claude_adapter import ClaudeAdapter
from ..gemini_adapter import GeminiAdapter
from ..gpt_adapter import GPTAdapter
from .anthropic_client import AnthropicClient
from .compat_client import OpenAICompatChatClient
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
VIAS = ("direct", "aicredits")
VIA_ENV = {"anthropic": "BIE_ANTHROPIC_VIA", "openai": "BIE_OPENAI_VIA", "google": "BIE_GEMINI_VIA"}
RESELLER_KEY_ENV = {"aicredits": "AICREDITS_API_KEY"}
# Navin keeps one AICredits key per model family; the shared key is the fallback.
RESELLER_PROVIDER_KEY_ENV = {"aicredits": {"anthropic": "AICREDITS_ANTHROPIC_API_KEY", "openai": "AICREDITS_OPENAI_API_KEY",
                                           "google": "AICREDITS_GEMINI_API_KEY"}}
# AICredits model ids from aicredits.in/models (read 2026-10-20); the probe run confirms them.
DEFAULT_MODELS_VIA = {"direct": DEFAULT_MODELS,
                      "aicredits": {"anthropic": "anthropic/claude-opus-5.5", "openai": "openai/gpt-5",
                                    "google": "google/gemini-4-argon"}}


def key_for(provider: str, env=None) -> str:
    """The direct key for ``provider`` (empty when not set)."""
    env = os.environ if env is None else env
    for name in KEY_ENV[provider]:
        value = (env.get(name) or "").strip()
        if value:
            return value
    return ""


def route_for(provider: str, env=None):
    """(via, key) for ``provider``: a forced route, else direct, else AICredits; ("", "") when none."""
    env = os.environ if env is None else env
    forced = (env.get(VIA_ENV[provider]) or "").strip().lower()
    if forced and forced not in VIAS:
        raise ValueError(f"{VIA_ENV[provider]} must be one of {', '.join(VIAS)}")
    direct = key_for(provider, env)
    reseller = ((env.get(RESELLER_PROVIDER_KEY_ENV["aicredits"][provider]) or "").strip()
                or (env.get(RESELLER_KEY_ENV["aicredits"]) or "").strip())
    if forced == "direct" or (not forced and direct):
        return ("direct", direct) if direct else ("", "")
    if forced == "aicredits" or reseller:
        return ("aicredits", reseller) if reseller else ("", "")
    return "", ""


def all_keys(env=None):
    env = os.environ if env is None else env
    names = list(RESELLER_KEY_ENV.values()) + [n for per in RESELLER_PROVIDER_KEY_ENV.values() for n in per.values()]
    keys = [key_for(p, env) for p in PROVIDERS] + [(env.get(n) or "").strip() for n in names]
    return [k for k in keys if k]


def model_for(provider: str, env=None, via: str = "direct") -> str:
    env = os.environ if env is None else env
    return (env.get(MODEL_ENV[provider]) or "").strip() or DEFAULT_MODELS_VIA[via or "direct"][provider]


def make_client(provider: str, key: str, *, via: str = "direct", timeout: float = 600.0):
    transport = HttpTransport(timeout=timeout)
    if via == "aicredits":
        return OpenAICompatChatClient(key, via="aicredits", transport=transport)
    if via != "direct":
        raise ValueError("unknown route " + repr(via))
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
        if fake:
            client = FakeProviderClient(provider, script=(fake_scripts or {}).get(provider, ()))
            model = model_for(provider, env)
        else:
            via, key = route_for(provider, env)
            if not key:
                missing.append(provider)
                continue
            client = make_client(provider, key, via=via, timeout=timeout)
            model = model_for(provider, env, via)
        routes[provider] = ADAPTERS[provider](client, model)
    return routes, missing
