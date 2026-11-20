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

Living films (Navin, 20 November 2026, on the first three Photosynthesis films: "slides jaisa lag raha hai", the stroma was a
box with "CO2 fixation" written in it, and no voice reached him). A film is now one world the camera travels into: every shot
after the first dives into a point of the picture before it (at most one cut), the pictures share one look (``look``), and
processes happen on AI pictures, not on flat diagrams (at most one diagram, for a comparison or a graph). Molecules are
actors from BIE's kit (``molecule_kit.json``: ATP, NADPH, CO2, RuBP, 3-PGA, G3P, ...); ``reacts`` brings inputs in to one
point and sends the products out, ``cycles`` turns a wheel of stations (the Calvin cycle takes CO2, ATP and NADPH and gives
ADP, NADP+ and sugar as it turns), the ``spin`` effect turns a rotor. Every shot moves, at least half the sentences of a long
film move, and the film opens on a question. The player's voice goes through Web Audio (``studio_voice_player.js``).
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .studio import SOURCE_WORDS, parse

N = {"type": "number"}
S = {"type": "string"}
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
SHOTS = {"long": (5, 12), "short": (2, 5)}
EFFECTS = ("rise", "rain", "glow", "spin")
SPRITES = ("pollen", "cell", "dot", "drop", "molecule", "light", "spark")
KIT_FILE = Path(__file__).with_name("molecule_kit.json")
KIT = json.loads(KIT_FILE.read_text(encoding="utf-8"))
MOLECULES = tuple(KIT["molecules"])
ACTORS = SPRITES + MOLECULES                 # what can travel, react or ride a cycle
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


WHAT = {"type": "string", "enum": list(ACTORS)}
SENTENCE = _obj({
    "roman": S, "voice": S,
    "pins": _arr(_obj({"label": S, "x": N, "y": N})),
    "arrows": _arr(_obj({"points": _arr(_arr(N)), "label": S})),
    "effects": _arr(_obj({"type": {"type": "string", "enum": list(EFFECTS)}, "x0": N, "x1": N, "y0": N, "y1": N})),
    "focus": _arr(S),
    "zoom": _obj({"x": N, "y": N, "scale": N}),
    "moves": _arr(_obj({"what": {"type": "string", "enum": list(ACTORS)},
                        "colour": {"type": "string", "enum": list(COLOURS)}, "label": S,
                        "points": _arr(_arr(N)), "count": I, "ms": N, "loop": B})),
    "grows": _arr(_obj({"points": _arr(_arr(N)), "label": S, "ms": N})),
    "fuses": _arr(_obj({"x": N, "y": N, "label": S})),
    "reacts": _arr(_obj({"inputs": _arr(_obj({"what": WHAT, "from": _arr(N)})), "at": _arr(N),
                         "outputs": _arr(_obj({"what": WHAT, "to": _arr(N)})), "label": S, "ms": N, "loop": B})),
    "cycles": _arr(_obj({"x": N, "y": N, "rx": N, "ry": N, "label": S, "carriers": I, "ms": N,
                         "stations": _arr(_obj({"at": N, "label": S, "becomes": WHAT, "takes": _arr(WHAT),
                                                "gives": _arr(WHAT)}))})),
})
SCHEMA = _obj({
    "title": S, "look": S,
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

How a BIE film works (approved benchmark: Monsoon and Pollen-to-seed films; Navin rejected films that felt like slides,
with a process written inside a box instead of happening on screen):
- ONE WORLD, NOT SLIDES. The film is one journey the camera makes into the real thing (leaf, then the cell, then the
  chloroplast, then the membrane and the stroma). Every shot after the first is a closer look INSIDE a point of the picture
  before it, and sets dive to that point; at most one shot may cut instead (dive -1, -1). "look" is one line of art
  direction every picture shares (palette, light, material, camera), so the pictures read as one place.
- REAL PLACES, LIVING PROCESSES. Places and processes are shown on AI pictures (photo or cutaway) that look like the real
  structure (for a chloroplast: stacked thylakoid discs, the fluid stroma between them, membranes with depth), and the
  process HAPPENS on that picture: molecules arrive, join, split, are spent and are made while the narration says so. Leave
  open space in the picture where the action will happen and say so in image_prompt. A diagram is only for a comparison or
  a graph, at most one per film; never draw a process as boxes with its name written inside.
- The film opens on the question's curiosity (its first sentence is a question) and ends on a one-line recap.
- A TEACHER TELLING WHAT HAPPENS, not a textbook read aloud. Speak in the present tense while it happens on screen
  ("Dekhiye, yeh CO2 andar aata hai...", "ab RuBP isse pakad leta hai..."), one step per sentence, naming each molecule or
  part as it appears; ask a small why or what-next before the answer at least once in every process shot; no textbook
  label lines ("CF0 membrane mein channel hai" becomes what the learner watches the channel do). It teaches like the best teacher: result first,
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
  moves: things sent along a path over the picture: what (pollen, cell, dot, drop, molecule, light, spark, or a molecule
  from BIE's kit: {molecules}), colour (gold,
  green, blue, red, white, purple), label (1 to 3 spoken words, or ""), points (2 to 6 [x, y] in percent, the path in
  order), count (1 to 12 copies, one after another), ms (how long one trip takes, 800 to 8000) and loop (keep moving
  until the shot ends). grows: a living line that grows along points (a pollen tube, a root tip, a signal): points (2 to 8),
  label, ms (1000 to 8000). fuses: two parts become one at x, y, with label ("n + n → 2n", "glucose").
  reacts: a reaction seen happening: inputs (1 to 3, each what + from [x, y]) fly to "at" [x, y], a flash, and the outputs
  (1 to 3, each what + to [x, y]) appear there and travel to where they go, where they stay; label is the spoken equation
  ("CO2 + RuBP → 3-PGA") or ""; ms 1500 to 9000; loop true repeats it while the shot lasts (a steady process).
  cycles: a process that goes round (the Calvin cycle): an oval track at x, y with rx, ry (percent of width and of height,
  8 to 40; the whole oval inside the picture), carriers (1 to 4 molecules riding it), ms (one lap, 6000 to 30000), label (the
  cycle's spoken name or ""), and 2 to 5 stations: at (degrees, 0 = right, 90 = bottom, clockwise), label (spoken in this
  sentence), becomes (what a carrier turns into at this station), takes (molecules that fly in here, e.g. CO2, ATP, NADPH)
  and gives (molecules that leave here, e.g. ADP, NADP+, G3P). Example for the Calvin cycle: stations at 300 "fixation"
  (becomes 3-PGA, takes CO2), 90 "reduction" (becomes G3P, takes ATP and NADPH, gives ADP, NADP+ and G3P), 200
  "regeneration" (becomes RuBP, takes ATP, gives ADP).
  effects can also be spin (a turning rotor, such as the head of ATP synthase; the box is where it turns).
  Use [] when nothing moves in that sentence. EVERY shot moves in at least one sentence, and in a long film at least half
  of all sentences move (moves, grows, fuses, reacts or cycles).
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
                                                              shots=f"{low} to {high}", length=length,
                                                              molecules=", ".join(MOLECULES))},
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


MOTION = ("moves", "grows", "fuses", "reacts", "cycles")


def moves(sentence: dict) -> bool:
    return any(sentence.get(key) for key in MOTION)


def _inside(points, low: int, high: int) -> bool:
    return isinstance(points, list) and low <= len(points) <= high and all(
        isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 100 for v in p) for p in points)


def motion_problems(sentence: dict, spoken: set, where: str) -> list:
    """moves, grows and fuses: inside the picture, in time ranges a learner can follow, labels spoken (dikhaya = bola)."""
    out = []
    for move in sentence.get("moves") or []:
        if move.get("what") not in ACTORS:
            out.append(f"{where}: a move's what must be one of {', '.join(SPRITES)} or a kit molecule")
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
    for react in sentence.get("reacts") or []:
        ins, outs = react.get("inputs") or [], react.get("outputs") or []
        if not (1 <= len(ins) <= 3 and 1 <= len(outs) <= 3):
            out.append(f"{where}: a react has 1 to 3 inputs and 1 to 3 outputs")
        if any(x.get("what") not in ACTORS for x in ins + outs):
            out.append(f"{where}: a react's what must be a sprite or a kit molecule")
        if not _inside([react.get("at")] + [x.get("from") for x in ins] + [x.get("to") for x in outs], 2, 7):
            out.append(f"{where}: a react's at, from and to are [x, y] in 0..100")
        if not 1500 <= float(react.get("ms") or 0) <= 9000:
            out.append(f"{where}: a react's ms is 1500 to 9000")
        label = react.get("label") or ""
        if _words(label) and not _words(label) & spoken:
            out.append(f"{where}: react label {label!r} is not spoken in this sentence (dikhaya = bola)")
    for cycle in sentence.get("cycles") or []:
        x, y, rx, ry = (float(cycle.get(k) or 0) for k in ("x", "y", "rx", "ry"))
        if not (8 <= rx <= 40 and 8 <= ry <= 40 and x - rx >= 2 and x + rx <= 98 and y - ry >= 2 and y + ry <= 98):
            out.append(f"{where}: a cycle's oval (x, y, rx, ry: 8 to 40) must sit inside the picture")
        if not 1 <= int(cycle.get("carriers") or 0) <= 4:
            out.append(f"{where}: a cycle has 1 to 4 carriers")
        if not 6000 <= float(cycle.get("ms") or 0) <= 30000:
            out.append(f"{where}: a cycle's ms (one lap) is 6000 to 30000")
        stations = cycle.get("stations") or []
        if not 2 <= len(stations) <= 5:
            out.append(f"{where}: a cycle has 2 to 5 stations")
        for station in stations:
            if not 0 <= float(station.get("at", -1)) < 360:
                out.append(f"{where}: a station's at is 0 to 359 degrees")
            names = [station.get("becomes")] + list(station.get("takes") or []) + list(station.get("gives") or [])
            if any(n not in ACTORS for n in names):
                out.append(f"{where}: a station's becomes, takes and gives must be sprites or kit molecules")
            if station.get("label") and not _words(station["label"]) & spoken:
                out.append(f"{where}: station label {station['label']!r} is not spoken in this sentence (dikhaya = bola)")
        if cycle.get("label") and _words(cycle["label"]) and not _words(cycle["label"]) & spoken:
            out.append(f"{where}: cycle label {cycle['label']!r} is not spoken in this sentence (dikhaya = bola)")
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
    covered, moving_shots, diagrams, cuts, moving, total = set(), set(), 0, 0, 0, 0
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
            diagrams += 1
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
        if number > 1 and dive.get("x", -1) == -1:
            cuts += 1
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
            total += 1
            if moves(sentence):
                moving_shots.add(sid)
                moving += 1
            if SOURCE_WORDS.search(roman) or SOURCE_WORDS.search(voice):
                out.append(f"{where}: names the source; remove it")
        if len(labels) > 6:
            out.append(f"{sid}: {len(labels)} different pins on one picture; at most 6")
    still = [shot.get("id") or f"shot {n}" for n, shot in enumerate(shots, 1)
             if (shot.get("id") or f"shot {n}") not in moving_shots]
    if shots and still:
        out.append(f"nothing moves in {', '.join(still)}: every shot shows its process happening (moves, grows, fuses, "
                   "reacts or cycles); show what travels travelling")
    if length == "long" and total and moving * 2 < total:
        out.append(f"only {moving} of {total} sentences move; in a long film at least half move (a still picture with a "
                   "voice over it is a slide)")
    if cuts > 1:
        out.append(f"{cuts} shots cut instead of diving; the film is one world: every shot after the first dives into a "
                   "point of the picture before it (at most one cut)")
    if diagrams > 1:
        out.append(f"{diagrams} diagram shots; at most one, for a comparison or a graph: show places and processes on AI "
                   "pictures (photo or cutaway)")
    opening = ((shots[0].get("sentences") or [{}])[0].get("roman") or "") if shots else ""
    if shots and "?" not in opening:
        out.append("the film's first sentence must be the question that opens it (a learner's curiosity, ending with ?)")
    if not (film.get("look") or "").strip() or len(film.get("look", "").strip()) < 20:
        out.append("look is missing: one line of art direction every picture shares (palette, light, material, camera)")
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


def image_prompt(shot: dict, look: str = "") -> str:
    """The shot's picture prompt; ``look`` (the film's shared art direction) keeps every picture in one world."""
    visual = shot.get("visual") or {}
    suffix = CUTAWAY_SUFFIX if visual.get("type") == "cutaway" else IMAGE_SUFFIX
    shared = f" Same look as the other pictures of this film: {look.strip()}." if (look or "").strip() else ""
    return visual.get("image_prompt", "").strip() + shared + suffix


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
                              "fuses": sentence.get("fuses") or [], "reacts": sentence.get("reacts") or [],
                              "cycles": sentence.get("cycles") or []})
        dive = shot.get("dive") or {}
        shots.append({"id": shot.get("id"), "title": shot.get("title"), "key": shot.get("key"),
                      "type": visual.get("type"), "img": images.get(shot.get("id"), ""),
                      "dive": dive if dive.get("x", -1) != -1 else None,
                      "svg": visual.get("svg", "") if visual.get("type") == "diagram" else "", "sentences": sentences})
    return {"title": film.get("title") or question.get("question"), "question": question.get("question"),
            "qid": question.get("id"), "chapter": chapter, "tint": tint, "shots": shots, "kit": kit_for(shots)}


def kit_for(shots: list) -> dict:
    """Only the kit molecules this film uses (the page stays small), with the element colours."""
    used = set()
    for shot in shots:
        for sentence in shot.get("sentences") or []:
            used.update(m.get("what") for m in sentence.get("moves") or [])
            for react in sentence.get("reacts") or []:
                used.update(x.get("what") for x in (react.get("inputs") or []) + (react.get("outputs") or []))
            for cycle in sentence.get("cycles") or []:
                for station in cycle.get("stations") or []:
                    used.update([station.get("becomes")] + list(station.get("takes") or []) + list(station.get("gives") or []))
    return {"elements": KIT["elements"], "molecules": {k: v for k, v in KIT["molecules"].items() if k in used}}


def html(data: dict, template: str) -> str:
    from .studio_voice import with_player_voice
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return with_player_voice(template).replace("/*__FILM__*/null", blob, 1)
