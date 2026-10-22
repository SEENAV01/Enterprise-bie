"""The cost guard ("pahra"): a hard rupee cap per run, checked before every provider call, and a preflight.

Cap. ``CostGuard(max_inr)`` is handed to ``LiveGateway``. Before each call (first attempts, retries and
repair turns alike) the gateway asks the guard to reserve the call's projected cost; if the money already
spent, plus the calls still running, plus this projection would cross the cap, the call is not sent:
``BudgetExceeded`` (kind ``budget``) is raised and the guard stays stopped, so every later call is refused
too and the work that already passed is kept. After the call the reservation is replaced by its real
ledger cost. A call that is already running is never cut off, so the final ledger total can pass the cap
by at most the difference between projected and real cost of the calls in flight.

Projection. Input tokens are counted from the request itself (text characters, the schema, a fixed
allowance per page image); output tokens are the average this run has seen for the same model, section
and role, else ``DEFAULT_OUTPUT_TOKENS``, never more than the client's output cap. Prices come from
``pricing.py``. A model without a price is refused (fail closed) until it is priced.

Balance. When a provider says the wallet, key budget or quota is used up (error kind ``balance``), the
gateway trips the guard as well, so the run stops instead of sending more calls that cannot succeed.

Preflight. ``preflight(gateway)`` sends one tiny structured call per route before a live run (and, for
AICredits routes, reads the free wallet balance). Any failure stops the run before real work is spent.

Rupees. All ledger costs are price-table ESTIMATES in USD from exact token counts (``pricing.py``),
converted at ``BIE_USD_INR`` (default ``DEFAULT_USD_INR``, the AICredits rate of 20 October 2026, not a
live rate). The real bill is what the provider dashboard shows; runs keep a slot for it to compare.
"""
from __future__ import annotations

import json
import os
import threading

from ..model_interface import ModelRequest
from .errors import ProviderError
from .pricing import VIA_MARKUP, price_for

DEFAULT_USD_INR = 94.59         # AICredits exchange_rate in api.aicredits.in/api/models (last_updated 2026-10-20)
DEFAULT_OUTPUT_TOKENS = 8000    # first call of a kind: about the measured maker output of one page (Task 039 ledgers)
DEFAULT_OUTPUT_CAP = 16000
IMAGE_TOKENS = 1600             # allowance per page image (a 1568 px page is about 1,100-1,600 tokens)
MESSAGE_OVERHEAD = 50
COST_NOTE = ("Ledger cost is an estimate: exact token counts times the dated price table in "
             "bie/model_gateway/live/pricing.py (plus the AICredits 10% markup), converted at usd_inr. "
             "It is not the bill. Write the provider dashboard amount for this run into real_bill_inr "
             "(and docs/roadmap/COST_LOG.md) to compare.")
PREFLIGHT_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["status"],
                    "properties": {"status": {"type": "string", "enum": ["ready"]}}}
PREFLIGHT_VERSION = "bie-preflight/1"
STOP_KINDS = frozenset({"budget", "balance"})


class BudgetExceeded(ProviderError):
    """BIE's own cap (or a used-up provider balance) stopped a call before it was sent."""

    def __init__(self, message: str, *, provider: str | None = None):
        super().__init__("budget", message, provider=provider)


def usd_inr(env=None) -> float:
    raw = ((env if env is not None else os.environ).get("BIE_USD_INR") or "").strip()
    if not raw:
        return DEFAULT_USD_INR
    rate = float(raw)
    if not 1.0 <= rate <= 1000.0:
        raise ValueError("BIE_USD_INR must be a rupees-per-dollar rate")
    return rate


def section_of(request_id: str) -> str:
    """``understand:page-003:r1:review`` -> ``understand``."""
    return str(request_id).split(":", 1)[0] or "other"


def role_of(request_id: str) -> str:
    return "review" if str(request_id).endswith(":review") else "make"


def input_tokens(messages, schema=None) -> int:
    """A deliberately generous token count for a request: ASCII text at 3.5 characters per token, other
    scripts (Devanagari Hinglish) at one character per token, a fixed allowance per image."""
    ascii_chars = other_chars = images = 0
    texts = [json.dumps(schema, ensure_ascii=False)] if schema is not None else []
    for message in messages:
        content = message.get("content")
        parts = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
        for part in parts:
            if part.get("type") == "image":
                images += 1
            else:
                texts.append(str(part.get("text") or ""))
    for text in texts:
        ascii_count = len(text.encode("ascii", "ignore"))
        ascii_chars += ascii_count
        other_chars += len(text) - ascii_count
    return int(ascii_chars / 3.5 + other_chars + images * IMAGE_TOKENS) + MESSAGE_OVERHEAD * max(1, len(messages))


def output_cap(adapter) -> int:
    client = getattr(adapter, "client", None)
    for name in ("max_tokens", "max_output_tokens"):
        value = getattr(client, name, None)
        if isinstance(value, int) and value > 0:
            return value
    return DEFAULT_OUTPUT_CAP


class CostGuard:
    """A thread-safe rupee cap for one run (see the module docstring)."""

    def __init__(self, max_inr: float, *, rate: float | None = None, env=None):
        if max_inr is None or float(max_inr) <= 0:
            raise ValueError("max_inr must be a positive number of rupees")
        self.max_inr = float(max_inr)
        self.rate = float(rate) if rate is not None else usd_inr(env)
        self._env = env
        self._lock = threading.Lock()
        self.spent_usd = 0.0
        self.in_flight_usd = 0.0
        self.by_section = {}
        self.calls = 0
        self.refused = 0
        self.stop_reason = None
        self._outputs = {}

    @property
    def max_usd(self) -> float:
        return self.max_inr / self.rate

    @property
    def spent_inr(self) -> float:
        return round(self.spent_usd * self.rate, 2)

    @property
    def stopped(self) -> bool:
        return self.stop_reason is not None

    def expected_output(self, model, request_id, cap) -> int:
        seen = self._outputs.get((model, section_of(request_id), role_of(request_id)))
        expected = round(seen[0] / seen[1]) if seen else DEFAULT_OUTPUT_TOKENS
        return max(1, min(int(cap), expected))

    def project(self, *, model, via, request: ModelRequest, messages=None, cap=DEFAULT_OUTPUT_CAP,
                expected_output_tokens=None) -> dict:
        """The projected tokens and USD of one call; ``usd`` is None when the model has no price."""
        tokens_in = input_tokens(messages if messages is not None else request.messages, request.response_schema)
        tokens_out = (max(1, min(int(cap), int(expected_output_tokens))) if expected_output_tokens
                      else self.expected_output(model, request.request_id, cap))
        price = price_for(model, self._env)
        usd = None if price is None else (tokens_in * price[0] + tokens_out * price[1]) / 1e6 * VIA_MARKUP.get(via, 1.0)
        return {"input_tokens": tokens_in, "output_tokens": tokens_out, "usd": usd}

    def reserve(self, request_id: str, projected_usd, *, model: str = "", provider: str | None = None) -> float:
        """Reserve a call's projected cost or raise ``BudgetExceeded`` (and stay stopped)."""
        with self._lock:
            if self.stop_reason is None and projected_usd is None:
                self.stop_reason = f"no price for model {model}; add it to pricing.py or BIE_MODEL_PRICES_JSON"
            if self.stop_reason is None and self.spent_usd + self.in_flight_usd + projected_usd > self.max_usd:
                self.stop_reason = (f"budget: the next call ({request_id}, about Rs {projected_usd * self.rate:.2f}) would cross "
                                    f"the cap of Rs {self.max_inr:g} (spent Rs {self.spent_usd * self.rate:.2f}, "
                                    f"running Rs {self.in_flight_usd * self.rate:.2f})")
            if self.stop_reason is not None:
                self.refused += 1
                raise BudgetExceeded(self.stop_reason, provider=provider)
            self.in_flight_usd += projected_usd
            self.calls += 1
            return projected_usd

    def settle(self, request_id: str, reserved_usd: float, actual_usd, *, model: str = "", output_tokens: int | None = None):
        """Replace a reservation by the call's ledger cost (the reservation itself when the cost is unknown)."""
        cost = reserved_usd if actual_usd is None else float(actual_usd)
        with self._lock:
            self.in_flight_usd = max(0.0, self.in_flight_usd - reserved_usd)
            self.spent_usd += cost
            section = section_of(request_id)
            self.by_section[section] = self.by_section.get(section, 0.0) + cost
            if output_tokens:
                key = (model, section, role_of(request_id))
                total, count = self._outputs.get(key, (0, 0))
                self._outputs[key] = (total + int(output_tokens), count + 1)

    def trip(self, reason: str):
        with self._lock:
            if self.stop_reason is None:
                self.stop_reason = reason

    def restore(self, reason):
        """Put back an earlier stop state (preflight checks every route on its own)."""
        with self._lock:
            self.stop_reason = reason

    def report(self) -> dict:
        with self._lock:
            return {"cap_inr": self.max_inr, "usd_inr": self.rate, "spent_inr": round(self.spent_usd * self.rate, 2),
                    "spent_usd": round(self.spent_usd, 6), "calls_allowed": self.calls, "calls_refused": self.refused,
                    "stopped": self.stop_reason is not None, "stop_reason": self.stop_reason,
                    "by_section_inr": {k: round(v * self.rate, 2) for k, v in sorted(self.by_section.items())}}


def preflight(gateway, routes=None, *, wallet=True) -> dict:
    """One tiny structured call per route, plus the free AICredits wallet balance where the route has one.

    Returns ``{"passed": bool, "routes": {route: {...}}}``. A failed route carries its error kind and a
    short, already redacted message; the caller stops the run before any real work. Every route is checked
    on its own: one route's used-up balance does not hide the state of the others. After a failed
    preflight the guard is left stopped."""
    guard = getattr(gateway, "guard", None)
    out = {}
    for route in routes or list(gateway.routes):
        adapter = gateway.routes[route]
        client = getattr(adapter, "client", None)
        entry = {"model": adapter.model, "via": getattr(client, "via", "direct")}
        if wallet and callable(getattr(client, "credits", None)):
            try:
                entry["wallet"] = client.credits()
            except ProviderError as exc:
                entry["wallet"] = {"unavailable": exc.kind}
        request = ModelRequest(request_id=f"preflight:{route}", response_schema=PREFLIGHT_SCHEMA, messages=(
            {"role": "system", "content": "You are a health check. Answer with JSON only."},
            {"role": "user", "content": "Set status to ready."}))
        before = guard.stop_reason if guard is not None else None
        try:
            response = gateway.complete(route, request, prompt_version=PREFLIGHT_VERSION, expected_output_tokens=50)
            entry.update(status="ok", returned_model=response.provenance.get("returned_model"),
                         input_tokens=response.usage.get("input_tokens", 0), output_tokens=response.usage.get("output_tokens", 0))
        except ProviderError as exc:
            entry.update(status="failed", error_kind=exc.kind, error=exc.message[:240])
            if guard is not None:
                guard.restore(before)
        out[route] = entry
    passed = all(e["status"] == "ok" for e in out.values())
    if guard is not None and not passed:
        guard.trip("preflight: " + ", ".join(f"{r} {e['error_kind']}" for r, e in out.items() if e["status"] != "ok"))
    return {"passed": passed, "routes": out}


PREFLIGHT_ADVICE = {
    "balance": "the wallet, key budget or quota is used up: top up or raise the key budget on the provider dashboard",
    "budget": "the cap (max_inr) is too small even for the preflight call",
    "auth": "the key is wrong, expired or not allowed to use this model",
    "not_found": "the model name is not available on this key: run the probe mode",
    "config": "a key or setting is missing",
}


def preflight_message(route: str, entry: dict) -> str:
    kind = entry.get("error_kind", "")
    return (f"{route} ({entry.get('model')} via {entry.get('via')}): {kind} - "
            f"{PREFLIGHT_ADVICE.get(kind, 'the provider did not answer the tiny test call')}. "
            f"Provider said: {entry.get('error', '')}")
