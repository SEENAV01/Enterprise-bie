"""The UGC NET and GATE map of the toolbox (Task 046a, batch 3): every UGC NET subject and every GATE paper mapped to
the toolbox's subject families (``exam_map.json``), with how well the toolbox already covers it and what is missing.

``load()`` checks the file (codes unique, families known, a gap named for every subject that is not strong) and
``coverage()`` adds, for each subject, the usable tools and the capabilities its families have today.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .registry import Toolbox, load as load_toolbox

EXAM_MAP = Path(__file__).resolve().parent / "exam_map.json"
FITS = ("strong", "partial", "general")


class ExamMapError(ValueError):
    pass


def load(box: Toolbox | None = None) -> dict:
    box = box or load_toolbox()
    data = json.loads(EXAM_MAP.read_text(encoding="utf-8"))
    families = {f for c in box.capabilities.values() for f in c.families} | {"all_subjects"}
    problems = []
    for exam in ("ugc_net", "gate"):
        codes = [e["code"] for e in data[exam]]
        for code, n in Counter(codes).items():
            if n > 1:
                problems.append(f"{exam} {code}: listed {n} times")
        for e in data[exam]:
            where = f"{exam} {e['code']} {e['name']}"
            if not e["families"]:
                problems.append(f"{where}: no family")
            problems += [f"{where}: unknown family {f!r}" for f in e["families"] if f not in families]
            if e["fit"] not in FITS:
                problems.append(f"{where}: fit {e['fit']!r} is not one of {FITS}")
            if e["fit"] != "strong" and not e["gap"].strip():
                problems.append(f"{where}: fit {e['fit']} needs the gap named")
    if problems:
        raise ExamMapError("; ".join(problems[:12]))
    return data


def coverage(box: Toolbox | None = None) -> dict:
    """Each exam subject with the usable tools of its families and the capabilities they serve; and the totals."""
    box = box or load_toolbox()
    data = load(box)
    out = {}
    for exam in ("ugc_net", "gate"):
        rows = []
        for e in data[exam]:
            tools = [t for t in box.tools if t.usable and (set(t.subjects) & set(e["families"]))]
            caps = sorted({c for t in tools for c in t.capabilities})
            rows.append(dict(e, tools=len(tools), capabilities=caps))
        out[exam] = rows
    subjects = [r for r in out["ugc_net"] if r["code"] != "00"]
    out["totals"] = {"ugc_net_subjects": len(subjects), "gate_papers": len(out["gate"]),
                     "ugc_net_fit": dict(Counter(r["fit"] for r in subjects)), "gate_fit": dict(Counter(r["fit"] for r in out["gate"])),
                     "without_a_tool": [f"{r['code']} {r['name']}" for r in subjects + out["gate"] if not r["tools"]]}
    return out
