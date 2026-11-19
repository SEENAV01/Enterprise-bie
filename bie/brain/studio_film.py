"""The film-first course studio, stage 2: one film per approved student question (Navin, 18 November 2026).

The maker writes the film as shots. Each shot has one visual (an AI photo made by Codex image_gen, or a diagram the maker
draws as SVG) and its sentences; every sentence carries what appears on screen while it is spoken: pins (label + point),
arrows, effects (rise, rain, glow), the SVG parts it lights up and where the camera moves. That is Navin's rule from the
Monsoon reviews: the picture speaks with the narration ("dikhaya = bola"), the scenes play by themselves, caution lines and
source names never reach the screen. Code checks all of it and sends the exact problems back.

Motion (Navin, 19 November 2026, to reach the Campbell 17 film): what travels is shown travelling. A sentence can send
things along a path over the picture (``moves``: pollen grains, cells, molecules, drops, light, sparks), grow a living line
(``grows``: a pollen tube, a root, a signal), show a fusion (``fuses``: two parts merge into one with its label), and move
the camera (``zoom`` up to 2.2x: from the whole flower into the anther). A shot can be a ``cutaway`` (an AI picture drawn
as a transparent scientific cutaway, like the inside of the ovule) and can ``dive`` into a point of the previous picture.
The phone's browser plays all of it; nothing is rendered on a GPU.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

from .studio import SOURCE_WORDS, parse

N = {"type": "number"}
S = {"type": "string"}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
SHOTS = {"long": (5, 12), "short": (2, 5)}
EFFECTS = ("rise", "rain", "glow")
SPRITES = ("pollen", "cell", "dot", "drop", "molecule", "light", "spark")
COLOURS = ("gold", "green", "blue", "red", "white", "purple")
VISUALS = ("photo", "cutaway", "diagram")
ZOOM_MAX = 2.2
I = {"type": "integer"}
B = {"type": "boolean"}
SVG_BANNED = re.compile(r"(?i)<\s*(script|foreignObject|iframe|image|use|style)\b|\son[a-z]+\s*=|javascript:|href\s*=")
MAX_SVG = 60000
WORD = re.compile(r"[A-Za-zऀ-ॿ]{3,}")


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


SENTENCE = _obj({
    "roman": S, "voice": S,
    "pins": _arr(_obj({"label": S, "x": N, "y": N})),
    "arrows": _arr(_obj({"points": _arr(_arr(N)), "label": S})),
    "effects": _arr(_obj({"type": {"type": "string", "enum": list(EFFECTS)}, "x0": N, "x1": N, "y0": N, "y1": N})),
    "focus": _arr(S),
    "zoom": _obj({"x": N, "y": N, "scale": N}),
    "moves": _arr(_obj({"what": {"type": "string", "enum": list(SPRITES)},
                        "colour": {"type": "string", "enum": list(COLOURS)}, "label": S,
                        "points": _arr(_arr(N)), "count": I, "ms": N, "loop": B})),
    "grows": _arr(_obj({"points": _arr(_arr(N)), "label": S, "ms": N})),
    "fuses": _arr(_obj({"x": N, "y": N, "label": S})),
})
SCHEMA = _obj({
    "title": S,
    "shots": _arr(_obj({
        "id": S, "title": S, "key": S, "covers": _arr({"type": "integer"}),
        "visual": _obj({"type": {"type": "string", "enum": list(VISUALS)}, "image_prompt": S, "svg": S}),
        "dive": _obj({"x": N, "y": N}),
        "sentences": _arr(SENTENCE),
    })),
})

INSTRUCTIONS = """You are BIE's film director and teacher. Write ONE film that teaches ONE student question of a {course}
chapter. Learner-facing language: {language} (Navin's natural spoken Hinglish in Roman script for "roman"; the same
sentence in Devanagari for "voice", which the narrator speaks).

How a BIE film works (approved benchmark: Monsoon and Pollen-to-seed films):
- The film opens on the question's curiosity and ends on a one-line recap. It teaches like the best teacher: result first,
  then how and why, step by step, with an everyday example where it helps. Never "the book says", never a source name,
  never a caution line ("assume", "illustrative") on screen.
- Shots: {shots} shots for this film ({length}). Each shot has one visual and 2 to 6 short sentences spoken over it.
  shot.key is the one-line takeaway shown in the bottom band; shot.covers lists the indexes (0-based) of the question's
  points this shot teaches; together the shots cover every point.
- visual.type "photo": a photorealistic picture made by an image model. image_prompt describes it fully (place, subject,
  camera, light, 16:9) and must leave room for labels; svg is "". Use photo for real things, places, organisms, machines.
  visual.type "diagram": you draw it as one SVG illustration in the style of BIE's Pollen Lab (a calm background colour,
  gradients and soft shading, rounded natural shapes, depth, short labels with leader lines; at least one gradient and at
  least 12 drawn shapes; viewBox; no script, no images, no style element; give every part you will light up an id);
  image_prompt is "". Use diagram for graphs, cycles, flow charts and comparisons.
  visual.type "cutaway": an AI picture drawn as a transparent scientific cutaway or cross-section (glossy cells, soft
  volumetric light, depth, a calm dark background), for the inside of things a camera cannot see: the inside of a leaf,
  a chloroplast, an ovule, a root. image_prompt describes it fully like a photo prompt; svg is "".
- dive: {{"x": 0-100, "y": 0-100}} when this shot is a close-up INSIDE a point of the previous picture (the camera dives
  into that point, then this shot opens); {{"x": -1, "y": -1}} otherwise (and always for the first shot).
- Every sentence says what appears WHILE it is spoken ("dikhaya = bola"): pins (a short label at x,y in percent of the
  picture, 3 to 97; the label's words must be spoken in that sentence), arrows (2 to 4 points in percent, a short label or
  ""), effects (rise for rising air or heat, rain, glow; a box x0,x1,y0,y1 in percent), focus (ids of SVG parts to light up;
  [] for photos) and zoom (x, y in percent and scale 1.0 to 2.2: where the camera moves for this sentence; 1.0 shows the
  whole picture, 1.6 to 2.2 goes close to one part, as a camera pushes in from the whole flower to the anther).
- Motion, as in the approved Pollen-to-seed film: whatever travels in the story is SHOWN travelling while it is spoken.
  moves: things sent along a path over the picture: what (pollen, cell, dot, drop, molecule, light, spark), colour (gold,
  green, blue, red, white, purple), label (1 to 3 spoken words, or ""), points (2 to 6 [x, y] in percent, the path in
  order), count (1 to 12 copies, one after another), ms (how long one trip takes, 800 to 8000) and loop (keep moving
  until the shot ends). grows: a living line that grows along points (a pollen tube, a root tip, a signal): points (2 to 8),
  label, ms (1000 to 8000). fuses: two parts become one at x, y, with label ("n + n → 2n", "glucose"). Use [] when nothing
  moves in that sentence. A long film shows motion in at least 2 shots, a short film in at least 1.
- At most 3 pins per sentence and at most 6 on a picture overall; labels of 1 to 3 words.

Answer with the JSON object only."""

PROBLEMS_PROMPT = "BIE's code checked the film and found these problems. Send the whole corrected JSON again:\n- "


def messages(question: dict, *, course: str, language: str, chapter: str = "") -> list:
    length = (question.get("film") or {}).get("length", "long")
    low, high = SHOTS.get(length, SHOTS["long"])
    points = "\n".join(f"{i}. ({p.get('kind')}) {p.get('point')}" for i, p in enumerate(question.get("points") or []))
    user = (f"Chapter: {chapter}\nQuestion {question.get('id')}: {question.get('question')}\nCuriosity: {question.get('hook')}\n"
            f"Showing moment planned: {(question.get('film') or {}).get('showing_moment', '')}\nPoints to teach:\n{points}\n"
            + ("\nThe book's lines for these points:\n" + question["source_text"] if question.get("source_text") else ""))
    return [{"role": "system", "content": INSTRUCTIONS.format(course=course or "school", language=language or "Hinglish",
                                                              shots=f"{low} to {high}", length=length)},
            {"role": "user", "content": user}]


def svg_problems(svg: str) -> list:
    if not svg.strip():
        return ["the diagram has no svg"]
    out = []
    if len(svg) > MAX_SVG:
        out.append(f"the svg is {len(svg)} characters; keep it under {MAX_SVG}")
    if SVG_BANNED.search(svg):
        out.append("the svg uses a banned element or attribute (script, foreignObject, image, use, style, on*, href)")
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        return out + [f"the svg is not valid XML ({exc})"]
    if not root.tag.endswith("svg") or not root.get("viewBox"):
        out.append("the svg needs an <svg> root with a viewBox")
    return out


SHAPES = ("path", "rect", "circle", "ellipse", "polygon", "polyline", "line")
MIN_SHAPES = 12


def illustration_problems(svg: str) -> list:
    """An illustration in the Chapter 17 Pollen Lab style (Navin, 19 November 2026), not a bare sketch: at least one
    gradient and at least MIN_SHAPES drawn shapes."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError:
        return []
    tags = [el.tag.rsplit("}", 1)[-1] for el in root.iter()]
    out = []
    if not any(t in ("linearGradient", "radialGradient") for t in tags):
        out.append("the illustration has no gradient; draw it in the Pollen Lab style (gradients, soft shading, depth)")
    shapes = sum(1 for t in tags if t in SHAPES)
    if shapes < MIN_SHAPES:
        out.append(f"the illustration has {shapes} shapes; a bare sketch is not enough, draw at least {MIN_SHAPES}")
    return out


def svg_ids(svg: str) -> set:
    try:
        return {el.get("id") for el in ET.fromstring(svg).iter() if el.get("id")}
    except ET.ParseError:
        return set()


def _inside(points, low: int, high: int) -> bool:
    return isinstance(points, list) and low <= len(points) <= high and all(
        isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 100 for v in p) for p in points)


def motion_problems(sentence: dict, spoken: set, where: str) -> list:
    """moves, grows and fuses: inside the picture, in time ranges a learner can follow, labels spoken (dikhaya = bola)."""
    out = []
    for move in sentence.get("moves") or []:
        if move.get("what") not in SPRITES:
            out.append(f"{where}: a move's what must be one of {', '.join(SPRITES)}")
        if not _inside(move.get("points"), 2, 6):
            out.append(f"{where}: a move needs 2 to 6 points [x, y] in 0..100")
        if not 1 <= int(move.get("count") or 0) <= 12:
            out.append(f"{where}: a move's count is 1 to 12")
        if not 800 <= float(move.get("ms") or 0) <= 8000:
            out.append(f"{where}: a move's ms is 800 to 8000")
        if move.get("label") and not _words(move["label"]) & spoken:
            out.append(f"{where}: move label {move['label']!r} is not spoken in this sentence (dikhaya = bola)")
    for grow in sentence.get("grows") or []:
        if not _inside(grow.get("points"), 2, 8):
            out.append(f"{where}: a grow needs 2 to 8 points [x, y] in 0..100")
        if not 1000 <= float(grow.get("ms") or 0) <= 8000:
            out.append(f"{where}: a grow's ms is 1000 to 8000")
        if grow.get("label") and not _words(grow["label"]) & spoken:
            out.append(f"{where}: grow label {grow['label']!r} is not spoken in this sentence (dikhaya = bola)")
    for fuse in sentence.get("fuses") or []:
        if not (0 <= float(fuse.get("x", -1)) <= 100 and 0 <= float(fuse.get("y", -1)) <= 100):
            out.append(f"{where}: a fuse is x, y in 0..100")
        label = fuse.get("label") or ""
        if not label.strip():
            out.append(f"{where}: a fuse needs its label (what the two parts become)")
        elif _words(label) and not _words(label) & spoken:
            out.append(f"{where}: fuse label {label!r} is not spoken in this sentence (dikhaya = bola)")
    return out


def _words(text: str) -> set:
    return {w.lower() for w in WORD.findall(text or "")}


def problems(film, question: dict) -> list:
    if not isinstance(film, dict):
        return ["the answer is not a JSON object"]
    out = []
    length = (question.get("film") or {}).get("length", "long")
    low, high = SHOTS.get(length, SHOTS["long"])
    shots = film.get("shots") or []
    if not low <= len(shots) <= high:
        out.append(f"there are {len(shots)} shots; this {length} film needs {low} to {high}")
    covered, moving_shots = set(), set()
    for number, shot in enumerate(shots, 1):
        sid = shot.get("id") or f"shot {number}"
        covered.update(shot.get("covers") or [])
        visual = shot.get("visual") or {}
        if len((shot.get("key") or "").strip()) < 8:
            out.append(f"{sid}: key (the takeaway line) is missing")
        ids = set()
        if visual.get("type") in ("photo", "cutaway"):
            if len((visual.get("image_prompt") or "").strip()) < 60:
                out.append(f"{sid}: image_prompt needs a full description (at least 60 characters)")
        elif visual.get("type") == "diagram":
            out += [f"{sid}: {p}" for p in svg_problems(visual.get("svg") or "") + illustration_problems(visual.get("svg") or "")]
            ids = svg_ids(visual.get("svg") or "")
        else:
            out.append(f"{sid}: visual.type must be photo, cutaway or diagram")
        dive = shot.get("dive") or {"x": -1, "y": -1}
        if not (dive.get("x") == -1 and dive.get("y") == -1) and not (0 <= float(dive.get("x", -5)) <= 100
                                                                    and 0 <= float(dive.get("y", -5)) <= 100):
            out.append(f"{sid}: dive is x, y in 0..100, or -1, -1 for no dive")
        if number == 1 and dive.get("x", -1) != -1:
            out.append(f"{sid}: the first shot cannot dive (there is no picture before it)")
        sentences = shot.get("sentences") or []
        if not 2 <= len(sentences) <= 6:
            out.append(f"{sid}: {len(sentences)} sentences; write 2 to 6")
        labels = set()
        for k, sentence in enumerate(sentences, 1):
            where = f"{sid} sentence {k}"
            roman, voice = sentence.get("roman") or "", sentence.get("voice") or ""
            if len(roman.strip()) < 15:
                out.append(f"{where}: roman is missing or too short")
            if not DEVANAGARI.search(voice):
                out.append(f"{where}: voice must be the same sentence in Devanagari")
            spoken = _words(roman) | _words(voice)
            pins = sentence.get("pins") or []
            if len(pins) > 3:
                out.append(f"{where}: {len(pins)} pins; at most 3 per sentence")
            for pin in pins:
                labels.add(pin.get("label"))
                if not (3 <= float(pin.get("x", -1)) <= 97 and 3 <= float(pin.get("y", -1)) <= 97):
                    out.append(f"{where}: pin {pin.get('label')!r} is outside 3..97")
                if not _words(pin.get("label")) & spoken:
                    out.append(f"{where}: pin {pin.get('label')!r} is not spoken in this sentence (dikhaya = bola)")
            for arrow in sentence.get("arrows") or []:
                pts = arrow.get("points") or []
                if not 2 <= len(pts) <= 4 or any(len(p) != 2 or not all(0 <= v <= 100 for v in p) for p in pts):
                    out.append(f"{where}: an arrow needs 2 to 4 points [x, y] in 0..100")
            missing = [f for f in sentence.get("focus") or [] if f not in ids]
            if missing:
                out.append(f"{where}: focus ids not in the svg: {', '.join(missing[:5])}")
            zoom = sentence.get("zoom") or {}
            if not 1.0 <= float(zoom.get("scale", 0)) <= ZOOM_MAX:
                out.append(f"{where}: zoom.scale must be 1.0 to {ZOOM_MAX}")
            found_motion = motion_problems(sentence, spoken, where)
            out += found_motion
            if sentence.get("moves") or sentence.get("grows") or sentence.get("fuses"):
                moving_shots.add(sid)
            if SOURCE_WORDS.search(roman) or SOURCE_WORDS.search(voice):
                out.append(f"{where}: names the source; remove it")
        if len(labels) > 6:
            out.append(f"{sid}: {len(labels)} different pins on one picture; at most 6")
    need = 2 if length == "long" else 1
    if shots and len(moving_shots) < need:
        out.append(f"only {len(moving_shots)} shot(s) show motion (moves, grows or fuses); a {length} film needs at least "
                   f"{need}: show what travels travelling")
    points = range(len(question.get("points") or []))
    missing_points = [i for i in points if i not in covered]
    if missing_points:
        out.append("no shot covers the question's points " + ", ".join(map(str, missing_points)))
    return out


def write(client, model: str, question: dict, *, course: str = "", language: str = "Hinglish", chapter: str = "",
          max_rounds: int = 3) -> dict:
    convo = messages(question, course=course, language=language, chapter=chapter)
    rounds, usage, film, found = [], {"input_tokens": 0, "output_tokens": 0}, None, ["no answer yet"]
    for number in range(1, max_rounds + 1):
        reply = client.chat(model=model, messages=convo, schema=SCHEMA)
        for key in usage:
            usage[key] += int((reply.get("usage") or {}).get(key) or 0)
        film = parse(reply.get("content", ""))
        found = problems(film, question)
        rounds.append({"round": number, "problems": found})
        if not found:
            break
        convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                         {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
    return {"film": film, "problems": found, "rounds": rounds, "usage": usage}


IMAGE_SUFFIX = (" Photorealistic, natural colours, documentary quality, 16:9 landscape. No text, no letters, no numbers, "
                "no labels, no logos, no watermark, no recognisable real person.")


CUTAWAY_SUFFIX = (" Scientific cutaway illustration: transparent cross-section, glossy cells, soft volumetric light, depth, "
                  "calm dark teal background, painterly 3D look, 16:9 landscape. No text, no letters, no numbers, no labels, "
                  "no logos, no watermark.")


def image_prompt(shot: dict) -> str:
    visual = shot.get("visual") or {}
    suffix = CUTAWAY_SUFFIX if visual.get("type") == "cutaway" else IMAGE_SUFFIX
    return visual.get("image_prompt", "").strip() + suffix


def player_data(film: dict, *, images: dict, audio: dict, chapter: str, question: dict, tint: str = "#2c6e87") -> dict:
    """The JSON the film player reads: shots with their visual (image data URI or SVG) and timed sentences."""
    shots = []
    for shot in film.get("shots") or []:
        visual = shot.get("visual") or {}
        sentences = []
        for k, sentence in enumerate(shot.get("sentences") or []):
            clip = audio.get((shot.get("id"), k)) or {}
            text = sentence.get("roman", "")
            sentences.append({"text": text, "audio": clip.get("uri", ""),
                              "dur": clip.get("dur") or max(2.5, 0.075 * len(text)),
                              "pins": [{"t": p["label"], "x": p["x"], "y": p["y"]} for p in sentence.get("pins") or []],
                              "arrows": sentence.get("arrows") or [], "effects": sentence.get("effects") or [],
                              "focus": sentence.get("focus") or [], "zoom": sentence.get("zoom") or {},
                              "moves": sentence.get("moves") or [], "grows": sentence.get("grows") or [],
                              "fuses": sentence.get("fuses") or []})
        dive = shot.get("dive") or {}
        shots.append({"id": shot.get("id"), "title": shot.get("title"), "key": shot.get("key"),
                      "type": visual.get("type"), "img": images.get(shot.get("id"), ""),
                      "dive": dive if dive.get("x", -1) != -1 else None,
                      "svg": visual.get("svg", "") if visual.get("type") == "diagram" else "", "sentences": sentences})
    return {"title": film.get("title") or question.get("question"), "question": question.get("question"),
            "qid": question.get("id"), "chapter": chapter, "tint": tint, "shots": shots}


def html(data: dict, template: str) -> str:
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("/*__FILM__*/null", blob, 1)
