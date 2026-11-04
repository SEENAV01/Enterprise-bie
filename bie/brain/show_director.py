"""Phase 1, part C: BIE's director writes scene plans in the plan language (agreement of 3 November 2026).

For every passed video of the lesson plan, the maker (Codex on the VM, under the cost guard) writes one
``bie.scene-plan/1``: scenes over the video's narration lines, steps from ``plan_vocab.json``, every time a cue
word. The code check is the compiler itself (``bie/brain/video/showplan.py``): a plan that misses a cue word, a
saancha parameter, the text floor, the subtitle strip or the no-text-alone rule comes back with every problem named
exactly, and the maker patches. The Money v2 gold plan is the example in the prompt (Claude's demo, not BIE
output). Outputs per video: ``plans/<video>.plan.json`` and the compiled ``video_specs/<video>.json``.
"""
from __future__ import annotations

import json
from pathlib import Path

from .common import S, arr, fmt, obj
from .runner import NOTES_SCHEMA, Step
from .understanding import Course
from bie.brain import formats, saanche
from bie.brain.video import narration, showplan

SECTION = "showplan"
VERSION = "show-plan/1"

PATCH_SCHEMA = obj({"notes": NOTES_SCHEMA, "replace_scenes": arr({"type": "object"}), "remove_scene_ids": arr(S)})
PATCH_HINT = ("Reply with a patch: replace_scenes = complete corrected or new scenes (same id replaces), "
              "remove_scene_ids = scenes to delete. Fix every named problem.")

ROLE = """You are BIE's showing director for one video of a {subject} chapter for {learners}. The narration is written and timed;
you write the scene plan (bie.scene-plan/1) that SHOWS it: for every line, the thing said is on screen and the action said
happens on the word it is said (W-01: show, never say "the book says").

The plan language (its vocabulary is the JSON below; the compiler refuses anything else, naming the step and field):
- scenes cover the video's lines in order, each scene a place (bg) and a list of steps;
- a place is a bg name, or a world item (draw "world", x 960, y 540, z 1) when the place itself must change on a word
  (the vault opens, the market board turns down, night falls, the stalls get signs); a world is the place, never the
  thing being taught, so it does not count as showing the thing said;
- steps are people (person + pose/expr/hold/walk/face/give/shake/nod), things (item: a saancha with parameters, a fetched
  asset, or a mini person), texts (>= 36px on screen after the camera), marks, arrows, bubbles, rects, glows and cameras;
- every time is a cue into the narration: {{"line": "...", "word": "..."}} or {{"line": "...", "edge": "start"|"end"}},
  with "plus" seconds to nudge; write a bare number only when no word fits.
Hard rules the compiler enforces: every cue word must be in that line's subtitle; every saancha parameter must fit the
manifest; no text under 36px on screen; nothing in the subtitle strip; texts never cover each other; never 2 seconds with
only text on screen - the thing being said stays visible; every line in exactly one scene.
Style, from the gold example below: few words on screen, things and people act out the story, give/walk/hold on the spoken
word, a camera move only when it helps, marks (cross/tick) for judgements, bubbles for thoughts.

VOCABULARY:
{vocab}

SAANCHE (drawings you may use with their parameters; manifest excerpt):
{saanche}

GOLD EXAMPLE (one scene of the Money v2 demo's plan - imitate the craft, not the content):
{example}

{rules}"""


def library_text(limit: int = 120, text: str = "") -> str:
    """The saanche the director may use, with their parameters. All of them while the manifest fits ``limit``; past
    that, the ones whose words the narration ``text`` uses come first (a world, a vault, a podium for the lesson that
    speaks of them), then the rest in manifest order up to ``limit``."""
    names = saanche.names()
    if len(names) > limit:
        hits = [r["name"] for r in saanche.search(text, limit=limit, icons_limit=0)] if text else []
        chosen = set((hits + [n for n in names if n not in hits])[:limit])
        names = [n for n in names if n in chosen]
    rows = []
    for name in names:
        entry = saanche.get(name)
        params = ", ".join(f"{k}:{v['type']}" + (f"[{'|'.join(v['choices'])}]" if v["type"] == "choice" else "")
                           for k, v in entry["params"].items())
        rows.append(f"- {name} ({entry['anchor']}): {entry['what']} · p = {{{params}}}")
    return "\n".join(rows)


def gold_example() -> str:
    from bie.brain.gold.money_v2 import gold_plan
    plan, _ = gold_plan()
    scene = next(s for s in plan["scenes"] if s["id"] == "B")       # the haat trade: people, things, give, camera
    return json.dumps(scene, ensure_ascii=False)


def payload_of(video: dict, T: narration.Timeline, assets: dict | None) -> dict:
    lines = []
    for lid in T.line_ids():
        line = T.L(lid)
        lines.append({"id": lid, "scene": line["scene"], "sub": line["sub"], "covers": line.get("covers") or [],
                      "t0": round(line["t0"], 2), "t1": round(line["t1"], 2)})
    return {"video_id": video["video_id"], "title": video.get("title", ""), "lines": lines,
            "assets": sorted(assets or {}), "parts": [sc["id"] for sc in T.script]}


def check_plan(value: dict, T: narration.Timeline) -> list:
    problems = [p for p in formats.problems("scene_plan", value)]
    if problems:
        return problems
    try:
        showplan.compile_plan(json.loads(json.dumps(value)), T, width=1920, height=1080)
    except showplan.PlanProblems as exc:
        return list(exc.problems)[:40]
    except Exception as exc:                                        # a step so wrong the compiler broke: name it
        return [f"the compiler failed on this plan: {exc}"]
    return []


def apply_patch(previous: dict, patch: dict) -> dict:
    scenes = {s.get("id"): s for s in previous.get("scenes") or []}
    for s in patch.get("replace_scenes") or []:
        scenes[s.get("id")] = s
    for sid in patch.get("remove_scene_ids") or []:
        scenes.pop(sid, None)
    return {"schema": "bie.scene-plan/1", "video": previous.get("video", ""), "scenes": list(scenes.values())}


def video_step(course: Course, video: dict, T: narration.Timeline, *, rulebook, assets: dict | None = None,
               max_rounds: int = 4, start: dict | None = None) -> Step:
    system = fmt(ROLE, course, vocab=json.dumps(showplan.vocab(), ensure_ascii=False),
                 saanche=library_text(text=" ".join(T.L(lid)["sub"] for lid in T.line_ids())), example=gold_example(), rules=rulebook.instructions(SECTION))
    user = (f"Video {video['video_id']}: {video.get('title', '')}.\n"
            f"The narration (JSON; cue words come from each line's sub):\n"
            f"{json.dumps(payload_of(video, T, assets), ensure_ascii=False)}\n\n"
            f"Reply with the scene plan JSON (schema bie.scene-plan/1).")
    return Step(section=SECTION, unit=video["video_id"], instructions_version=VERSION, system=system, user=user,
                schema=formats.SCENE_PLAN, check=lambda value: check_plan(value, T),
                patch_schema=PATCH_SCHEMA, patch_hint=PATCH_HINT, apply_patch=apply_patch,
                max_rounds=max_rounds, start=start)


def run_show_director(lesson: dict, course: Course, runner, out_dir, *, videos: list | None = None,
                      assets: dict | None = None, durations: dict | None = None, max_rounds: int = 4) -> dict:
    """Scene plans for every passed video of the lesson (or ``videos``): the AI writes, the compiler judges."""
    out = Path(out_dir)
    (out / "plans").mkdir(parents=True, exist_ok=True)
    (out / "video_specs").mkdir(exist_ok=True)
    rows = []
    for video in lesson.get("videos") or []:
        if video.get("status") != "passed" or (videos and video["video_id"] not in videos):
            continue
        script = narration.script_of(video)
        if not script:
            rows.append({"video_id": video["video_id"], "status": "failed", "problem": "no narration beats"})
            continue
        T = narration.Timeline(script, durations)
        for lid in T.line_ids():                                   # covers travel with the line for the payload
            T.L(lid).setdefault("covers", next((l["covers"] for sc in script for l in sc["lines"] if l["id"] == lid), []))
        result = runner.run(video_step(course, video, T, rulebook=runner.rulebook, assets=assets, max_rounds=max_rounds))
        row = {"video_id": video["video_id"], "status": result.status, "rounds": len(result.rounds),
               "cost_usd": result.cost_usd}
        if result.status == "passed" and result.output:
            plan = dict(result.output, video=video["video_id"])
            T2 = narration.Timeline(narration.script_of(video), durations)
            spec = showplan.compile_plan(json.loads(json.dumps(plan)), T2, width=1920, height=1080, assets=assets)
            formats.check("scene_plan", plan, where=f"plans/{video['video_id']}.plan.json")
            (out / "plans" / f"{video['video_id']}.plan.json").write_text(
                json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
            (out / "video_specs" / f"{video['video_id']}.json").write_text(
                json.dumps(spec, ensure_ascii=False), encoding="utf-8")
            row.update(scenes=len(spec["scenes"]), els=sum(len(s["els"]) for s in spec["scenes"]),
                       seconds=spec["duration"])
        rows.append(row)
    summary = {"schema": f"bie.brain.{SECTION}/1", "videos": rows,
               "passed": sum(1 for r in rows if r["status"] == "passed"),
               "first_try": sum(1 for r in rows if r["status"] == "passed" and r["rounds"] == 1)}
    (out / "showplan.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# Scene plans ({summary['passed']}/{len(rows)} passed, {summary['first_try']} first try)", ""]
    for r in rows:
        lines.append(f"- {r['video_id']}: {r['status']}, {r.get('rounds', 0)} round(s)"
                     + (f", {r['scenes']} scenes, {r['els']} elements, {r['seconds']:.0f} s" if r.get("scenes") else "")
                     + (f" — {r['problem']}" if r.get("problem") else ""))
    (out / "SHOWPLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
