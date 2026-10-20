"""Cost estimates per call from token counts.

Token counts come from the provider and are exact. Prices are ESTIMATES copied from public
secondary sources on the dates shown and must be checked against each provider's own pricing
page before any budget decision. Unknown models report ``cost_usd: null``; nothing is guessed.
Override or extend with ``BIE_MODEL_PRICES_JSON='{"model-prefix": [input_per_1m, output_per_1m]}'``.
"""
from __future__ import annotations

import json
import os

# model prefix -> (USD per 1M input tokens, USD per 1M output tokens, source note)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, "anotherwrapper.com citing Anthropic pricing, 2026-10-19; aicredits.in/models 2026-10-20"),
    "claude-sonnet-5-5": (2.00, 10.00, "aicredits.in/models USD list price, 2026-10-20"),
    "claude-fable-5-1": (10.00, 50.00, "aicredits.in/models USD list price, 2026-10-20"),
    "gpt-6-astra": (10.00, 50.00, "magora-systems.com, checked 2026-10-13"),
    "gpt-6.1-sol": (2.00, 10.00, "magora-systems.com, checked 2026-10-13"),
    "gpt-6-luna": (0.10, 0.50, "magora-systems.com, checked 2026-10-13"),
    "gemini-3.1-pro": (2.00, 12.00, "morphllm.com 2026-08-21; aicredits.in/models 2026-10-20 (<=200k context)"),
    "gemini-3.5-flash": (1.50, 9.00, "morphllm.com, checked 2026-08-21"),
    "gemini-2.5-pro": (1.25, 10.00, "morphllm.com, checked 2026-08-21 (<=200k context)"),
    "gemini-2.5-flash": (0.30, 2.50, "morphllm.com, checked 2026-08-21"),
    "fake": (0.0, 0.0, "offline fake provider"),
}
VERIFIED = False
# Resellers bill on top of the provider price. AICredits: 5% platform fee + 5% forex buffer (aicredits.in, 2026-10-20).
VIA_MARKUP = {"direct": 1.0, "aicredits": 1.10}


def normalize(model: str) -> str:
    """Reseller ids to provider ids: ``anthropic/claude-opus-5.5`` -> ``claude-opus-5-5``."""
    name = model.removeprefix("models/")
    if "/" in name:
        name = name.split("/", 1)[1]
    if name.startswith("claude-"):
        name = name.replace(".", "-")
    return name


def _table(env=None):
    table = dict(PRICES)
    raw = (env if env is not None else os.environ).get("BIE_MODEL_PRICES_JSON")
    if raw:
        for prefix, pair in json.loads(raw).items():
            table[str(prefix)] = (float(pair[0]), float(pair[1]), "BIE_MODEL_PRICES_JSON override")
    return table


def price_for(model: str | None, env=None):
    """(input_per_1m, output_per_1m, source) for the longest matching prefix, or None."""
    if not model:
        return None
    name = normalize(model)
    matches = [p for p in _table(env) if name == p or name.startswith(p + "-") or name.startswith(p + "@")]
    if not matches:
        return None
    return _table(env)[max(matches, key=len)]


def estimate_cost(model: str | None, usage: dict, env=None, via: str = "direct"):
    price = price_for(model, env)
    if price is None:
        return None
    cost = usage.get("input_tokens", 0) * price[0] / 1e6 + usage.get("output_tokens", 0) * price[1] / 1e6
    return round(cost * VIA_MARKUP.get(via, 1.0), 6)
