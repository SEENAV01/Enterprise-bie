"""The PYQ lab's science models behind one interface (Navin, 19 November 2026).

A PYQ investigation names one model; the model is the single source of truth for both views of the lesson (the main scene
and the enlarged detail) and for every number, structure or count the narration and the solving board may use:

  projectile  the ideal projectile (``pyq_math.projectile``): every intermediate value, units, traps
  numeric     any numerical working (``pyq_math.work``): given/step/trap/answer lines, exact values and units
  mechanism   electron-pair arrows on real molecules (``pyq_chem``, RDKit): bonds, charges, carbocations, product
  fusion      fusions and chromosome sets (``pyq_bio``): ploidy, maternal/paternal shares, cells vs nuclei
  scene       any other subject: an AI-drawn labelled SVG with timed part moves; its structure is checked, but code does
              not vouch for its science (``verified`` false, written in the record and the review page)

``build`` returns one shape for all: problems, the option the model proves right (or None), which wrong option each trap
explains, the parts and moments a narration cue may point at, the numbers the narration may say, and the player's data.
"""
from __future__ import annotations

import re
from fractions import Fraction

from . import pyq_bio, pyq_chem, pyq_math
from .studio_film import SVG_BANNED, svg_ids, svg_problems

KINDS = ("projectile", "numeric", "mechanism", "fusion", "scene")
PROJECTILE_PARTS = ("launcher", "projectile", "path", "v", "vx", "vy", "gravity", "height", "peak", "ground", "range", "ref",
                    "ghost")
PROJECTILE_MOMENTS = ("launch", "rise", "peak", "descent", "land")
MOMENT_T = {"launch": (0.0, 0.02), "rise": (0.02, 0.5), "peak": (0.5, 0.5), "descent": (0.5, 1.0), "land": (1.0, 1.0)}


def _num(v) -> float:
    return float(v)


def build(model: dict, options: list) -> dict:
    kind = (model or {}).get("kind")
    lines = [str(x) for x in (model or {}).get("lines") or []]
    base = {"kind": kind, "problems": [], "answer_option": None, "trap_options": {}, "parts": [], "moments": [],
            "numbers": set(), "values": {}, "data": {}, "verified": kind != "scene", "board": {}}
    if kind not in KINDS:
        base["problems"].append(f"model.kind must be one of {', '.join(KINDS)}")
        return base
    if kind in ("projectile", "numeric"):
        result = pyq_math.projectile(lines) if kind == "projectile" else pyq_math.work(lines)
        base["problems"] += result.get("problems", [])
        if base["problems"]:
            return base
        values = result["values"]
        rows = {r["name"]: r for r in result["steps"] + result["traps"]}
        base["values"] = {k: pyq_math.fmt(v) for k, v in values.items()}
        base["numbers"] = {round(_num(v), 6) for v in values.values()}
        base["board"] = {name: {"expr": r["expr"], "with_values": r.get("with_values") or pyq_math.fmt(r["value"]),
                                "value": pyq_math.fmt(r["value"]), "unit": r["unit"], "label": r["label"], "kind": r["kind"]}
                         for name, r in rows.items()}
        answer = values.get(result["answer"])
        base["answer_option"] = pyq_math.match_option(answer, options) if answer is not None else None
        if base["answer_option"] is None:
            base["problems"].append(f"the worked answer {pyq_math.fmt(answer) if answer is not None else '?'} matches no "
                                    f"single option")
        base["trap_options"] = {t["name"]: pyq_math.match_option(t["value"], options) for t in result["traps"]}
        base["answer_value"] = pyq_math.fmt(answer) if answer is not None else ""
        if kind == "projectile":
            base["parts"], base["moments"] = list(PROJECTILE_PARTS), list(PROJECTILE_MOMENTS)
            base["data"] = {"flight": result["flight"], "asked": result["asked"],
                            "clear_decimal": result.get("clear_decimal"), "square_split": result.get("square_split"),
                            "traps": {t["name"]: {"value": _num(t["value"]), "label": t["label"]} for t in result["traps"]}}
            for extra in (result.get("square_split") or {}, result.get("clear_decimal") or {}):
                for v in extra.values():
                    try:
                        base["numbers"].add(float(str(v).replace(",", "")))
                    except ValueError:
                        pass
        else:
            base["parts"], base["moments"] = [r["name"] for r in result["steps"]], ["start", "end"]
        return base
    if kind == "mechanism":
        result = pyq_chem.run(lines, options)
        base["problems"] += result["problems"]
        if base["problems"]:
            return base
        atoms = {a["id"] for state in result["states"] for a in state["atoms"]}
        base["parts"] = sorted(atoms) + [f"{b['a']}-{b['b']}" for b in result["states"][0]["bonds"]]
        base["moments"] = ["start"] + result["step_ids"] + [t["id"] for t in result["traps"]]
        base["answer_option"], base["trap_options"] = result["answer_option"], result["trap_options"]
        base["data"] = {"states": result["states"], "steps": result["steps"], "traps": result["traps"],
                        "product": result["product"]}
        base["board"] = {s["id"]: {"label": s["label"], "facts": s["facts"],
                                   "cations": [f"{c['word']} C⁺ at {c['atom']}" for c in s["cations"]]}
                         for s in result["steps"]}
        base["numbers"] = {1, 2, 3, 4, 5, 6} | {len(atoms)}
        return base
    if kind == "fusion":
        result = pyq_bio.run(lines, options)
        base["problems"] += result["problems"]
        if base["problems"]:
            return base
        base["parts"] = [e["id"] for e in result["entities"]]
        base["moments"] = ["start", "entry"] + [f["id"] for f in result["fusions"]] + ["end"]
        base["answer_option"] = result["answer_option"]
        base["numbers"] = {float(n) for n in result["numbers"] if n is not None}
        base["data"] = {"entities": result["entities"], "fusions": result["fusions"], "counts": result["counts"],
                        "diploid": result["diploid"], "asked_value": result["asked_value"]}
        base["board"] = {f["id"]: {"label": f["name"], "sum": f["sum"], "product": f["label"]} for f in result["fusions"]}
        return base
    # scene: any subject, structure-checked only
    svg = (model or {}).get("svg") or ""
    found = svg_problems(svg)
    ids = svg_ids(svg)
    moments, keys = ["start"], []
    for raw in lines:
        m = re.match(r'^\s*moment\s+([a-z][a-z0-9_]*)\s*"?([^"]*)"?\s*$', raw, re.I)
        k = re.match(r"^\s*key\s+([a-z][a-z0-9_]*)\s+([A-Za-z][\w-]*)\s+(.*)$", raw)
        if m:
            moments.append(m.group(1))
        elif k:
            if k.group(2) not in ids:
                found.append(f"key line {raw!r}: part {k.group(2)!r} is not an id in the svg")
            props = dict(p.split("=", 1) for p in k.group(3).split() if "=" in p)
            keys.append({"moment": k.group(1), "part": k.group(2), **{a: float(b) for a, b in props.items()
                                                                       if a in ("x", "y", "scale", "opacity")}})
        elif raw.strip() and not raw.strip().startswith("#"):
            found.append(f"scene line not understood: {raw!r} (moment <id> \"label\" | key <moment> <part> x= y= scale= opacity=)")
    for key in keys:
        if key["moment"] not in moments:
            found.append(f"key for {key['part']}: moment {key['moment']!r} is not declared")
    base["problems"] += found
    base["parts"], base["moments"] = sorted(ids), moments
    base["data"] = {"svg": svg, "keys": keys}
    base["answer_option"] = None
    return base


def override(lines: list, changes: list) -> list:
    """A question-family variant: a change line replaces the line with the same key (u =, theta =, diploid, asked ...)."""
    def key(line: str) -> str:
        line = line.strip()
        m = re.match(r"^(given|step|trap)\s+([A-Za-z_]\w*)", line)
        if m:
            return m.group(2)
        m = re.match(r"^([A-Za-z_]\w*)\s*=", line)
        if m:
            return m.group(1)
        return line.split()[0] if line.split() and line.split()[0] in ("diploid", "asked", "answer") else line
    out = list(lines)
    for change in changes:
        k = key(change)
        hits = [i for i, line in enumerate(out) if key(line) == k]
        if hits:
            out[hits[-1]] = change
        else:
            out.append(change)
    return out


def family(model: dict, changes: list, choices: list) -> dict:
    """Recompute the model with the family's changes; which choice is right, by the model (projectile/numeric/fusion)."""
    kind = (model or {}).get("kind")
    if kind not in ("projectile", "numeric", "fusion"):
        return {"checked": False, "correct": None, "problems": []}
    variant = {"kind": kind, "lines": override([str(x) for x in model.get("lines") or []], changes)}
    if kind == "fusion":
        variant["lines"] = [line for line in variant["lines"] if not line.strip().startswith("option")]
    result = build(variant, choices)
    problems = [p for p in result["problems"] if "matches no" not in p and "no option matches" not in p]
    return {"checked": True, "correct": result["answer_option"], "problems": problems,
            "value": result.get("answer_value") or (result["data"] or {}).get("asked_value"),
            "numbers": result["numbers"]}


NUMBER = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?![\w])")


def spoken_numbers(text: str) -> list:
    out = []
    for raw in NUMBER.findall(text or ""):
        try:
            out.append(float(Fraction(raw.replace(",", ""))))
        except (ValueError, ZeroDivisionError):
            pass
    return out


def stray_numbers(text: str, allowed: set, free_upto: int = 12) -> list:
    """Numbers in a narration line that the model never produced (an invented number is a wrong number)."""
    allowed_f = {round(float(a), 4) for a in allowed}
    bad = []
    for n in spoken_numbers(text):
        if n <= free_upto and n == int(n):
            continue
        if round(n, 4) in allowed_f or any(abs(n - a) <= 0.006 * max(abs(a), 1) for a in allowed_f):
            continue
        bad.append(pyq_math.fmt(n))
    return bad
