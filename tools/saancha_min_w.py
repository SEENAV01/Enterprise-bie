"""The readable-width table (pilot ch02 v1, Sloman: "no min w for 36 px words" was the most frequent compile problem,
~70 of the pilot's hits): for every saancha with a ``w`` parameter, the smallest ``w`` at which its own words reach the
36 px floor at scale 1, measured by the engine's own drawing (``box_rules.min_readable_w``) with its default parameters
and, where a word parameter is empty by default, a short sample word in it.

    python3 -B tools/saancha_min_w.py            # rewrite bie/brain/video/engine/min_readable_w.json
    python3 -B tools/saancha_min_w.py --check    # exit 1 if the table is stale

The table is a guide for planning (``bk.py library`` / ``bk.py fit``); the compiler measures the exact params of each
thing itself and names the width in its under-36px message.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import saanche  # noqa: E402
from bie.brain.video import box_rules  # noqa: E402

TABLE = ROOT / "bie" / "brain" / "video" / "engine" / "min_readable_w.json"
SAMPLE = "आलू"
WORD_PARAMS = ("label", "title", "name", "text", "value", "caption")
SAMPLES = {"table": {"cols": "भाव;सीता;राजू", "cells": "₹50;10;6|₹40;14;9"}}   # a saancha whose words come from other params


def sample_p(entry: dict) -> tuple:
    p, filled = {}, []
    for k in WORD_PARAMS:
        spec = entry["params"].get(k)
        if spec and spec["type"] == "text" and spec.get("default") in ("", None):
            p[k] = SAMPLE
            filled.append(k)
    return p, filled


def row(name: str) -> dict | None:
    entry = saanche.get(name)
    if "w" not in entry["params"]:
        return None
    p, filled = sample_p(entry)
    for k, v in SAMPLES.get(name, {}).items():
        p[k] = v
        filled.append(k)
    got = box_rules.min_readable_w(name, p)
    return {"w_default": entry["params"]["w"].get("default"), "min_w": got["w"],
            "px_at_default": None if got["px_now"] is None else round(got["px_now"], 1),
            "sample": {k: p[k] for k in filled}, "note": got.get("reason") or ""}


def table(names=None) -> dict:
    rows = {}
    for name in names or saanche.names():
        r = row(name)
        if r is not None:
            rows[name] = r
    return {"schema": "bie.saancha-min-w/1", "floor_px": box_rules.FLOOR_PX,
            "what": "smallest w at scale 1 at which a saancha's own words reach the floor, default params (+ sample word)",
            "made_by": "tools/saancha_min_w.py", "saanche": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    got = table()
    if a.check:
        old = json.loads(TABLE.read_text(encoding="utf-8")) if TABLE.exists() else {}
        if old != got:
            print("min_readable_w.json is stale: run python3 -B tools/saancha_min_w.py")
            sys.exit(1)
        print("min_readable_w.json is fresh")
        return
    TABLE.write_text(json.dumps(got, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(got['saanche'])} saanche -> {TABLE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
