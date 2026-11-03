"""The text audit of a rendered video: texts under the readable floor, and texts that cover each other (Task 048 frame checks).

Navin, 3 November 2026: "minimum on-screen text size readable on a phone", "label overlap in every mode". The compilers check
sizes and places in Python (canvas CV-17, the world label checks), but only the drawn frame shows the size a text really has
after every camera and scale, and where it really lands. ``preview/audit.mjs`` measures each visible text of sampled frames
(see ``render.audit``); this module turns those measurements into the record:

- ``small``: each showing of a text whose settled size (its largest while it shows, so a pop-in or a zoom caught half-way
  does not count) stays under the floor (``spec["min_text_px"]``, else 36 px on the 1080p frame), with when it shows;
  ``lasting_small_count`` counts those seen on at least two samples. A text with no letter or digit (a lone ``₹`` or ``→``)
  is a symbol and is listed apart in ``symbols``.
- ``overlaps``: each pair of different texts whose line boxes cover each other by more than ``OVERLAP_SHARE`` of the smaller
  line, with when and how much. ``lasting`` is the overlaps seen on at least two samples in a row (a fade between two
  scenes crosses one sample at most). An overlap with the caption strip is marked ``caption``.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path

FLOOR_PX = 36
TOLERANCE_PX = 0.5          # sizes are measured to 0.1 px; rounding never makes a 36 px text "small"
OVERLAP_SHARE = 0.25        # of the smaller line box


def is_symbol(text: str) -> bool:
    """True for a text with no letter and no digit: a sign drawn as a picture, not words to read."""
    return not any(unicodedata.category(ch)[0] in "LN" for ch in text)


def _area(b) -> float:
    return max(0.0, b[2]) * max(0.0, b[3])


def _cover(a, b) -> float:
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def overlap_share(a: dict, b: dict) -> float:
    """The largest share of a line box of one text that a line box of the other covers (0 when they do not touch)."""
    best = 0.0
    for x in a.get("boxes") or [a["box"]]:
        for y in b.get("boxes") or [b["box"]]:
            small = min(_area(x), _area(y))
            if small > 0:
                best = max(best, _cover(x, y) / small)
    return best


def _same_drawing(a: dict, b: dict) -> bool:
    """The same words drawn twice in the same place (a halo under a fill): one text on screen, not an overlap."""
    if a["t"] != b["t"]:
        return False
    union = _area(a["box"]) + _area(b["box"]) - _cover(a["box"], b["box"])
    return union > 0 and _cover(a["box"], b["box"]) / union > 0.8


def caption_texts(spec: dict) -> set:
    """The captions of a spec as the audit records them (spaces folded, the first 80 characters)."""
    return {" ".join(str(c.get("text", "")).split())[:80] for scene in spec.get("scenes") or [] for c in scene.get("captions") or []}


def _close(run: dict, small: list, symbols: list, floor: float) -> None:
    """One showing of a text ended: it is small when even its settled (largest) size stayed under the floor."""
    run["_settled"] = run["px"]
    if run["px"] < floor - TOLERANCE_PX:
        row = {k: v for k, v in run.items() if not k.startswith("_")}
        (symbols if is_symbol(run["t"]) else small).append(row)


def summarize(frames: list, *, floor: float = FLOOR_PX, fps: int = 30, every: int | None = None, captions=()) -> dict:
    """The record of the measured frames (``[{"frame", "texts": [...]}]`` in frame order); ``captions`` (see
    ``caption_texts``) marks the caption strip for a page drawn before it carried its own mark."""
    captions = set(captions)
    frames = sorted(frames, key=lambda f: f["frame"])
    for f in frames:
        for t in f.get("texts") or []:
            if t["t"] in captions:
                t["caption"] = True
    if every is None:
        steps = [b["frame"] - a["frame"] for a, b in zip(frames, frames[1:])]
        every = min(steps) if steps else 1
    small, symbols, pairs = [], [], {}
    seen, sizes, showing = set(), [], {}
    for f in frames:
        texts = f.get("texts") or []
        now = {}
        for t in texts:
            seen.add(t["t"])
            if t.get("caption"):
                continue
            now[t["t"]] = min(now.get(t["t"], t["px"]), t["px"])
        for text, px in now.items():
            run = showing.get(text)
            if run is None or run["_last"] != f["frame"] - every:
                if run is not None:
                    _close(run, small, symbols, floor)
                run = showing[text] = {"t": text, "px": px, "first_s": round(f["frame"] / fps, 1), "samples": 0}
            run["px"] = max(run["px"], px)
            run["samples"] += 1
            run["_last"] = f["frame"]
            run["last_s"] = round(f["frame"] / fps, 1)
        for i, a in enumerate(texts):
            for b in texts[i + 1:]:
                if _same_drawing(a, b):
                    continue
                share = overlap_share(a, b)
                if share <= OVERLAP_SHARE:
                    continue
                key = tuple(sorted((a["t"], b["t"])))
                row = pairs.setdefault(key, {"a": key[0], "b": key[1], "first_s": round(f["frame"] / fps, 1), "samples": 0,
                                             "share": 0.0, "run": 0, "longest_run": 0, "_last": None,
                                             "caption": bool(a.get("caption") or b.get("caption"))})
                row["run"] = row["run"] + 1 if row["_last"] == f["frame"] - every else 1
                row["longest_run"] = max(row["longest_run"], row["run"])
                row["_last"] = f["frame"]
                row["samples"] += 1
                row["share"] = round(max(row["share"], share), 2)
                row["last_s"] = round(f["frame"] / fps, 1)
    for run in showing.values():
        _close(run, small, symbols, floor)
    sizes = [r["px"] for r in small] + [r["px"] for r in symbols] + [r["_settled"] for r in showing.values()]
    overlaps = []
    for row in pairs.values():
        row.pop("_last")
        row.pop("run")
        overlaps.append(row)
    overlaps.sort(key=lambda r: (r["first_s"], r["a"]))
    small_rows = sorted(small, key=lambda r: (r["first_s"], r["t"]))
    return {
        "schema": "bie.text_audit/1",
        "floor_px": floor,
        "frames_sampled": len(frames),
        "every_frames": every,
        "texts_seen": len(seen),
        "min_px": min(sizes) if sizes else None,
        "small": small_rows,
        "small_count": len(small_rows),
        "lasting_small_count": sum(1 for r in small_rows if r["samples"] >= 2),
        "symbols": sorted(symbols, key=lambda r: (r["first_s"], r["t"])),
        "overlaps": overlaps,
        "overlap_count": sum(1 for r in overlaps if not r["caption"]),
        "lasting_overlap_count": sum(1 for r in overlaps if not r["caption"] and r["longest_run"] >= 2),
        "caption_overlap_count": sum(1 for r in overlaps if r["caption"]),
    }


def read_jsonl(path) -> list:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
