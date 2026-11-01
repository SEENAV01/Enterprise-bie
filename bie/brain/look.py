"""LOOK-01: the look check (Task 046 one-shot test, after Navin rejected Part B on 26 October 2026).

The Part B frame checks measured presence (a caption band, a label box, accent pixels, a dark frame, motion) and passed
frames that looked nothing like the benchmark (SEEKH_LOG entry 13). LOOK-01 asks a reviewer with image input to compare
our frames with the benchmark's frames on what the eye sees: organic shape, translucency, lighting and depth, detail,
scientific correctness and the overall class of the picture, each 1 to 10 with its reason. The score is advice only;
Navin's eye decides. The benchmark's frames never leave the machine that holds them (they are not ours to publish): a
request names a private reference set kept on that machine, or, without it, a written description of the benchmark's
look, and the result says which one was used.
"""
from __future__ import annotations

RULE = "LOOK-01"
VERSION = "2026-10-26.1"
AXES = (
    ("organic_shape", "Organic shape: irregular, interlocking cell outlines, soft domed tops, a nucleus bulge; not geometric prisms."),
    ("translucency", "Translucency: light passes into and through the cells (subsurface scattering); nuclei read as denser bodies inside."),
    ("lighting_depth", "Lighting and depth: a key light and a rim light, soft haze, depth of field, planes separated in depth."),
    ("detail", "Detail: fine surface texture and membranes, crisp at the focus, nothing plastic or flat-shaded."),
    ("science", "Scientific correctness for the shot: one single thin layer of flat cells, a nucleus per cell, a basement membrane below."),
    ("same_class", "Overall: would a viewer place this in the same class of animation as the reference frames?"),
)
SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["scores", "reasons", "biggest_gap", "verdict"],
    "properties": {
        "scores": {"type": "object", "additionalProperties": False, "required": [a for a, _ in AXES],
                   "properties": {a: {"type": "integer", "minimum": 1, "maximum": 10} for a, _ in AXES}},
        "reasons": {"type": "object", "additionalProperties": False, "required": [a for a, _ in AXES],
                    "properties": {a: {"type": "string", "minLength": 10} for a, _ in AXES}},
        "biggest_gap": {"type": "string", "minLength": 10},
        "verdict": {"type": "string", "enum": ["same class", "close", "far"]},
    },
}
SYSTEM = ("You are BIE's look reviewer (rule LOOK-01). You compare frames of a science animation BIE rendered with reference "
          "frames of the animation BIE is measured against. Judge only what the eye sees in the images; text, labels and "
          "captions drawn on frames are BIE's code overlays and are not part of the look. Be strict and honest: a 10 means "
          "indistinguishable in quality from the reference, a 5 means clearly a step below, a 1 means a different class "
          "entirely. Give one short concrete reason per score. Reply with one JSON object that matches the schema.")


def task_text(shot: dict, *, reference: str, route: str, frames: int, references: int, description: str = "") -> str:
    axes = "\n".join(f"- {name}: {text}" for name, text in AXES)
    ref = (f"The first {references} images are the REFERENCE frames (the benchmark). The next {frames} images are BIE's frames "
           f"from {route}." if reference == "frames" else
           f"No reference image is attached; the benchmark's look is described in words here: {description}\n"
           f"The {frames} images are BIE's frames from {route}.")
    return (f"Shot: {shot.get('sentence', '')}\nWhat it must show: {shot.get('must_show', '')}\n\n{ref}\n\n"
            f"Score BIE's frames 1 to 10 on each axis, against the reference:\n{axes}\n\n"
            "Then name the biggest gap in one sentence and give the verdict: same class, close or far.")


def messages(shot: dict, route: str, frames: list, references: list, description: str = "") -> tuple:
    """BIE messages for one route: ``frames`` and ``references`` are [(media_type, base64)]."""
    parts = [{"type": "text", "text": task_text(shot, reference="frames" if references else "description", route=route,
                                                frames=len(frames), references=len(references), description=description)}]
    for label, images in (("REFERENCE", references), ("BIE", frames)):
        for number, (media, data) in enumerate(images, 1):
            parts.append({"type": "text", "text": f"{label} frame {number}:"})
            parts.append({"type": "image", "media_type": media, "data": data})
    return ({"role": "system", "content": SYSTEM}, {"role": "user", "content": parts})


def problems(value: dict) -> list:
    """Content checks beyond the schema: a reason per axis that is more than a label."""
    out = []
    for name, _ in AXES:
        reason = str((value.get("reasons") or {}).get(name, ""))
        if len(reason.split()) < 3:
            out.append(f"{name}: give a concrete reason of a few words")
    return out


def summary(results: dict) -> dict:
    """{route: {axis: score}, ...} → the rows of the rule table: mean per route and the overall."""
    rows = {}
    for route, value in results.items():
        scores = (value or {}).get("scores") or {}
        if scores:
            rows[route] = {"mean": round(sum(scores.values()) / len(scores), 2), "same_class": scores.get("same_class"),
                           "verdict": value.get("verdict")}
    return rows


# ---------------------------------------------------------------- LOOK-D1 (Task 046 Part D1; Navin, 30 October 2026)
# "jo bola ja rha hai screen ke visuals se wo baat clear ho"; "agar puri video mein sirf text hi text screen par dikha to video,
# video nhi ek book ban jaayegi". One still per part, judged without the narration: does the picture alone hint at the point,
# and is it text only? Advice for Navin's eye, never a blocker (Part D1).
D1_RULE = "LOOK-D1"
D1_VERSION = "2026-10-31.1"
D1_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["hints_point", "text_only", "what_it_shows", "missing"],
    "properties": {
        "hints_point": {"type": "integer", "minimum": 1, "maximum": 10},
        "text_only": {"type": "boolean"},
        "what_it_shows": {"type": "string", "minLength": 5},
        "missing": {"type": "string"},
    },
}
D1_SYSTEM = ("You are BIE's look reviewer for rule LOOK-D1. You see ONE still from one part of a lesson video for Indian learners; "
             "you do not hear the teacher. Judge only what the eye gets from the picture: would a learner who sees this frame, "
             "without the narration, get a hint of the teacher's point? 10 = the picture alone says it (things, marks, arrows, a "
             "timeline or a table that carry the idea); 5 = some picture but the idea needs the words; 1 = no hint at all. "
             "text_only is true when the frame is essentially words on a background (headings, boards, sentences) with no "
             "picture of the things. what_it_shows: what the frame shows, in a few words. missing: the one picture that would make "
             "the point clear, or \"\". Reply with one JSON object that matches the schema.")


def d1_task(part: dict) -> str:
    return (f"Lesson part {part.get('id', '')}. The teacher's point here: {part.get('point', '')}\n"
            "Judge the still below as described.")


def d1_messages(part: dict, media: str, data: str) -> tuple:
    return ({"role": "system", "content": D1_SYSTEM},
            {"role": "user", "content": [{"type": "text", "text": d1_task(part)}, {"type": "image", "media_type": media, "data": data}]})


def d1_problems(value: dict) -> list:
    return [] if len(str(value.get("what_it_shows", "")).split()) >= 3 else ["what_it_shows: say what the frame shows in a few words"]


def d1_summary(results: dict) -> dict:
    scored = {k: v for k, v in results.items() if isinstance(v, dict) and "hints_point" in v}
    if not scored:
        return {}
    return {"parts": len(scored), "mean_hints_point": round(sum(v["hints_point"] for v in scored.values()) / len(scored), 2),
            "text_only": sum(1 for v in scored.values() if v.get("text_only")),
            "low": sorted(k for k, v in scored.items() if v["hints_point"] <= 4)}


# ---------------------------------------------------------------- LOOK-D2 (Task 046 Part D2; Navin, 1 November 2026)
# "mera meaning hai ki visuals dekhkar concept clear ho aur user narration se connect kar sake". LOOK-D1 asked one loose
# question per part and scored 5.25 while Navin found the worlds empty of process. LOOK-D2 asks, per beat, about the very things
# the dikhane ki list names (its nouns and its relation): is each one VISIBLE in the beat's still, and is it HAPPENING (an action
# in progress or its result: the hand giving, the cross on the coin, the phone showing paid)? The reviewer only answers yes or
# no; code computes the score from those answers. Report only, never a blocker.
D2_RULE = "LOOK-D2"
D2_VERSION = "2026-11-01.1"
D2_MAX_BEATS = 8
D2_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["beats", "missing"],
    "properties": {
        "beats": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["beat_id", "items", "text_only", "what_it_shows"],
            "properties": {
                "beat_id": {"type": "string"},
                "items": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "visible", "happening"],
                                                     "properties": {"name": {"type": "string"}, "visible": {"type": "boolean"},
                                                                    "happening": {"type": "boolean"}}}},
                "text_only": {"type": "boolean"},
                "what_it_shows": {"type": "string"}}}},
        "missing": {"type": "string"},
    },
}
D2_SYSTEM = ("You are BIE's look reviewer for rule LOOK-D2. You see stills from one part of a lesson video for Indian learners, one "
             "still per beat, each labelled with its beat id; you do not hear the teacher. For every beat you get the things that "
             "beat should show (its nouns, and its relation as what should happen). For each item answer two yes/no questions "
             "from the still alone: visible = can a learner see this thing (or this relation's mark, arrow, meter, scale) in the "
             "frame? happening = is it shown happening or just happened: an action in progress or its result (a hand giving or "
             "taking, a phone raised to a QR code, a paid screen, a cross landing on a coin, a meter at its red line, a value "
             "struck and replaced)? A thing that only stands there is visible but not happening; a word naming it is neither. "
             "text_only is true when the still is essentially words on a background. what_it_shows: a few words. missing: the one "
             "picture that would most help the part, or \"\". Answer every beat and every item, names exactly as given. Reply with "
             "one JSON object that matches the schema.")


def d2_items(beat: dict) -> list:
    """The items a beat's still is asked about: its nouns (at most three) and its relation, with what should be seen."""
    items = [{"name": str(n), "expect": "visible"} for n in (beat.get("nouns") or [])[:3] if str(n).strip()]
    rel = beat.get("relation") or ""
    if rel and rel not in ("other", "place", "part_whole"):
        items.append({"name": f"relation: {rel}", "expect": beat.get("shows") or rel})
    if beat.get("template") not in (None, "", "none", "other"):
        items.append({"name": f"process: {beat['template']}", "expect": beat.get("shows") or beat["template"]})
    return items


def d2_task(part: dict) -> str:
    lines = [f"Lesson part {part.get('id', '')}. The stills follow in this order, one per beat."]
    for b in part.get("beats") or []:
        lines.append(f"- beat {b['beat_id']}: the teacher says \"{str(b.get('say', ''))[:160]}\"; it should show: {b.get('shows', '')}")
        for it in b.get("items") or []:
            lines.append(f"    · {it['name']} (expected: {it.get('expect', 'visible')})")
    return "\n".join(lines)


def d2_messages(part: dict, frames: list) -> tuple:
    """``frames``: [(beat_id, media type, base64 data)] in the part's beat order."""
    content = [{"type": "text", "text": d2_task(part)}]
    for bid, media, data in frames:
        content += [{"type": "text", "text": f"Still of beat {bid}:"}, {"type": "image", "media_type": media, "data": data}]
    return ({"role": "system", "content": D2_SYSTEM}, {"role": "user", "content": content})


def d2_problems(value: dict, part: dict | None = None) -> list:
    if part is None:
        return []
    want = {b["beat_id"]: {it["name"] for it in b.get("items") or []} for b in part.get("beats") or []}
    got = {b.get("beat_id"): {it.get("name") for it in b.get("items") or []} for b in value.get("beats") or []}
    out = [f"beat {bid}: answer it" for bid in want if bid not in got]
    out += [f"beat {bid}: answer every item ({', '.join(sorted(names - got.get(bid, set())))})" for bid, names in want.items()
            if bid in got and names - got[bid]]
    return out


def d2_score(value: dict) -> dict:
    """The part's numbers, computed by code from the yes/no answers: score = 10 x (visible answers + happening answers) / (2 x
    items); a text-only still counts its items as neither."""
    items = vis = hap = 0
    text_only = 0
    for b in value.get("beats") or []:
        flat = bool(b.get("text_only"))
        text_only += flat
        for it in b.get("items") or []:
            items += 1
            vis += bool(it.get("visible")) and not flat
            hap += bool(it.get("happening")) and not flat
    return {"items": items, "visible": vis, "happening": hap, "text_only_beats": text_only,
            "score": round(10 * (vis + hap) / (2 * items), 2) if items else None}


def d2_summary(results: dict) -> dict:
    scored = {k: v for k, v in results.items() if isinstance(v, dict) and (v.get("numbers") or {}).get("score") is not None}
    if not scored:
        return {}
    items = sum(v["numbers"]["items"] for v in scored.values())
    return {"parts": len(scored), "mean_score": round(sum(v["numbers"]["score"] for v in scored.values()) / len(scored), 2),
            "items": items, "visible_pct": round(100 * sum(v["numbers"]["visible"] for v in scored.values()) / items, 1) if items else None,
            "happening_pct": round(100 * sum(v["numbers"]["happening"] for v in scored.values()) / items, 1) if items else None,
            "text_only_beats": sum(v["numbers"]["text_only_beats"] for v in scored.values()),
            "low": sorted(k for k, v in scored.items() if v["numbers"]["score"] <= 4)}
