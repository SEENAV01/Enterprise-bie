"""Rupee estimate before a brain run, and rupees per section and per page after it.

The estimate is pages x cost per page per section. Only Section 1 has been measured on a whole real
chapter so far; the other sections carry an ASSUMED number until a live run measures them, and the
estimate says which is which. All numbers are ledger costs: exact token counts times the dated price
table (``bie/model_gateway/live/pricing.py``), not the provider's bill.

Measured basis (blindtest-results branch, chapter "10. Tissues and Its Types", 14 pages, maker
GPT-6.1 Sol direct, reviewer Gemini 4 Argon via AICredits, both priced at $2 / $10 per 1M tokens):
- understand: run 39620281561, all 14 pages incl. retries and remakes: $2.5286 -> $0.181 per page.
- connect (chapter map): run 39627682253, maker $0.7785 for 14 pages; the reviewer call failed there,
  so its share is assumed from run 39617164262 (2 pages, $0.052) -> about $0.06 per page.
- lesson: VM job t045b-tissue-lesson (job 2, 23 October 2026), maker Codex on the ChatGPT plan, checker Gemini 4 Argon:
  $1.1046 of checker for 14 pages, so $0.0789 per page is the reviewer's 16% share -> $0.493 per page on the basis. That
  run spoke 458 minutes; the time rule of 23 October (6-8 minutes per page) makes scripts about a quarter as long, so
  this basis is on the high side until the next lesson run is measured.
When the run's models are priced differently, the estimate scales by their blended price (output
tokens dominate: 30% input, 70% output price), maker 84% and reviewer 16% of the cost as measured.
"""
from __future__ import annotations

from bie.model_gateway.live.budget import section_of
from bie.model_gateway.live.pricing import price_for

# section -> (USD per page with the basis models, "measured" or "assumed", source)
PER_PAGE_USD = {
    "understand": (0.181, "measured", "run 39620281561, 14 pages"),
    "connect": (0.060, "measured", "run 39627682253 maker + run 39617164262 reviewer share"),
    "notes": (0.12, "assumed", "not measured yet; about two thirds of a page reading"),
    "game": (0.05, "assumed", "not measured yet; one design step per chapter"),
    "lesson": (0.493, "measured", "VM job t045b-tissue-lesson, 14 pages (458 minutes spoken, before the time rule)"),
    "director": (0.20, "assumed", "not measured yet; scenes with timed actions"),
    "visual": (0.25, "assumed", "not measured yet; asset choice by sight and layouts reviewed on frames"),
}
SECTIONS_OF_MODE = {
    "understand": ("understand", "connect"),
    "lesson": ("lesson",),
    "director": ("director",),
    "notes": ("notes",),
    "game": ("game",),
    "visual": ("visual",),
    "chain": ("understand", "connect", "notes", "game", "lesson", "director"),
}
BASIS_BLEND = 0.3 * 2.00 + 0.7 * 10.00
MAKER_SHARE = 0.84
SECTION_NAMES = {"understand": "Section 1 · page reading", "connect": "Section 1 · chapter map", "lesson": "Section 2 · lesson",
                 "director": "Section 3 · director", "visual": "Section 4 · visual", "game": "Section 6 · game design",
                 "notes": "Section 7 · notes", "preflight": "preflight"}


def _blend(model, env=None):
    price = price_for(model, env)
    return None if price is None else 0.3 * price[0] + 0.7 * price[1]


def price_scale(maker_model, reviewer_model, env=None, *, maker_subscription=False) -> float | None:
    """Price of these models against the measured basis; a subscription maker (Codex) adds no rupees."""
    maker, reviewer = (0.0 if maker_subscription else _blend(maker_model, env)), _blend(reviewer_model, env)
    if maker is None or reviewer is None:
        return None
    return (MAKER_SHARE * maker + (1 - MAKER_SHARE) * reviewer) / BASIS_BLEND


def estimate(mode: str, pages: int, *, rate: float, maker_model=None, reviewer_model=None, with_visual=False, env=None,
             maker_subscription=False) -> dict:
    """Rupees per section for ``pages`` pages. ``scale`` is None when a model has no price (estimate on the basis)."""
    sections = SECTIONS_OF_MODE[mode] + (("visual",) if mode == "chain" and with_visual else ())
    scale = (price_scale(maker_model, reviewer_model, env, maker_subscription=maker_subscription)
             if maker_model and reviewer_model else None)
    factor = 1.0 if scale is None else scale
    rows = {}
    for name in sections:
        usd, kind, source = PER_PAGE_USD[name]
        rows[name] = {"inr": round(pages * usd * factor * rate, 2), "inr_per_page": round(usd * factor * rate, 2),
                      "basis": kind, "source": source}
    total = round(sum(r["inr"] for r in rows.values()), 2)
    return {"pages": pages, "usd_inr": rate, "price_scale": None if scale is None else round(scale, 3),
            "maker_billing": "subscription" if maker_subscription else "api",
            "sections": rows, "total_inr": total,
            "measured_share_inr": round(sum(r["inr"] for r in rows.values() if r["basis"] == "measured"), 2)}


def actual(ledger_rows, *, pages: int, rate: float) -> dict:
    """Rupees per section and per page from the ledger rows of this run."""
    by = {}
    for row in ledger_rows:
        section = section_of(row.get("request_id") or "")
        entry = by.setdefault(section, {"calls": 0, "usd": 0.0})
        entry["calls"] += 1
        entry["usd"] += row.get("cost_usd") or 0.0
    out = {}
    for section, entry in sorted(by.items()):
        inr = entry["usd"] * rate
        out[section] = {"name": SECTION_NAMES.get(section, section), "calls": entry["calls"], "usd": round(entry["usd"], 6),
                        "inr": round(inr, 2), "inr_per_page": round(inr / pages, 2) if pages else None}
    total_usd = sum(e["usd"] for e in by.values())
    plan = [r for r in ledger_rows if r.get("billing") == "subscription"]
    subscription = None
    if plan:
        seconds = sum((r.get("latency_ms") or 0) for r in plan) / 1000
        subscription = {"calls": len(plan), "failed_calls": sum(r.get("outcome") != "ok" for r in plan),
                        "input_tokens": sum(r.get("input_tokens") or 0 for r in plan),
                        "output_tokens": sum(r.get("output_tokens") or 0 for r in plan),
                        "reasoning_tokens": sum(r.get("reasoning_tokens") or 0 for r in plan),
                        "minutes": round(seconds / 60, 1),
                        "note": "paid by the ChatGPT plan, no rupees; time is the sum of call times"}
    return {"pages": pages, "usd_inr": rate, "sections": out, "total_usd": round(total_usd, 6),
            "total_inr": round(total_usd * rate, 2), "inr_per_page": round(total_usd * rate / pages, 2) if pages else None,
            "subscription": subscription}


def estimate_line(est: dict, cap_inr: float) -> str:
    parts = ", ".join(f"{name} Rs {row['inr']:g}" + ("" if row["basis"] == "measured" else " (assumed)")
                      for name, row in est["sections"].items())
    return (f"Andaaza Rs {est['total_inr']:g}, seema Rs {cap_inr:g} ({est['pages']} pages; {parts}; "
            f"Rs {est['measured_share_inr']:g} of it from measured runs)")
