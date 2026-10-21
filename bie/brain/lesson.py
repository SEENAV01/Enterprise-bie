"""Section 2 · Lesson plan and teacher script.

From the chapter map (Section 1) BIE plans the chapter's videos like the best teacher (how many,
which concepts, prerequisites taught first, length from content) and then writes each video's
spoken teacher script in beats, in Navin's Hinglish. Every beat claims which chapter-map items it
covers and which teacher questions it answers; BIE's code checks that every item and every question
of the video is covered, and the independent reviewer checks that the claims are true and the flow
is a real teacher's. Every step runs through ``SectionRunner``.

Outputs (``run_lesson``): ``lesson_plan.json`` (plan plus scripts, what the director consumes),
``SCRIPT.md`` (readable), one process record per step under ``records/``.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .runner import NOTES_SCHEMA, Step
from .common import SEVERITY, S, arr as _arr, checklist_text as _checklist_text, fmt as _fmt, obj as _obj, review_problems
from .understanding import Course

SECTION = "lesson"
PLAN_VERSION = "lesson-plan/1"
SCRIPT_VERSION = "lesson-script/1"
PURPOSES = ["hook", "prerequisite", "explain", "example", "analogy", "story", "compare", "process_walkthrough",
            "misconception", "exam_tip", "question_to_student", "recap", "transition"]
DEVANAGARI = re.compile(r"[ऀ-ॿ]")

PLAN_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "videos": _arr(_obj({
        "video_id": S,
        "title": S,
        "goal": S,
        "concept_ids": _arr(S),
        "prerequisites_taught": _arr(S),
        "opening_hook": S,
        "story_or_analogy": S,
        "estimated_minutes": {"type": "integer"},
        "why_this_unit": S,
    })),
    "chapter_flow": S,
})
BEAT_SCHEMA = _obj({
    "beat_id": S,
    "purpose": {"type": "string", "enum": PURPOSES},
    "say": S,
    "covers_item_ids": _arr(S),
    "answers": _arr(S),
    "on_screen": S,
    "basis": {"type": "string", "enum": ["book", "outside", "mixed"]},
})
SCRIPT_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "title": S,
    "beats": _arr(BEAT_SCHEMA),
})
SCRIPT_PATCH_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "replace_beats": _arr(BEAT_SCHEMA),
    "insert_beats": _arr(_obj({"after_beat_id": S, "beat": BEAT_SCHEMA})),
    "remove_beat_ids": _arr(S),
})
SCRIPT_PATCH_HINT = ("Reply with a patch, not the whole script: replace_beats = complete corrected beats (same beat_id), insert_beats = "
                     "new beats with the beat_id they follow (\"\" for the very start), remove_beat_ids = beats to delete.")
REVIEW_SCHEMA = _obj({
    "notes": NOTES_SCHEMA,
    "verdict": {"type": "string", "enum": ["pass", "fail"]},
    "problems": _arr(_obj({"where": S, "problem": S, "fix": S, "severity": SEVERITY})),
    "checklist": _arr(_obj({"rule_id": S, "met": {"type": "boolean"}, "note": S})),
})


def apply_script_patch(previous: dict, patch: dict) -> dict:
    replace = {b["beat_id"]: b for b in patch.get("replace_beats") or []}
    removed = set(patch.get("remove_beat_ids") or [])
    beats = [replace.get(b["beat_id"], b) for b in previous.get("beats") or [] if b["beat_id"] not in removed]
    for entry in patch.get("insert_beats") or []:
        ids = [b["beat_id"] for b in beats]
        at = ids.index(entry["after_beat_id"]) + 1 if entry["after_beat_id"] in ids else (0 if not entry["after_beat_id"] else len(beats))
        beats.insert(at, entry["beat"])
    return dict(previous, notes=patch.get("notes") or previous.get("notes"), beats=beats)

PLAN_ROLE = """You are BIE's lesson section: the best teacher of {subject} for {learners} preparing for {exam}, planning the video
lessons of one chapter from BIE's chapter map. Students learn only from these videos, so the plan must make the whole chapter
understandable, starting from what they already know.

Course: "{title}" · learner language: {language}.

Navin's rules for this section (follow every one):
{rules}

How to fill the JSON:
- notes: brief notes for the reviewer: what the chapter is about, the key questions the plan must serve, your main decisions with a
  reason each, what is uncertain.
- videos: in teaching order. video_id "v1", "v2" ...; title in {language}; goal = what the student will understand after it;
  concept_ids = the chapter-map concept ids taught in it, in order (every concept in some video); prerequisites_taught = names from
  "prerequisites to teach" that this video teaches first; opening_hook = a real-life question, puzzle or surprise that opens it;
  story_or_analogy = the story or analogy that genuinely helps, or "" if none fits; estimated_minutes from the content (a teacher
  explaining every item and question at a natural pace), never a fixed length; why_this_unit = why these concepts belong together.
- chapter_flow: how the videos build on each other.
Reply with the JSON object only."""

SCRIPT_ROLE = """You are BIE's lesson section writing what the teacher says in one video lesson: you are the best teacher of {subject}
for {learners} preparing for {exam}, speaking to one student. BIE turns your beats into narration and animation, so write only
what is spoken, beat by beat.

Course: "{title}" · learner language: {language}.

Navin's rules for this section (follow every one):
{rules}

How to fill the JSON:
- notes: brief notes for the reviewer: what this video is about, the key questions it must answer, your main decisions (order,
  hook, analogy, where prerequisites are taught) with a reason each, what is uncertain.
- title: the video title in {language}.
- beats: the whole video in order. beat_id "b1", "b2" ...; purpose (hook, prerequisite, explain, example, analogy, story, compare,
  process_walkthrough, misconception, exam_tip, question_to_student, recap, transition); say = the exact spoken words (one to four
  short spoken sentences); covers_item_ids = the chapter-map item ids this beat really explains; answers = the teacher question ids
  (like "p003-i4#q2") this beat really answers; on_screen = what the student should see while hearing it (for the director);
  basis = book, outside or mixed.
Every item and every teacher question listed for this video must be covered by some beat. Reply with the JSON object only."""

REVIEW_ROLE = """You are BIE's independent reviewer for the lesson section ({subject}, {learners}, {exam}, learner language {language}).
Another AI wrote the work below from BIE's chapter map. You check it as Navin would: is this how the best teacher would teach it?

{review_rules}

Check against this list (answer every item in "checklist" with its rule id):
{checklist}

You also get the maker's notes. Report every problem with where it is (video or beat id), what is wrong, the fix and a severity
("blocking" or "minor", see R-01): an item or teacher question not really covered (even if claimed), a prerequisite named but not
taught, a jump a student cannot follow, an analogy that does not fit, a fact wrong at this level, language that is not natural spoken
Hinglish, beats that read out lists. Precision beyond the level of a standard textbook for {learners} ({exam}) is minor.
verdict is "pass" when nothing is blocking. Fill your own brief notes first. Reply with the JSON object only."""


def question_ids(item: dict):
    return [f"{item['item_id']}#q{n}" for n in range(1, len(item.get("teacher_understanding") or []) + 1)]


def _concepts(chapter):
    return {c["concept_id"]: c for c in (chapter.get("map") or {}).get("concepts", [])}


def _plan_input(chapter):
    m = chapter.get("map") or {}
    concepts = [{"concept_id": c["concept_id"], "name": c["name"], "content_type": c["content_type"],
                 "core_explanation": c["core_explanation"], "items": len(c["item_ids"]),
                 "teacher_questions": sum(len(chapter["items"][i].get("teacher_understanding") or [])
                                          for i in c["item_ids"] if i in chapter["items"])} for c in m.get("concepts", [])]
    return {"chapter_summary": m.get("chapter_summary", ""), "concepts": concepts, "relations": m.get("relations", []),
            "prerequisites_to_teach": m.get("prerequisites_to_teach", []), "teaching_order": m.get("teaching_order", []),
            "exam_focus": m.get("exam_focus", [])}


def check_plan(value, chapter):
    problems = []
    concepts = _concepts(chapter)
    ids = [v["video_id"] for v in value.get("videos") or []]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"video_id {dup!r} is used more than once")
    taught = set()
    for video in value.get("videos") or []:
        for cid in video["concept_ids"]:
            if cid not in concepts:
                problems.append(f"video {video['video_id']}: unknown concept {cid!r}")
            taught.add(cid)
        if video["estimated_minutes"] < 1:
            problems.append(f"video {video['video_id']}: estimated_minutes must be at least 1")
        if not video["concept_ids"]:
            problems.append(f"video {video['video_id']}: teaches no concept")
    for cid in sorted(set(concepts) - taught):
        problems.append(f"concept {cid} ({concepts[cid]['name']}) is in no video (S2-01)")
    wanted = {p["name"].strip().lower() for p in (chapter.get("map") or {}).get("prerequisites_to_teach", [])}
    given = {p.strip().lower() for v in value.get("videos") or [] for p in v["prerequisites_taught"]}
    for name in sorted(wanted - given):
        problems.append(f"prerequisite {name!r} is taught in no video (S2-03); use the exact name from the list")
    if not value.get("videos"):
        problems.append("the plan has no videos")
    return problems


def video_scope(chapter, video):
    """The items and teacher questions a video must cover."""
    concepts = _concepts(chapter)
    item_ids = []
    for cid in video["concept_ids"]:
        for iid in (concepts.get(cid) or {}).get("item_ids", []):
            if iid in chapter["items"] and iid not in item_ids:
                item_ids.append(iid)
    items = [chapter["items"][i] for i in item_ids]
    questions = [qid for item in items if item.get("teachable") for qid in question_ids(item)]
    return items, questions


def _script_input(chapter, plan, video):
    items, _ = video_scope(chapter, video)
    concepts = _concepts(chapter)
    prereq = [p for p in (chapter.get("map") or {}).get("prerequisites_to_teach", [])
              if p["name"].strip().lower() in {x.strip().lower() for x in video["prerequisites_taught"]}]
    rows = []
    for item in items:
        rows.append({"item_id": item["item_id"], "page": item["page"], "kind": item["kind"], "content_type": item["content_type"],
                     "teachable": item["teachable"], "content": item["content"],
                     "teacher_questions": [{"id": qid, "ask": qa["ask"], "question": qa["question"], "answer": qa["answer"],
                                            "basis": qa["basis"]}
                                           for qid, qa in zip(question_ids(item), item.get("teacher_understanding") or [])]})
    order = [v["video_id"] for v in plan["videos"]]
    position = order.index(video["video_id"])
    return {"video": video, "previous_video": plan["videos"][position - 1]["title"] if position else "",
            "next_video": plan["videos"][position + 1]["title"] if position + 1 < len(order) else "",
            "concepts": [concepts[c] for c in video["concept_ids"] if c in concepts], "prerequisites_to_teach_here": prereq,
            "items": rows}


def check_script(value, chapter, video, language):
    problems = []
    items, questions = video_scope(chapter, video)
    scope_items = {i["item_id"] for i in items}
    scope_questions = set(questions)
    beats = value.get("beats") or []
    ids = [b["beat_id"] for b in beats]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"beat_id {dup!r} is used more than once")
    covered, answered = set(), set()
    for beat in beats:
        if not beat["say"].strip():
            problems.append(f"beat {beat['beat_id']}: say is empty")
        for iid in beat["covers_item_ids"]:
            if iid not in scope_items:
                problems.append(f"beat {beat['beat_id']}: item {iid!r} is not an item of this video")
            covered.add(iid)
        for qid in beat["answers"]:
            if qid not in scope_questions:
                problems.append(f"beat {beat['beat_id']}: {qid!r} is not a teacher question of this video")
            answered.add(qid)
    teachable = [i["item_id"] for i in items if i.get("teachable")]
    missing_items = [i for i in teachable if i not in covered]
    if missing_items:
        problems.append(f"{len(missing_items)} items are covered by no beat (S2-02): {', '.join(missing_items[:40])}")
    missing_q = [q for q in questions if q not in answered]
    if missing_q:
        problems.append(f"{len(missing_q)} teacher questions are answered by no beat (S2-02): {', '.join(missing_q[:40])}")
    if language.strip().lower() in ("hinglish", "hindi"):
        hindi = sum(1 for b in beats if DEVANAGARI.search(b["say"]))
        if beats and hindi < 0.8 * len(beats):
            problems.append(f"only {hindi} of {len(beats)} beats are written in Devanagari Hindi; write spoken Hinglish (S2-04)")
    if len(beats) < 3:
        problems.append("a video needs more than a couple of beats")
    return problems


def plan_step(course: Course, chapter, *, rulebook, max_rounds=3) -> Step:
    system = _fmt(PLAN_ROLE, course, rules=rulebook.instructions(SECTION))
    payload = json.dumps(_plan_input(chapter), ensure_ascii=False)
    user = f"Chapter: {course.title}.\nBIE's chapter map (JSON):\n{payload}\n\nReply with the lesson plan JSON."
    review_system = _fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(),
                         checklist=_checklist_text(rulebook, SECTION))

    def review_user(value):
        shown = value
        return (f"Chapter: {course.title}.\nBIE's chapter map (JSON):\n{payload}\n\n"
                f"The lesson plan to review (JSON):\n{json.dumps(shown, ensure_ascii=False)}")

    return Step(section=SECTION, unit="plan", instructions_version=PLAN_VERSION, system=system, user=user, schema=PLAN_SCHEMA,
                check=lambda value: check_plan(value, chapter), review_system=review_system, review_user=review_user,
                review_schema=REVIEW_SCHEMA, review_problems=review_problems, max_rounds=max_rounds)


def script_step(course: Course, chapter, plan, video, *, rulebook, max_rounds=3) -> Step:
    system = _fmt(SCRIPT_ROLE, course, rules=rulebook.instructions(SECTION))
    payload = json.dumps(_script_input(chapter, plan, video), ensure_ascii=False)
    user = (f"Chapter: {course.title}. Video {video['video_id']} of {len(plan['videos'])}.\n"
            f"What this video must teach (JSON):\n{payload}\n\nReply with the teacher script JSON.")
    review_system = _fmt(REVIEW_ROLE, course, review_rules=rulebook.reviewer_instructions(),
                         checklist=_checklist_text(rulebook, SECTION))

    def review_user(value):
        shown = value
        return (f"Chapter: {course.title}. Video {video['video_id']}.\nWhat this video must teach (JSON):\n{payload}\n\n"
                f"The teacher script to review (JSON):\n{json.dumps(shown, ensure_ascii=False)}")

    return Step(section=SECTION, unit=f"script-{video['video_id']}", instructions_version=SCRIPT_VERSION, system=system,
                user=user, schema=SCRIPT_SCHEMA, check=lambda value: check_script(value, chapter, video, course.language),
                review_system=review_system, review_user=review_user, review_schema=REVIEW_SCHEMA,
                review_problems=review_problems, patch_schema=SCRIPT_PATCH_SCHEMA, apply_patch=apply_script_patch,
                patch_hint=SCRIPT_PATCH_HINT, max_rounds=max_rounds)


def run_lesson(chapter: dict, course: Course, runner, out_dir, *, workers: int = 4, max_rounds: int = 3):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    plan_result = runner.run(plan_step(course, chapter, rulebook=runner.rulebook, max_rounds=max_rounds))
    plan = plan_result.output or {"videos": []}
    videos = plan.get("videos") or []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        scripts = list(pool.map(lambda v: runner.run(script_step(course, chapter, plan, v, rulebook=runner.rulebook,
                                                                 max_rounds=max_rounds)), videos))
    lesson = {
        "schema": "bie.brain.lesson/1",
        "course": chapter["course"],
        "source_sha256": chapter.get("source_sha256"),
        "rulebook_version": runner.rulebook.version,
        "maker_route": runner.maker,
        "reviewer_route": runner.reviewer,
        "plan_status": plan_result.status,
        "plan": {k: v for k, v in plan.items() if k != "notes"},
        "videos": [{
            "video_id": video["video_id"],
            "title": (result.output or {}).get("title") or video["title"],
            "status": result.status,
            "rounds": len(result.rounds),
            "beats": (result.output or {}).get("beats", []),
            "last_problems": (result.rounds[-1].get("code_problems") or []) + (result.rounds[-1].get("review_problems") or [])
            if result.rounds and not result.passed else [],
            "record": Path(result.record_path).name if result.record_path else None,
            "cost_usd": result.cost_usd,
        } for video, result in zip(videos, scripts)],
        "cost_usd": round(plan_result.cost_usd + sum(r.cost_usd for r in scripts), 6),
    }
    words = sum(len(b["say"].split()) for v in lesson["videos"] for b in v["beats"])
    lesson["quality"] = {"videos": len(videos), "videos_passed": sum(1 for v in lesson["videos"] if v["status"] == "passed"),
                         "plan_passed": plan_result.passed, "beats": sum(len(v["beats"]) for v in lesson["videos"]),
                         "spoken_words": words, "estimated_minutes_at_130_wpm": round(words / 130, 1),
                         "cost_usd": lesson["cost_usd"]}
    (out / "lesson_plan.json").write_text(json.dumps(lesson, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "SCRIPT.md").write_text(render_markdown(lesson), encoding="utf-8")
    return lesson


def render_markdown(lesson: dict) -> str:
    q = lesson["quality"]
    lines = [f"# Lesson plan and scripts · {lesson['course']['title']}", "",
             f"Plan: {lesson['plan_status']}; scripts passed: {q['videos_passed']} of {q['videos']}; {q['beats']} beats, "
             f"{q['spoken_words']} spoken words (about {q['estimated_minutes_at_130_wpm']} minutes); estimated cost ${q['cost_usd']:.4f}.", ""]
    if lesson["plan"].get("chapter_flow"):
        lines += [lesson["plan"]["chapter_flow"], ""]
    plans = {v["video_id"]: v for v in lesson["plan"].get("videos", [])}
    for video in lesson["videos"]:
        p = plans.get(video["video_id"], {})
        lines += [f"## {video['video_id']} · {video['title']} · {video['status']} after {video['rounds']} round(s)", "",
                  f"Goal: {p.get('goal', '')}", f"Hook: {p.get('opening_hook', '')}",
                  f"Story or analogy: {p.get('story_or_analogy', '') or '(none)'}", ""]
        if video["last_problems"]:
            lines += ["Open problems:", ""] + [f"- {x}" for x in video["last_problems"][:15]] + [""]
        for beat in video["beats"]:
            lines.append(f"**{beat['beat_id']} · {beat['purpose']}** — {beat['say']}")
            lines.append(f"  _screen: {beat['on_screen']}_")
            lines.append("")
    return "\n".join(lines)
