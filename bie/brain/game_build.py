"""Section 6 · Game builder: the chapter game design becomes playable data for BIE's game runtime.

For every mission of the design, the AI writes stages for one of the runtime's engines (drag parts onto
places, choose as a character, predict with a slider), with the wrong moves and what they break, the way the
designer planned. BIE's code checks that every stage can be played and won, that every wrong move teaches,
that choices appear only where the mechanic is a real choice, and that the mission's items are all played.
A bot then plays each mission in a phone-sized browser (one wrong move, then the right ones); the independent
reviewer judges the screenshots. The passed missions become one self-contained HTML game.

Outputs (``run_game_build``): ``GAME.html``, ``game.json``, screenshots under ``game_shots/``.

A picture on a game board must come from BIE's asset library: before GAME.html is written, the lesson licence gate
(``bie.toolbox.licence``) checks every board picture; one it cannot read, or one that is refused or waits for Navin,
stops the game with the reason. The game's credits come from the same records.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .game_runtime import render_game_html
from .runner import NOTES_SCHEMA, Step
from .understanding import Course

SECTION = "game"
VERSION = "game-build/1"
NUM = {"type": "number"}
BOX = obj({"x": NUM, "y": NUM, "w": NUM, "h": NUM})
EFFECTS = ["glow", "flow", "grow", "break", "fade", "shake"]
CHOICE_MECHANICS = {"choose_as_character", "judge_the_case"}
STAGE_SCHEMA = obj({
    "stage_id": S, "kind": {"type": "string", "enum": ["drag", "branch", "slider"]}, "instruction": S,
    "tokens": arr(obj({"id": S, "label": S})), "targets": arr(obj({"id": S, "label": S, "box": BOX})),
    "rules": arr(obj({"token": S, "target": S, "correct": {"type": "boolean"}, "feedback": S,
                      "effect": {"type": "string", "enum": EFFECTS}})),
    "ordered": {"type": "boolean"},
    "situation": S, "choices": arr(obj({"label": S, "correct": {"type": "boolean"}, "feedback": S})),
    "slider": obj({"label": S, "unit": S, "min": NUM, "max": NUM, "step": NUM, "answer": NUM, "tolerance": NUM,
                   "predict_prompt": S, "reveal_label": S, "data": arr(obj({"x": NUM, "y": NUM}))}),
    "feedback_close": S, "feedback_far": S, "item_ids": arr(S),
})
MISSION_SCHEMA = obj({"notes": NOTES_SCHEMA, "title": S, "intro": S, "stages": arr(STAGE_SCHEMA), "win_text": S,
                      "replay_twist": {"type": "string", "enum": ["shuffle_tokens", "new_order", "none"]}})
PATCH_SCHEMA = obj({"notes": NOTES_SCHEMA, "replace_stages": arr(STAGE_SCHEMA), "remove_stage_ids": arr(S)})
PATCH_HINT = "Reply with a patch: replace_stages = complete corrected or new stages (same stage_id replaces), remove_stage_ids."
REVIEW_SCHEMA = obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": arr(obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": arr(obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})

ROLE = """You are BIE's game builder for one mission of a {subject} chapter game for {learners} ({exam}). The game designer planned
the mission; you write it as data for BIE's game runtime, which has three engines:
- drag: tokens (parts, steps, rule cards) the student drags onto targets (places on a board; box = x, y, w, h as fractions of the
  board, or all zero to let BIE lay them out). Every token gets rules: for its right target (correct, feedback = what happens and why,
  effect glow/flow/grow) and for tempting wrong targets (feedback = what breaks and why, effect break/fade/shake). ordered = true when
  the steps must happen in sequence (a process).
- branch: the student is a character: situation, choices; a wrong choice breaks the timeline (feedback = what went wrong and why).
  Use branch only for real choices of a character or a judge, never as a quiz.
- slider: the student predicts first: slider (label, unit, min, max, step, answer, tolerance, predict_prompt, reveal_label, data =
  points of the real relationship), feedback_close and feedback_far explain the science.
Fill unused fields with empty values. item_ids per stage = the chapter-map items that stage makes the student play.

Navin's rules for this section (follow every one):
{rules}

Write title, intro, instructions, feedback and win_text in {language} with the book's English terms. Reply with the JSON object only:
notes (brief), title, intro, stages, win_text, replay_twist."""

REVIEW_ROLE = """You are BIE's independent reviewer for one mission of a chapter game ({subject}, {learners}, {exam}). You see the
mission data, the designer's plan and screenshots from BIE's bot playing it on a phone screen (a wrong move first, then the right
ones). Judge it as Navin would: is the learning itself the game, does every wrong move show what breaks and why, is it clear and
playable on a phone, is every fact right at this level?

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

Report every problem with where it is (stage id), what is wrong, the fix and a severity ("blocking" or "minor", see R-01).
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


def check_mission(value: dict, mission: dict, known_items: set) -> list:
    problems = []
    ids = [s["stage_id"] for s in value.get("stages") or []]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"stage_id {dup!r} is used more than once")
    played = set()
    for s in value.get("stages") or []:
        sid, kind = s["stage_id"], s["kind"]
        played.update(s["item_ids"])
        for iid in s["item_ids"]:
            if iid not in known_items:
                problems.append(f"stage {sid}: unknown item {iid!r}")
        if not s["instruction"].strip():
            problems.append(f"stage {sid}: needs an instruction")
        if kind == "drag":
            tokens, targets = {t["id"] for t in s["tokens"]}, {t["id"] for t in s["targets"]}
            if len(tokens) < 2 or not targets:
                problems.append(f"stage {sid}: a drag stage needs at least two tokens and a target")
            for r in s["rules"]:
                if r["token"] not in tokens or r["target"] not in targets:
                    problems.append(f"stage {sid}: rule {r['token']}→{r['target']} uses an unknown token or target")
                if not r["feedback"].strip():
                    problems.append(f"stage {sid}: rule {r['token']}→{r['target']} needs feedback (S6-03)")
            if not any(r["correct"] for r in s["rules"]):
                problems.append(f"stage {sid}: no token has a correct target, so it cannot be won")
            if not any(not r["correct"] for r in s["rules"]):
                problems.append(f"stage {sid}: add tempting wrong moves that show what breaks and why (S6-03)")
            for t in sorted(tokens - {r["token"] for r in s["rules"]}):
                problems.append(f"stage {sid}: token {t!r} has no rule")
            for t in s["targets"]:
                b = t["box"]
                if (b["w"] or b["h"]) and not (0 <= b["x"] <= 1 and 0 <= b["y"] <= 1 and 0 < b["w"] and 0 < b["h"]
                                               and b["x"] + b["w"] <= 1.001 and b["y"] + b["h"] <= 1.001):
                    problems.append(f"stage {sid}: target {t['id']!r} box must lie inside the board")
        elif kind == "branch":
            if mission["mechanic"] not in CHOICE_MECHANICS:
                problems.append(f"stage {sid}: a {mission['mechanic']} mission must be played by doing (drag or slider), not by "
                                "choosing an option (S6-01)")
            if not s["situation"].strip() or len(s["choices"]) < 2:
                problems.append(f"stage {sid}: a branch needs a situation and at least two choices")
            if not any(c["correct"] for c in s["choices"]):
                problems.append(f"stage {sid}: no choice moves the story on")
            for c in s["choices"]:
                if not c["correct"] and not c["feedback"].strip():
                    problems.append(f"stage {sid}: wrong choice {c['label']!r} needs what breaks and why (S6-03)")
        elif kind == "slider":
            sl = s["slider"]
            if not sl["min"] < sl["max"] or not sl["min"] <= sl["answer"] <= sl["max"] or sl["step"] <= 0:
                problems.append(f"stage {sid}: the slider needs min < max, a step and an answer inside the range")
            if not sl["predict_prompt"].strip() or not s["feedback_close"].strip() or not s["feedback_far"].strip():
                problems.append(f"stage {sid}: the slider needs a prediction prompt and feedback for close and far guesses")
    missing = sorted(set(mission["item_ids"]) - played)
    if missing:
        problems.append(f"{len(missing)} items of this mission are played in no stage (S6-02): {', '.join(missing[:30])}")
    if not value.get("stages"):
        problems.append("the mission has no stages")
    return problems


def apply_patch(previous: dict, patch: dict) -> dict:
    replace = {s["stage_id"]: s for s in patch.get("replace_stages") or []}
    removed = set(patch.get("remove_stage_ids") or [])
    stages = [replace.pop(s["stage_id"], s) for s in previous.get("stages") or [] if s["stage_id"] not in removed]
    stages.extend(replace.values())
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), stages=stages)


def mission_game(design: dict, mission: dict, value: dict) -> dict:
    return {"id": "preview", "title": design.get("game_title", ""), "world": design.get("world", ""),
            "missions": [dict(value, mission_id=mission["mission_id"], stages=value.get("stages") or [])]}


def bot_screenshots(game: dict, *, width: int = 390, height: int = 844, limit: int = 6, out_dir=None):
    """Screenshots of BIE's bot playing the first mission: the start, after one wrong move, and the end."""
    script = Path(__file__).resolve().parent / "game_bot.mjs"
    with tempfile.TemporaryDirectory(prefix="bie-game-") as tmp:
        page = Path(tmp) / "game.html"
        page.write_text(render_game_html(game), encoding="utf-8")
        env = dict(os.environ)
        if "NODE_PATH" not in env:
            try:
                env["NODE_PATH"] = subprocess.check_output(["npm", "root", "-g"], text=True).strip()
            except (OSError, subprocess.CalledProcessError):
                pass
        try:
            run = subprocess.run(["node", str(script), str(page), tmp, str(width), str(height), str(limit)], capture_output=True,
                                 text=True, env=env, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [], f"the bot could not run: {exc}"
        if run.returncode != 0:
            return [], (run.stderr or run.stdout)[-600:]
        result = json.loads(run.stdout.strip().splitlines()[-1])
        shots = []
        for name in result.get("shots", []):
            data = (Path(tmp) / name).read_bytes()
            shots.append((name, data))
            if out_dir:
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                (Path(out_dir) / name).write_bytes(data)
        return shots, json.dumps({k: v for k, v in result.items() if k != "shots"}, ensure_ascii=False)


def mission_step(course: Course, chapter: dict, design: dict, mission: dict, *, rulebook, shots_dir=None, max_rounds=3) -> Step:
    items = [{"item_id": i, "content": chapter["items"][i]["content"], "content_type": chapter["items"][i]["content_type"]}
             for i in mission["item_ids"] if i in chapter["items"]]
    payload = json.dumps({"game": {k: design.get(k) for k in ("game_title", "world")}, "mission": mission, "items": items},
                         ensure_ascii=False)
    user = f"Chapter: {course.title}. Mission {mission['mission_id']}.\nThe designer's plan and its items (JSON):\n{payload}\n\nReply with the mission data JSON."
    review_system = fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(), checklist=checklist_text(rulebook, SECTION))
    known = set(chapter["items"])

    def review_user(value):
        shots, log = bot_screenshots(mission_game(design, mission, value),
                                     out_dir=Path(shots_dir) / mission["mission_id"] if shots_dir else None)
        parts = [{"type": "text", "text": f"The designer's plan and its items (JSON):\n{payload}\n\nThe mission data (JSON):\n"
                                          f"{json.dumps(value, ensure_ascii=False)}\n\nBot playtest log: {log}"}]
        for name, data in shots:
            parts += [{"type": "text", "text": f"Screenshot {name}:"},
                      {"type": "image", "media_type": "image/jpeg", "data": base64.b64encode(data).decode("ascii")}]
        return parts

    return Step(section=SECTION, unit=f"build-{mission['mission_id']}", instructions_version=VERSION,
                system=fmt(ROLE, course, rules=rulebook.instructions(SECTION)), user=user, schema=MISSION_SCHEMA,
                check=lambda value: check_mission(value, mission, known), review_system=review_system, review_user=review_user,
                review_schema=REVIEW_SCHEMA, review_problems=review_problems, patch_schema=PATCH_SCHEMA, apply_patch=apply_patch,
                patch_hint=PATCH_HINT, max_rounds=max_rounds)


def game_pictures(game: dict, library=None) -> tuple:
    """(asset ids of the board pictures, licence problems): a picture without a library record has no licence to read."""
    ids, problems = [], []
    for m in game.get("missions") or []:
        for n, s in enumerate(m.get("stages") or []):
            bg = s.get("background") or {}
            if not bg.get("src"):
                continue
            if library is None or not bg.get("asset_id"):
                problems.append(f"mission {m.get('mission_id')} stage {n + 1}: picture {str(bg['src'])[:80]} has no asset-library record, "
                                "so its licence cannot be read")
            elif bg["asset_id"] not in ids:
                ids.append(bg["asset_id"])
    if library is not None and ids:
        problems += library.lesson_check(ids)
    return ids, problems


def run_game_build(chapter: dict, design: dict, course: Course, runner, out_dir, *, workers: int = 4, max_rounds: int = 3,
                   library=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    game_plan = design.get("game") or {}
    missions = game_plan.get("missions") or []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(lambda m: runner.run(mission_step(course, chapter, game_plan, m, rulebook=runner.rulebook,
                                                                  shots_dir=out / "game_shots", max_rounds=max_rounds)), missions))
    played = [dict(r.output, mission_id=m["mission_id"]) for m, r in zip(missions, results) if r.output]
    game = {"id": (chapter.get("source_sha256") or "chapter")[:12], "title": game_plan.get("game_title", ""),
            "world": game_plan.get("world", ""), "missions": [{k: v for k, v in m.items() if k != "notes"} for m in played]}
    pictures, licence_problems = game_pictures(game, library)
    if pictures and not licence_problems:
        game["credits"] = library.credits(pictures)
    (out / "game.json").write_text(json.dumps(game, ensure_ascii=False, indent=1), encoding="utf-8")
    if not licence_problems:                    # the lesson licence gate: a game with a refused picture is not written
        (out / "GAME.html").write_text(render_game_html(game), encoding="utf-8")
    summary = {"missions": len(missions), "missions_passed": sum(1 for r in results if r.passed),
               "status": "stopped_by_licence" if licence_problems else "written", "licence_problems": licence_problems,
               "stages": sum(len(m.get("stages") or []) for m in played),
               "engines": sorted({s["kind"] for m in played for s in m.get("stages") or []}),
               "cost_usd": round(sum(r.cost_usd for r in results), 6),
               "open_problems": {m["mission_id"]: (r.rounds[-1].get("code_problems") or []) + (r.rounds[-1].get("review_problems") or [])
                                 for m, r in zip(missions, results) if r.rounds and not r.passed}}
    return summary
