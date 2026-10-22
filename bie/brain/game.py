"""Section 6 · Chapter game design: learning itself is the game.

From the chapter map only (no drift), BIE's game designer plans one game per chapter: a small world
whose missions make the student perform the content. The mechanic follows the content type (run a
process, choose as a character in history, build a structure, predict with sliders, change a map, judge
a case); every wrong move shows what breaks and why. Every key item of the chapter is played in some
mission. A mission that is really a multiple-choice question is rejected by BIE's code check. The
design is data; BIE's game builder (next step) turns it into a playable phone game.

Outputs (``run_game_design``): ``game_design.json`` and ``GAME.md``.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .runner import NOTES_SCHEMA, Step
from .understanding import Course

SECTION = "game"
VERSION = "game-design/1"
MECHANICS = ["run_process", "choose_as_character", "build_structure", "predict_with_sliders", "change_the_map", "judge_the_case",
             "assemble_sequence", "diagnose_and_fix"]
INTERACTIONS = ["drag", "tap", "hold", "slider", "draw_path", "rotate", "choose_action", "connect"]
MISSION_SCHEMA = obj({
    "mission_id": S,
    "title": S,
    "item_ids": arr(S),
    "content_type": S,
    "mechanic": {"type": "string", "enum": MECHANICS},
    "player_role": S,
    "goal": S,
    "scene": S,
    "interactions": arr({"type": "string", "enum": INTERACTIONS}),
    "steps": arr(obj({"step_id": S, "player_does": S, "correct_when": S, "wrong_moves": arr(obj({
        "move": S, "what_breaks": S, "why": S, "item_ids": arr(S)}))})),
    "win": S,
    "feedback_on_win": S,
    "replay_twist": S,
    "assets_needed": arr(S),
})
DESIGN_SCHEMA = obj({
    "notes": NOTES_SCHEMA,
    "game_title": S,
    "world": S,
    "missions": arr(MISSION_SCHEMA),
    "revision_loop": S,
})
PATCH_SCHEMA = obj({"notes": NOTES_SCHEMA, "replace_missions": arr(MISSION_SCHEMA), "remove_mission_ids": arr(S)})
PATCH_HINT = ("Reply with a patch, not the whole game: replace_missions = complete corrected or new missions (same mission_id "
              "replaces), remove_mission_ids = missions to delete.")
REVIEW_SCHEMA = obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": arr(obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": arr(obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})
QUIZ_WORDS = ("which of the following", "choose the correct option", "select the correct answer", "multiple choice", "mcq",
              "pick the right option", "option a", "options:")

ROLE = """You are BIE's game designer for one chapter of {subject} for {learners} ({exam}). Navin's rule: "padhai hi game hai": the
student learns by doing the content, the way moving tectonic plates teaches plate tectonics or a history timeline breaks on a wrong
choice. Design one chapter game from BIE's chapter map only; BIE's game builder turns your design into a playable phone game.

Course: "{title}" · learner language: {language} (titles, goals and feedback in {language}; the book's English terms stay).

Navin's rules for this section (follow every one):
{rules}

How to fill the JSON:
- notes: brief notes for the reviewer: what the game is about, the key decisions with a reason each, what is uncertain.
- game_title and world: the setting that ties the missions together (the student's role and where they are).
- missions: in teaching order. mission_id "m1", "m2" ...; item_ids = the chapter-map items this mission makes the student play
  (every teachable item must appear in some mission); content_type of those items; mechanic from the content type (S6-03);
  player_role, goal, scene (what is on screen); interactions (drag, tap, hold, slider, draw_path, rotate, choose_action, connect);
  steps = what the player does, when it is correct, and the wrong moves with what visibly breaks, why (the science or history behind
  it) and the item_ids that wrong move teaches; win and feedback_on_win; replay_twist = how a replay changes so the student must
  really understand; assets_needed = the visuals the builder must find or draw.
- revision_loop: how missions the student failed come back later.
A mission must never be a question with options to pick. Reply with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the game design of one chapter ({subject}, {learners}, {exam}). Judge it as
Navin would: is the learning itself the game, or is it a quiz in disguise?

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

You also get the maker's notes. Report every problem with where it is (mission or step id), what is wrong, the fix and a severity
("blocking" or "minor", see R-01): a hidden quiz, a mechanic that does not fit the content type, a wrong move that does not show
what breaks and why, a key item not played, a fact or story that drifts away from the chapter, a mission a phone game could not
build. verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


def _chapter_input(chapter):
    m = chapter.get("map") or {}
    items = [{"item_id": iid, "page": i["page"], "kind": i["kind"], "content_type": i["content_type"], "content": i["content"],
              "teachable": i["teachable"]} for iid, i in chapter["items"].items()]
    return {"concepts": [{k: c[k] for k in ("concept_id", "name", "content_type", "core_explanation", "item_ids")}
                         for c in m.get("concepts", [])],
            "relations": m.get("relations", []), "teaching_order": m.get("teaching_order", []), "items": items}


def check_design(value: dict, chapter: dict) -> list:
    problems = []
    known = chapter["items"]
    teachable = {iid for iid, i in known.items() if i.get("teachable") and i["kind"] not in ("question", "answer_option")}
    played = set()
    ids = [m["mission_id"] for m in value.get("missions") or []]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"mission_id {dup!r} is used more than once")
    for mission in value.get("missions") or []:
        mid = mission["mission_id"]
        for iid in mission["item_ids"]:
            if iid not in known:
                problems.append(f"mission {mid}: unknown item {iid!r} (S6-02)")
            played.add(iid)
        if not mission["steps"]:
            problems.append(f"mission {mid}: has no steps")
        if not mission["interactions"]:
            problems.append(f"mission {mid}: has no interaction")
        text = " ".join([mission["goal"], mission["scene"]] + [s["player_does"] for s in mission["steps"]]).lower()
        if any(word in text for word in QUIZ_WORDS):
            problems.append(f"mission {mid}: reads like a multiple-choice question; make the student do the content (S6-01)")
        if not any(s["wrong_moves"] for s in mission["steps"]):
            problems.append(f"mission {mid}: no wrong move shows what breaks and why (S6-03)")
        for step in mission["steps"]:
            for wrong in step["wrong_moves"]:
                if not wrong["what_breaks"].strip() or not wrong["why"].strip():
                    problems.append(f"mission {mid}, step {step['step_id']}: a wrong move needs what breaks and why (S6-03)")
                for iid in wrong["item_ids"]:
                    if iid not in known:
                        problems.append(f"mission {mid}, step {step['step_id']}: unknown item {iid!r}")
    missing = sorted(teachable - played)
    if missing:
        problems.append(f"{len(missing)} teachable items are played in no mission (S6-02): {', '.join(missing[:40])}")
    if not value.get("missions"):
        problems.append("the game has no missions")
    return problems


def apply_patch(previous: dict, patch: dict) -> dict:
    replace = {m["mission_id"]: m for m in patch.get("replace_missions") or []}
    removed = set(patch.get("remove_mission_ids") or [])
    missions = [replace.pop(m["mission_id"], m) for m in previous.get("missions") or [] if m["mission_id"] not in removed]
    missions.extend(replace.values())
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), missions=missions)


def design_step(course: Course, chapter, *, rulebook, max_rounds=3) -> Step:
    text = json.dumps(_chapter_input(chapter), ensure_ascii=False)
    system = fmt(ROLE, course, rules=rulebook.instructions(SECTION))
    user = f"Chapter: {course.title}.\nBIE's chapter map (JSON):\n{text}\n\nReply with the game design JSON."
    review_system = fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(), checklist=checklist_text(rulebook, SECTION))

    def review_user(value):
        return (f"Chapter: {course.title}.\nBIE's chapter map (JSON):\n{text}\n\n"
                f"The game design to review (JSON):\n{json.dumps(value, ensure_ascii=False)}")

    return Step(section=SECTION, unit="design", instructions_version=VERSION, system=system, user=user, schema=DESIGN_SCHEMA,
                check=lambda value: check_design(value, chapter), review_system=review_system, review_user=review_user,
                review_schema=REVIEW_SCHEMA, review_problems=review_problems, patch_schema=PATCH_SCHEMA, apply_patch=apply_patch,
                patch_hint=PATCH_HINT, max_rounds=max_rounds)


def run_game_design(chapter: dict, course: Course, runner, out_dir, *, max_rounds: int = 3):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = runner.run(design_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds))
    value = result.output or {}
    design = {
        "schema": "bie.brain.game-design/1",
        "course": chapter["course"],
        "rulebook_version": runner.rulebook.version,
        "maker_route": runner.maker,
        "reviewer_route": runner.reviewer,
        "reviewer_independence": runner.independence,
        "status": result.status,
        "rounds": len(result.rounds),
        "game": {k: v for k, v in value.items() if k != "notes"},
        "last_problems": (result.rounds[-1].get("code_problems") or []) + (result.rounds[-1].get("review_problems") or [])
        if result.rounds and not result.passed else [],
        "record": Path(result.record_path).name if result.record_path else None,
        "cost_usd": result.cost_usd,
    }
    missions = value.get("missions") or []
    design["quality"] = {"missions": len(missions), "mechanics": sorted({m["mechanic"] for m in missions}),
                         "wrong_moves": sum(len(s["wrong_moves"]) for m in missions for s in m["steps"]),
                         "items_played": len({i for m in missions for i in m["item_ids"]}), "passed": result.passed,
                         "cost_usd": result.cost_usd}
    (out / "game_design.json").write_text(json.dumps(design, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "GAME.md").write_text(render_markdown(design), encoding="utf-8")
    return design


def render_markdown(design: dict) -> str:
    g, q = design["game"], design["quality"]
    lines = [f"# Game design · {design['course']['title']} · {design['status']} after {design['rounds']} round(s)", "",
             f"**{g.get('game_title', '')}** · {g.get('world', '')}", "",
             f"{q['missions']} missions ({', '.join(q['mechanics'])}), {q['wrong_moves']} teaching wrong moves, "
             f"{q['items_played']} items played; estimated cost ${q['cost_usd']:.4f}.", ""]
    if design["last_problems"]:
        lines += ["Open problems:", ""] + [f"- {x}" for x in design["last_problems"][:15]] + [""]
    for m in g.get("missions", []):
        lines += [f"## {m['mission_id']} · {m['title']} · {m['mechanic']}", "",
                  f"- Role: {m['player_role']}", f"- Goal: {m['goal']}", f"- Scene: {m['scene']}",
                  f"- Interactions: {', '.join(m['interactions'])}"]
        for step in m["steps"]:
            lines.append(f"- **{step['step_id']}** {step['player_does']} → correct when {step['correct_when']}")
            for w in step["wrong_moves"]:
                lines.append(f"  - wrong: {w['move']} → {w['what_breaks']} (why: {w['why']})")
        lines += [f"- Win: {m['win']} · {m['feedback_on_win']}", f"- Replay twist: {m['replay_twist']}", ""]
    lines += ["## Revision loop", "", g.get("revision_loop", ""), ""]
    return "\n".join(lines)
