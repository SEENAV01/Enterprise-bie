"""The build-up canvas: a director's canvas plan → a scene the ``canvas_build`` / ``curve_story`` blocks render, with the
layout, the timing and the first-try checks done by code (Task 046 Part C, from the economy kit of 27 October 2026).

The director (AI) only says WHAT goes on the canvas, in which grid cell, and on which spoken word each piece appears.
This code turns that into exact positions, frames and block layers, and refuses a plan that would look wrong, so the
video passes on the first try:

- every element sits inside the safe area (side margins, top margin, and the caption strip kept clear);
- no two elements overlap (grid cells are exclusive, and measured boxes are checked again);
- text fits its cell at a readable size (it shrinks down to ``MIN_FONT``, never below; longer text must be split);
- at most ``MAX_VISIBLE`` elements are on screen at once (dense canvases must clear or use ``until``/focus);
- every cue word is found in its beat's text (or the plan says ``at_fraction``), and visual changes keep the measured
  pace (one change at least every ``MAX_STILL_S`` seconds of speech; rules CV-01 … CV-12 in
  ``rulebook/canvas_profile.json``, measured on 20 reference videos).

Plan shape (JSON):
{
  "id": "demand_pull", "theme": "paper", "grid": [12, 8], "touches": true,
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
  "graph": { ... curve_story data with cues instead of frames ... }     (optional: a graph beside or instead of the canvas)
}
A cue is [beat_id, word] (the word as spoken in the beat's text) or [beat_id, "", fraction]. ``touches`` turns on the
L3 touches (shadows, idle motion, walk-ins, flowing goods, a camera inside the block that never cuts an element in half):
Navin's "B" level (L2 canvas + L3 touches), the default for every economy part.

Captions are not part of the block: ``compile_plan`` returns the scene with ``captions`` (one per beat), drawn once by
the core Captions strip; ``video_spec`` wraps scenes into the VideoSpec the preview renderer and Remotion read.
"""
from __future__ import annotations

import copy
import json
import re
import math
from pathlib import Path

from . import formats
from . import shots as shots_module
from .video import timing

SCHEMA = formats.tag("video_spec")
PROFILE_PATH = Path(__file__).resolve().parent / "rulebook" / "canvas_profile.json"
PROFILE = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
LIMITS = PROFILE["limits"]

SAFE = {"left": 0.045, "right": 0.045, "top": 0.06, "bottom": 0.14}   # the bottom strip is kept for the captions
MIN_FONT = int(LIMITS["min_font_px"])             # CV-17 (Navin, 3 November 2026): 36 px, readable on a phone held sideways
MIN_ICON = int(LIMITS.get("min_icon_px", 64))       # an icon with a label is at least this many pixels wide
MAX_VISIBLE = int(LIMITS["max_visible"])            # CV-10
MAX_STILL_S = float(LIMITS["max_still_s"])          # CV-03: blocking (the references hold 40-80 s at worst; BIE must not)
TARGET_STILL_S = float(LIMITS["target_still_s"])    # reported when exceeded
TARGET_CHANGE_EVERY_S = float(LIMITS["target_change_every_s"])   # CV-02: measured median 5.0 s on 20 reference videos
ASPECT = 16 / 9
CHAR_W = 0.56            # average glyph width as a share of the font size (Noto Sans, mixed Latin/Devanagari)
TAG_CHAR_W = 0.72        # tags are bold capitals with letter spacing
KINDS = ("text", "callout", "icon", "crowd", "value", "arrow", "tree", "table", "mark", "highlight", "picture", "action")
# "action" (Task 046 Part D2): a kriya ka saancha, the same process templates a world plays (bie/brain/video/saanche.py), fitted
# into the node's cells (at least MIN_ACTION_ROWS rows, so its people are never stick figures), with a camera close-up
MIN_ACTION_ROWS = 3
SUBTITLE_TOP = 1 - SAFE["bottom"]       # the subtitle strip starts here on the frame (D2: no content under the captions)
# "picture" (Task 046 Part D1): a book diagram or table drawn as itself on the paper, placed by code
# (bie/brain/visual_thinking.picture_node) and expanded by ``expand_pictures`` into tags, icons, boxes, arrows or a table.


class PlanError(ValueError):
    pass


# ---------------------------------------------------------------- cues

def cue_frame(tl: dict, scene_id: str, says: dict, cue) -> int:
    """The frame of a cue: [beat_id, word] lands on the word (refused when the word is not in the beat); [beat_id, "",
    fraction] lands at that fraction of the beat. ``None`` is frame 0."""
    if cue is None:
        return 0
    bid, word = cue[0], cue[1]
    if bid not in says:
        raise PlanError(f"cue names an unknown beat {bid!r}")
    if word:
        if not timing.has_word(says[bid], word):
            raise PlanError(f"cue word {word!r} is not in beat {bid}: {says[bid][:80]!r}")
        return timing.cue_frame(tl, scene_id, bid, word, says)
    start, length = tl[scene_id]["beats"][bid]
    return start + round(length * (cue[2] if len(cue) > 2 else 0.0))


HOLD_CAPTION_S = 1.0     # a caption stays up through a pause shorter than this, until the next line starts (no flicker)
CAPTION_CHARS = int(LIMITS.get("caption_chars", 150))     # two lines of the 36 px strip (CV-17); a longer beat shows in pieces


def caption_pieces(text: str, max_chars: int = CAPTION_CHARS) -> list:
    """A beat's caption cut into pieces of at most ``max_chars`` (two lines of the strip at the readable size, Navin, 3 November
    2026): at the ends of sentences first (। . ? !), then at ; and , and last between words; never inside a word."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= max_chars:
        return [text] if text else []

    def split(t: str, marks: str) -> list:
        parts = re.split(f"(?<=[{marks}])\\s+", t)
        return [x for x in parts if x]

    out = []
    for sentence in split(text, "।.?!"):
        units = [sentence] if len(sentence) <= max_chars else split(sentence, ";,")
        for unit in units:
            if len(unit) > max_chars:
                words, cur = unit.split(), ""
                for w in words:
                    if cur and len(cur) + 1 + len(w) > max_chars:
                        out.append(cur)
                        cur = w
                    else:
                        cur = f"{cur} {w}".strip()
                if cur:
                    out.append(cur)
            elif out and len(out[-1]) + 1 + len(unit) <= max_chars:
                out[-1] = f"{out[-1]} {unit}"
            else:
                out.append(unit)
    return out


def captions_of(tl: dict, scene_id: str, beats: list) -> list:
    """The captions of the core strip: a beat's caption appears with the beat (in pieces of at most two lines, each for a share
    of the beat's time by its length) and holds through a short pause until the next line starts; only a pause longer than
    ``HOLD_CAPTION_S`` (and the tail after the last beat) shows no caption. Each caption carries its ``beat_id`` so the review
    page can say where in the rendered video a beat (and the book line it covers) plays (``coverage.beat_times``)."""
    out = []
    for b in beats:
        start, length = tl[scene_id]["beats"][b["beat_id"]]
        pieces = caption_pieces(b.get("caption", b["say"])) or [""]
        total, at = sum(len(x) for x in pieces) or 1, start
        for n, piece in enumerate(pieces):
            until = start + length if n == len(pieces) - 1 else at + max(1, round(length * len(piece) / total))
            out.append({"at": at, "until": max(at + 1, until), "text": piece, "beat_id": b["beat_id"]})
            at = until
    hold = HOLD_CAPTION_S * tl[scene_id]["fps"]
    for cap, following in zip(out, out[1:]):
        if 0 <= following["at"] - cap["until"] <= hold:
            cap["until"] = following["at"]
    return out


# ---------------------------------------------------------------- layout

ARROW_BEND = 0.18          # a curved arrow's bend: the control point sits this share of the arrow's length off its line


def arrow_bend(curve) -> float:
    """The bend the block draws for an arrow's ``curve``: the maker's plan says yes or no (the director's schema has a
    boolean), and the block reads a number, so ``True`` became a bend of 1 and the arrow swung a whole arrow-length off its
    line, across the canvas (the Money v2 render of 31 October 2026, wheat and cloth across the book's gallery). Yes is a
    gentle bend; a number is kept within ±0.35."""
    if isinstance(curve, bool):
        return ARROW_BEND if curve else 0.0
    try:
        return max(-0.35, min(0.35, float(curve)))
    except (TypeError, ValueError):
        return 0.0


CAMERA_PAD = 0.035        # a camera box keeps this much of the frame around what it shows


def pad_box(box: dict, pad: float = CAMERA_PAD) -> dict:
    """A camera box grown by ``pad`` on every side (within the frame) before it is fitted: the camera fits its box edge to
    edge, so what stood on the box's edge stood on the frame's edge and the camera's idle drift cut it (the Money v2
    render of 31 October 2026: the book's table across the whole grid lost its first letters on the left)."""
    x = max(0.0, float(box.get("x", 0)) - pad)
    y = max(0.0, float(box.get("y", 0)) - pad)
    x2 = min(1.0, float(box.get("x", 0)) + float(box.get("w", 1)) + pad)
    y2 = min(1.0, float(box.get("y", 0)) + float(box.get("h", 1)) + pad)
    return {"x": x, "y": y, "w": x2 - x, "h": y2 - y}


def fit_box(box: dict) -> dict:
    """A scene camera box the core camera can show without the backdrop: the core fits a box by its larger side (in
    fractions of the frame), so the visible region is always as wide as it is tall in those fractions; a box that is not
    (the Money chapter's v1, 28 October 2026: a 12x8-cell box 0.90 x 0.68 fitted by its width) shows a band of backdrop
    beyond the scene (4 % of the frame along the top for 30 s). The box grows around its centre to that square and is
    kept inside the frame."""
    side = min(1.0, max(float(box.get("w", 1)), float(box.get("h", 1))))
    cx, cy = float(box.get("x", 0)) + float(box.get("w", 1)) / 2, float(box.get("y", 0)) + float(box.get("h", 1)) / 2
    x = min(max(cx - side / 2, 0.0), 1.0 - side)
    y = min(max(cy - side / 2, 0.0), 1.0 - side)
    return {"x": round(x, 4), "y": round(y, 4), "w": round(side, 4), "h": round(side, 4)}


def above_strip(box: dict, content: dict, *, room: float = 0.85) -> dict:
    """A square camera box moved (and grown if it must) so that ``content`` (the cells the camera was asked to show) ends above
    the subtitle strip of the frame (Task 046 Part D2; Navin's D1 finding 7: subtitles covered content in v2_s2 and v4_s3,
    where a camera box clamped to the top of the canvas pushed the bottom row under the captions)."""
    side = float(box["w"])
    top, bottom = float(content.get("y", 0)), float(content.get("y", 0)) + float(content.get("h", 1))
    side = min(1.0, max(side, (bottom - top) / room))
    y = float(box["y"])
    if bottom > y + room * side:
        y = bottom - room * side
    y = min(max(y, 0.0), 1.0 - side)
    cx = float(box["x"]) + float(box["w"]) / 2
    x = min(max(cx - side / 2, 0.0), 1.0 - side)
    return {"x": round(x, 4), "y": round(y, 4), "w": round(side, 4), "h": round(side, 4)}


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


LABEL_LINE = 1.35          # a label's line height as a share of its font size


def label_lines(label: str, width_px: float, px: int = MIN_FONT, most: int = 2):
    """The label's words in lines that fit ``width_px`` at ``px`` (at most ``most`` lines, never inside a word), or None."""
    per = max(1, int((width_px - 8) / (px * CHAR_W)))
    lines, cur = [], ""
    for w in str(label).split():
        if len(w) > per:
            return None
        if cur and len(cur) + 1 + len(w) > per:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines if len(lines) <= most else None


def fit_icon(box, label, label_px: int = MIN_FONT, lines: int = 1):
    """Largest square (on screen) inside the box, centred, with room under it for a label of ``lines`` lines at the readable size
    (CV-17); the box is as wide as the label when the label is wider than the icon (never wider than the cell). ``label``: the
    label's text, its lines (a list) or True/False. Returns the element's box with ``label_share``, the share of its height the
    label takes."""
    rows = label if isinstance(label, list) else [label] if isinstance(label, str) and label else []
    lines = max(lines, len(rows))
    lh = (label_px * LABEL_LINE * lines + 4) if label else 0.0
    side_px = max(0.0, min(box["w"] * 1920, box["h"] * 1080 - lh))
    lw = min(box["w"] * 1920, max(len(t) for t in rows) * label_px * CHAR_W + 8) if rows else 0.0
    w_px, h_px = max(side_px, lw), side_px + lh
    out = {"x": box["x"] + (box["w"] - w_px / 1920) / 2, "y": box["y"] + (box["h"] - h_px / 1080) / 2, "w": w_px / 1920, "h": h_px / 1080,
           "side_px": side_px}
    if label:
        out["label_share"] = round(lh / max(1.0, h_px), 4)
    return out


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
    """A "tree" node (root + children inside one grid area) becomes text boxes and elbow arrows placed by code; the tree's
    until_cue goes to every one of them (seekh -> BIE, the first Part D2 run: it was dropped, so a tree never left and a
    later picture in its place was refused as an overlap)."""
    out = []
    for n in nodes:
        if n.get("kind") != "tree":
            out.append(n)
            continue
        leave = {"until_cue": n["until_cue"]} if n.get("until_cue") else {}
        area = cell_box(n["cell"], grid)
        kids = n["children"]
        k = len(kids)
        if k < 1:
            raise PlanError(f"tree {n['id']} has no children")
        size = max(MIN_FONT, n.get("size", 28))
        bh = min(area["h"] * 0.36, size * 2.4 / 1080)
        gap = 0.012
        cw = (area["w"] - gap * (k - 1)) / k
        rw = min(area["w"], max(cw * 1.1, (len(n["root"]) * size * 0.62 + 48) / 1920))
        style = n.get("style", "box")
        out.append({"id": n["id"] + "_root", "kind": "text", "style": style, "text": n["root"], "size": size + 2, "align": "center",
                    "abs": {"x": area["x"] + (area["w"] - rw) / 2, "y": area["y"], "w": rw, "h": bh}, "cue": n["cue"],
                    **({"fill": n["root_fill"]} if "root_fill" in n else {}), **leave})
        for i, child in enumerate(kids):
            text = child["text"] if isinstance(child, dict) else child
            cue = child.get("cue", n["cue"]) if isinstance(child, dict) else n["cue"]
            cid = f"{n['id']}_{i}"
            out.append({"id": cid, "kind": "text", "style": style, "text": text, "size": size, "align": "center",
                        "abs": {"x": area["x"] + i * (cw + gap), "y": area["y"] + area["h"] - bh, "w": cw, "h": bh}, "cue": cue, **leave})
            out.append({"id": cid + "_a", "kind": "arrow", "from": n["id"] + "_root", "to": cid, "from_side": "b", "to_side": "t",
                        "elbow": "vhv" if k > 1 else None, "cue": cue, **leave})
    return out


COL_PX = 1920 * (1 - SAFE["left"] - SAFE["right"]) / 12      # one grid column in pixels (the safe area over 12 columns)


def _fit_words(text: str, max_chars: int) -> str:
    """The book's own words, shortened to fit by code: the parenthesis dropped, then the first part before ' / ' or ',', then
    whole words up to ``max_chars`` (a cell or a label never runs out of its box)."""
    t = re.sub(r"\s*\([^)]*\)", "", str(text or "")).strip()
    if len(t) > max_chars:
        t = re.split(r"\s+/\s+|,\s*|;\s*", t)[0].strip()
    if len(t) > max_chars:
        cut = ""
        for w in t.split():
            if len(cut) + len(w) + (1 if cut else 0) > max_chars:
                break
            cut = f"{cut} {w}".strip()
        t = cut or t[:max_chars]
    return t


def expand_pictures(nodes: list, grid, frame_of=None, block_layers=None) -> list:
    """A picture node (Task 046 Part D1; placed by code from the book, ``bie/brain/visual_thinking.picture_node``) becomes canvas
    elements on the paper, one group the density limit counts once (it is one anchor diagram, CV-09):

    - timeline: per event a tag with the book's date (and the place or dynasty when it fits), the event's icon with its name, an
      arrow to the next event; each event appears on the beat that covers its book line;
    - gallery: per panel the thing's icon with its number and name, an arrow to the next panel when the book joins them;
    - flow: per step a box with the book's words, an arrow to the next step;
    - table: the book's table, a row on the beat that says it, a band on the row being spoken.
    """
    out = []
    for n in nodes:
        if n.get("kind") != "picture":
            out.append(n)
            continue
        pic = n.get("picture") or {}
        ptype, nid = pic.get("type"), n.get("id", "picture")
        if "cell" not in n:
            raise PlanError(f"{nid}: a picture needs a cell")
        col, row, w, h = n["cell"]
        until = n.get("until_cue")
        group = {"group": nid, **({"until_cue": until} if until else {})}
        if ptype in ("timeline", "gallery", "flow"):
            seq = pic.get({"timeline": "events", "gallery": "panels", "flow": "nodes"}[ptype]) or []
            if len(seq) < 2:
                raise PlanError(f"{nid}: a {ptype} picture needs at least two {'events' if ptype == 'timeline' else 'panels' if ptype == 'gallery' else 'steps'}")
            per = max(1, w // len(seq))
            one = cell_box([col, row, per, 1], grid)["w"] * 1920                        # one item's cell, in pixels
            label_chars = max(4, int((one - 8) / (MIN_FONT * CHAR_W)))                   # labels and tags at the readable size (CV-17)
            tag_chars = max(4, int((one - 48) / (MIN_FONT * TAG_CHAR_W)))
            icon_rows = h - 1 if ptype == "timeline" else h
            if ptype in ("timeline", "gallery") and icon_rows < 2:
                raise PlanError(f"{nid}: a {ptype} picture needs at least {3 if ptype == 'timeline' else 2} rows of the grid, so its "
                                f"icons and their labels are readable ({MIN_FONT}px, CV-17)")
            main = []
            for i, it in enumerate(seq):
                c0, cue = col + i * per, it.get("cue") or n.get("cue")
                if ptype == "timeline":
                    when, name = str(it.get("when") or it.get("date", "")[:4]), str(it.get("name") or it.get("label", ""))
                    tag = f"{when} {name}" if name and len(f"{when} {name}") <= tag_chars and it.get("detail") else when
                    label = it.get("detail") if tag != when else name
                    out.append({"id": f"{nid}_y{i + 1}", "kind": "text", "style": "tag", "text": _fit_words(tag, tag_chars),
                                "cell": [c0, row, per, 1], "cue": cue, **group})
                    out.append({"id": f"{nid}_e{i + 1}", "kind": "icon", "icon": it.get("icon") or "tw:1f4c5",
                                "label": _fit_words(label or name, label_chars), "cell": [c0, row + 1, per, max(1, h - 1)], "cue": cue, **group})
                    main.append(f"{nid}_e{i + 1}")
                elif ptype == "gallery":
                    label = (f"{it.get('n', i + 1)}. {_fit_words(it.get('name', ''), label_chars - 3)}" if it.get("numbered", True)
                             else _fit_words(it.get("name", ""), label_chars))         # the book's numbers only when the book numbers them
                    out.append({"id": f"{nid}_p{i + 1}", "kind": "icon", "icon": it.get("icon") or "tw:1f5bc", "label": label,
                                "cell": [c0, row, per, h], "cue": cue, **group})
                    main.append(f"{nid}_p{i + 1}")
                else:
                    out.append({"id": f"{nid}_s{i + 1}", "kind": "text", "style": "box", "text": _fit_words(it.get("label", ""), 40),
                                "size": MIN_FONT, "cell": [c0, row, per, h], "cue": cue, **group})
                    main.append(f"{nid}_s{i + 1}")
            if pic.get("arrows", True):
                for i in range(1, len(main)):
                    cue = seq[i].get("cue") or n.get("cue")
                    out.append({"id": f"{nid}_a{i}", "kind": "arrow", "from": main[i - 1], "to": main[i], "from_side": "r", "to_side": "l",
                                "cue": cue, "tone": "muted", **group})
        elif ptype == "table":
            columns, rows = list(pic.get("columns") or []), list(pic.get("rows") or [])
            if not rows or not columns:
                raise PlanError(f"{nid}: a table picture needs columns and rows")
            cell_px = cell_box([col, row, w, h], grid)["h"] * 1080
            per_page = max(1, int(cell_px / (MIN_FONT / 0.42)) - 1)       # rows that fit the cell at the readable size (CV-17)
            pages = [rows[i:i + per_page] for i in range(0, len(rows), per_page)]
            size = min(40, int(cell_px / (min(per_page, len(rows)) + 1) * 0.42))
            cw = w * COL_PX / len(columns)
            chars = max(6, int((cw - 28) / (size * 0.62)))
            # A book table longer than its cell shows a page at a time (Navin, 3 November 2026: "long tables"; CV-17): each page takes
            # the cell when its first row is said, the page before it leaves then; pages that start on the same beat share its time.
            starts = [p[0].get("cue") or n.get("cue") for p in pages]
            for k in range(1, len(pages)):
                same = [j for j in range(len(pages)) if (starts[j] or [None])[0] == (starts[k] or [None])[0]]
                if len(same) > 1 and starts[k] and not (len(starts[k]) > 1 and starts[k][1]):
                    starts[k] = [starts[k][0], "", round(same.index(k) / len(same), 3)]
            for k, page in enumerate(pages):
                fit_rows = [{"cells": [_fit_words(c, chars) for c in r.get("cells") or []], "cue": r.get("cue") or n.get("cue")} for r in page]
                if k:
                    fit_rows[0]["cue"] = starts[k]
                highlights = []
                for i, r in enumerate(fit_rows):
                    h_ = {"row": i, "cue": r["cue"], "tone": "band"}
                    if i + 1 < len(fit_rows) and fit_rows[i + 1]["cue"] != r["cue"]:
                        h_["until_cue"] = fit_rows[i + 1]["cue"]
                    highlights.append(h_)
                part = {"id": nid if len(pages) == 1 else f"{nid}_t{k + 1}", "kind": "table", "cell": n["cell"],
                        "cue": n.get("cue") if k == 0 else starts[k], "size": size,
                        "columns": [_fit_words(c, chars) for c in columns], "rows": fit_rows, "highlights": highlights, **group}
                if k + 1 < len(pages):
                    part["until_cue"] = starts[k + 1]
                out.append(part)
        else:
            raise PlanError(f"{nid}: unknown picture type {ptype!r} (timeline, gallery, flow, table)")
    return out


def _date(year: int) -> str:
    return f"{year:04d}-01-01" if year > 0 else f"-{abs(year):06d}-01-01"


def _elem_box(e, by_id):
    if "x" in e:
        return (e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"])
    refs = [e.get("target"), (e.get("from") or {}).get("id"), (e.get("to") or {}).get("id")]
    boxes = [_elem_box(by_id[r], by_id) for r in refs if r and r in by_id and "x" in by_id[r]]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def _strip_fix(box, hits, visible):
    """An auto camera box [x, y, size] moved down (and grown when it must) until every element it shows ends above the
    subtitle strip; the beat's own elements (``hits``) stay in view. A box that grows to the whole canvas is the full view."""
    room = SUBTITLE_TOP - 0.02
    for _ in range(4):
        x, y, sz = box
        if sz >= 1.0:
            return [0.0, 0.0, 1.0]
        inside = [b for b in visible if b[0] < x + sz and b[2] > x and b[1] < y + sz and b[3] > y]
        low = max([b[3] for b in inside] + [h[3] for h in hits])
        if low <= y + room * sz + 1e-6:
            return box
        top = min([h[1] for h in hits] + [y])
        nsz = min(1.0, max(sz, (low - top) / room))
        box = [min(max(x + sz / 2 - nsz / 2, 0.0), 1 - nsz), min(max(low - room * nsz, 0.0), 1 - nsz), nsz]
    return box


def auto_camera(els, beat_frames, beat_order, duration, min_size=0.72, margin=0.06):
    """L3 touch: a camera that frames, beat by beat, what appears in this beat and the one before (and what those point
    at); it never crops an element in half (the frame grows to take it in whole) and the last beat pulls back to the
    whole canvas. Boxes keep the 16:9 shape (equal fractions) and stay inside the canvas."""
    by_id = {e["id"]: e for e in els}

    def times(e):
        return ([e.get("at", 0)] + [s["at"] for s in e.get("steps", [])] + [m["at"] for m in e.get("marks", [])]
                + list((e.get("step_at") or {}).values()))

    def square(x0, y0, x1, y1):
        size = min(1.0, max(min_size, x1 - x0, y1 - y0))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        return [min(max(cx - size / 2, 0.0), 1 - size), min(max(cy - size / 2, 0.0), 1 - size), size]

    keys, prev = [], None
    for i, bid in enumerate(beat_order):
        start, length = beat_frames[bid]
        end = start + length
        lo = start
        hits = [b for e in els if any(lo - 3 <= t < end for t in times(e)) for b in [_elem_box(e, by_id)] if b]
        if i == len(beat_order) - 1 or not hits:
            if i != len(beat_order) - 1:
                continue
            box = [0.0, 0.0, 1.0]
        else:
            box = square(min(h[0] for h in hits) - margin, min(h[1] for h in hits) - margin,
                         max(h[2] for h in hits) + margin, max(h[3] for h in hits) + margin * 1.6)
            visible = [b for e in els if e.get("at", 0) < end and e.get("until", 10 ** 9) > start for b in [_elem_box(e, by_id)] if b]
            hx0, hy0 = min(h[0] for h in hits), min(h[1] for h in hits)
            hx1, hy1 = max(h[2] for h in hits), max(h[3] for h in hits)

            def cuts(bx):           # an element the frame cuts, or one that would sit under the subtitle strip (D2)
                x, y, sz = bx
                low = y + (SUBTITLE_TOP - 0.01) * sz if sz < 1.0 else y + sz
                return [b for b in visible if b[0] < x + sz and b[2] > x and b[1] < y + sz and b[3] > y
                        and not (b[0] >= x - 1e-6 and b[2] <= x + sz + 1e-6 and b[1] >= y - 1e-6 and b[3] <= low + 1e-6)]

            for _ in range(6):
                cut = cuts(box)
                if not cut:
                    break
                x, y, sz = box
                moved = None
                for b in cut:                       # first try to slide the frame so the element is fully out (or in)
                    for nx, ny in ((b[2] + 0.01, y), (b[0] - 0.01 - sz, y), (x, b[3] + 0.01), (x, b[1] - 0.01 - sz),
                                   (b[0] - 0.01, y), (b[2] + 0.01 - sz, y), (x, b[1] - 0.01), (x, b[3] + 0.01 - sz)):
                        nx, ny = min(max(nx, 0.0), 1 - sz), min(max(ny, 0.0), 1 - sz)
                        if nx <= hx0 and nx + sz >= hx1 and ny <= hy0 and ny + sz >= hy1 and len(cuts([nx, ny, sz])) < len(cut):
                            moved = [nx, ny, sz]
                            break
                    if moved:
                        break
                box = moved or square(min([x] + [b[0] - 0.02 for b in cut]), min([y] + [b[1] - 0.02 for b in cut]),
                                      max([x + sz] + [b[2] + 0.02 for b in cut]), max([y + sz] + [b[3] + 0.02 for b in cut]))
            box = _strip_fix(box, hits, visible)        # D2: nothing on screen under the subtitle strip of the frame
        b = {"x": round(box[0], 4), "y": round(box[1], 4), "w": round(box[2], 4), "h": round(box[2], 4)}
        if prev and all(abs(b[k] - prev[k]) < 0.02 for k in b):
            continue
        keys.append({"at": max(0, start - 6), "box": b, "frames": 30})
        prev = b
    return keys


def _zoomed_during(keys: list, start: int, end: int, *, wide: float = 0.95) -> bool:
    """Whether a camera (its keys with ``at`` and ``box``) is zoomed in at any time between ``start`` and ``end``."""
    keys = sorted((k for k in keys or [] if "box" in k), key=lambda k: k["at"])
    for i, k in enumerate(keys):
        until = keys[i + 1]["at"] if i + 1 < len(keys) else 10 ** 9
        if k["at"] < end and until > start and float(k["box"].get("w", 1)) < wide:
            return True
    return False


def one_camera_at_a_time(keys: list, scene_keys: list | None) -> list:
    """The block camera stays on the whole canvas while the scene camera (the plan's own) is zoomed in: two zooms together
    pushed a node under the captions though each kept it above them (seekh -> BIE, the addendum proof's run a)."""
    if not scene_keys:
        return keys
    keys = sorted((dict(k) for k in keys or []), key=lambda k: k["at"])
    for i, k in enumerate(keys):
        until = keys[i + 1]["at"] if i + 1 < len(keys) else 10 ** 9
        if "box" in k and float(k["box"].get("w", 1)) < 1 and _zoomed_during(scene_keys, k["at"], until):
            k["box"] = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
    return keys


def action_close_ups(keys: list, els: list, scene_keys: list | None = None) -> list:
    """The block camera moves in to each action's close-up (its box, square, with the action above the subtitle strip) and back
    to the auto camera's frame after it (D2: "the camera moves in to the action and back out"). Not while the scene camera
    (``scene_keys``, the plan's own camera) is zoomed in already: the two zooms together pushed an action under the captions
    though each kept it above them (seekh -> BIE, the addendum proof's run a: 3 parts refused after three rounds)."""
    out = [dict(k) for k in keys]
    for e in sorted((e for e in els if e.get("close_up")), key=lambda e: e["close_up"]["at"]):
        cu = e["close_up"]
        if scene_keys and _zoomed_during(scene_keys, cu["at"], min(cu["until"], e.get("until", 10 ** 9))):
            continue
        size = min(1.0, max(e["w"], e["h"] / (SUBTITLE_TOP - 0.04)) + 0.04)
        x = min(max(e["x"] + e["w"] / 2 - size / 2, 0.0), 1 - size)
        y = min(max(e["y"] + e["h"] - (SUBTITLE_TOP - 0.03) * size, 0.0), 1 - size)
        until = min(cu["until"], e.get("until", 10 ** 9))      # the camera never stays close on a box whose action has left
        if until - cu["at"] < 24:
            continue
        cu = dict(cu, until=until)
        before = [k for k in out if k["at"] <= cu["until"] and not k.get("close_up")]
        back = dict(before[-1]["box"]) if before else {"x": 0, "y": 0, "w": 1, "h": 1}
        out = [k for k in out if not (cu["at"] <= k["at"] <= cu["until"])]
        out.append({"at": cu["at"], "box": {"x": round(x, 4), "y": round(y, 4), "w": round(size, 4), "h": round(size, 4)}, "frames": 22,
                    "close_up": e["id"]})
        out.append({"at": cu["until"], "box": back, "frames": 30})
        out.sort(key=lambda k: k["at"])
    return out


def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2          # Easing.inOut(Easing.cubic)


def _cam_box(keys: list, frame: int, *, span: int = 24, first_direct: bool = False) -> dict:
    """A camera's box at a frame, eased between keys as the renderer does: the block camera (canvas.tsx ``camBox``, from the
    full canvas, 24 frames a move) or the scene camera (``first_direct``: blocks/index.tsx ``cameraBox``, the first key at
    once, 36 frames a move)."""
    keys = [k for k in keys or [] if "box" in k]
    box = dict(keys[0]["box"]) if first_direct and keys else {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0}
    for k in keys[1:] if first_direct else keys:
        if frame < k["at"]:
            break
        t = _ease((frame - k["at"]) / max(1, k.get("frames", span)))
        box = {n: box[n] + (k["box"][n] - box[n]) * t for n in ("x", "y", "w", "h")}
    return box


def subtitle_problems(scene: dict, *, step: int = 6) -> list:
    """D2: nothing the canvas shows sits under the subtitle strip. The block camera (``data.cam``) and the scene camera both
    move the canvas; an element on screen whose bottom lands below the strip's top (0.86 of the frame) is named."""
    data = scene["layers"][0]["data"]
    els = [e for e in data.get("elements") or [] if "x" in e]
    out, named = [], set()
    for f in range(0, scene["duration"], step):
        inner, outer = _cam_box(data.get("cam"), f), _cam_box(scene.get("camera"), f, span=36, first_direct=True)
        for e in els:
            if e["id"] in named or not e.get("at", 0) + 12 <= f < e.get("until", 10 ** 9):
                continue
            x0, y0 = (e["x"] - inner["x"]) / inner["w"], (e["y"] - inner["y"]) / inner["h"]
            x1, y1 = (e["x"] + e["w"] - inner["x"]) / inner["w"], (e["y"] + e["h"] - inner["y"]) / inner["h"]
            x0, x1 = (x0 - outer["x"]) / outer["w"], (x1 - outer["x"]) / outer["w"]
            y0, y1 = (y0 - outer["y"]) / outer["h"], (y1 - outer["y"]) / outer["h"]
            if x1 > 0 and x0 < 1 and y0 < SUBTITLE_TOP and y1 > SUBTITLE_TOP + 0.01 and y1 < 1.3:
                named.add(e["id"])
                out.append(f"{e['id']} sits under the subtitle strip at {f / timing.FPS:.1f} s (its bottom at {y1:.2f} of the frame, the "
                           f"strip starts at {SUBTITLE_TOP:.2f}): move it up a row or let the camera show it higher")
    return out


# ---------------------------------------------------------------- compile

SHOWN = 6        # frames of a process's last step shown before it fades out (15 frames) for the next thing in its place


def _hand_over(first: dict, second: dict, later: list | None = None) -> str | None:
    """Code lets ``first`` give its place to ``second`` (seekh -> BIE, the first Part D2 run): only when the second starts at
    least 12 frames later and neither belongs to a book picture's group. The first leaves as the second comes when it has
    nothing left to do then (no value step, action step or counted item at or after the second's start); two processes on one
    place hand over after the first's last step has begun (at least SHOWN of its 24 motion frames, then the 15-frame fade of
    saanche.tsx), the second coming on by its own first step. An action that meets the other only in its own lead-in (the
    other leaves by the action's first step) comes on as the other leaves, whatever the other is (a book picture too).
    ``later`` gives the first's step frames while it is still being compiled. Returns what was done, or None (the maker moves
    one)."""
    at = second.get("at", 0)
    nxt = min((second.get("step_at") or {}).values(), default=None)
    gone = first.get("until", 10 ** 9)
    if second.get("kind") == "action" and nxt is not None and at < gone <= nxt:
        second["at"] = gone                   # they meet only in the action's lead-in: it comes on as the other leaves
        return f"{second['id']} comes on when {first['id']} leaves (its lead-in shortened)"
    if at - first.get("at", 0) < 12 or first.get("group") or second.get("group"):
        return None
    if later is None:
        if first.get("items"):                # code spread count_stack's items: they finish before the next thing comes
            from .video import saanche
            saanche.fit_items(first, at)
        later = [st.get("at", 0) for st in first.get("steps") or [] if isinstance(st, dict)]
        later += list((first.get("step_at") or {}).values()) + list(first.get("items") or [])
    pad = SHOWN if first.get("kind") == "action" else 0       # a process shows at least SHOWN frames of its last step's motion
    if not any(f + pad > at for f in later):
        first["until"] = at
        return f"{first['id']} leaves when {second['id']} comes"
    if nxt is None and second.get("kind") == "action":
        nxt = at                                 # still being compiled: it is on screen from its first step's word
    if first.get("kind") == "action" and second.get("kind") == "action" and nxt is not None and later:
        return hand_over_after(first, second, max(later), nxt)
    return None


def hand_over_after(first: dict, second: dict, last: int, nxt: int) -> str | None:
    """A process gives its place to the next thing there, the first's last step at ``last``, the next thing's first moment at
    ``nxt`` (an action's first step, or another element's start): the first plays its last step for at least SHOWN of its 24
    motion frames (then fades in 15) and leaves by ``nxt``; a next action comes on by its own first step. None when ``nxt``
    comes too soon (the maker moves one). Used by the canvas and the world alike."""
    end = min(last + 12, nxt)
    if end < last + SHOWN:
        return None
    first["until"] = end
    if second.get("kind") == "action":
        second["at"] = max(second.get("at", 0), end)
    return f"{first['id']} plays its last step, then {second['id']} comes on in its place"


def compile_plan(plan: dict, *, voice: dict | None = None, icon_paths: dict | None = None, lead_in: float = timing.LEAD_IN):
    """Return (scene_spec, report). Raises PlanError for a plan that would render wrong."""
    grid = plan.get("grid", [12, 8])
    beats = plan["beats"]
    if not beats:
        raise PlanError("a plan needs at least one beat")
    says = {b["beat_id"]: b["say"] for b in beats}
    scene_id = plan.get("id", "canvas")
    voice = voice if voice is not None else formats.voice_of(beats)      # Task 047: the spoken words, once the voice section writes them
    tl = timing.build(beats, [{"scene_id": scene_id, "beat_ids": [b["beat_id"] for b in beats]}], voice=voice, lead_in=lead_in)
    fps = tl[scene_id]["fps"]
    problems = []

    def frame_of(cue):
        return cue_frame(tl, scene_id, says, cue)

    els, boxes, cells_used, fixes = [], {}, [], []
    for n in expand_pictures(expand_trees(plan.get("nodes", []), grid), grid):
        kind = n["kind"]
        if kind not in KINDS:
            raise PlanError(f"{n.get('id', '?')}: unknown element kind {kind!r} (kinds: {', '.join(KINDS)})")
        if kind == "action" and "cue" not in n and n.get("steps"):
            n = dict(n, cue=n["steps"][0].get("cue"))          # an action is on screen from its first step (the cell check reads it)
        el = {"id": n["id"], "kind": kind}
        for k in ("tone", "style", "label", "label_tone", "mark", "pos", "dir", "fill", "border", "align", "dashed", "curve",
                  "elbow", "head", "width", "cols", "stagger", "write_on", "label_size", "pad", "group"):
            if k in n:
                el[k] = n[k]
        if "curve" in el:
            el["curve"] = arrow_bend(el["curve"])
        if el.get("style") == "tag":
            el.pop("tone", None)          # a tag's words are white on its own fill (the v2 render: blue "accent" words on pink)
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
                        # seekh -> BIE (the first Part D2 run): a later element in the same cells takes them over, the earlier
                        # one leaves as it comes; two that start together stay a problem for the maker
                        first, second = (o, el) if b_on[0] <= a_on[0] else (el, o)
                        own = [frame_of(st["cue"]) for st in n.get("steps") or [] if isinstance(st, dict) and st.get("cue")]
                        done = _hand_over(first, second, own if first is el else None)
                        if done:
                            fixes.append(done + " (its cells)")
                        else:
                            raise PlanError(f"{n['id']} and {other_id} share grid cells while both are on screen")
            if "cell" in n:
                cells_used.append((n["id"], n["cell"]))
            if kind == "icon":
                label = str(n.get("label") or "")
                rows = [label] if label else []
                if label and len(label) * MIN_FONT * CHAR_W + 8 > box["w"] * 1920 + 1:
                    rows = label_lines(label, box["w"] * 1920)          # a long label takes a second line before it is refused
                    if not rows:
                        raise PlanError(f"{n['id']}: its label {label!r} is wider than its cell at the readable size ({MIN_FONT}px, CV-17) "
                                        "even on two lines: shorten the label or give the icon a wider cell")
                box = fit_icon(box, rows or label)
                if label and box["side_px"] < MIN_ICON:
                    raise PlanError(f"{n['id']}: the icon is {box['side_px']:.0f}px with its label at the readable size ({MIN_FONT}px, "
                                    f"CV-17); give it a taller cell (2 rows) or no label")
                box.pop("side_px", None)
                if label:
                    el.update(label_size=MIN_FONT, label_share=box.pop("label_share"))
                    if len(rows) > 1:
                        el["label_lines"] = rows
                el["src"] = (icon_paths or {}).get(n["icon"], n["icon"])
            elif kind in ("text", "callout"):
                style = n.get("style", "note" if kind == "callout" else "plain")
                size, h = fit_text(n["text"], box, max(MIN_FONT, n.get("size", 56 if style == "title" else MIN_FONT)), style)
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
                el["size"] = max(MIN_FONT, n.get("size", 52))
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
                if "cue" not in n and el["rows"]:
                    el["at"] = min(r["at"] for r in el["rows"])      # the header arrives with the first row, not at frame 0
                if any(len(r["cells"]) != len(n["columns"]) for r in n["rows"]):
                    raise PlanError(f"table {n['id']} has a row whose cell count differs from its columns")
                rh = box["h"] * 1080 / (len(n["rows"]) + 1)
                size = max(n.get("size") or 0, min(40, int(rh * 0.42)))
                if size < MIN_FONT:
                    raise PlanError(f"table {n['id']} has too many rows for its cell: its text would be {size}px, under the readable "
                                    f"{MIN_FONT}px (CV-17); give it more rows of the grid or split it in two")
                cw = box["w"] * 1920 / len(n["columns"])
                widest = max(len(str(t)) for r in [n["columns"]] + [r["cells"] for r in n["rows"]] for t in r)
                if widest * size * 0.62 + 28 > cw:
                    raise PlanError(f"table {n['id']}: a cell's text is wider than its column")
                el["size"] = size
                el["highlights"] = [{**{k: v for k, v in h.items() if k in ("row", "col", "tone")}, "at": frame_of(h["cue"]),
                                     **({"until": frame_of(h["until_cue"])} if "until_cue" in h else {})} for h in n.get("highlights", [])]
            elif kind == "action":
                from .video import saanche                     # lazy: saanche imports this module's PlanError
                if n["cell"][3] < MIN_ACTION_ROWS:
                    raise PlanError(f"{n['id']}: an action needs at least {MIN_ACTION_ROWS} rows of the grid (its people must be big "
                                    "enough to see their hands and faces)")
                a = saanche.compile_action(n, frame_of, says, icon_paths=icon_paths, main_look=saanche.main_look(scene_id.split("_")[0]),
                                           beat_spans={k: tuple(v) for k, v in tl[scene_id]["beats"].items()})
                el.update({k: v for k, v in a.items() if k not in ("id", "kind")})
                wpx, hpx = box["w"] * 1920, box["h"] * 1080
                k = min(wpx / saanche.STAGE_W, hpx / saanche.STAGE_H)
                w, h = saanche.STAGE_W * k / 1920, saanche.STAGE_H * k / 1080
                box = {"x": box["x"] + (box["w"] - w) / 2, "y": box["y"] + box["h"] - h, "w": w, "h": h}
            elif kind == "crowd":
                el["src"] = (icon_paths or {}).get(n["icon"], n["icon"])
                el["steps"] = [{"n": s["n"], "at": frame_of(s["cue"])} for s in n["steps"]]
                if any(not isinstance(s["n"], int) or s["n"] < 0 for s in n["steps"]):
                    raise PlanError(f"crowd {n['id']}: every step count must be a whole number")
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
        else:
            raise PlanError(f"{n['id']}: a {kind} needs a cell")
        els.append(el)

    ids = [e["id"] for e in els]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        raise PlanError(f"element id {dup!r} is used twice")
    ids = set(ids)
    # A picture node becomes many elements of one group (expand_pictures), so its own id is no element: a reference to it means
    # the picture (the Money v4 run of 31 October 2026: a focus on the maker's gallery 'status' was refused three rounds running).
    members = {}
    for e in els:
        if e.get("group") and e["group"] not in ids:
            members.setdefault(e["group"], []).append(e["id"])

    def known(ref):
        return ref in ids or ref in members

    def missing(what, ref):
        names = sorted(ids - {e["id"] for e in els if e.get("group") in members}) + sorted(members)
        return PlanError(f"{what} a missing element {ref!r}; the plan's ids are: {', '.join(names[:40])}")

    for e in els:
        for ref in [e.get("target"), (e.get("from") or {}).get("id"), (e.get("to") or {}).get("id")]:
            if ref and not known(ref):
                raise missing(f"{e['id']} refers to", ref)
        if e.get("target") in members:
            e["target"] = members[e["target"]][0]
        for end in ("from", "to"):
            if (e.get(end) or {}).get("id") in members:
                e[end] = dict(e[end], id=members[e[end]["id"]][0 if end == "to" else -1])
    # measured boxes must not overlap while on screen together (catches rounding and value/text growth)
    placed = [e for e in els if "x" in e]
    for i, a in enumerate(placed):
        for b in placed[i + 1:]:
            on = max(a.get("at", 0), b.get("at", 0)) < min(a.get("until", 10 ** 9), b.get("until", 10 ** 9))
            if on and overlap(a, b):
                first, second = (a, b) if a.get("at", 0) <= b.get("at", 0) else (b, a)
                done = _hand_over(first, second)      # seekh -> BIE: the earlier one gives its place to the later one
                if done:
                    fixes.append(done + " (same place)")
                else:
                    raise PlanError(f"{a['id']} and {b['id']} overlap on screen")
    by_id = {e["id"]: e for e in els}
    for e in els:                          # an arrow, mark or highlight leaves with the element it points at
        ends = [by_id.get(r) for r in (e.get("target"), (e.get("from") or {}).get("id"), (e.get("to") or {}).get("id")) if r]
        untils = [x["until"] for x in ends if x and "until" in x]
        if untils and min(untils) < e.get("until", 10 ** 9):
            e["until"] = min(untils)
    duration = tl[scene_id]["duration"]
    # density: how many elements are visible at once (peak)
    peak = max((len({e.get("group") or e["id"] for e in els if e.get("at", 0) <= f < e.get("until", 10 ** 9)}) for f in range(0, duration, 5)),
               default=0)                          # a book picture (one group) is one anchor diagram (CV-09), counted once (D1)
    if peak > MAX_VISIBLE:
        problems.append(f"{peak} elements on screen at once (limit {MAX_VISIBLE}): clear the canvas or use until/focus")
    # pace: the longest stretch of speech with no visual change
    changes = sorted({e.get("at", 0) for e in els} | {s["at"] for e in els for s in e.get("steps", [])}
                     | {f for e in els for f in (e.get("step_at") or {}).values()} | {f for e in els for f in e.get("items", [])}
                     | {m["at"] for e in els for m in e.get("marks", [])}
                     | {r["at"] for e in els for r in e.get("rows", [])})          # a book table's rows arrive on their beats (D1)
    camera_keys = []
    for k in plan.get("camera", []):
        f = frame_of(k.get("cue"))
        changes.append(f)
        want = cell_box(k["cells"], grid) if "cells" in k else k.get("box", {"x": 0, "y": 0, "w": 1, "h": 1})
        key = {"at": f, "box": above_strip(fit_box(pad_box(want)), want)}
        if "frames" in k:
            key["frames"] = k["frames"]
        camera_keys.append(key)
    for f in plan.get("focus", []):
        changes.append(frame_of(f["cue"]))
        for fid in f["ids"]:
            if not known(fid):
                raise missing("focus names", fid)
        f["ids"] = [m for fid in f["ids"] for m in (members.get(fid) or [fid])]
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
        problems.append(f"the picture stays the same for {still:.1f} s (limit {MAX_STILL_S:.0f} s): add a step, a mark or a camera move")
    elif still > TARGET_STILL_S:
        advisories.append(f"the picture stays the same for {still:.1f} s (target {TARGET_STILL_S:.0f} s)")
    every = duration / fps / max(1, len(changes) - 1)
    if every > TARGET_CHANGE_EVERY_S:
        advisories.append(f"one change every {every:.1f} s (target {TARGET_CHANGE_EVERY_S:.0f} s)")
    data = {"theme": plan.get("theme", "paper"), "elements": els}
    if plan.get("touches"):
        data["touches"] = True
        data["cam"] = one_camera_at_a_time(action_close_ups(auto_camera(els, tl[scene_id]["beats"], [b["beat_id"] for b in beats],
                                                                        duration), els, camera_keys), camera_keys)
    for e, n in zip(els, expand_pictures(expand_trees(plan.get("nodes", []), grid), grid)):
        if n.get("flow"):
            f = dict(n["flow"])
            f["src"] = (icon_paths or {}).get(f.get("icon", ""), f.get("icon", ""))
            if "cue" in f:
                f["at"] = frame_of(f.pop("cue"))
            if "until_cue" in f:
                f["until"] = frame_of(f.pop("until_cue"))
            e["flow"] = f
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
    scene = {"id": scene_id, "duration": duration, "layers": layers, "camera": camera_keys or [{"at": 0}],
             "captions": captions_of(tl, scene_id, beats)}
    report = {"scene": scene_id, "seconds": round(duration / fps, 1), "elements": len(els), "peak_visible": peak,
              "longest_still_s": round(still, 1), "changes": len(changes) - 1,
              "change_every_s": round(every, 1), "problems": problems, "advisories": advisories,
              "mode": "B" if plan.get("touches") else "A", "level": "L2 + touches" if plan.get("touches") else "L2",
              "auto_fixes": fixes + [f for e in els for f in e.pop("auto_fixes", [])]}
    return scene, report


def icons_in(plan: dict) -> list:
    """Every icon id a plan names (icons, crowds, flows), once each, in order."""
    out = []
    for n in plan.get("nodes", []):
        refs = [n.get("icon"), (n.get("flow") or {}).get("icon")] + [o.get("icon") for o in n.get("objects") or []]
        if n.get("kind") == "picture":
            pic = n.get("picture") or {}
            refs += [p.get("icon") or ("tw:1f5bc" if group == "panels" else "tw:1f4c5") for group in ("panels", "events") for p in pic.get(group) or []]
        for ref in refs:
            if ref and ref not in out:
                out.append(ref)
    return out


# ---------------------------------------------------------------- the video around the scenes

def video_spec(scenes: list, *, audio: str | None = None) -> dict:
    """The VideoSpec the preview renderer and Remotion read: the scenes in order, captions drawn by the core strip."""
    out = {"schema": SCHEMA, "fps": timing.FPS, "width": 1920, "height": 1080, "captions": True, "scenes": scenes}
    if audio:
        out["audio"] = audio
    return out


CREDITS_PER_PAGE = 7      # two text rows each at the readable size (CV-17) fill a 1080p frame under the title
CREDITS_GRID = [12, 16]


def credits_scene(lines: list, seconds: float = 5.0, *, scene_id: str = "credits", title: str = "Credits · श्रेय") -> dict:
    """A closing card on the paper canvas that lists the CC BY credits of the assets the video shows (the licence gate's
    lines), at the readable size (CV-17): seven credits a page, each in a two-row box, one page after another (``seconds`` a
    page)."""
    page_frames = int(round(seconds * timing.FPS))
    pages = [lines[i:i + CREDITS_PER_PAGE] for i in range(0, len(lines), CREDITS_PER_PAGE)] or [[]]
    grid = CREDITS_GRID
    els = []
    title_box = cell_box([0, 0, 12, 2], grid)
    size, h = fit_text(title, title_box, 48, "title")
    els.append({"id": "title", "kind": "text", "style": "title", "text": title, "size": size, "at": 6, "align": "center",
                **{**title_box, "y": title_box["y"] + max(0, (title_box["h"] - h) / 2), "h": h}})
    for p, page in enumerate(pages):
        start, end = p * page_frames, (p + 1) * page_frames
        for i, line in enumerate(page):
            box = cell_box([1, 2 + 2 * i, 10, 2], grid)
            text = line
            while True:
                try:
                    size, h = fit_text(text, box, MIN_FONT, "box")
                    break
                except PlanError:
                    text = text[: max(20, int(len(text) * 0.85))].rstrip() + "…"   # a very long credit keeps its start (title, author, licence)
            el = {"id": f"c{p}_{i}", "kind": "text", "style": "box", "text": text, "size": size, "at": start + 6 + 8 * i, "align": "left",
                  **{**box, "y": box["y"] + max(0, (box["h"] - h) / 2), "h": h}}
            if p < len(pages) - 1:
                el["until"] = end
            els.append(el)
    layer = {"id": scene_id + "_canvas", "type": "block", "block": "canvas_build", "at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1},
             "data": {"theme": "paper", "elements": els}}
    return {"id": scene_id, "duration": page_frames * len(pages), "layers": [layer], "camera": [{"at": 0}], "captions": []}


def stubs(video: dict) -> list:
    """One canvas plan stub per script part (the AI director fills ``nodes``), grouped exactly as the shot-list director
    groups scenes (``shots.scenes_of``: a hook before the first part belongs to that part; a closing beat without a part
    stays with the last part), so canvas scenes line up with the code director's scenes."""
    by_id = {b["beat_id"]: b for b in video.get("beats") or []}
    out = []
    for sc in shots_module.scenes_of(video.get("beats") or []):
        beats = [by_id[b] for b in sc["beat_ids"]]
        out.append({"id": f"{video.get('video_id', 'v')}_{sc['scene_id']}", "part_id": sc["part_id"], "theme": "paper", "grid": [12, 8],
                    "touches": True,
                    "beats": [{"beat_id": b["beat_id"], "say": b["say"]} for b in beats],
                    "covers_item_ids": sorted({i for b in beats for i in (b.get("covers_item_ids") or [])}),
                    "on_screen_hints": [b.get("on_screen") for b in beats if b.get("on_screen")],
                    "nodes": []})
    return out


# ---------------------------------------------------------------- short proof clips (toolbox demos and tests)

def trim_plan(plan: dict, keep: int) -> dict:
    """The plan's first ``keep`` beats with only the pieces cued inside them: how a long test fixture becomes a 3-5 s proof
    clip. A node, step, camera key, focus entry or graph piece whose cue names a later beat is dropped; an ``until_cue`` or
    any other ``*_cue`` beyond the kept beats is removed (the piece then stays to the end); a node left with no steps, or one
    pointing at a dropped node, is dropped too. Works on canvas plans and on world plans."""
    plan = copy.deepcopy(plan)
    beats = plan["beats"][:keep]
    kept = {b["beat_id"] for b in beats}

    def inside(cue):
        return cue is None or (isinstance(cue, (list, tuple)) and len(cue) > 0 and cue[0] in kept)

    def walk(node):
        if isinstance(node, list):
            return [walk(x) for x in node if not (isinstance(x, dict) and "cue" in x and not inside(x["cue"]))]
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if k.endswith("_cue") and not inside(v):
                    continue
                if isinstance(v, dict) and "cue" in v and not inside(v["cue"]):
                    continue
                out[k] = walk(v)
            return out
        return node

    plan = walk(plan)
    plan["beats"] = beats
    for key in ("nodes", "elements"):
        if key in plan:
            plan[key] = [n for n in plan[key] if all(n.get(k) for k in ("steps", "packets") if k in n)]
    if "graph" in plan:
        g = plan["graph"]
        curves = {c.get("id") for c in g.get("curves", [])}
        g["dots"] = [d for d in g.get("dots", []) if d.get("steps") and d.get("curve") in curves]
    if "nodes" in plan:
        nodes = plan["nodes"]
        while True:
            ids = {n["id"] for n in nodes} | {f"{n['id']}_{i}" for n in nodes if n.get("kind") == "tree"
                                               for i in range(len(n.get("children") or []))}
            left = [n for n in nodes if all(n.get(k) in ids for k in ("from", "to", "target") if k in n)]
            if len(left) == len(nodes):
                break
            nodes = left
        plan["nodes"] = nodes
        for f in plan.get("focus") or []:
            f["ids"] = [i for i in f.get("ids", []) if i in ids]
    return plan


def squeeze(beats: list, seconds: float, *, lead_in: float = timing.LEAD_IN) -> dict:
    """A voice timing (``timing.build``'s ``voice``) that fits ``beats`` into ``seconds`` of clip: proof clips only. A lesson's
    timing comes from the words as spoken or, before there is a voice, from the character count."""
    natural = [timing.beat_seconds(b["say"]) for b in beats]
    room = seconds - lead_in - timing.TAIL - timing.GAP * (len(beats) - 1)
    k = max(0.1, room) / sum(natural)
    return {b["beat_id"]: {"duration": n * k} for b, n in zip(beats, natural)}


def write_spec(spec: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    return out
