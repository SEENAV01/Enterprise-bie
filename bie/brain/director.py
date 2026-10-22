"""Section 3 · Director.

For each video of the lesson, BIE's director turns the teacher script into scenes: for every topic it
first answers the universal questions (what process, how it works, when or in what sequence, the
conditions and atmosphere, who or what changes), applies the subject's own style, shows numbers to
scale (visual mathematics), describes every visual at anatomy-level detail, ties every camera move and
action to the exact spoken word, and marks pause questions and tap-to-explore moments for the
interactive player. Every step runs through ``SectionRunner`` with code checks and an independent
reviewer.

Outputs (``run_director``): ``director.json`` (what the visual section consumes), ``DIRECTOR.md``.
"""
from __future__ import annotations

import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .common import SEVERITY, S, arr, checklist_text, fmt, obj, review_problems
from .lesson import question_ids, video_scope
from .runner import NOTES_SCHEMA, Step
from .understanding import Course

SECTION = "director"
VERSION = "director-video/1"
ELEMENT_KINDS = ["structure_3d", "illustration", "diagram", "cell_or_micro", "organ_or_body", "molecule", "signal_or_flow", "map",
                 "timeline", "chart", "number_scale", "equation", "table", "text_card", "label", "arrow", "character", "icon"]
CAMERA_MOVES = ["establish", "zoom_in", "zoom_out", "pan", "orbit", "follow", "cut", "hold"]
ACTIONS = ["appear", "draw_on", "label", "highlight", "zoom_into", "move_along_path", "flow", "pulse", "split", "merge",
           "transform", "grow", "shrink", "compare_side_by_side", "count_up", "scale_compare", "fade_out"]
CUE = obj({"beat_id": S, "word": S})
SCENE_SCHEMA = obj({
    "scene_id": S,
    "beat_ids": arr(S),
    "frame": obj({"process": S, "how_it_works": S, "when_or_sequence": S, "conditions_or_atmosphere": S, "who_or_what_changes": S}),
    "style": S,
    "setting": S,
    "elements": arr(obj({
        "element_id": S,
        "kind": {"type": "string", "enum": ELEMENT_KINDS},
        "shows": S,
        "parts_to_label": arr(S),
        "detail": {"type": "string", "enum": ["anatomy", "schematic", "iconic"]},
        "source_item_ids": arr(S),
    })),
    "camera": arr(obj({"cue": CUE, "move": {"type": "string", "enum": CAMERA_MOVES}, "target_element_id": S, "note": S})),
    "actions": arr(obj({"cue": CUE, "element_id": S, "action": {"type": "string", "enum": ACTIONS}, "detail": S})),
    "visual_math": arr(obj({"what": S, "values": S, "shown_as": S})),
    "interaction": obj({"type": {"type": "string", "enum": ["none", "pause_question", "tap_explore"]}, "question_id": S,
                        "prompt": S, "target_element_id": S}),
})
DIRECTOR_SCHEMA = obj({"notes": NOTES_SCHEMA, "scenes": arr(SCENE_SCHEMA)})
PATCH_SCHEMA = obj({"notes": NOTES_SCHEMA, "replace_scenes": arr(SCENE_SCHEMA), "remove_scene_ids": arr(S)})
PATCH_HINT = ("Reply with a patch, not the whole video: replace_scenes = complete corrected scenes (same scene_id to replace; a new "
              "scene_id is inserted in beat order), remove_scene_ids = scenes to delete.")
REVIEW_SCHEMA = obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": arr(obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": arr(obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})

ROLE = """You are BIE's director: you decide what the student sees in one video lesson of {subject} for {learners} ({exam}), beat by
beat, like the director of a cinematic, anatomy-level explainer film. BIE's visual section will find or build every asset you describe
and animate it with code, so describe precisely; never write code.

Course: "{title}" · learner language: {language} (on-screen labels use the book's English terms; prompts to the student use
{language}).

Navin's rules for this section (follow every one):
{rules}

How to fill the JSON:
- notes: brief notes for the reviewer: what this video shows, the key visual decisions with a reason each, what is uncertain.
- scenes: in order; together they cover every beat of the script exactly once (beat_ids in script order).
  - frame: your answers to the universal questions for this scene ("" where a question does not apply).
  - style: how the subject's style is applied here; setting: what the whole screen looks like (background, environment).
  - elements: what appears. shows = exactly what must be visible (structure, parts, arrangement, cut-away or cross-section, scale);
    parts_to_label = the labels; detail = anatomy (realistic, detailed), schematic or iconic; source_item_ids = chapter-map items shown.
  - camera and actions: each with a cue = the beat_id and the exact word in that beat's spoken text where it happens.
  - visual_math: every number, comparison or change shown to scale ([] if none).
  - interaction: none, pause_question (question_id from the teacher questions given, prompt in {language}) or tap_explore
    (target_element_id and prompt).
Reply with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the director section ({subject}, {learners}, {exam}). Another AI planned what the
student sees in one video, from BIE's teacher script and chapter map. Judge it as Navin would: is this cinematic, anatomy-level,
process-showing teaching that makes the spoken words visible?

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

You also get the maker's notes. Report every problem with where it is (scene id, beat id), what is wrong, the fix and a severity
("blocking" or "minor", see R-01): a beat not covered, a visual that does not show what is being said, a vague asset description, a
process shown as a still picture, numbers not shown to scale, a cue on the wrong word, a wrong fact in a label, an interaction that
does not make the student think. Precision beyond the level of a standard textbook for {learners} ({exam}) is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


def _norm(text: str) -> str:
    return re.sub(r"[^\wऀ-ॿ]+", " ", unicodedata.normalize("NFC", text).lower()).strip()


def word_in(word: str, say: str) -> bool:
    target = _norm(word)
    return bool(target) and f" {target} " in f" {_norm(say)} "


def apply_patch(previous: dict, patch: dict, beat_order: list) -> dict:
    replace = {s["scene_id"]: s for s in patch.get("replace_scenes") or []}
    removed = set(patch.get("remove_scene_ids") or [])
    scenes = [replace.pop(s["scene_id"], s) for s in previous.get("scenes") or [] if s["scene_id"] not in removed]
    scenes.extend(replace.values())
    position = {b: i for i, b in enumerate(beat_order)}
    scenes.sort(key=lambda s: min((position.get(b, 10 ** 6) for b in s["beat_ids"]), default=10 ** 6))
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), scenes=scenes)


def check_video(value: dict, beats: list, scope_items: set, scope_questions: set) -> list:
    problems = []
    says = {b["beat_id"]: b["say"] for b in beats}
    order = [b["beat_id"] for b in beats]
    seen = []
    ids = [s["scene_id"] for s in value.get("scenes") or []]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"scene_id {dup!r} is used more than once")
    for scene in value.get("scenes") or []:
        sid = scene["scene_id"]
        elements = {e["element_id"] for e in scene["elements"]}
        if not elements:
            problems.append(f"scene {sid}: shows no element")
        for e in scene["elements"]:
            if not e["shows"].strip():
                problems.append(f"scene {sid}: element {e['element_id']} does not say what it shows (S3-04)")
            for iid in e["source_item_ids"]:
                if iid not in scope_items:
                    problems.append(f"scene {sid}: element {e['element_id']} uses unknown item {iid!r}")
        for bid in scene["beat_ids"]:
            if bid not in says:
                problems.append(f"scene {sid}: unknown beat {bid!r}")
            seen.append(bid)
        for kind, entries, key in (("camera", scene["camera"], "target_element_id"), ("action", scene["actions"], "element_id")):
            for entry in entries:
                cue = entry["cue"]
                if cue["beat_id"] not in scene["beat_ids"]:
                    problems.append(f"scene {sid}: {kind} cue beat {cue['beat_id']!r} is not one of this scene's beats")
                elif not word_in(cue["word"], says.get(cue["beat_id"], "")):
                    problems.append(f"scene {sid}: {kind} cue word {cue['word']!r} is not spoken in beat {cue['beat_id']} (S3-03)")
                if entry[key] and entry[key] not in elements:
                    problems.append(f"scene {sid}: {kind} targets unknown element {entry[key]!r}")
        if not scene["actions"]:
            problems.append(f"scene {sid}: nothing happens on screen; add actions tied to spoken words (S3-03)")
        inter = scene["interaction"]
        if inter["type"] == "pause_question" and inter["question_id"] not in scope_questions:
            problems.append(f"scene {sid}: pause question {inter['question_id']!r} is not a teacher question of this video (S3-05)")
        if inter["type"] == "tap_explore" and inter["target_element_id"] not in elements:
            problems.append(f"scene {sid}: tap_explore targets unknown element {inter['target_element_id']!r}")
    missing = [b for b in order if b not in seen]
    doubled = sorted({b for b in seen if seen.count(b) > 1})
    if missing:
        problems.append(f"{len(missing)} beats are in no scene: {', '.join(missing[:30])}")
    if doubled:
        problems.append(f"beats in more than one scene: {', '.join(doubled[:30])}")
    if [b for b in seen if b in order] != [b for b in order if b in seen]:
        problems.append("scenes must follow the script's beat order")
    return problems


def _video_input(chapter, lesson_video, plan_video):
    items, questions = video_scope(chapter, plan_video)
    rows = [{"item_id": i["item_id"], "kind": i["kind"], "content_type": i["content_type"], "content": i["content"]} for i in items]
    qs = []
    for item in items:
        for qid, qa in zip(question_ids(item), item.get("teacher_understanding") or []):
            qs.append({"id": qid, "question": qa["question"]})
    beats = [{"beat_id": b["beat_id"], "purpose": b["purpose"], "say": b["say"], "on_screen": b["on_screen"],
              "covers_item_ids": b["covers_item_ids"]} for b in lesson_video["beats"]]
    return {"video": {"video_id": plan_video["video_id"], "title": lesson_video["title"], "goal": plan_video.get("goal", "")},
            "beats": beats, "items": rows, "teacher_questions": qs}, {i["item_id"] for i in items}, set(questions)


def video_step(course: Course, chapter, lesson_video, plan_video, *, rulebook, max_rounds=3) -> Step:
    payload, scope_items, scope_questions = _video_input(chapter, lesson_video, plan_video)
    text = json.dumps(payload, ensure_ascii=False)
    beats = lesson_video["beats"]
    order = [b["beat_id"] for b in beats]
    system = fmt(ROLE, course, rules=rulebook.instructions(SECTION))
    user = f"Chapter: {course.title}. Video {plan_video['video_id']}.\nScript, items and teacher questions (JSON):\n{text}\n\nReply with the scenes JSON."
    review_system = fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(), checklist=checklist_text(rulebook, SECTION))

    def review_user(value):
        return (f"Chapter: {course.title}. Video {plan_video['video_id']}.\nScript, items and teacher questions (JSON):\n{text}\n\n"
                f"The scenes to review (JSON):\n{json.dumps(value, ensure_ascii=False)}")

    return Step(section=SECTION, unit=f"video-{plan_video['video_id']}", instructions_version=VERSION, system=system, user=user,
                schema=DIRECTOR_SCHEMA, check=lambda value: check_video(value, beats, scope_items, scope_questions),
                review_system=review_system, review_user=review_user, review_schema=REVIEW_SCHEMA, review_problems=review_problems,
                patch_schema=PATCH_SCHEMA, apply_patch=lambda previous, patch: apply_patch(previous, patch, order),
                patch_hint=PATCH_HINT, max_rounds=max_rounds)


def run_director(chapter: dict, lesson: dict, course: Course, runner, out_dir, *, workers: int = 4, max_rounds: int = 3):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    plans = {v["video_id"]: v for v in (lesson.get("plan") or {}).get("videos", [])}
    videos = [v for v in lesson.get("videos", []) if v["beats"] and v["video_id"] in plans]
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        results = list(pool.map(lambda v: runner.run(video_step(course, chapter, v, plans[v["video_id"]], rulebook=runner.rulebook,
                                                                max_rounds=max_rounds)), videos))
    director = {
        "schema": "bie.brain.director/1",
        "course": chapter["course"],
        "rulebook_version": runner.rulebook.version,
        "maker_route": runner.maker,
        "reviewer_route": runner.reviewer,
        "reviewer_independence": runner.independence,
        "videos": [{
            "video_id": video["video_id"],
            "title": video["title"],
            "status": result.status,
            "rounds": len(result.rounds),
            "scenes": (result.output or {}).get("scenes", []),
            "last_problems": (result.rounds[-1].get("code_problems") or []) + (result.rounds[-1].get("review_problems") or [])
            if result.rounds and not result.passed else [],
            "record": Path(result.record_path).name if result.record_path else None,
            "cost_usd": result.cost_usd,
        } for video, result in zip(videos, results)],
    }
    director["cost_usd"] = round(sum(v["cost_usd"] for v in director["videos"]), 6)
    scenes = [s for v in director["videos"] for s in v["scenes"]]
    director["quality"] = {"videos": len(videos), "videos_passed": sum(1 for v in director["videos"] if v["status"] == "passed"),
                           "scenes": len(scenes), "elements": sum(len(s["elements"]) for s in scenes),
                           "anatomy_elements": sum(1 for s in scenes for e in s["elements"] if e["detail"] == "anatomy"),
                           "actions": sum(len(s["actions"]) for s in scenes),
                           "visual_math": sum(len(s["visual_math"]) for s in scenes),
                           "pause_questions": sum(1 for s in scenes if s["interaction"]["type"] == "pause_question"),
                           "tap_explore": sum(1 for s in scenes if s["interaction"]["type"] == "tap_explore"),
                           "cost_usd": director["cost_usd"]}
    (out / "director.json").write_text(json.dumps(director, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "DIRECTOR.md").write_text(render_markdown(director), encoding="utf-8")
    return director


def render_markdown(director: dict) -> str:
    q = director["quality"]
    lines = [f"# Director · {director['course']['title']}", "",
             f"Videos passed: {q['videos_passed']} of {q['videos']}; {q['scenes']} scenes, {q['elements']} elements "
             f"({q['anatomy_elements']} anatomy-level), {q['actions']} word-timed actions, {q['visual_math']} visual-math moments, "
             f"{q['pause_questions']} pause questions, {q['tap_explore']} tap-to-explore; estimated cost ${q['cost_usd']:.4f}.", ""]
    for video in director["videos"]:
        lines += [f"## {video['video_id']} · {video['title']} · {video['status']} after {video['rounds']} round(s)", ""]
        if video["last_problems"]:
            lines += ["Open problems:", ""] + [f"- {x}" for x in video["last_problems"][:15]] + [""]
        for scene in video["scenes"]:
            f = scene["frame"]
            lines += [f"### {scene['scene_id']} · beats {', '.join(scene['beat_ids'])}", "",
                      f"- Setting: {scene['setting']}", f"- Style: {scene['style']}"]
            for label, key in (("Process", "process"), ("How it works", "how_it_works"), ("When / sequence", "when_or_sequence"),
                               ("Conditions", "conditions_or_atmosphere"), ("Who or what changes", "who_or_what_changes")):
                if f[key]:
                    lines.append(f"- {label}: {f[key]}")
            for e in scene["elements"]:
                lines.append(f"- **{e['element_id']}** ({e['kind']}, {e['detail']}): {e['shows']}"
                             + (f" · labels: {', '.join(e['parts_to_label'])}" if e["parts_to_label"] else ""))
            for c in scene["camera"]:
                lines.append(f"  - camera {c['move']} → {c['target_element_id']} on \"{c['cue']['word']}\" ({c['cue']['beat_id']})")
            for a in scene["actions"]:
                lines.append(f"  - {a['action']} {a['element_id']} on \"{a['cue']['word']}\" ({a['cue']['beat_id']}): {a['detail']}")
            for m in scene["visual_math"]:
                lines.append(f"  - visual math: {m['what']} = {m['values']} → {m['shown_as']}")
            if scene["interaction"]["type"] != "none":
                lines.append(f"  - interaction {scene['interaction']['type']}: {scene['interaction']['prompt']}")
            lines.append("")
    return "\n".join(lines)
