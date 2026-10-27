"""Canvas plan → BIE scene spec, with layout and checks done by code (asset intake, economy batch, 27 Oct 2026).

The director (AI) only says WHAT goes on the canvas, in which grid cell, and on which spoken word each piece appears.
This code turns that into exact positions, frames and a ``canvas_build`` / ``curve_story`` block layer, and refuses a
plan that would look wrong, so the video passes on the first try:

- every element sits inside the safe area (side margins, top margin, and the caption strip kept clear);
- no two elements overlap (grid cells are exclusive, and measured boxes are checked again);
- text fits its cell at a readable size (it shrinks down to ``MIN_FONT``, never below; longer text must be split);
- at most ``MAX_VISIBLE`` elements are on screen at once (dense canvases must clear or use ``until``/focus);
- every cue word is found in its beat's text (or the plan says ``at_fraction``), and visual changes keep the measured
  pace (one change at least every ``MAX_STILL_S`` seconds of speech, see rules/econ_canvas_rules.json).

Plan shape (JSON):
{
  "id": "demand_pull", "theme": "paper", "grid": [12, 8],
  "beats": [{"beat_id": "b1", "say": "..."}, ...],
  "nodes": [
    {"id": "shop", "kind": "icon", "icon": "tw:1f3ea", "label": "SUPPLY", "cell": [0, 3, 2, 2], "cue": ["b1", "दुकान"]},
    {"id": "t1", "kind": "text", "style": "box", "text": "...", "cell": [8, 0, 4, 2], "cue": ["b2", "मतलब"],
     "marks": [{"phrase": "...", "cue": ["b3", "..."]}]},
    {"id": "p", "kind": "value", "cell": [5, 3, 2, 1], "steps": [{"text": "50 ₹", "cue": ["b1", "50"]},
                                                                 {"text": "65 ₹", "dir": "up", "cue": ["b3", "65"]}]},
    {"id": "buyers", "kind": "crowd", "icon": "tw:1f9cd", "cell": [8, 4, 4, 2], "steps": [{"n": 2, "cue": [...]}, ...]},
    {"id": "a1", "kind": "arrow", "from": "shop", "to": "p", "cue": [...]},
    {"id": "x1", "kind": "mark", "mark": "cross", "target": "buyers", "cue": [...]},
    {"id": "h1", "kind": "highlight", "target": "p", "cue": [...], "until_cue": [...]}
  ],
  "camera": [{"cells": [0, 0, 12, 8], "cue": ["b1", ""]}],
  "graph": { ... curve_story data with cues instead of frames ... }     (optional: a graph scene instead of a canvas)
}
A cue is [beat_id, word] (the word as spoken in the beat's text) or [beat_id, "", fraction].
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)
from bie.brain.video import timing  # noqa: E402
import re as _re  # noqa: E402
import unicodedata as _ud  # noqa: E402


def _norm_fixed(text: str) -> str:
    """timing._norm keeps the Devanagari danda (। U+0964, ॥ U+0965) glued to the last word, so a cue on a sentence's
    last word ("... CPI।") is never found and silently lands at the start of the beat. Found while building this kit;
    the fix belongs in bie/brain/video/timing.py (with a test) — patched here until then."""
    return _re.sub(r"[^\wऀ-ॣ०-ॿ]+", " ", _ud.normalize("NFC", text).lower())


timing._norm = _norm_fixed

SAFE = {"left": 0.045, "right": 0.045, "top": 0.06, "bottom": 0.14}   # bottom strip is kept for captions
MIN_FONT = 24
MAX_VISIBLE = 16
MAX_STILL_S = 15.0       # CV-03: blocking (the references hold 40-80 s at worst; BIE must not)
TARGET_STILL_S = 7.0     # reported when exceeded
TARGET_CHANGE_EVERY_S = 6.0   # CV-02: measured median 5.0 s on 20 reference videos
ASPECT = 16 / 9
CHAR_W = 0.56            # average glyph width as a share of the font size (Noto Sans, mixed Latin/Devanagari)
TAG_CHAR_W = 0.72        # tags are bold capitals with letter spacing


class PlanError(ValueError):
    pass


def cell_box(cell, grid):
    cols, rows = grid
    c, r, cw, rh = cell
    if c < 0 or r < 0 or cw <= 0 or rh <= 0 or c + cw > cols or r + rh > rows:
        raise PlanError(f"cell {cell} is outside the {cols}x{rows} grid")
    W = 1 - SAFE["left"] - SAFE["right"]
    H = 1 - SAFE["top"] - SAFE["bottom"]
    gx, gy = 0.012, 0.02          # gutter between cells
    return {"x": SAFE["left"] + c / cols * W + gx / 2, "y": SAFE["top"] + r / rows * H + gy / 2,
            "w": cw / cols * W - gx, "h": rh / rows * H - gy}


def fit_icon(box, label: bool):
    """Largest square (on screen) inside the box, centred; room for a label under it."""
    hh = box["h"] * (0.78 if label else 1.0)
    side_px = min(box["w"] * 1920, hh * 1080)
    w, h = side_px / 1920, side_px / 1080 / (0.78 if label else 1.0)
    return {"x": box["x"] + (box["w"] - w) / 2, "y": box["y"] + (box["h"] - h) / 2, "w": w, "h": h}


def fit_text(text: str, box, size: int, style: str):
    pad_x = 32 if style in ("box", "note", "tag") else 0
    pad_y = 20 if style in ("box", "note") else (8 if style == "tag" else 0)
    width_px = box["w"] * 1920 - pad_x
    height_px = box["h"] * 1080 - pad_y
    s = size
    while s >= MIN_FONT:
        per_line = max(1, int(width_px / (s * CHAR_W)))
        words, lines, cur = text.split(), 1, 0
        for w in words:
            n = len(w) + (1 if cur else 0)
            if cur + n > per_line:
                lines += 1
                cur = len(w)
            else:
                cur += n
        need = lines * s * 1.3
        if need <= height_px and (style != "tag" or lines == 1):
            return s, (need + pad_y) / 1080
        s -= 2
    raise PlanError(f"text does not fit its cell even at {MIN_FONT}px: {text[:60]!r} (split it or give it a bigger cell)")


def overlap(a, b):
    return not (a["x"] + a["w"] <= b["x"] or b["x"] + b["w"] <= a["x"] or a["y"] + a["h"] <= b["y"] or b["y"] + b["h"] <= a["y"])


def expand_trees(nodes, grid):
    """A "tree" node (root + children inside one grid area) becomes text boxes and elbow arrows placed by code."""
    out = []
    for n in nodes:
        if n.get("kind") != "tree":
            out.append(n)
            continue
        area = cell_box(n["cell"], grid)
        kids = n["children"]
        k = len(kids)
        size = n.get("size", 28)
        bh = min(area["h"] * 0.36, size * 2.4 / 1080)
        gap = 0.012
        cw = (area["w"] - gap * (k - 1)) / k
        rw = min(area["w"], max(cw * 1.1, (len(n["root"]) * size * 0.62 + 48) / 1920))
        style = n.get("style", "box")
        out.append({"id": n["id"] + "_root", "kind": "text", "style": style, "text": n["root"], "size": size + 2, "align": "center",
                    "abs": {"x": area["x"] + (area["w"] - rw) / 2, "y": area["y"], "w": rw, "h": bh}, "cue": n["cue"],
                    **({"fill": n["root_fill"]} if "root_fill" in n else {})})
        for i, child in enumerate(kids):
            text = child["text"] if isinstance(child, dict) else child
            cue = child.get("cue", n["cue"]) if isinstance(child, dict) else n["cue"]
            cid = f"{n['id']}_{i}"
            out.append({"id": cid, "kind": "text", "style": style, "text": text, "size": size, "align": "center",
                        "abs": {"x": area["x"] + i * (cw + gap), "y": area["y"] + area["h"] - bh, "w": cw, "h": bh}, "cue": cue})
            out.append({"id": cid + "_a", "kind": "arrow", "from": n["id"] + "_root", "to": cid, "from_side": "b", "to_side": "t",
                        "elbow": "vhv" if k > 1 else None, "cue": cue})
    return out


def compile_plan(plan: dict, *, voice: dict | None = None, icon_paths: dict | None = None):
    """Return (scene_spec, report). Raises PlanError for a plan that would render wrong."""
    grid = plan.get("grid", [12, 8])
    beats = plan["beats"]
    says = {b["beat_id"]: b["say"] for b in beats}
    scene_id = plan.get("id", "canvas")
    tl = timing.build(beats, [{"scene_id": scene_id, "beat_ids": [b["beat_id"] for b in beats]}], voice=voice)
    fps = tl[scene_id]["fps"]
    problems = []

    def frame_of(cue):
        if cue is None:
            return 0
        bid, word = cue[0], cue[1]
        if bid not in says:
            raise PlanError(f"cue names an unknown beat {bid!r}")
        if word:
            norm = timing._norm(says[bid])
            if f" {timing._norm(word).strip()} " not in f" {norm} ":
                raise PlanError(f"cue word {word!r} is not in beat {bid}: {says[bid][:80]!r}")
            return timing.cue_frame(tl, scene_id, bid, word, says)
        start, length = tl[scene_id]["beats"][bid]
        return start + round(length * (cue[2] if len(cue) > 2 else 0.0))

    els, boxes, cells_used = [], {}, []
    for n in expand_trees(plan.get("nodes", []), grid):
        kind = n["kind"]
        el = {"id": n["id"], "kind": kind}
        for k in ("tone", "style", "label", "label_tone", "mark", "pos", "dir", "fill", "border", "align", "dashed", "curve",
                  "elbow", "head", "width", "cols", "stagger", "write_on", "label_size", "pad"):
            if k in n:
                el[k] = n[k]
        if "cue" in n:
            el["at"] = frame_of(n["cue"])
        if "until_cue" in n:
            el["until"] = frame_of(n["until_cue"])
        if "cell" in n or "abs" in n:
            box = dict(n["abs"]) if "abs" in n else cell_box(n["cell"], grid)
            for other_id, other_cell in (cells_used if "cell" in n else []):
                c1, c2 = n["cell"], other_cell
                if not (c1[0] + c1[2] <= c2[0] or c2[0] + c2[2] <= c1[0] or c1[1] + c1[3] <= c2[1] or c2[1] + c2[3] <= c1[1]):
                    # two elements may share cells only if they are never on screen together
                    a_on = (el.get("at", 0), el.get("until", 10 ** 9))
                    o = next(e for e in els if e["id"] == other_id)
                    b_on = (o.get("at", 0), o.get("until", 10 ** 9))
                    if a_on[0] < b_on[1] and b_on[0] < a_on[1]:
                        raise PlanError(f"{n['id']} and {other_id} share grid cells while both are on screen")
            if "cell" in n:
                cells_used.append((n["id"], n["cell"]))
            if kind == "icon":
                box = fit_icon(box, bool(n.get("label")))
                el["src"] = (icon_paths or {}).get(n["icon"], n["icon"])
            elif kind in ("text", "callout"):
                style = n.get("style", "note" if kind == "callout" else "plain")
                size, h = fit_text(n["text"], box, n.get("size", 56 if style == "title" else 24 if style == "tag" else 30), style)
                el.update({"text": n["text"], "size": size})
                if style == "tag":
                    tw = (len(n["text"]) * size * TAG_CHAR_W + 48) / 1920
                    if tw > box["w"]:
                        raise PlanError(f"tag {n['id']} is wider than its cell: {n['text']!r}")
                    box = {**box, "w": tw}
                elif style == "plain" and h <= size * 1.35 / 1080 + 1e-6:
                    tw = min(box["w"], (len(n["text"]) * size * CHAR_W + 8) / 1920)
                    align = n.get("align", "left")
                    x = box["x"] + (box["w"] - tw) / 2 if align == "center" else box["x"] + box["w"] - tw if align == "right" else box["x"]
                    box = {**box, "x": x, "w": tw}
                box = {**box, "y": box["y"] + max(0, (box["h"] - h) / 2) if n.get("valign", "middle") == "middle" else box["y"], "h": h}
                if "marks" in n:
                    el["marks"] = [{"phrase": m["phrase"], "at": frame_of(m["cue"]), **({"tone": m["tone"]} if "tone" in m else {})}
                                   for m in n["marks"]]
                    for m in n["marks"]:
                        if m["phrase"] not in n["text"]:
                            raise PlanError(f"mark phrase {m['phrase']!r} is not in the text of {n['id']}")
            elif kind == "value":
                el["steps"] = [{"text": s["text"], "at": frame_of(s["cue"]), **({"dir": s["dir"]} if "dir" in s else {})}
                               for s in n["steps"]]
                el["size"] = n.get("size", 52)
                arrow = any(s.get("dir") for s in n["steps"])
                longest = max(len(s["text"]) for s in n["steps"]) * el["size"] * 0.62 + (el["size"] * 0.95 if arrow else 0)
                if longest > box["w"] * 1920:
                    raise PlanError(f"value {n['id']} is wider than its cell")
                tw = longest / 1920
                align = n.get("align", "left")
                x = box["x"] + (box["w"] - tw) / 2 if align == "center" else box["x"]
                top = box["y"] + max(0.0, box["h"] - el["size"] * 1.25 / 1080) / 2 + (el["size"] * 0.3 / 1080 if len(n["steps"]) > 1 else 0)
                box = {"x": x, "y": top, "w": tw, "h": el["size"] * 1.2 / 1080}
            elif kind == "table":
                el.update({"columns": n["columns"], "rows": [{"cells": r["cells"], "at": frame_of(r["cue"])} for r in n["rows"]]})
                if any(len(r["cells"]) != len(n["columns"]) for r in n["rows"]):
                    raise PlanError(f"table {n['id']} has a row whose cell count differs from its columns")
                rh = box["h"] * 1080 / (len(n["rows"]) + 1)
                size = n.get("size", min(30, int(rh * 0.42)))
                if size < MIN_FONT:
                    raise PlanError(f"table {n['id']} is too tall for its cell (text would be {size}px)")
                cw = box["w"] * 1920 / len(n["columns"])
                widest = max(len(str(t)) for r in [n["columns"]] + [r["cells"] for r in n["rows"]] for t in r)
                if widest * size * 0.62 + 28 > cw:
                    raise PlanError(f"table {n['id']}: a cell's text is wider than its column")
                el["size"] = size
                el["highlights"] = [{**{k: v for k, v in h.items() if k in ("row", "col", "tone")}, "at": frame_of(h["cue"]),
                                     **({"until": frame_of(h["until_cue"])} if "until_cue" in h else {})} for h in n.get("highlights", [])]
            elif kind == "crowd":
                el["src"] = (icon_paths or {}).get(n["icon"], n["icon"])
                el["steps"] = [{"n": s["n"], "at": frame_of(s["cue"])} for s in n["steps"]]
            el.update(box)
            boxes[n["id"]] = box
        elif kind == "arrow":
            el["from"] = {"id": n["from"]} if isinstance(n["from"], str) else n["from"]
            el["to"] = {"id": n["to"]} if isinstance(n["to"], str) else n["to"]
            if isinstance(n.get("from_side"), str):
                el["from"]["side"] = n["from_side"]
            if isinstance(n.get("to_side"), str):
                el["to"]["side"] = n["to_side"]
        elif kind in ("mark", "highlight"):
            el["target"] = n["target"]
        els.append(el)

    ids = {e["id"] for e in els}
    for e in els:
        for ref in [e.get("target"), (e.get("from") or {}).get("id"), (e.get("to") or {}).get("id")]:
            if ref and ref not in ids:
                raise PlanError(f"{e['id']} refers to a missing element {ref!r}")
    # measured boxes must not overlap while on screen together (catches rounding and value/text growth)
    placed = [e for e in els if "x" in e]
    for i, a in enumerate(placed):
        for b in placed[i + 1:]:
            on = max(a.get("at", 0), b.get("at", 0)) < min(a.get("until", 10 ** 9), b.get("until", 10 ** 9))
            if on and overlap(a, b):
                raise PlanError(f"{a['id']} and {b['id']} overlap on screen")
    duration = tl[scene_id]["duration"]
    # density: how many elements are visible at once (peak)
    peak = max((sum(1 for e in els if e.get("at", 0) <= f < e.get("until", 10 ** 9)) for f in range(0, duration, 5)), default=0)
    if peak > MAX_VISIBLE:
        problems.append(f"{peak} elements on screen at once (limit {MAX_VISIBLE}): clear the canvas or use until/focus")
    # pace: the longest stretch of speech with no visual change
    changes = sorted({e.get("at", 0) for e in els} | {s["at"] for e in els for s in e.get("steps", [])}
                     | {m["at"] for e in els for m in e.get("marks", [])})
    camera_keys = []
    for k in plan.get("camera", []):
        f = frame_of(k.get("cue"))
        changes.append(f)
        key = {"at": f, "box": cell_box(k["cells"], grid) if "cells" in k else k.get("box", {"x": 0, "y": 0, "w": 1, "h": 1})}
        if "frames" in k:
            key["frames"] = k["frames"]
        camera_keys.append(key)
    for f in plan.get("focus", []):
        changes.append(frame_of(f["cue"]))
    g0 = plan.get("graph") or {}
    for group in ("curves", "guides", "shades", "notes"):
        for item in g0.get(group, []):
            changes.append(frame_of(item["cue"]))
            if "until_cue" in item:
                changes.append(frame_of(item["until_cue"]))
    for d in g0.get("dots", []):
        changes += [frame_of(s["cue"]) for s in d["steps"]]
    changes = sorted(set(changes)) + [duration]
    still = max((b - a) for a, b in zip(changes, changes[1:])) / fps if len(changes) > 1 else duration / fps
    advisories = []
    if still > MAX_STILL_S:
        problems.append(f"the picture stays the same for {still:.1f} s (limit {MAX_STILL_S} s): add a step, a mark or a camera move")
    elif still > TARGET_STILL_S:
        advisories.append(f"the picture stays the same for {still:.1f} s (target {TARGET_STILL_S} s)")
    every = duration / fps / max(1, len(changes) - 1)
    if every > TARGET_CHANGE_EVERY_S:
        advisories.append(f"one change every {every:.1f} s (target {TARGET_CHANGE_EVERY_S} s)")
    data = {"theme": plan.get("theme", "paper"), "elements": els}
    if plan.get("focus"):
        data["focus"] = [{"at": frame_of(f["cue"]), **({"until": frame_of(f["until_cue"])} if "until_cue" in f else {}),
                          "ids": f["ids"]} for f in plan["focus"]]
    layers = [{"id": scene_id + "_canvas", "type": "block", "block": "canvas_build", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1},
               "data": data}]
    if plan.get("graph"):
        g = json.loads(json.dumps(plan["graph"]))
        for group in ("curves", "guides", "shades", "notes"):
            for item in g.get(group, []):
                item["at"] = frame_of(item.pop("cue"))
                if "until_cue" in item:
                    item["until"] = frame_of(item.pop("until_cue"))
        for d in g.get("dots", []):
            for s in d["steps"]:
                s["at"] = frame_of(s.pop("cue"))
        g["axes_at"] = frame_of(g.pop("axes_cue", None))
        g.setdefault("theme", plan.get("theme", "paper"))
        g["transparent"] = True          # the canvas layer underneath always draws the paper
        layers.append({"id": scene_id + "_graph", "type": "block", "block": "curve_story", "at": 0,
                       "box": g.pop("box", {"x": 0, "y": 0, "w": 1, "h": 1}), "data": g})
    captions = []
    for b in beats:
        start, length = tl[scene_id]["beats"][b["beat_id"]]
        captions.append({"at": start, "until": start + length, "text": b.get("caption", b["say"])})
    data["subtitles"] = captions           # drawn by canvas_build on a dark strip (readable on paper)
    scene = {"id": scene_id, "duration": duration, "layers": layers, "camera": camera_keys or [{"at": 0}], "captions": []}
    report = {"scene": scene_id, "seconds": round(duration / fps, 1), "elements": len(els), "peak_visible": peak,
              "longest_still_s": round(still, 1), "changes": len(changes) - 1,
              "change_every_s": round(every, 1), "problems": problems, "advisories": advisories}
    return scene, report


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("plans", nargs="+")
    ap.add_argument("--icons", default="", help="JSON map icon id -> asset path (from icon_index.py copy)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    icon_paths = json.load(open(a.icons)) if a.icons else {}
    scenes, reports = [], []
    for p in a.plans:
        s, r = compile_plan(json.load(open(p, encoding="utf-8")), icon_paths=icon_paths)
        scenes.append(s)
        reports.append(r)
    json.dump({"fps": timing.FPS, "width": 1920, "height": 1080, "captions": False, "scenes": scenes}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps(reports, ensure_ascii=False, indent=1))
