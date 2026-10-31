"""The canvas director: one plan per script part, written by the AI maker on the director card and checked by code
(Task 046 Part C, PR 2; Navin, 27 October 2026: "B default ke saath kahani wale hisson mein C").

For a subject whose profile is the build-up canvas (``rulebook/canvas_profile.json``, ``families``), every part of a
passed script becomes ONE canvas (B: L2 + L3 touches) by default; a story part with actors in a place (a shop and its
buyers, ...) becomes an L3 world (C) when a kit exists for that place (``video/world.py``, ``KITS``), else a canvas plus a
line in the missing-capability log. The maker (Codex on the VM, ₹0) writes WHAT appears, in which grid cell, on which
spoken word; ``bie/brain/canvas.py`` and ``bie/brain/video/world.py`` place, time and check it, and a refused plan goes
back to the maker with the exact code error (no reviewer round for layout). First-try passes and rounds are counted per
part. The video spec of every video (scenes in part order, captions, the credits card) is written to ``video_specs/``,
the same place the visual section writes, for the renderer.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import canvas, shots, soul, visual_thinking as vt
from . import formats
from .assets import AssetLibrary
from .canvas import PlanError
from .video import screen_text
from .common import S, arr, fmt, obj
from .lesson import video_scope
from .runner import NOTES_SCHEMA, Step
from .understanding import Course
from .video import timing, world
from ..toolbox import icons, licence as licence_policy

SECTION = "canvas"
VERSION = "canvas-plan/1"
CARD_PATH = Path(__file__).resolve().parent / "rulebook" / "canvas_director_card.md"
WORLD_CARD_PATH = Path(__file__).resolve().parent / "rulebook" / "world_director_card.md"
FAMILIES = tuple(canvas.PROFILE.get("families") or ())
MAX_PART_BEATS = 12          # CV: a longer part is split into two or three canvases (one plan each), never one dense canvas
# The icon menu every plan can draw from (the maker has no search tool at run time; the menu is the index's answer to the
# words an economy part uses most; an id outside the index is refused with the nearest matches).
ICON_QUERIES = ("shop", "store", "factory", "bank", "money bag", "coin", "banknote", "person", "people", "worker", "farmer", "farm",
                "wheat", "truck", "ship", "airplane", "government building", "house", "laptop", "package", "basket", "shopping cart",
                "chart increasing", "chart decreasing", "scale balance", "oil", "fuel pump", "gold", "credit card", "receipt",
                "handshake", "globe", "india", "hospital", "school", "tractor", "warehouse", "industry", "gear", "lightbulb")

# ---------------------------------------------------------------- schemas (strict: every field present, defaults mean "unset")

N = {"type": "number"}
I = {"type": "integer"}
B = {"type": "boolean"}
STR_LIST = arr(S)
CUE = STR_LIST           # [beat_id, word] or [beat_id, ""] (the start of the beat; cue_fraction moves it into the beat)
STEP = obj({"text": S, "n": I, "dir": S, "cue": CUE})
CHILD = obj({"text": S, "cue": CUE})
ROW = obj({"cells": STR_LIST, "cue": CUE})
HIGHLIGHT = obj({"row": I, "col": I, "cue": CUE, "until_cue": CUE, "tone": S})
MARK = obj({"phrase": S, "cue": CUE})
FLOW = obj({"icon": S, "count": I, "period": I, "size": I, "reverse": B, "cue": CUE})
# Task 046 Part D1: a picture the maker draws itself (a numbered row of things, a timeline of dates, a flow of steps); the book's
# own pictures are placed by code before the maker plans (visual_thinking.place_pictures).
PICTURE_ITEM = obj({"when": S, "name": S, "icon": S, "cue": CUE})
PICTURE = obj({"type": S, "title": S, "items": arr(PICTURE_ITEM), "arrows": B})
NODE = obj({
    "id": S, "kind": {"type": "string", "enum": list(canvas.KINDS)}, "cell": arr(I), "cue": CUE, "cue_fraction": N,
    "until_cue": CUE, "until_fraction": N,
    "text": S, "style": S, "size": I, "tone": S, "fill": S, "align": S,
    "icon": S, "label": S, "cols": I, "steps": arr(STEP),
    "from": S, "to": S, "from_side": S, "to_side": S, "elbow": S, "dashed": B, "curve": B,
    "target": S, "mark": S, "pos": S,
    "root": S, "children": arr(CHILD),
    "columns": STR_LIST, "rows": arr(ROW), "highlights": arr(HIGHLIGHT),
    "marks": arr(MARK), "flow": FLOW, "picture": PICTURE,
})
CURVE = obj({"id": S, "points": arr(arr(N)), "tone": S, "label": S, "cue": CUE, "draw_frames": I})
DOT = obj({"id": S, "curve": S, "tone": S, "drops": S, "steps": arr(obj({"x": N, "cue": CUE}))})
SHADE = obj({"id": S, "x0": N, "x1": N, "tone": S, "hatch": B, "label": S, "cue": CUE, "until_cue": CUE})
GUIDE = obj({"id": S, "x": N, "tone": S, "dashed": B, "width": I, "label": S, "cue": CUE})
NOTE = obj({"id": S, "fx": N, "fy": N, "fw": N, "text": S, "tone": S, "cue": CUE})
GRAPH = obj({"plot": obj({"x": N, "y": N, "w": N, "h": N}), "x_label": S, "y_label": S, "x_domain": arr(N), "y_domain": arr(N),
             "axes_cue": CUE, "curves": arr(CURVE), "dots": arr(DOT), "shades": arr(SHADE), "guides": arr(GUIDE), "notes": arr(NOTE)})
CAMERA = obj({"cells": arr(I), "cue": CUE})
FOCUS = obj({"cue": CUE, "until_cue": CUE, "ids": STR_LIST})
PLAN_SCHEMA = obj({"notes": NOTES_SCHEMA, "nodes": arr(NODE), "camera": arr(CAMERA), "focus": arr(FOCUS), "graph_used": B, "graph": GRAPH})

WELEMENT = obj({
    "id": S, "kind": {"type": "string", "enum": sorted(world.KINDS)}, "x": N, "y": N, "sign": S, "text": S, "fill": S, "string": N,
    "steps": arr(STEP), "packets": arr(obj({"n": I, "cue": CUE})), "cue": CUE, "until_cue": CUE, "tilt_cue": CUE, "tilt": N,
    "x0": N, "x1": N, "y0": N, "y1": N, "spacing": N, "enter_x": N, "exit_x": N, "face": I, "seed": I, "count": I,
    "lift_cue": CUE, "lift_dy": N, "carry_cue": CUE, "carry_n": I,
})
WCAMERA = obj({"cue": CUE, "x": N, "y": N, "zoom": N, "frames": I})
WORLD_SCHEMA = obj({"notes": NOTES_SCHEMA, "elements": arr(WELEMENT), "camera": arr(WCAMERA)})

ROLE = """You are BIE's canvas director for one part of a video lesson of {subject} for {learners} ({exam}). The script is
already written and passed; you do not change a word of it. You plan ONE build-up canvas for this part: what appears, in
which grid cell, and on which spoken word. Code places, times and checks it; a refused plan comes back to you with the
exact error, and you answer with the whole corrected plan.

Course: "{title}" · learner language: {language}. Navin's level for this part: {level} ({level_note}).

Navin's rules for this section (follow every one):
{rules}

{card}

Icons you may use (id · name): the ones listed under the part for its nouns, and these; any other id is refused:
{icon_menu}

How to fill the JSON (every field is present; "" / 0 / [] / false mean "not used"):
- notes: brief notes for the record: the idea of this canvas, the running example with numbers, what is uncertain.
- nodes: the elements, in the order they appear. id (unique), kind, cell [col, row, width, height] on the 12 x 8 grid
  (arrows, marks and highlights have no cell), cue [beat_id, word] with the word exactly as written in that beat (or
  [beat_id, ""] for the start of the beat, cue_fraction 0..1 moves it into the beat). until_cue when the element leaves.
  value/crowd use steps (text or n, with cue each; dir "up"/"down" on a value step). tree: root + children (text, cue).
  table: columns + rows (cells, cue) + highlights (row or col, -1 when not used). callout/text: marks (phrase, cue).
  arrow: from, to (+ from_side/to_side l r t b, elbow hv/vh/vhv). mark: mark tick/cross + target + pos c/tr.
  highlight: target + style box/dashed/band. flow on an arrow (icon, count, period, size, reverse, cue) makes goods or
  money travel along it.
- camera: zoom to a region of cells on a cue (use it to re-frame instead of a new canvas). focus: dim everything but ids.
- graph_used true + graph for an economic curve (axes, curves as [x, y] points, a dot that walks to x values, guides,
  shades, notes); plot is the graph's box as fractions of the canvas.
Reply with the JSON object only."""

WORLD_ROLE = """You are BIE's world director for one STORY part of a video lesson of {subject} for {learners} ({exam}): actors
act in a place ({place}), so this part is shown inside a small designed world (Navin's level C, an L3 world). The script
is already written and passed; you do not change a word of it. You place the props, the people, the effects and the
camera moves, each on a spoken word; code builds, times and checks the world and a refused plan comes back to you with
the exact error, and you answer with the whole corrected plan.

Course: "{title}" · learner language: {language}.

Navin's rules for this section (follow every one):
{rules}

{card}

How to fill the JSON (every field is present; "" / 0 / [] mean "not used"):
- notes: the story of this part in two lines, what each camera move shows, what is uncertain.
- elements: in story order; id (unique), kind, the fields of that kind (card), cue [beat_id, word] (word exactly as written
  in that beat; [beat_id, ""] for the beat's start) and until_cue when it leaves; steps (text/n + cue) for a price tag, a
  board or a crowd; packets (n + cue) for the shop's stock; lift_cue + lift_dy lifts a price tag; carry_cue + carry_n sends
  buyers away with goods; tilt_cue tilts the balance. The place element (shop or bank) is the kit named above, once.
- camera: keys in time order, each with cue, x and y in world pixels, zoom and frames (how long the move takes).
Reply with the JSON object only."""

LEVEL_NOTE = {"B": "a build-up canvas with L3 touches (shadows, idle motion, walk-ins, flowing goods and money, a camera that follows)",
              "C": "a story told inside a small designed world"}


# ---------------------------------------------------------------- the mode of a part

def profile_fits(course: Course) -> bool:
    return shots.subject_family(course.subject) in FAMILIES


def story_of(items) -> dict:
    """The real-world example the part's items carry (Navin, 27 October 2026, S1-16): the first filled one, or {}."""
    for item in items or []:
        example = item.get("real_world_example") or soul.real_world_of(item.get("unpack"))
        if soul.real_world_filled(example):
            return example
    return {}


def mode_of(course: Course, beats: list, items=None, *, story: bool = False) -> dict:
    """{"mode": "B" | "C" | "", "place", "kit", "missing", "story"}: "" when the subject is not a canvas subject (the
    shot-list director of Part A applies); C for a story part whose place has a kit; B otherwise, with ``missing`` naming
    the place that has no kit yet (the missing-capability line). A ``story`` piece is the real-world example of the
    concept (Navin, 27 October 2026): its place is the example's place first, then the words of the beats; a place
    outside the known list (a petrol pump before its kit) still goes to the missing-capability log by its own name."""
    if not profile_fits(course):
        return {"mode": "", "place": "", "kit": "", "missing": "", "story": False}
    # D1-05 (Navin, 30 October 2026): no world by keyword. A world is used only for the STORY piece of the concept's real-world
    # example, and its place comes from the example itself; every other part is a canvas whose picture type decides.
    example = story_of(items) if story else {}
    hint = (example.get("place") or "").strip()
    place = world.place_of(hint) if hint else ""
    label = world.place_label(place) if place else hint
    kit = place if place in world.KITS else ""
    if story and kit:
        return {"mode": "C", "place": place, "kit": kit, "missing": "", "story": story}
    return {"mode": "B", "place": place or hint, "kit": "", "missing": f"world kit for a {label}" if (story and label) else "", "story": story}


def story_split(stub: dict, full_beats: dict, items) -> list:
    """A part whose items carry a real-world example (S1-16) is split so the example's beats (they cover such an item and
    carry its numbers, S2-08) become their own STORY piece ``<id>s`` (world mode when its place has a kit), the beats
    before and after stay canvases ``<id>a`` and ``<id>b``. A part without an example, or whose beats carry none of the
    numbers, is returned unchanged."""
    example_of = {}
    for item in items or []:
        example = item.get("real_world_example") or soul.real_world_of(item.get("unpack"))
        if soul.real_world_filled(example):
            example_of[item["item_id"]] = soul.real_world_numbers(example)
    if not example_of:
        return [dict(stub, story=False)]
    hits = []
    for n, beat in enumerate(stub["beats"]):
        full = full_beats.get(beat["beat_id"], beat)
        numbers = set().union(*[example_of[i] for i in (full.get("covers_item_ids") or []) if i in example_of] or [set()])
        if numbers & soul.number_tokens(beat.get("say", "")):
            hits.append(n)
    if not hits:
        return [dict(stub, story=False)]
    first, last = hits[0], hits[-1]
    if first == 0 and last == len(stub["beats"]) - 1:
        return [dict(stub, story=True)]
    pieces = []
    for suffix, chunk, story in (("a", stub["beats"][:first], False), ("s", stub["beats"][first:last + 1], True),
                                 ("b", stub["beats"][last + 1:], False)):
        if chunk:
            ids = sorted({i for b in chunk for i in (full_beats.get(b["beat_id"], {}).get("covers_item_ids") or [])})
            hints = [full_beats.get(b["beat_id"], {}).get("on_screen") for b in chunk]
            pieces.append(dict(stub, id=f"{stub['id']}{suffix}", beats=chunk, story=story, covers_item_ids=ids or stub.get("covers_item_ids", []),
                               on_screen_hints=[h for h in hints if h] or stub.get("on_screen_hints") or []))
    return pieces


# ---------------------------------------------------------------- the card and the icon menu

def card_text(path: Path = CARD_PATH) -> str:
    """The director card without its 'Examples' section (the examples are test fixtures, not lesson content)."""
    text = path.read_text(encoding="utf-8")
    head, _, _ = text.partition("\n## Examples")
    return head.strip()


def relation_icons() -> list:
    """The icons the relations are shown with (visual_verbs.json): the cross, the tick, the law scroll, the meter, the scale ..."""
    by_id = icons.by_id()
    ids = []
    for r in vt.load_verbs()["relations"]:
        for i in (r.get("canvas") or {}).get("icons") or []:
            if i in by_id and i not in ids:
                ids.append(i)
    return [(i, by_id[i]["name"]) for i in ids]


def icon_menu(queries=ICON_QUERIES, per_query: int = 3) -> list:
    out, seen = [], set()
    for q in queries:
        for row in icons.search(q, limit=per_query):
            if row["id"] not in seen:
                seen.add(row["id"])
                out.append((row["id"], row["name"]))
    return out


def _menu_text(menu: list) -> str:
    return "\n".join(f"- {i} · {name}" for i, name in menu)


# ---------------------------------------------------------------- from the maker's strict answer to a kit plan

def _cue(value, fraction=0.0):
    if not value or not value[0]:
        return None
    if len(value) > 1 and value[1]:
        return [value[0], value[1]]
    return [value[0], "", float(fraction or 0.0)]


def _clean_step(step: dict, kind: str) -> dict:
    out = {"cue": _cue(step.get("cue"))}
    if kind == "crowd":
        out["n"] = int(step.get("n", 0))
    else:
        out["text"] = step.get("text", "")
        if step.get("dir"):
            out["dir"] = step["dir"]
    return out


def plan_from(stub: dict, value: dict) -> dict:
    """The maker's strict answer → the kit's plan (unset fields dropped) on the stub's beats."""
    plan = {k: stub[k] for k in ("id", "part_id", "theme", "grid", "beats") if k in stub}
    plan.setdefault("theme", "paper")
    plan.setdefault("grid", [12, 8])
    plan["touches"] = True
    nodes = [json.loads(json.dumps(n)) for n in (stub.get("picture_nodes") or [])]     # the book's pictures, placed by code (D1-04)
    for v in value.get("nodes") or []:
        n = {"id": v.get("id", ""), "kind": v.get("kind", "")}
        if v.get("cell"):
            n["cell"] = [int(c) for c in v["cell"]]
        cue = _cue(v.get("cue"), v.get("cue_fraction"))
        if cue is not None:
            n["cue"] = cue
        until = _cue(v.get("until_cue"), v.get("until_fraction"))
        if until is not None:
            n["until_cue"] = until
        for key in ("text", "style", "tone", "fill", "align", "icon", "label", "from", "to", "from_side", "to_side", "elbow",
                    "target", "mark", "pos", "root"):
            if v.get(key):
                n[key] = v[key]
        for key in ("size", "cols"):
            if v.get(key):
                n[key] = int(v[key])
        for key in ("dashed", "curve"):
            if v.get(key):
                n[key] = True
        if v.get("steps"):
            n["steps"] = [_clean_step(s, n["kind"]) for s in v["steps"]]
        if v.get("children"):
            n["children"] = [({"text": c.get("text", ""), "cue": _cue(c.get("cue"))} if c.get("cue") and c["cue"][0] else c.get("text", ""))
                             for c in v["children"]]
        if v.get("columns"):
            n["columns"] = list(v["columns"])
        if v.get("rows"):
            n["rows"] = [{"cells": list(r.get("cells") or []), "cue": _cue(r.get("cue"))} for r in v["rows"]]
        if v.get("highlights"):
            hs = []
            for h in v["highlights"]:
                item = {"cue": _cue(h.get("cue")), "tone": h.get("tone") or "band"}
                if int(h.get("row", -1)) >= 0:
                    item["row"] = int(h["row"])
                if int(h.get("col", -1)) >= 0:
                    item["col"] = int(h["col"])
                until = _cue(h.get("until_cue"))
                if until is not None:
                    item["until_cue"] = until
                hs.append(item)
            n["highlights"] = hs
        if v.get("marks"):
            n["marks"] = [{"phrase": m.get("phrase", ""), "cue": _cue(m.get("cue"))} for m in v["marks"]]
        pic = v.get("picture") or {}
        if n["kind"] == "picture" and pic.get("type"):
            items = pic.get("items") or []
            group = {"timeline": "events", "gallery": "panels", "flow": "nodes"}.get(pic["type"], "items")
            rows = []
            for i, it in enumerate(items):
                row = {"cue": _cue(it.get("cue")) or n.get("cue")}
                if pic["type"] == "flow":
                    row.update(id=f"n{i + 1}", label=it.get("name", ""))
                else:
                    row.update(name=it.get("name", ""), icon=it.get("icon", ""), numbered=False)
                    if pic["type"] == "timeline":
                        row["when"] = it.get("when", "")
                rows.append(row)
            n["picture"] = {"type": pic["type"], "title": pic.get("title", ""), "item_id": "", group: rows, "arrows": bool(pic.get("arrows", True))}
        flow = v.get("flow") or {}
        if flow.get("icon"):
            f = {"icon": flow["icon"]}
            for key in ("count", "period", "size"):
                if flow.get(key):
                    f[key] = int(flow[key])
            if flow.get("reverse"):
                f["reverse"] = True
            cue = _cue(flow.get("cue"))
            if cue is not None:
                f["cue"] = cue
            n["flow"] = f
        nodes.append(n)
    plan["nodes"] = nodes
    cams = [{"cells": [int(c) for c in k["cells"]], "cue": _cue(k.get("cue"))} for k in value.get("camera") or [] if k.get("cells")]
    if cams:
        plan["camera"] = cams
    focus = []
    for f in value.get("focus") or []:
        if f.get("ids"):
            item = {"cue": _cue(f.get("cue")), "ids": list(f["ids"])}
            until = _cue(f.get("until_cue"))
            if until is not None:
                item["until_cue"] = until
            focus.append(item)
    if focus:
        plan["focus"] = focus
    if value.get("graph_used") and value.get("graph"):
        g = value["graph"]
        graph = {"plot": dict(g.get("plot") or {}), "x_label": g.get("x_label", ""), "y_label": g.get("y_label", ""),
                 "x_domain": list(g.get("x_domain") or [0, 10]), "y_domain": list(g.get("y_domain") or [0, 10]),
                 "axes_cue": _cue(g.get("axes_cue"))}
        graph["curves"] = [{"id": c.get("id", ""), "points": [list(p) for p in c.get("points") or []], "tone": c.get("tone") or "accent",
                            "label": c.get("label", ""), "cue": _cue(c.get("cue")), **({"draw_frames": int(c["draw_frames"])} if c.get("draw_frames") else {})}
                           for c in g.get("curves") or []]
        graph["dots"] = [{"id": d.get("id", ""), "curve": d.get("curve", ""), "tone": d.get("tone") or "danger", "drops": d.get("drops") or "xy",
                          "steps": [{"x": s.get("x", 0), "cue": _cue(s.get("cue"))} for s in d.get("steps") or []]} for d in g.get("dots") or []]
        graph["shades"] = [{"id": s.get("id", ""), "x0": s.get("x0", 0), "x1": s.get("x1", 0), "tone": s.get("tone") or "accent",
                            "hatch": bool(s.get("hatch")), "label": s.get("label", ""), "cue": _cue(s.get("cue")),
                            **({"until_cue": _cue(s["until_cue"])} if s.get("until_cue") and s["until_cue"][0] else {})}
                           for s in g.get("shades") or []]
        graph["guides"] = [{"id": u.get("id", ""), "x": u.get("x", 0), "tone": u.get("tone") or "warm", "dashed": bool(u.get("dashed")),
                            **({"width": int(u["width"])} if u.get("width") else {}), "label": u.get("label", ""), "cue": _cue(u.get("cue"))}
                           for u in g.get("guides") or []]
        graph["notes"] = [{"id": n.get("id", ""), "fx": n.get("fx", 0), "fy": n.get("fy", 0), "fw": n.get("fw", 0.25), "text": n.get("text", ""),
                           **({"tone": n["tone"]} if n.get("tone") else {}), "cue": _cue(n.get("cue"))} for n in g.get("notes") or []]
        plan["graph"] = graph
    return plan


def world_from(stub: dict, value: dict, kit: str = "") -> dict:
    plan = {"id": stub["id"], "part_id": stub.get("part_id", ""), "world_width": 5200, "beats": stub["beats"]}
    if kit:
        plan["kit"] = kit
    els = []
    for v in value.get("elements") or []:
        e = {"id": v.get("id", ""), "kind": v.get("kind", "")}
        for key in ("x", "y", "string", "tilt", "x0", "x1", "y0", "y1", "spacing", "enter_x", "exit_x"):
            if v.get(key):
                e[key] = v[key]
        for key in ("face", "seed", "count"):
            if v.get(key):
                e[key] = int(v[key])
        for key in ("sign", "text", "fill"):
            if v.get(key):
                e[key] = v[key]
        for key in ("cue", "until_cue", "tilt_cue"):
            cue = _cue(v.get(key))
            if cue is not None:
                e[key] = cue
        if v.get("steps"):
            e["steps"] = [_clean_step(s, "crowd" if e["kind"] == "crowd" else "value") for s in v["steps"]]
        if v.get("packets"):
            e["packets"] = [{"n": int(p.get("n", 0)), "cue": _cue(p.get("cue"))} for p in v["packets"]]
        lift = _cue(v.get("lift_cue"))
        if lift is not None:
            e["lift"] = {"cue": lift, "dy": v.get("lift_dy") or 130}
        carry = _cue(v.get("carry_cue"))
        if carry is not None:
            e["carry"] = {"cue": carry, "n": int(v.get("carry_n") or 0)}
        els.append(e)
    plan["elements"] = els
    cams = []
    for k in value.get("camera") or []:
        key = {"cue": _cue(k.get("cue")), "x": k.get("x", 0)}
        for name, default in (("y", 540), ("zoom", 1.0), ("frames", 36)):
            if k.get(name):
                key[name] = int(k[name]) if name == "frames" else k[name]
        cams.append(key)
    plan["camera"] = cams
    return plan


# ---------------------------------------------------------------- the code check (the exact error goes back to the maker)

def _icon_problems(plan: dict, library=None) -> list:
    ids = canvas.icons_in(plan)
    images = [i for i in ids if str(i).startswith("asset:")]
    out = [f"image {i!r} is not in this lesson's asset library" for i in images
           if library is None or i.split(":", 1)[1] not in library.assets]
    bad = icons.check_ids([i for i in ids if i not in images])
    for i in bad:
        near = ", ".join(f"{r['id']} ({r['name']})" for r in icons.search(str(i).split(":", 1)[-1].replace("/", " ").replace("-", " "), limit=3))
        out.append(f"icon {i!r} is not in the icon index" + (f"; nearest: {near}" if near else ""))
    return out


def check_plan(stub: dict, value: dict, mode, *, picture: dict | None = None, library=None) -> list:
    """The code check of a maker's answer: ``mode`` is the mode dict ({"mode", "kit", ...}) or the letter alone. Part D1 adds:
    every beat shows a non-text thing on its words, no text-only screen over 10 s, screen text a name or a short phrase, the
    book's pictures drawn, no caution line on screen."""
    letter, kit = (mode["mode"], mode.get("kit", "")) if isinstance(mode, dict) else (mode, "")
    try:
        if letter == "C":
            plan = world_from(stub, value, kit=kit)
            _, report = world.compile_world(plan)
            texts = screen_text.world_texts(plan)
            return (report["problems"] + screen_text.problems(texts, plan["beats"])                     # CV-13 … CV-16
                    + vt.beat_cover_problems(plan, plan["beats"], "C") + vt.phrase_problems(texts) + vt.caution_problems(texts))
        plan = plan_from(stub, value)
        problems = _icon_problems(plan, library)
        if problems:
            return problems
        scene, report = canvas.compile_plan(plan)
        texts = screen_text.canvas_texts(plan)
        text_only, _ = vt.text_only_problems(scene, timing.FPS)
        return (report["problems"] + screen_text.problems(texts, plan["beats"])                         # CV-13 … CV-16
                + vt.beat_cover_problems(plan, plan["beats"], "B") + text_only + vt.phrase_problems(texts)
                + vt.caution_problems(texts) + vt.book_picture_problems(plan, picture))
    except PlanError as exc:
        return [str(exc)]
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return [f"plan shape: {type(exc).__name__}: {exc}"]


# ---------------------------------------------------------------- the step

def _items_of(chapter: dict, plan_video: dict, stub: dict) -> list:
    items, _ = video_scope(chapter, plan_video)
    wanted = set(stub.get("covers_item_ids") or [])
    rows = []
    for i in items:
        if i["item_id"] not in wanted:
            continue
        row = {"item_id": i["item_id"], "content_type": i.get("content_type", ""), "content": i.get("content", "")}
        example = soul.real_world_of(i.get("unpack"))
        if soul.real_world_filled(example):
            row["real_world_example"] = example
        rows.append(row)
    return rows


STORY_NOTE = ("This part is the STORY of the concept's real-world example (Navin, 27 October 2026): {place}; actors {actors}; "
              "goods {goods}; numbers {numbers}. No world kit exists for this place yet, so build the story on the canvas with "
              "crowd, value and icon elements: the actors as icons, the buyers or workers as a crowd whose n follows the numbers, "
              "the price or amount as a value whose steps follow the numbers, the goods or money flowing on arrows; every change "
              "cued on the word that says it.")


def ideas_step(course: Course, stub: dict, items: list, picture: dict, *, max_rounds: int = 3) -> Step:
    """Dikhane ki soch (Task 046 Part D1): before any layout the maker says, per beat, the idea, its relation, its things, people
    and places, what is seen and on which word; code checks the shape and the words."""
    beats = [{"beat_id": b["beat_id"], "say": b["say"], "relation_guess": vt.guess_relation(b["say"])} for b in stub["beats"]]
    if picture.get("by") == "book":
        first = picture["pictures"][0]
        line = vt.PICTURE_BY_CODE.format(ptype=picture["type"], ptitle=first.get("title", ""), source=first.get("kind", "picture"))
    else:
        line = vt.PICTURE_BY_MAKER.format(card_type=stub.get("card_type") or "")
    system = fmt(vt.ROLE, course, verbs=vt.verbs_text(), phrase_words=vt.PHRASE_WORDS, picture_line=line)
    payload = {"part": {"id": stub["id"], "part_id": stub.get("part_id", ""), "card_type": stub.get("card_type", ""), "story": bool(stub.get("story"))},
               "beats": beats, "items": [{k: i.get(k, "") for k in ("item_id", "content_type", "content")} for i in items],
               "book_pictures": [{"item_id": p["item_id"], "type": p["type"], "title": p["title"]} for p in picture.get("pictures") or []]}
    user = (f"Chapter: {course.title}. Part {stub.get('part_id') or stub['id']} ({len(beats)} beats).\nThe part (JSON):\n"
            f"{json.dumps(payload, ensure_ascii=False)}\n\nReply with the ideas JSON.")
    return Step(section=SECTION, unit=f"{stub['id']}-ideas", instructions_version=vt.VERSION, system=system, user=user, schema=vt.IDEAS_SCHEMA,
                check=lambda value: vt.check_ideas(stub, value, picture=picture), max_rounds=max_rounds)


IDEAS_NOTE = """
Dikhane ki soch for this part (the visual-idea step; every beat shows its thing on its word, D1-01):
{ideas}
Icons found for the things named (id · name); you may also use any id from the general menu below:
{candidates}
"""
PICTURE_NOTE = ("\nCode has already placed the book's own picture in this plan: node '{nid}' ({ptype}: {ptitle}) in cells {cell} (col, row, "
                "width, height). Do not add another timeline, table or row for it and do not reuse its id or its cells; build your "
                "elements in the rows below it (row {row} onward) and let the picture carry the beats that cover its items (D1-04).")


def part_step(course: Course, stub: dict, items: list, mode: dict, *, rulebook, menu: list | None = None, max_rounds: int = 3,
              ideas: dict | None = None, candidates: dict | None = None, images: dict | None = None, library=None) -> Step:
    """The maker writes this part's plan (B: canvas; C: world) and code checks it; no reviewer round for layout. With the
    dikhane ki soch (``ideas``) and the icon candidates code found for its nouns (``candidates``), and the code-placed book
    picture of the stub (``stub["picture_nodes"]``)."""
    beats = [{"beat_id": b["beat_id"], "say": b["say"]} for b in stub["beats"]]
    picture_nodes = stub.get("picture_nodes") or []
    payload = {"part": {"id": stub["id"], "part_id": stub.get("part_id", ""), "mode": mode["mode"], "place": mode.get("place", ""),
                        "story": bool(mode.get("story"))},
               "beats": beats, "items": items, "on_screen_hints": stub.get("on_screen_hints") or [],
               "ideas": [{k: r.get(k) for k in ("beat_id", "idea", "relation", "things", "people", "places", "shows", "on_word")}
                         for r in (ideas or {}).get("beats") or []],
               "picture": [{"id": n["id"], "type": n["picture"]["type"], "cell": n["cell"]} for n in picture_nodes]}
    story = story_of(items) if mode.get("story") else {}
    note = ""
    if story and mode["mode"] == "B":
        numbers = "; ".join(f"{n.get('what', '')} {n.get('before', '')} → {n.get('after', '')}".strip() for n in story.get("numbers") or [])
        note = "\n" + STORY_NOTE.format(place=story.get("place", ""), actors=", ".join(story.get("actors") or []),
                                         goods=", ".join(story.get("goods") or []), numbers=numbers)
    if ideas and ideas.get("beats"):
        lines = "\n".join(f"- {r['beat_id']}: {r.get('idea', '')} · relation {r.get('relation', '')} · shows: {r.get('shows', '')}"
                          + (f" · on '{r['on_word']}'" if r.get("on_word") else "") for r in ideas["beats"])
        note += IDEAS_NOTE.format(ideas=lines, candidates=vt.candidates_text(candidates or {}) or "- (none found: use the general menu)")
        if images:
            note += ("Pictures in this lesson's asset library for the things named (use the id as an icon; the credit is added by code):\n"
                     + "\n".join(f"- {noun}: " + "; ".join(f"asset:{a}" for a in ids) for noun, ids in images.items()) + "\n")
    for n in picture_nodes:
        note += PICTURE_NOTE.format(nid=n["id"], ptype=n["picture"]["type"], ptitle=n["picture"].get("title", ""), cell=n["cell"],
                                    row=n["cell"][1] + n["cell"][3])
    rules = rulebook.instructions(SECTION)
    if mode["mode"] == "C":
        place = f"{world.KITS[mode['kit']]['label']}; its place element is kind '{world.PLACE_KINDS[mode['kit']]}'"
        system = fmt(WORLD_ROLE, course, rules=rules, card=card_text(WORLD_CARD_PATH), place=place)
        schema = WORLD_SCHEMA
    else:
        # D1 (Navin, 30 October 2026): the maker gets the icons code found for the beats' own nouns, plus the relation icons;
        # the fixed economy menu only when the visual-idea step gave nothing to search for.
        menu = (relation_icons() if candidates else icon_menu()) if menu is None else menu
        system = fmt(ROLE, course, rules=rules, card=card_text(), icon_menu=_menu_text(menu), level=mode["mode"],
                     level_note=LEVEL_NOTE[mode["mode"]])
        schema = PLAN_SCHEMA
    user = (f"Chapter: {course.title}. Part {stub.get('part_id') or stub['id']} ({len(beats)} beats).{note}\n"
            f"The part (JSON):\n{json.dumps(payload, ensure_ascii=False)}\n\nReply with the plan JSON.")
    picture = stub.get("picture") or {}
    return Step(section=SECTION, unit=stub["id"], instructions_version=VERSION, system=system, user=user, schema=schema,
                check=lambda value: check_plan(stub, value, mode, picture=picture, library=library), max_rounds=max_rounds)


def split_stub(stub: dict, max_beats: int = MAX_PART_BEATS) -> list:
    """A part longer than ``max_beats`` becomes two or three canvases of near-equal length (CV-10), ids ``<id>a``, ``<id>b``."""
    beats = stub["beats"]
    if len(beats) <= max_beats:
        return [stub]
    pieces = -(-len(beats) // max_beats)
    size = -(-len(beats) // pieces)
    out = []
    for n in range(pieces):
        chunk = beats[n * size:(n + 1) * size]
        if chunk:
            out.append(dict(stub, id=f"{stub['id']}{chr(97 + n)}", beats=chunk,
                            on_screen_hints=[h for b in chunk for h in [b.get("on_screen")] if h] or stub.get("on_screen_hints") or []))
    return out


# ---------------------------------------------------------------- the run

def run_canvas(chapter: dict, lesson: dict, course: Course, runner, out_dir, *, videos=None, workers: int = 4, max_rounds: int = 3,
               opener=None, shared_library=None) -> dict:
    """``shared_library``: a folder or an https URL of BIE's asset library (the images the fetch step found for earlier needs,
    licence-checked and credited); its assets are copied into this run's library first, so the next run looks there first."""
    chapter = formats.accept("chapter_map", chapter, where="chapter_map.json")              # the section boundary
    lesson = formats.accept("lesson_plan", lesson, where="lesson_plan.json")
    out = Path(out_dir)
    (out / "video_specs").mkdir(parents=True, exist_ok=True)
    (out / "plans").mkdir(exist_ok=True)
    library = AssetLibrary(out / "assets")
    if shared_library:
        from .assets import seed_library
        seed_library(library, shared_library, opener=opener)
    plans = {v["video_id"]: v for v in (lesson.get("plan") or {}).get("videos", [])}
    wanted = set(videos or [])
    chosen = [v for v in lesson.get("videos", []) if v.get("beats") and v["video_id"] in plans and v.get("status", "passed") == "passed"
              and (not wanted or v["video_id"] in wanted)]
    menu = None                       # per part: the relation icons with the nouns' candidates, or the fixed menu (part_step)
    summary = {"schema": formats.tag("canvas_summary"), "course": chapter["course"], "rulebook_version": runner.rulebook.version,
               "licence_policy": licence_policy.version(), "profile": canvas.PROFILE["profile"], "profile_version": canvas.PROFILE["version"],
               "family": shots.subject_family(course.subject), "canvas_subject": profile_fits(course), "maker_route": runner.maker,
               "videos": [], "missing_kits": []}
    if not profile_fits(course):
        summary["note"] = "not a canvas subject: the shot-list director (Part A) applies"
    summary["missing_capabilities"] = []
    run_needs = []
    (out / "visual_ideas").mkdir(exist_ok=True)
    for video in chosen:
        if not profile_fits(course):
            break
        beats = video["beats"]
        full_beats = {b["beat_id"]: b for b in beats}
        card_types = {p.get("part_id"): p.get("type", "") for p in video.get("card_parts") or []}
        stubs = [piece for stub in canvas.stubs(video)
                 for story in story_split(stub, full_beats, _items_of(chapter, plans[video["video_id"]], stub))
                 for piece in split_stub(story)]
        # Dikhane ki soch, step 1 by code (D1-04): the book's own pictures a part covers, placed before the maker plans; and the mode of
        # every part, with the kit-sequence rule (D1-05) applied in order before the parts run side by side.
        for stub in stubs:
            stub["card_type"] = card_types.get(stub.get("part_id"), "")
            own = [full_beats.get(b["beat_id"], b) for b in stub["beats"]]           # the items this piece's own beats cover
            stub["picture"], stub["picture_nodes"] = vt.place_pictures(chapter["items"], own, stub["card_type"])
            stub["mode"] = mode_of(course, stub["beats"], _items_of(chapter, plans[video["video_id"]], stub), story=bool(stub.get("story")))
        # A world piece does not draw the book's picture: when a canvas piece of the video draws the same pictures the world keeps its
        # story (the canvas piece shows the picture); when none does, the piece goes to the canvas so the picture is drawn (D1-04).
        on_canvas = {p["item_id"] for st in stubs if st["mode"]["mode"] != "C" for p in st["picture"]["pictures"]}
        prev = None
        for stub in stubs:
            mode, own_pics = stub["mode"], {p["item_id"] for p in stub["picture"]["pictures"]}
            if mode["mode"] == "C" and own_pics:
                if own_pics <= on_canvas:
                    own = [full_beats.get(b["beat_id"], b) for b in stub["beats"]]
                    stub["picture"], stub["picture_nodes"] = vt.place_pictures({}, own, stub["card_type"])
                else:
                    mode = dict(mode, mode="B", kit="", missing="", note="the part covers the book's own picture, drawn on the canvas (D1-04)")
                    on_canvas |= own_pics
            if mode["mode"] == "C" and prev and prev["mode"] == "C" and prev.get("kit") == mode.get("kit"):
                mode = dict(mode, mode="B", kit="", missing="", note=f"the {prev['kit']} world was used by the part before (D1-05)")
            stub["mode"] = mode
            prev = mode

        def work(stub):
            stub["beats"] = [dict(b, **{k: full_beats[b["beat_id"]].get(k, "") for k in ("caption",)}) if "caption" in full_beats[b["beat_id"]] else b
                             for b in stub["beats"]]
            items = _items_of(chapter, plans[video["video_id"]], stub)
            mode = stub["mode"]
            ideas = runner.run(ideas_step(course, stub, items, stub["picture"], max_rounds=max_rounds))
            found = vt.resolve_needs(ideas.output, library) if ideas.passed and ideas.output else {"found": {}, "images": {}, "needs": []}
            result = runner.run(part_step(course, stub, items, mode, rulebook=runner.rulebook, menu=menu, max_rounds=max_rounds,
                                          ideas=ideas.output if ideas.passed else None, candidates=found["found"], images=found["images"],
                                          library=library))
            return stub, mode, result, ideas, found

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            rows = list(pool.map(work, stubs))
        scenes, parts, icon_ids, idea_parts = [], [], [], []
        for stub, mode, result, ideas, found in rows:
            entry = {"id": stub["id"], "part_id": stub.get("part_id", ""), "beats": len(stub["beats"]), "mode": mode["mode"],
                     "place": mode.get("place", ""), "kit": mode.get("kit", ""), "story": bool(mode.get("story")), "status": result.status,
                     "rounds": len(result.rounds), "first_try": result.passed and len(result.rounds) == 1, "cost_usd": result.cost_usd + ideas.cost_usd,
                     "last_problems": (result.rounds[-1].get("code_problems") or []) if result.rounds and not result.passed else [],
                     "ideas_status": ideas.status, "ideas_rounds": len(ideas.rounds), "ideas_first_try": ideas.passed and len(ideas.rounds) == 1,
                     "picture": {"type": stub["picture"]["type"], "by": stub["picture"]["by"]},
                     "book_pictures": len(stub["picture"]["pictures"]), "needs": len(found["needs"])}
            if mode.get("note"):
                entry["note"] = mode["note"]
            if mode.get("missing") and mode["missing"] not in summary["missing_kits"]:
                summary["missing_kits"].append(mode["missing"])
            if mode.get("missing"):
                cap = next((c for c in summary["missing_capabilities"] if c["what"] == mode["missing"]), None)
                if cap is None:
                    cap = {"what": mode["missing"], "kind": "world kit", "parts": [], "beats": []}
                    summary["missing_capabilities"].append(cap)
                cap["parts"].append(stub["id"])
                cap["beats"] += [b["beat_id"] for b in stub["beats"]]
            run_needs += [dict(n, part=stub["id"], video=video["video_id"]) for n in found["needs"]]
            icons_by_beat = {}
            for row in (ideas.output or {}).get("beats") or [] if ideas.passed else []:
                nouns = [n for k in ("things", "people", "places") for n in row.get(k) or []]
                icons_by_beat[row["beat_id"]] = [i for n in nouns for i in found["found"].get(n, [])[:1]]
            part_data = {"id": stub["id"], "part_id": stub.get("part_id", ""), "mode": mode["mode"], "kit": mode.get("kit", ""),
                         "picture": stub["picture"], "ideas": ideas.output if ideas.passed else {}, "needs": found["needs"],
                         "icons_by_beat": icons_by_beat, "status": result.status, "seconds": 0.0, "text_only_seconds": 0.0,
                         "icon_ids": [], "picture_types": [], "book_pictures_drawn": 0}
            if result.passed:
                if mode["mode"] == "C":
                    plan = world_from(stub, result.output, kit=mode.get("kit", ""))
                    scene, report = world.compile_world(plan)
                    part_data["picture_types"] = ["world"]
                else:
                    plan = plan_from(stub, result.output)
                    ids = canvas.icons_in(plan)
                    index_ids = [i for i in ids if not str(i).startswith("asset:")]
                    paths = icons.add_to_library(index_ids, library, opener=opener) if index_ids else {}
                    paths.update({i: "assets/" + library.assets[i.split(":", 1)[1]].path for i in ids if str(i).startswith("asset:")})
                    icon_ids += [i for i in ids if i not in icon_ids]
                    scene, report = canvas.compile_plan(plan, icon_paths=paths)
                    part_data["icon_ids"] = ids
                    part_data["text_only_seconds"] = vt.text_only_problems(scene, timing.FPS)[1]
                    pics = [n["picture"]["type"] for n in plan.get("nodes") or [] if n.get("kind") == "picture"]
                    part_data["picture_types"] = sorted(set(pics)) or (["things"] if ids else ["text"])
                    drawn = sorted({(n.get("picture") or {}).get("item_id") for n in plan.get("nodes") or []
                                    if n.get("kind") == "picture" and (n.get("picture") or {}).get("item_id")})
                    part_data["book_pictures_drawn"], part_data["book_picture_ids"] = len(drawn), drawn
                formats.check("world_c_plan" if "elements" in plan else "canvas_b_plan", formats.stamp("world_c_plan" if "elements" in plan else "canvas_b_plan", plan),
                              where=f"plans/{stub['id']}.plan.json")
                (out / "plans" / f"{stub['id']}.plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
                scenes.append(scene)
                part_data["seconds"] = report["seconds"]
                entry.update(level=report["level"], seconds=report["seconds"], elements=report["elements"],
                             longest_still_s=report["longest_still_s"], advisories=report.get("advisories", []),
                             text_only_seconds=part_data["text_only_seconds"], picture_types=part_data["picture_types"],
                             distinct_icons=len(part_data["icon_ids"]))
            parts.append(entry)
            idea_parts.append(part_data)
        asset_ids = sorted(library.assets)
        credits = library.credits(asset_ids)
        if scenes and credits:
            scenes.append(canvas.credits_scene(credits, scene_id=f"{video['video_id']}_credits"))
        ideas_record = vt.dikhane_list(video["video_id"], idea_parts)
        formats.check("visual_ideas", ideas_record, where=f"visual_ideas/{video['video_id']}.json")
        (out / "visual_ideas" / f"{video['video_id']}.json").write_text(json.dumps(ideas_record, ensure_ascii=False, indent=1), encoding="utf-8")
        row = {"video_id": video["video_id"], "title": video.get("title", ""), "parts": parts,
               "parts_passed": sum(1 for p in parts if p["status"] == "passed"), "first_try_passes": sum(1 for p in parts if p["first_try"]),
               "rounds": sum(p["rounds"] for p in parts), "cost_usd": round(sum(p["cost_usd"] for p in parts), 6),
               "modes": {m: sum(1 for p in parts if p["mode"] == m) for m in ("B", "C")}, "credits": credits,
               "seconds": round(sum(s["duration"] for s in scenes) / timing.FPS, 1),
               "ideas_first_try": sum(1 for p in parts if p.get("ideas_first_try")), "ideas_rounds": sum(p.get("ideas_rounds", 0) for p in parts),
               "report": vt.report(idea_parts)}
        if len(scenes) and all(p["status"] == "passed" for p in parts):
            spec = canvas.video_spec(scenes)
            problems = licence_policy.lesson_spec_check(spec) + library.lesson_check(asset_ids)
            if problems:
                row.update(status="stopped_by_licence", licence_problems=problems)
            else:
                formats.check("video_spec", spec, where=f"video_specs/{video['video_id']}.json")
                canvas.write_spec(spec, out / "video_specs" / f"{video['video_id']}.json")
                row["status"] = "spec_written"
        else:
            row["status"] = "failed"
        summary["videos"].append(row)
    needs = vt.needs_record(run_needs, summary["missing_capabilities"])
    formats.check("needs", needs, where=str(out / "needs.json"))
    (out / "needs.json").write_text(json.dumps(needs, ensure_ascii=False, indent=1), encoding="utf-8")
    library.save()
    parts = [p for v in summary["videos"] for p in v["parts"]]
    summary["quality"] = {"videos": len(summary["videos"]), "videos_written": sum(1 for v in summary["videos"] if v.get("status") == "spec_written"),
                          "parts": len(parts), "parts_passed": sum(1 for p in parts if p["status"] == "passed"),
                          "first_try_passes": sum(1 for p in parts if p["first_try"]),
                          "first_try_rate": round(sum(1 for p in parts if p["first_try"]) / len(parts), 3) if parts else 0.0,
                          "rounds": sum(p["rounds"] for p in parts), "modes": {m: sum(1 for p in parts if p["mode"] == m) for m in ("B", "C")},
                          "story_parts": sum(1 for p in parts if p.get("story")),
                          "story_parts_in_a_world": sum(1 for p in parts if p.get("story") and p["mode"] == "C"),
                          "missing_kits": list(summary["missing_kits"]), "seconds": round(sum(v["seconds"] for v in summary["videos"]), 1),
                          "cost_usd": round(sum(p["cost_usd"] for p in parts), 6),
                          # Task 046 Part D1 (Navin's verdict of 30 October 2026): what the learner sees
                          "distinct_icons": len({i for v in summary["videos"] for i in (v.get("report") or {}).get("icons", [])}),
                          "text_only_seconds": round(sum((v.get("report") or {}).get("text_only_seconds", 0) for v in summary["videos"]), 1),
                          "book_pictures": sum((v.get("report") or {}).get("book_pictures", 0) for v in summary["videos"]),
                          "book_pictures_drawn": sum((v.get("report") or {}).get("book_pictures_drawn", 0) for v in summary["videos"]),
                          "world_share": round(sum(1 for p in parts if p["mode"] == "C") / len(parts), 3) if parts else 0.0,
                          "relations_outside_list": sum((v.get("report") or {}).get("relations_outside_list", 0) for v in summary["videos"]),
                          "ideas_first_try": sum(v.get("ideas_first_try", 0) for v in summary["videos"]),
                          "needs": len(needs["needs"]), "missing_capabilities": len(summary["missing_capabilities"])}
    formats.check("canvas_summary", summary, where=str(out / "canvas.json"))
    (out / "canvas.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "CANVAS.md").write_text(render_markdown(summary), encoding="utf-8")
    return summary


def render_markdown(summary: dict) -> str:
    q = summary["quality"]
    lines = [f"# Canvas plans · {summary['course']['title']}", "",
             f"Subject family {summary['family']} ({'canvas subject' if summary['canvas_subject'] else 'not a canvas subject'}); "
             f"{q['parts_passed']} of {q['parts']} parts passed, {q['first_try_passes']} on the first try ({q['first_try_rate']:.0%}), "
             f"{q['rounds']} rounds; modes B {q['modes']['B']}, C {q['modes']['C']}; {q['seconds']:.0f} s planned; cost ${q['cost_usd']:.4f}.", ""]
    if summary.get("note"):
        lines += [summary["note"], ""]
    if q.get("story_parts"):
        lines += [f"Story parts (a concept's real-world example, Navin 27 October 2026): {q['story_parts']}, "
                  f"{q['story_parts_in_a_world']} inside a world (C), the rest on the canvas with crowd, value and icon elements (B).", ""]
    if q["missing_kits"]:
        lines += ["Missing world kits (these parts fell back to the canvas): " + "; ".join(q["missing_kits"]), ""]
    if "distinct_icons" in q:
        lines += [f"Dikhane ki soch (Part D1): {q['distinct_icons']} distinct icons; text-only screen {q['text_only_seconds']} s; book pictures drawn "
                  f"{q['book_pictures_drawn']} of {q['book_pictures']}; world share {q['world_share']:.0%}; relations outside the list "
                  f"{q['relations_outside_list']}; ideas passed first try {q['ideas_first_try']}; needs {q['needs']}; missing capabilities "
                  f"{q['missing_capabilities']}.", ""]
    for v in summary["videos"]:
        lines += [f"## {v['video_id']} · {v['title']} ({v['seconds']} s) · {v.get('status')}", ""]
        for p in v["parts"]:
            level = p.get("level", "")
            lines.append(f"- {p['id']} ({p['part_id'] or 'no part'}, {p['beats']} beats): mode {p['mode']} {level}; {p['status']} after {p['rounds']} round(s)"
                         + (" · first try" if p["first_try"] else "") + (f" · {p['elements']} elements, longest still {p['longest_still_s']} s" if "elements" in p else "")
                         + (f" · place {p['place']}" if p.get("place") else "") + (" · story (the real-world example)" if p.get("story") else ""))
            for problem in (p.get("last_problems") or [])[:4]:
                lines.append(f"  - {problem}")
            for note in (p.get("advisories") or [])[:2]:
                lines.append(f"  - advisory: {note}")
        if v.get("licence_problems"):
            lines += ["", "Stopped by the lesson licence gate:"] + [f"- {x}" for x in v["licence_problems"]]
        if v.get("credits"):
            lines += ["", "Credits:"] + [f"- {c}" for c in v["credits"]]
        lines.append("")
    return "\n".join(lines)
