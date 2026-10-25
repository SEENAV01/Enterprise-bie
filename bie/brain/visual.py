"""Section 4 · Visuals: assets and frame layout for every scene the director planned.

For each video:
1. Asset plan (AI): search queries and a must-show list for every element that needs a picture.
2. Search (code): open sources (Wikimedia Commons) with licences the licence policy allows in a lesson
   (``bie/toolbox/licence_policy.json``: CC0, public domain, CC BY with its credit fields).
3. Asset choice (AI that sees the candidate pictures): the most accurate, detailed one, with the regions and
   points of the parts to label and zoom into; the file goes into the asset library with its licence.
4. Layout (AI that sees the chosen pictures): the scene as choreography data for BIE's block library, every
   layer and camera move cued to a spoken word. BIE's code checks references, boxes, overlaps and cues; the
   independent reviewer looks at rendered frames at the cue moments and judges them against the scene.
5. The passed scenes become one VideoSpec per video (frames from the beat timing), ready to render.

Before a video's layout is planned and again before its VideoSpec is written, the lesson licence gate
(``bie.toolbox.licence``) checks every asset the video uses and the spec itself (a block that draws India's
boundary); a refused or needs-Navin asset stops that video with the reason, and nothing is swapped silently.

Outputs (``run_visual``): ``video_specs/<video>.json``, ``assets/`` (library with index and credits),
``VISUAL.md``, and stills of the reviewed frames under ``stills/``.
"""
from __future__ import annotations

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .assets import AssetLibrary, AssetError, Candidate, _open, search_commons
from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .director import word_in
from .runner import NOTES_SCHEMA, Step
from .understanding import Course
from .video import timing
from .video.render import RenderError, small_jpeg, stills
from bie.toolbox import licence as licence_policy

SECTION = "visual"
PLAN_VERSION = "visual-assets/1"
CHOOSE_VERSION = "visual-choose/2"
LAYOUT_VERSION = "visual-layout/1"
IMAGE_KINDS = {"structure_3d", "illustration", "diagram", "cell_or_micro", "organ_or_body", "molecule", "map", "character", "icon"}
LAYER_TYPES = ["image", "title", "label", "highlight", "flow", "steps", "timeline", "scale", "table", "arrow", "question"]
PANEL_TYPES = {"title", "steps", "timeline", "scale", "table"}
NUM = {"type": "number"}
BOX = obj({"x": NUM, "y": NUM, "w": NUM, "h": NUM})
PT = obj({"x": NUM, "y": NUM})
CUE = obj({"beat_id": S, "word": S})
REF = obj({"layer": S, "x": NUM, "y": NUM})

PLAN_SCHEMA = obj({"notes": NOTES_SCHEMA, "needs": arr(obj({"element_key": S, "queries": arr(S), "must_show": arr(S)}))})
CHOOSE_SCHEMA = obj({"notes": NOTES_SCHEMA, "choice": {"type": "integer"}, "reason": S,
                     "parts": arr(obj({"name": S, "region": BOX, "point": PT}))})
LAYER_SCHEMA = obj({
    "id": S, "type": {"type": "string", "enum": LAYER_TYPES}, "cue": CUE, "until": CUE, "box": BOX, "element_id": S, "text": S,
    "subtitle": S, "tone": {"type": "string", "enum": ["accent", "warm", "danger"]}, "anchor": REF, "target_layer": S,
    "region": BOX, "path": arr(PT),
    "entries": arr(obj({"label": S, "detail": S, "value": NUM, "unit": S, "when": S, "cue": CUE})),
    "columns": arr(S), "rows": arr(obj({"label": S, "cells": arr(S)})),
    "focus": arr(obj({"column": {"type": "integer"}, "cue": CUE})), "from_ref": REF, "to_ref": REF,
})
LAYOUT_SCHEMA = obj({"notes": NOTES_SCHEMA, "layers": arr(LAYER_SCHEMA),
                     "camera": arr(obj({"cue": CUE, "layer": S, "region": BOX, "frames": {"type": "integer"}}))})
PATCH_SCHEMA = obj({"notes": NOTES_SCHEMA, "replace_layers": arr(LAYER_SCHEMA), "remove_layer_ids": arr(S),
                    "camera": arr(obj({"cue": CUE, "layer": S, "region": BOX, "frames": {"type": "integer"}}))})
PATCH_HINT = ("Reply with a patch: replace_layers = complete corrected or new layers (same id replaces), remove_layer_ids = layers "
              "to delete, camera = the complete corrected camera list.")
REVIEW_SCHEMA = obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": arr(obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": arr(obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})

PLAN_ROLE = """You are BIE's visual section, finding pictures for a {subject} video for {learners} ({exam}). For every element below
that needs a picture, write two or three search queries for Wikimedia Commons (English, specific: structure, view, style, for example
"smooth muscle cell histology diagram", "neuron synapse labeled diagram") and the parts the picture must show.

Navin's rules for this section:
{rules}

Reply with the JSON object only: notes (brief, for the reviewer), needs = one entry per element_key given, with queries and must_show."""

CHOOSE_ROLE = """You are BIE's visual section choosing the picture for one element of a {subject} lesson (a video scene or a game
board) for {learners} ({exam}). You see
numbered candidate pictures (all with licences allowed in a paid course). Choose the one that shows the element most accurately and in
the most detail (choice = its number), or -1 if none is good enough. For the chosen picture, give every part that must be labelled or
zoomed into: its name, its region (x, y, w, h as fractions of the picture, 0 to 1) and the point a label line should touch (x, y as
fractions). Be precise: these numbers place the labels on the real part.

Navin's rules for this section:
{rules}

Reply with the JSON object only: notes (brief), choice, reason, parts."""

LAYOUT_ROLE = """You are BIE's visual section laying out one scene of a {subject} video for {learners} ({exam}) as data for BIE's
animation block library. The screen is a 1920x1080 world; every box is x, y, w, h as fractions of the world (0 to 1). Points inside a
layer (label anchors, highlight regions, flow paths) are fractions of that layer's box.

Blocks you can use (type → fields):
- image: box, element_id (a chosen picture below; keep its proportions so it is not cut). Credit is added automatically.
- title: box, text, subtitle.
- label: box (where the label sits, off the picture's important parts), text (short, the book's term), anchor = {{layer, x, y}} the
  point on the part, tone.
- highlight: target_layer, region (inside that layer), tone. A pulsing ring on a part.
- flow: target_layer, path (points inside that layer, in order), tone. Particles moving along the path: signals, blood, water, ions.
- steps: box, text (title), entries = [{{label, detail, cue}}]: a process that lights up step by step.
- timeline: box, entries = [{{when, label, cue}}].
- scale: box, text (title), entries = [{{label, value, unit, cue}}]: numbers shown to scale (visual mathematics).
- table: box, columns, rows = [{{label, cells}}], focus = [{{column, cue}}]: a comparison whose columns light up.
- arrow: from_ref and to_ref = {{layer, x, y}}, text (optional label).
- question: text (in {language}): the pause question overlay.
Every layer has an id and a cue = {{beat_id, word}}: the spoken word on which it appears (the word must be in that beat); until = the
cue where it leaves, or {{beat_id: "", word: ""}} to stay. Fill unused fields with empty values. camera = keys {{cue, layer, region,
frames}}: zoom into a region of a layer on a spoken word (layer "" = the whole world); use it to go inside structures for processes.

Navin's rules for this section (follow every one):
{rules}

Reply with the JSON object only: notes (brief), layers, camera."""

REVIEW_ROLE = """You are BIE's independent reviewer for the visuals of one scene ({subject}, {learners}, {exam}). You see rendered frames
of the scene at its key moments, the director's plan and the spoken words. Judge them as Navin would: cinematic, anatomy-level, clear on
a phone, and showing exactly what is being said.

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

Report every problem with where it is (frame time or layer id), what is wrong, the fix and a severity ("blocking" or "minor", see R-01):
a label on the wrong part, overlapping or unreadable text, a picture that does not show what is said, a process not shown happening,
an empty or cluttered frame, numbers not to scale, a fact wrong at this level. verdict is "pass" when nothing is blocking.
Fill your own brief notes first. Reply with the JSON object only."""


def _b64(data: bytes, media: str):
    return {"type": "image", "media_type": media, "data": base64.b64encode(data).decode("ascii")}


def needs_picture(element: dict) -> bool:
    return element["kind"] in IMAGE_KINDS


def _media(data: bytes) -> str:
    if data[:8].startswith(b"\x89PNG"):
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/png"


def bigger_thumb(url: str, width: int = 1600) -> str:
    """Commons thumbnail URLs carry their width (".../800px-Name.png"); ask for a larger one for the video."""
    import re
    return re.sub(r"/(\d+)px-", f"/{width}px-", url, count=1)


# ---------------------------------------------------------------- checks

def _inside(box) -> bool:
    return 0 <= box["x"] <= 1 and 0 <= box["y"] <= 1 and box["w"] > 0 and box["h"] > 0 and box["x"] + box["w"] <= 1.001 \
        and box["y"] + box["h"] <= 1.001


def _overlap(a, b) -> float:
    w = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
    h = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
    if w <= 0 or h <= 0:
        return 0.0
    return (w * h) / max(1e-9, min(a["w"] * a["h"], b["w"] * b["h"]))


def check_layout(value: dict, scene: dict, says: dict, assets: dict) -> list:
    problems = []
    layers = value.get("layers") or []
    ids = [l["id"] for l in layers]
    by_id = {l["id"]: l for l in layers}
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"layer id {dup!r} is used more than once")

    def cue_ok(cue, where, optional=False):
        if optional and not cue["beat_id"]:
            return
        if cue["beat_id"] not in scene["beat_ids"]:
            problems.append(f"{where}: cue beat {cue['beat_id']!r} is not a beat of this scene")
        elif not word_in(cue["word"], says.get(cue["beat_id"], "")):
            problems.append(f"{where}: cue word {cue['word']!r} is not spoken in beat {cue['beat_id']} (S4-03)")

    boxed = []
    for l in layers:
        lid, kind = l["id"], l["type"]
        cue_ok(l["cue"], f"layer {lid}")
        cue_ok(l["until"], f"layer {lid} until", optional=True)
        if kind in PANEL_TYPES | {"image", "label"}:
            if not _inside(l["box"]):
                problems.append(f"layer {lid}: box must lie inside the screen (0..1) with positive size")
            else:
                boxed.append(l)
        if kind == "image" and l["element_id"] not in assets:
            problems.append(f"layer {lid}: element {l['element_id']!r} has no chosen picture")
        if kind == "label":
            if not l["text"].strip() or len(l["text"]) > 48:
                problems.append(f"layer {lid}: a label needs short text (1-48 characters)")
            if l["anchor"]["layer"] and l["anchor"]["layer"] not in by_id:
                problems.append(f"layer {lid}: anchor layer {l['anchor']['layer']!r} does not exist")
        if kind in ("highlight", "flow") and l["target_layer"] not in by_id:
            problems.append(f"layer {lid}: target layer {l['target_layer']!r} does not exist")
        if kind == "flow" and len(l["path"]) < 2:
            problems.append(f"layer {lid}: a flow needs at least two path points")
        if kind in ("steps", "timeline", "scale"):
            if not l["entries"]:
                problems.append(f"layer {lid}: a {kind} needs entries")
            for entry in l["entries"]:
                cue_ok(entry["cue"], f"layer {lid} entry {entry['label']!r}")
            if kind == "steps" and len(l["entries"]) > 7:
                problems.append(f"layer {lid}: at most 7 steps fit on a phone screen")
        if kind == "table":
            if not l["columns"] or not l["rows"]:
                problems.append(f"layer {lid}: a table needs columns and rows")
            for row in l["rows"]:
                if len(row["cells"]) != len(l["columns"]):
                    problems.append(f"layer {lid}: row {row['label']!r} needs one cell per column")
        if kind == "arrow":
            for end in (l["from_ref"], l["to_ref"]):
                if end["layer"] not in by_id:
                    problems.append(f"layer {lid}: arrow end layer {end['layer']!r} does not exist")
        if kind == "question" and not l["text"].strip():
            problems.append(f"layer {lid}: the question needs its text")
    for i, a in enumerate(boxed):
        for b in boxed[i + 1:]:
            if a["type"] == "image" and b["type"] == "image":
                limit = 0.15
            elif "label" in (a["type"], b["type"]) and "image" in (a["type"], b["type"]):
                continue                     # labels may sit on a picture's margin; the reviewer checks they do not hide parts
            else:
                limit = 0.05
            if _overlap(a["box"], b["box"]) > limit and _together(a, b, scene):
                problems.append(f"layers {a['id']} and {b['id']} overlap on screen (S4-03)")
    for key in value.get("camera") or []:
        cue_ok(key["cue"], "camera key")
        if key["layer"] and key["layer"] not in by_id:
            problems.append(f"camera key: layer {key['layer']!r} does not exist")
    if not layers:
        problems.append("the scene has no layers")
    return problems


def _together(a, b, scene) -> bool:
    """Whether two layers can be on screen at the same time (by beat order of their cues)."""
    order = {bid: i for i, bid in enumerate(scene["beat_ids"])}

    def span(l):
        start = order.get(l["cue"]["beat_id"], 0)
        end = order.get(l["until"]["beat_id"], 10 ** 6) if l["until"]["beat_id"] else 10 ** 6
        return start, end
    (a0, a1), (b0, b1) = span(a), span(b)
    return a0 < b1 and b0 < a1 or a0 == b0


def apply_patch(previous: dict, patch: dict) -> dict:
    replace = {l["id"]: l for l in patch.get("replace_layers") or []}
    removed = set(patch.get("remove_layer_ids") or [])
    layers = [replace.pop(l["id"], l) for l in previous.get("layers") or [] if l["id"] not in removed]
    layers.extend(replace.values())
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), layers=layers,
                camera=patch.get("camera") if patch.get("camera") is not None else previous.get("camera"))


# ---------------------------------------------------------------- layout → SceneSpec

def to_scene_spec(layout: dict, scene: dict, timeline: dict, says: dict, assets: dict, captions: list) -> dict:
    sid = scene["scene_id"]

    def at(cue):
        return timing.cue_frame(timeline, sid, cue["beat_id"], cue["word"], says) if cue["beat_id"] else None

    def ref(r):
        return {"layer": r["layer"], "point": {"x": r["x"], "y": r["y"]}}

    layers = []
    for l in layout.get("layers") or []:
        base = {"id": l["id"], "type": l["type"], "at": at(l["cue"]) or 0}
        until = at(l["until"])
        if until is not None and until > base["at"]:
            base["until"] = until
        kind = l["type"]
        if kind == "image":
            asset = assets[l["element_id"]]
            base.update(box=l["box"], src=asset["src"], credit=asset["credit"])
        elif kind == "title":
            base.update(box=l["box"], title=l["text"], subtitle=l["subtitle"])
        elif kind == "label":
            base.update(box=l["box"], text=l["text"], tone="warm" if l["tone"] == "warm" else "accent")
            if l["anchor"]["layer"]:
                base["anchor"] = ref(l["anchor"])
        elif kind == "highlight":
            base.update(layer=l["target_layer"], region=l["region"], tone=l["tone"])
        elif kind == "flow":
            base.update(layer=l["target_layer"], path=l["path"], tone="warm" if l["tone"] == "warm" else "accent")
        elif kind == "steps":
            base.update(box=l["box"], title=l["text"], steps=[{"label": e["label"], "detail": e["detail"], "at": at(e["cue"]) or 0}
                                                             for e in l["entries"]])
        elif kind == "timeline":
            base.update(box=l["box"], events=[{"when": e["when"], "label": e["label"], "at": at(e["cue"]) or 0} for e in l["entries"]])
        elif kind == "scale":
            base.update(box=l["box"], title=l["text"], items=[{"label": e["label"], "value": e["value"], "unit": e["unit"],
                                                              "at": at(e["cue"]) or 0} for e in l["entries"]])
        elif kind == "table":
            base.update(box=l["box"], columns=l["columns"], rows=l["rows"],
                        focus=[{"column": f["column"], "at": at(f["cue"]) or 0} for f in l["focus"]])
        elif kind == "arrow":
            base.update(**{"from": ref(l["from_ref"]), "to": ref(l["to_ref"]), "label": l["text"]})
        elif kind == "question":
            base.update(text=l["text"])
        layers.append(base)
    camera = [{"at": 0, "box": {"x": 0, "y": 0, "w": 1, "h": 1}}]
    for key in sorted(layout.get("camera") or [], key=lambda k: at(k["cue"]) or 0):
        entry = {"at": at(key["cue"]) or 0, "frames": max(12, key["frames"] or 36)}
        if key["layer"]:
            entry.update(layer=key["layer"], region=key["region"])
        else:
            entry["box"] = {"x": 0, "y": 0, "w": 1, "h": 1}
        camera.append(entry)
    return {"id": sid, "duration": timeline[sid]["duration"], "layers": layers, "camera": camera, "captions": captions}


def scene_captions(scene: dict, timeline: dict, says: dict) -> list:
    out = []
    for bid in scene["beat_ids"]:
        start, length = timeline[scene["scene_id"]]["beats"][bid]
        out.append({"at": start, "until": start + length, "text": says.get(bid, "")})
    return out


def key_frames(spec: dict, limit: int = 5) -> list:
    """Moments worth looking at: shortly after layers and camera moves settle, spread over the scene."""
    moments = sorted({min(spec["duration"] - 1, l["at"] + 24) for l in spec["layers"]} |
                     {min(spec["duration"] - 1, k["at"] + k.get("frames", 36) + 6) for k in spec["camera"][1:]} |
                     {spec["duration"] - 2})
    if len(moments) <= limit:
        return moments
    step = (len(moments) - 1) / (limit - 1)
    return sorted({moments[round(i * step)] for i in range(limit)})


# ---------------------------------------------------------------- steps

def plan_step(course: Course, video: dict, *, rulebook) -> Step:
    rows = [{"element_key": f"{s['scene_id']}/{e['element_id']}", "kind": e["kind"], "shows": e["shows"],
             "parts_to_label": e["parts_to_label"], "detail": e["detail"]}
            for s in video["scenes"] for e in s["elements"] if needs_picture(e)]
    user = f"Video {video['video_id']}: {video['title']}.\nElements that need a picture (JSON):\n{json.dumps(rows, ensure_ascii=False)}"
    keys = {r["element_key"] for r in rows}

    def check(value):
        got = {n["element_key"] for n in value.get("needs") or []}
        problems = [f"element {k} has no search queries" for k in sorted(keys - got)]
        problems += [f"{n['element_key']}: give two or three queries" for n in value.get("needs") or [] if not n["queries"]]
        return problems

    return Step(section=SECTION, unit=f"assets-{video['video_id']}", instructions_version=PLAN_VERSION,
                system=fmt(PLAN_ROLE, course, rules=rulebook.instructions(SECTION)), user=user, schema=PLAN_SCHEMA, check=check)


def choose_step(course: Course, key: str, element: dict, need: dict, candidates: list, thumbs: list, *, rulebook) -> Step:
    parts = [{"type": "text", "text": f"Element {key} ({element['kind']}, {element['detail']}): {element['shows']}\n"
                                      f"Parts to label: {', '.join(element['parts_to_label']) or '-'}\n"
                                      f"Must show: {', '.join(need.get('must_show') or []) or '-'}"}]
    for n, (cand, data) in enumerate(zip(candidates, thumbs)):
        parts += [{"type": "text", "text": f"Candidate {n}: {cand.title} ({cand.licence})"}, _b64(data, _media(data))]

    def check(value):
        problems = []
        if not -1 <= value["choice"] < len(candidates):
            problems.append(f"choice must be -1 or 0-{len(candidates) - 1}")
        for p in value.get("parts") or []:
            if not _inside(p["region"]) or not (0 <= p["point"]["x"] <= 1 and 0 <= p["point"]["y"] <= 1):
                problems.append(f"part {p['name']!r}: region and point must be fractions of the picture (0..1)")
        return problems

    return Step(section=SECTION, unit=f"choose-{key.replace('/', '-')}", instructions_version=CHOOSE_VERSION,
                system=fmt(CHOOSE_ROLE, course, rules=rulebook.instructions(SECTION)), user=parts, schema=CHOOSE_SCHEMA, check=check,
                max_rounds=2)


def layout_step(course: Course, video: dict, scene: dict, beats: list, assets: dict, timeline: dict, *, rulebook, render_dist,
                assets_dir, stills_dir, max_rounds=3) -> Step:
    says = {b["beat_id"]: b["say"] for b in beats}
    scene_beats = [{"beat_id": bid, "say": says.get(bid, "")} for bid in scene["beat_ids"]]
    chosen = {e["element_id"]: assets[e["element_id"]] for e in scene["elements"] if e["element_id"] in assets}
    info = {"scene": scene, "beats": scene_beats,
            "pictures": {eid: {"parts": a["parts"], "width": a["width"], "height": a["height"]} for eid, a in chosen.items()}}
    user = [{"type": "text", "text": f"Video {video['video_id']}, scene {scene['scene_id']}.\nPlan, spoken beats and chosen pictures "
                                     f"(JSON):\n{json.dumps(info, ensure_ascii=False)}"}]
    for eid, a in chosen.items():
        user += [{"type": "text", "text": f"Picture for element {eid}:"}, _b64(a["preview"], _media(a["preview"]))]
    review_system = fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(), checklist=checklist_text(rulebook, SECTION))
    captions = scene_captions(scene, timeline, says)

    def review_user(value):
        spec = to_scene_spec(value, scene, timeline, says, chosen, captions)
        frames = key_frames(spec)
        parts = [{"type": "text", "text": f"Scene {scene['scene_id']}. Director's plan and spoken beats (JSON):\n"
                                          f"{json.dumps({'scene': scene, 'beats': scene_beats}, ensure_ascii=False)}\n\n"
                                          f"The layout (JSON):\n{json.dumps(value, ensure_ascii=False)}"}]
        try:
            pngs = stills({"fps": timing.FPS, "width": 1920, "height": 1080, "scenes": [spec], "captions": True}, frames,
                          dist=render_dist, assets=assets_dir)
        except RenderError as exc:
            parts.append({"type": "text", "text": f"(BIE could not render frames: {exc}; judge from the layout data.)"})
            return parts
        for frame, png in zip(frames, pngs):
            if stills_dir:
                path = Path(stills_dir) / video["video_id"] / scene["scene_id"]
                path.mkdir(parents=True, exist_ok=True)
                (path / f"frame-{frame:06d}.png").write_bytes(png)
            parts += [{"type": "text", "text": f"Frame at {frame / timing.FPS:.1f} s:"}, _b64(small_jpeg(png), "image/jpeg")]
        return parts

    return Step(section=SECTION, unit=f"layout-{video['video_id']}-{scene['scene_id']}", instructions_version=LAYOUT_VERSION,
                system=fmt(LAYOUT_ROLE, course, rules=rulebook.instructions(SECTION)), user=user, schema=LAYOUT_SCHEMA,
                check=lambda value: check_layout(value, scene, says, chosen), review_system=review_system,
                review_user=review_user, review_schema=REVIEW_SCHEMA, review_problems=review_problems, patch_schema=PATCH_SCHEMA,
                apply_patch=apply_patch, patch_hint=PATCH_HINT, max_rounds=max_rounds)


# ---------------------------------------------------------------- the section

def _fetch_candidates(need: dict, *, opener=None, per_element: int = 6):
    seen, found = set(), []
    for query in need.get("queries", [])[:3]:
        try:
            results = search_commons(query, limit=10, opener=opener)
        except Exception:  # one failed search must not stop the scene
            continue
        for cand in results:
            if cand.file_url not in seen:
                seen.add(cand.file_url)
                found.append(cand)
    return found[:per_element]


def find_picture(course: Course, key: str, element: dict, need: dict, runner, library: AssetLibrary, *, opener=None):
    """Search open sources for one element, let the vision AI choose and mark the parts, and keep it in the library.

    Returns (info, report_row); info is None when nothing fits. Used by the visual section and the game builder.
    """
    candidates = _fetch_candidates(need, opener=opener)
    thumbs, kept = [], []
    for cand in candidates:
        try:
            thumbs.append(_open(cand.thumb_url, opener=opener, max_bytes=4 * 1024 * 1024))
            kept.append(cand)
        except Exception:
            continue
    if not kept:
        return None, {"element": key, "status": "no_candidates", "queries": need.get("queries", [])}
    result = runner.run(choose_step(course, key, element, need, kept, thumbs, rulebook=runner.rulebook))
    value = result.output or {}
    index = value.get("choice", -1)
    if not result.passed or index < 0:
        return None, {"element": key, "status": "none_fits", "reason": value.get("reason", "")}
    cand = kept[index]
    try:
        big = _open(bigger_thumb(cand.thumb_url), opener=opener, max_bytes=12 * 1024 * 1024)
    except Exception:
        big = thumbs[index]
    asset = library.add_bytes(big, mime=_media(big), source=cand.source, title=cand.title, page_url=cand.page_url,
                              licence=cand.licence, licence_url=cand.licence_url, author=cand.author, credit=cand.credit,
                              tags=[element["kind"]] + element["parts_to_label"], description=element["shows"])
    from PIL import Image
    import io
    with Image.open(io.BytesIO(big)) as image:
        width, height = image.size
    info = {"asset_id": asset.asset_id, "src": "assets/" + asset.path, "parts": value.get("parts", []), "width": width,
            "height": height, "credit": f"{(cand.author or 'Wikimedia Commons')[:60]} · {cand.licence}", "preview": thumbs[index]}
    return info, {"element": key, "status": "chosen", "title": cand.title, "licence": cand.licence, "asset_id": asset.asset_id}


def resolve_assets(course: Course, video: dict, runner, library: AssetLibrary, *, opener=None, workers: int = 4):
    """element_id → chosen picture (library asset with parts, a preview for the AI and the src for the video)."""
    plan = runner.run(plan_step(course, video, rulebook=runner.rulebook))
    needs = {n["element_key"]: n for n in (plan.output or {}).get("needs") or []}
    elements = {f"{s['scene_id']}/{e['element_id']}": e for s in video["scenes"] for e in s["elements"] if needs_picture(e)}
    chosen, report = {}, []

    def one(key):
        element, need = elements[key], needs.get(key, {"queries": [element_text(elements[key])], "must_show": []})
        info, row = find_picture(course, key, element, need, runner, library, opener=opener)
        return key, info, row

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for key, info, row in pool.map(one, sorted(elements)):
            report.append(row)
            if info:
                chosen[key] = info
    return chosen, report


def element_text(element: dict) -> str:
    return element["shows"][:120]


def run_visual(chapter: dict, lesson: dict, director: dict, course: Course, runner, out_dir, *, workers: int = 4,
               max_rounds: int = 3, opener=None, render_dist=None, voice: dict | None = None):
    out = Path(out_dir)
    (out / "video_specs").mkdir(parents=True, exist_ok=True)
    library = AssetLibrary(out / "assets")
    render_dist = Path(render_dist or out / "_preview")
    beats_by_video = {v["video_id"]: v["beats"] for v in lesson.get("videos", [])}
    summary = {"schema": "bie.brain.visual/1", "course": chapter["course"], "rulebook_version": runner.rulebook.version,
               "licence_policy": licence_policy.version(), "videos": []}
    used = []
    for video in director.get("videos", []):
        if not video["scenes"]:
            continue
        beats = beats_by_video.get(video["video_id"], [])
        says = {b["beat_id"]: b["say"] for b in beats}
        timeline = timing.build(beats, video["scenes"], voice=voice)
        assets_by_key, report = resolve_assets(course, video, runner, library, opener=opener, workers=workers)
        asset_ids = sorted({info["asset_id"] for info in assets_by_key.values()})
        problems = library.lesson_check(asset_ids)            # the lesson licence gate, before any layout is paid for
        if problems:
            summary["videos"].append(_stopped(video, report, problems))
            continue
        results = []

        def lay(scene):
            assets = {key.split("/", 1)[1]: info for key, info in assets_by_key.items() if key.startswith(scene["scene_id"] + "/")}
            step = layout_step(course, video, scene, beats, assets, timeline, rulebook=runner.rulebook, render_dist=render_dist,
                               assets_dir=out / "assets", stills_dir=out / "stills", max_rounds=max_rounds)
            result = runner.run(step)
            spec = to_scene_spec(result.output, scene, timeline, says, assets, scene_captions(scene, timeline, says)) \
                if result.output else None
            return scene["scene_id"], result, spec

        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            results = list(pool.map(lay, video["scenes"]))
        scenes = [spec for _, _, spec in results if spec]
        video_spec = {"fps": timing.FPS, "width": 1920, "height": 1080, "scenes": scenes, "captions": True}
        problems = licence_policy.lesson_spec_check(video_spec) + library.lesson_check(asset_ids)
        if problems:                                        # the spec is not written: this video cannot be rendered
            summary["videos"].append(_stopped(video, report, problems))
            continue
        (out / "video_specs" / f"{video['video_id']}.json").write_text(json.dumps(video_spec, ensure_ascii=False), encoding="utf-8")
        used += [a for a in asset_ids if a not in used]
        summary["videos"].append({
            "video_id": video["video_id"], "title": video["title"], "assets": report, "status": "spec_written",
            "credits": library.credits(asset_ids),
            "scenes": [{"scene_id": sid, "status": r.status, "rounds": len(r.rounds), "cost_usd": r.cost_usd,
                        "last_problems": (r.rounds[-1].get("code_problems") or []) + (r.rounds[-1].get("review_problems") or [])
                        if r.rounds and not r.passed else []} for sid, r, _ in results],
            "seconds": round(sum(s["duration"] for s in scenes) / timing.FPS, 1),
        })
    library.save()
    scenes = [s for v in summary["videos"] for s in v["scenes"]]
    summary["credits"] = library.credits(used)
    summary["quality"] = {"videos": len(summary["videos"]), "scenes": len(scenes),
                          "videos_stopped_by_licence": sum(1 for v in summary["videos"] if v.get("status") == "stopped_by_licence"),
                          "scenes_passed": sum(1 for s in scenes if s["status"] == "passed"),
                          "pictures_chosen": sum(1 for v in summary["videos"] for a in v["assets"] if a["status"] == "chosen"),
                          "pictures_missing": sum(1 for v in summary["videos"] for a in v["assets"] if a["status"] != "chosen"),
                          "seconds": sum(v["seconds"] for v in summary["videos"]),
                          "cost_usd": round(sum(s["cost_usd"] for s in scenes), 6)}
    (out / "visual.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "VISUAL.md").write_text(render_markdown(summary), encoding="utf-8")
    return summary


def _stopped(video: dict, report: list, problems: list) -> dict:
    return {"video_id": video["video_id"], "title": video["title"], "assets": report, "status": "stopped_by_licence",
            "licence_problems": problems, "scenes": [], "seconds": 0}


def render_markdown(summary: dict) -> str:
    q = summary["quality"]
    lines = [f"# Visuals · {summary['course']['title']}", "",
             f"{q['scenes_passed']} of {q['scenes']} scenes passed; {q['pictures_chosen']} pictures chosen, {q['pictures_missing']} "
             f"missing; {q['seconds']:.0f} s of video planned; layout cost ${q['cost_usd']:.4f}.", ""]
    for v in summary["videos"]:
        lines += [f"## {v['video_id']} · {v['title']} ({v['seconds']} s)", ""]
        if v.get("status") == "stopped_by_licence":
            lines += ["Stopped by the lesson licence gate (no video spec written):", ""] + [f"- {p}" for p in v["licence_problems"]]
        for a in v["assets"]:
            lines.append(f"- picture {a['element']}: {a['status']}" + (f" · {a.get('title')} ({a.get('licence')})" if a["status"] == "chosen" else
                                                                      f" · {a.get('reason') or a.get('queries') or ''}"))
        for s in v["scenes"]:
            lines.append(f"- scene {s['scene_id']}: {s['status']} after {s['rounds']} round(s)")
            for p in s["last_problems"][:5]:
                lines.append(f"  - {p}")
        lines.append("")
    if summary.get("credits"):
        lines += ["## Picture credits", ""] + [f"- {c}" for c in summary["credits"]]
    return "\n".join(lines)
