"""Append-only JSONL ledger: one row per provider call (including failed and cached calls)."""
from __future__ import annotations

import json
import threading
from pathlib import Path

FIELDS = ("seq", "request_id", "provider", "via", "model", "returned_model", "attempt", "outcome", "error_kind",
          "cache_hit", "input_tokens", "output_tokens", "reasoning_tokens", "cost_usd", "latency_ms", "prompt_version",
          "cached_input_tokens", "billing")


class UsageLedger:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.rows = []
        self._lock = threading.Lock()
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, **row):
        unknown = set(row) - set(FIELDS)
        if unknown:
            raise ValueError("unknown ledger fields: " + ",".join(sorted(unknown)))
        with self._lock:
            full = {name: row.get(name) for name in FIELDS}
            full["seq"] = len(self.rows) + 1
            self.rows.append(full)
            if self.path:
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(full, sort_keys=True) + "\n")
        return full

    def summary(self):
        """Totals per provider; ``cost_usd`` is None if any priced call had an unknown price."""
        out = {}
        for row in self.rows:
            entry = out.setdefault(row["provider"], {"calls": 0, "failed_calls": 0, "cache_hits": 0, "input_tokens": 0,
                                                     "output_tokens": 0, "cost_usd": 0.0, "cost_complete": True})
            entry["calls"] += 1
            entry["failed_calls"] += row["outcome"] != "ok"
            entry["cache_hits"] += bool(row["cache_hit"])
            entry["input_tokens"] += row["input_tokens"] or 0
            entry["output_tokens"] += row["output_tokens"] or 0
            if row["cost_usd"] is None and not row["cache_hit"] and (row["input_tokens"] or row["output_tokens"]):
                entry["cost_complete"] = False
            entry["cost_usd"] = round(entry["cost_usd"] + (row["cost_usd"] or 0.0), 6)
        return out
