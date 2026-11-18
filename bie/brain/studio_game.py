"""The film-first course studio, stage 3: the chapter's revision game (Navin, 18 November 2026).

Navin's rule: the games revise the whole chapter, with mechanisms that fit the subject, and the learner's choice makes
something happen on screen ("date sahi chuni to ... sar ud gaya"); then the text explains what happened. Every student
question gets at least one stage, so every question of the chapter is cleared by playing.

The maker writes one stage per question: an SVG scene with named parts and one to five rounds. Each round uses one
mechanic; every option carries actions on the scene's parts (show, move, grow, fall, draw ...) and a feedback line, so
right and wrong choices both visibly do something. Code checks all of it and sends the exact problems back; the generic
game player (``studio_game_player.html``) plays any stage of any subject.
"""
from __future__ import annotations

import json

from .studio import MECHANICS, SOURCE_WORDS, ask
from .studio_film import svg_ids, svg_problems

N = {"type": "number"}
S = {"type": "string"}
DOES = ("show", "hide", "move", "fly", "fall", "grow", "shrink", "glow", "pulse", "shake", "color", "draw")
CHOOSE = ("choose_and_see", "predict_then_run", "slider_cause_effect")
DRAG = ("drag_to_target", "assemble_parts")
ORDER = ("build_sequence", "route_flow")
SORT = ("sort_groups",)
assert set(CHOOSE + DRAG + ORDER + SORT) == set(MECHANICS)
MAX_ROUNDS_PER_STAGE = 5


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


ACTION = _obj({"target": S, "do": {"type": "string", "enum": list(DOES)}, "x": N, "y": N, "scale": N, "color": S, "ms": N})
SCHEMA = _obj({
    "title": S, "intro": S, "scene_svg": S, "start_hidden": _arr(S),
    "rounds": _arr(_obj({
        "id": S, "mechanic": {"type": "string", "enum": list(MECHANICS)}, "covers": _arr({"type": "integer"}),
        "prompt": S, "groups": _arr(S),
        "options": _arr(_obj({"label": S, "correct": {"type": "boolean"}, "group": S, "order": {"type": "integer"},
                              "target": S, "feedback": S, "actions": _arr(ACTION)})),
        "success_actions": _arr(ACTION), "explain": S,
    })),
})

INSTRUCTIONS = """You are BIE's game designer and teacher. Make ONE revision game stage for ONE student question of a
{course} chapter. The learner plays it after watching the films. Learner-facing language: {language} (Navin's natural spoken
Hinglish in Roman script).

The heart of a BIE game: the learner's choice makes something happen on screen, then a short text explains it. Examples
of the feeling: drop the pollen grain on the stigma and a tube grows down the style; pick the right year and the fort's
gate swings open, a wrong year and the wall cracks; push the slider to more heat and the air parcel rises and rains.
Choose mechanics that fit this subject and this question; the planned one is "{mechanic}" ({idea}).

- scene_svg: ONE clean SVG scene, viewBox "0 0 800 450", drawn with shapes and a few short labels (text elements, font-size
  14 to 28). No script, style element, image, use, foreignObject, href or on* attributes. Give an id (letters, digits, -) to
  every part an action changes and to every drop target. Parts that appear only later go in start_hidden.
- rounds: 1 to {max_rounds} rounds. round.covers lists the indexes (0-based) of the question's points the round revises;
  together the rounds cover every point. prompt tells the learner what to do in one line.
- An action: target (an id in the scene), do (show, hide, move, fly, fall, grow, shrink, glow, pulse, shake, color, draw),
  x and y (move/fly: offset in viewBox units, else 0), scale (grow/shrink: 0.3 to 3, else 1), color ("#rrggbb" for color,
  else ""), ms (150 to 3000). draw makes a path or line draw itself (a tube growing, a route forming).
- Mechanics and their options:
  choose_and_see, predict_then_run, slider_cause_effect: 2 to 4 options, exactly one correct=true; group "", order 0,
    target "". slider_cause_effect options are the slider's stops in order (low to high).
  drag_to_target, assemble_parts: 2 to 6 options are the pieces; a piece to place has correct=true and target = the id of
    its drop zone; a distractor has correct=false and target "". group "", order 0.
  build_sequence, route_flow: 3 to 7 options, all correct=true, order = the right position 1..n; group "", target "".
  sort_groups: groups lists 2 or 3 group names; 4 to 8 options, each with group = one of them, correct=true; order 0,
    target "".
  groups is [] for every mechanic except sort_groups.
- EVERY option has at least one action, so every choice visibly does something: a right one moves the story forward, a
  wrong one shows its consequence (the wall cracks, the parcel sinks). Every option has feedback: for a wrong option one
  line saying WHY it is wrong, never only "galat".
- success_actions run when the round is solved (can be []); explain (1 to 3 lines, "Kya hua") says what the learner just
  saw and the idea behind it.
- Never "the book says", never a source name, never a caution line ("assume", "illustrative").

Answer with the JSON object only."""


def messages(question: dict, *, course: str, language: str, chapter: str = "") -> list:
    stage = question.get("game_stage") or {}
    points = "\n".join(f"{i}. ({p.get('kind')}) {p.get('point')}" for i, p in enumerate(question.get("points") or []))
    user = (f"Chapter: {chapter}\nQuestion {question.get('id')}: {question.get('question')}\nCuriosity: {question.get('hook')}\n"
            f"Points to revise:\n{points}\n"
            + ("\nWhat the film taught (its takeaway lines):\n" + question["film_keys"] if question.get("film_keys") else "")
            + ("\nThe book's lines for these points:\n" + question["source_text"] if question.get("source_text") else ""))
    return [{"role": "system", "content": INSTRUCTIONS.format(
                course=course or "school", language=language or "Hinglish", mechanic=stage.get("mechanic", "choose_and_see"),
                idea=stage.get("idea", ""), max_rounds=MAX_ROUNDS_PER_STAGE)},
            {"role": "user", "content": user}]


def _texts(stage: dict):
    yield "title", stage.get("title")
    yield "intro", stage.get("intro")
    for r in stage.get("rounds") or []:
        yield f"{r.get('id')} prompt", r.get("prompt")
        yield f"{r.get('id')} explain", r.get("explain")
        for o in r.get("options") or []:
            yield f"{r.get('id')} option", o.get("label")
            yield f"{r.get('id')} feedback", o.get("feedback")


def _action_problems(where: str, actions, ids: set) -> list:
    out = []
    for a in actions or []:
        if a.get("target") not in ids:
            out.append(f"{where}: action target {a.get('target')!r} is not an id in the scene")
        if a.get("do") not in DOES:
            out.append(f"{where}: action do {a.get('do')!r} is not one of {', '.join(DOES)}")
        if not 150 <= float(a.get("ms") or 0) <= 3000:
            out.append(f"{where}: action ms must be 150 to 3000")
        if a.get("do") in ("grow", "shrink") and not 0.3 <= float(a.get("scale") or 0) <= 3:
            out.append(f"{where}: grow/shrink scale must be 0.3 to 3")
    return out


def problems(stage, question: dict) -> list:
    if not isinstance(stage, dict):
        return ["the answer is not a JSON object"]
    out = []
    svg = stage.get("scene_svg") or ""
    out += [f"scene_svg: {p}" for p in svg_problems(svg)]
    ids = svg_ids(svg)
    for hidden in stage.get("start_hidden") or []:
        if hidden not in ids:
            out.append(f"start_hidden {hidden!r} is not an id in the scene")
    rounds = stage.get("rounds") or []
    if not 1 <= len(rounds) <= MAX_ROUNDS_PER_STAGE:
        out.append(f"there are {len(rounds)} rounds; make 1 to {MAX_ROUNDS_PER_STAGE}")
    covered = set()
    for number, r in enumerate(rounds, 1):
        rid = r.get("id") or f"round {number}"
        covered.update(r.get("covers") or [])
        mech, opts, groups = r.get("mechanic"), r.get("options") or [], r.get("groups") or []
        if len((r.get("prompt") or "").strip()) < 10:
            out.append(f"{rid}: prompt (what to do) is missing")
        if len((r.get("explain") or "").strip()) < 20:
            out.append(f"{rid}: explain (Kya hua) is missing or too short")
        out += _action_problems(f"{rid} success_actions", r.get("success_actions"), ids)
        for k, o in enumerate(opts, 1):
            where = f"{rid} option {k} ({o.get('label')!r})"
            if not (o.get("label") or "").strip():
                out.append(f"{where}: label is empty")
            if len((o.get("feedback") or "").strip()) < 10:
                out.append(f"{where}: feedback must say why (at least one short line)")
            if not o.get("actions"):
                out.append(f"{where}: no action; every choice must visibly do something on screen")
            out += _action_problems(where, o.get("actions"), ids)
        right = [o for o in opts if o.get("correct")]
        if mech in CHOOSE:
            if not 2 <= len(opts) <= 4 or len(right) != 1:
                out.append(f"{rid}: {mech} needs 2 to 4 options with exactly one correct")
        elif mech in DRAG:
            if not 2 <= len(opts) <= 6 or not right:
                out.append(f"{rid}: {mech} needs 2 to 6 pieces, at least one to place")
            for o in right:
                if o.get("target") not in ids:
                    out.append(f"{rid}: piece {o.get('label')!r} has drop target {o.get('target')!r}, not an id in the scene")
        elif mech in ORDER:
            orders = sorted(int(o.get("order") or 0) for o in opts)
            if not 3 <= len(opts) <= 7 or orders != list(range(1, len(opts) + 1)):
                out.append(f"{rid}: {mech} needs 3 to 7 options with order exactly 1..n")
        elif mech in SORT:
            if not 2 <= len(groups) <= 3 or len(set(groups)) != len(groups):
                out.append(f"{rid}: sort_groups needs 2 or 3 different groups")
            if not 4 <= len(opts) <= 8:
                out.append(f"{rid}: sort_groups needs 4 to 8 items")
            used = {o.get("group") for o in opts}
            if used - set(groups):
                out.append(f"{rid}: items use groups not listed: {', '.join(sorted(map(str, used - set(groups))))}")
            if set(groups) - used:
                out.append(f"{rid}: no item goes in {', '.join(sorted(set(groups) - used))}")
        else:
            out.append(f"{rid}: mechanic {mech!r} is not one of {', '.join(MECHANICS)}")
    missing = [i for i in range(len(question.get("points") or [])) if i not in covered]
    if missing:
        out.append("no round revises the question's points " + ", ".join(map(str, missing)))
    for where, text in _texts(stage):
        if text and SOURCE_WORDS.search(text):
            out.append(f"{where}: names the source; remove it")
    return out


def write(client, model: str, question: dict, *, course: str = "", language: str = "Hinglish", chapter: str = "",
          max_rounds: int = 3) -> dict:
    record = ask(client, model, messages(question, course=course, language=language, chapter=chapter), SCHEMA,
                 lambda stage: problems(stage, question), max_rounds=max_rounds)
    record["stage"] = record.pop("answer")
    return record


def player_data(stages: list, *, plan: dict, tint: str, heroes: dict = None) -> dict:
    """The JSON the game player reads: the chapter's pillars (worlds) and one stage per question, in plan order."""
    heroes = heroes or {}
    by_q = {s["qid"]: s for s in stages if isinstance(s.get("stage"), dict)}
    worlds = []
    for pillar in plan.get("pillars") or []:
        items = []
        for q in plan.get("questions") or []:
            if q.get("pillar") == pillar.get("id") and q.get("id") in by_q:
                stage = by_q[q["id"]]["stage"]
                items.append({"qid": q["id"], "question": q.get("question"), "title": stage.get("title"),
                              "intro": stage.get("intro"), "svg": stage.get("scene_svg"),
                              "hidden": stage.get("start_hidden") or [], "rounds": stage.get("rounds") or [],
                              "hero": heroes.get(q["id"], "")})
        if items:
            worlds.append({"id": pillar.get("id"), "title": pillar.get("title"), "line": pillar.get("line"), "stages": items})
    return {"chapter": plan.get("chapter_title", ""), "big": plan.get("big_question", ""), "tint": tint, "worlds": worlds}


def html(data: dict, template: str) -> str:
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("/*__GAME__*/null", blob, 1)
