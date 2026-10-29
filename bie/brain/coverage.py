"""Which lines of the book a video taught, by code (Task 046 Part C, work B; Navin, 29 October 2026: "har video ke saath
dikhao ki kitaab ki kaun-si lines usne padhaayi").

Three readers, no AI call and nothing written by hand:

* ``video_coverage``: for one video, every line the chapter map assigns to it (``lesson.video_scope`` on the plan's video, so
  the same scope the script was checked against), the beats that cover the line (their ``covers_item_ids``), where each beat
  plays in the rendered video (from the video spec's captions: one caption per beat, carrying its ``beat_id``), how the beat
  teaches the line (its ``purpose``: example, explain, misconception, recap ...), and the teacher questions it answers.
  Below the table: the assigned lines no beat covers (must be empty; the page shows them in red), the beats whose basis is
  outside the book, and beats that cover lines outside the video's scope.
* ``chapter_coverage``: for the whole chapter, every teachable line (383 for Money) and the video that teaches it, with that
  video's status; lines no video is assigned to are listed (must be empty).
* ``beat_times``: {beat_id: scene, start, end in seconds} from a spec; an older spec whose captions carry no ``beat_id`` is
  matched to the plans' beats in order (one caption per beat), else by the caption's text.

The record a review page writes (``coverage.json``) is the "review record" the video path's formats will lock (work D).
"""
from __future__ import annotations

from collections import Counter

from . import lesson as lesson_module

SCHEMA = "bie.brain.coverage/1"
CHAPTER_SCHEMA = "bie.brain.coverage.chapter/1"

# How a beat teaches a line, said the way the page says it to Navin (the beat's purpose, S2 schema).
HOW_WORDS = {"example": "example se", "explain": "samjhaya", "misconception": "galatfahmi door ki", "recap": "dohraav",
             "compare": "tulna", "exam_tip": "exam tip", "process_walkthrough": "process chala kar", "question_to_student": "sawaal poochha",
             "story": "kahani", "analogy": "analogy", "prerequisite": "pehle yeh jaan lo", "hook": "hook"}
HOW_ORDER = list(HOW_WORDS)


def how_word(purpose: str) -> str:
    return HOW_WORDS.get(purpose or "", purpose or "—")


# ---------------------------------------------------------------- the lesson's two views of a video

def plan_video(lesson: dict, video_id: str) -> dict:
    """The plan entry (concept_ids, kind, title) of a video in a lesson plan."""
    for v in (lesson.get("plan") or {}).get("videos") or []:
        if v.get("video_id") == video_id:
            return v
    return {}


def script_video(lesson: dict, video_id: str) -> dict:
    """The script entry (beats, status, card_parts) of a video in a lesson plan."""
    for v in lesson.get("videos") or []:
        if v.get("video_id") == video_id:
            return v
    return {}


def video_ids(lesson: dict) -> list:
    ids = [v["video_id"] for v in (lesson.get("plan") or {}).get("videos") or []]
    for v in lesson.get("videos") or []:
        if v.get("video_id") not in ids:
            ids.append(v["video_id"])
    return ids


def assigned_items(chapter: dict, plan: dict, script: dict | None = None) -> list:
    """The lines the chapter map assigns to a video, in the map's order: ``lesson.video_scope`` on the plan's video; a plan
    entry without concept_ids (a script resumed alone) falls back to the script's card_parts."""
    if plan and (plan.get("concept_ids") is not None or lesson_module.is_prerequisite_video(plan)):
        items, _ = lesson_module.video_scope(chapter, plan)
        if lesson_module.is_prerequisite_video(plan):
            names = dict(lesson_module.prerequisites_of(chapter))
            for item in items:
                item["content"] = (names.get(item["item_id"]) or {}).get("name", item["item_id"])
        return items
    items, seen = [], set()
    for part in (script or {}).get("card_parts") or []:
        for iid in part.get("item_ids") or []:
            if iid in seen:
                continue
            seen.add(iid)
            item = (chapter.get("items") or {}).get(iid)
            items.append(item if item else {"item_id": iid, "page": 0, "teachable": True, "kind": part.get("type", "")})
    return items


# ---------------------------------------------------------------- where a beat plays

def _match_text(caption: dict, beats: list, used: set) -> str:
    text = (caption.get("text") or "").strip()
    for b in beats:
        if b.get("beat_id") in used:
            continue
        if text and text in {(b.get("caption") or "").strip(), (b.get("say") or "").strip()}:
            return b["beat_id"]
    return ""


def beat_times(spec: dict, plans: dict | None = None) -> dict:
    """{beat_id: {"scene", "start_s", "end_s"}} in the joined video: scenes play one after another in the spec's order."""
    fps = float(spec.get("fps") or 30)
    out, offset = {}, 0
    for scene in spec.get("scenes") or []:
        captions = scene.get("captions") or []
        beats = ((plans or {}).get(scene.get("id")) or {}).get("beats") or []
        in_order = len(beats) == len(captions)
        used = set()
        for n, cap in enumerate(captions):
            bid = cap.get("beat_id") or (beats[n].get("beat_id", "") if in_order else "") or _match_text(cap, beats, used)
            if not bid:
                continue
            used.add(bid)
            out[bid] = {"scene": scene.get("id", ""), "start_s": round((offset + cap["at"]) / fps, 1),
                        "end_s": round((offset + cap["until"]) / fps, 1)}
        offset += int(scene.get("duration") or 0)
    return out


def mmss(seconds) -> str:
    s = int(round(float(seconds or 0)))
    return f"{s // 60}:{s % 60:02d}"


# ---------------------------------------------------------------- one video

def _beat_row(beat: dict, times: dict) -> dict:
    t = times.get(beat.get("beat_id", "")) or {}
    return {"beat_id": beat.get("beat_id", ""), "part_id": beat.get("part_id", ""), "purpose": beat.get("purpose", ""),
            "how": how_word(beat.get("purpose", "")), "basis": beat.get("basis", ""), "scene": t.get("scene", ""),
            "start_s": t.get("start_s"), "end_s": t.get("end_s"),
            "time": f"{mmss(t['start_s'])}–{mmss(t['end_s'])}" if t else "", "say": beat.get("say", "")}


def video_coverage(chapter: dict, lesson: dict, video_id: str, *, spec: dict | None = None, plans: dict | None = None) -> dict:
    """The coverage record of one video (see the module docstring)."""
    plan, script = plan_video(lesson, video_id), script_video(lesson, video_id)
    beats = script.get("beats") or []
    times = beat_times(spec, plans) if spec else {}
    items = assigned_items(chapter, plan, script)
    assigned_ids = [i["item_id"] for i in items]
    by_item = {}
    for b in beats:
        for iid in b.get("covers_item_ids") or []:
            by_item.setdefault(iid, []).append(b)
    answered = Counter(a.split("#")[0] for b in beats for a in (b.get("answers") or []))
    rows = []
    for item in items:
        covering = by_item.get(item["item_id"], [])
        purposes = sorted({b.get("purpose", "") for b in covering}, key=lambda p: HOW_ORDER.index(p) if p in HOW_ORDER else 99)
        questions = len(item.get("teacher_understanding") or [])
        rows.append({"item_id": item["item_id"], "page": item.get("page", 0), "kind": item.get("kind", ""),
                     "content": item.get("content", ""), "exam_importance": item.get("exam_importance", ""),
                     "beats": [_beat_row(b, times) for b in covering], "how": ", ".join(how_word(p) for p in purposes),
                     "questions": questions, "questions_answered": min(questions, answered.get(item["item_id"], 0)) if questions else 0,
                     "covered": bool(covering)})
    uncovered = [r for r in rows if not r["covered"]]
    outside = [_beat_row(b, times) for b in beats if b.get("basis") == "outside"]
    beyond = [dict(_beat_row(b, times), covers=[i for i in b.get("covers_item_ids") or [] if i not in assigned_ids])
              for b in beats if any(i not in assigned_ids for i in b.get("covers_item_ids") or [])]
    timed = sum(1 for b in beats if b.get("beat_id") in times)
    return {"schema": SCHEMA, "video_id": video_id, "title": plan.get("title") or script.get("title", ""),
            "kind": plan.get("kind", ""), "status": script.get("status", ""), "assigned": len(rows),
            "covered": len(rows) - len(uncovered), "beats": len(beats), "beats_timed": timed,
            "rows": rows, "uncovered": [{k: r[k] for k in ("item_id", "page", "kind", "content")} for r in uncovered],
            "outside_beats": outside, "beats_beyond_scope": beyond,
            "questions": sum(r["questions"] for r in rows), "questions_answered": sum(r["questions_answered"] for r in rows),
            "basis": dict(Counter(b.get("basis", "") for b in beats))}


# ---------------------------------------------------------------- the chapter

def chapter_coverage(chapter: dict, lesson: dict) -> dict:
    """Every teachable line of the chapter and the video that teaches it (383 lines for Money); lines no video is assigned to
    are listed under ``unassigned`` (must be empty)."""
    items = chapter.get("items") or {}
    teachable = [i for i in items.values() if i.get("teachable")]
    teachable.sort(key=lambda i: (i.get("page", 0), _item_order(i["item_id"])))
    video_of, videos = {}, []
    for vid in video_ids(lesson):
        plan, script = plan_video(lesson, vid), script_video(lesson, vid)
        if lesson_module.is_prerequisite_video(plan):
            scope = []
        else:
            scope = [i["item_id"] for i in assigned_items(chapter, plan, script)]
        covered = {iid for b in script.get("beats") or [] for iid in b.get("covers_item_ids") or []}
        for iid in scope:
            video_of.setdefault(iid, []).append((vid, iid in covered))
        videos.append({"video_id": vid, "title": plan.get("title") or script.get("title", ""), "kind": plan.get("kind", ""),
                       "status": script.get("status", ""), "assigned": len(scope), "covered": sum(1 for i in scope if i in covered),
                       "uncovered": [i for i in scope if i not in covered], "beats": len(script.get("beats") or [])})
    status = {v["video_id"]: v["status"] for v in videos}
    rows = []
    for item in teachable:
        where = video_of.get(item["item_id"], [])
        rows.append({"item_id": item["item_id"], "page": item.get("page", 0), "kind": item.get("kind", ""),
                     "content": item.get("content", ""), "exam_importance": item.get("exam_importance", ""),
                     "videos": [{"video_id": vid, "status": status.get(vid, ""), "covered": cov} for vid, cov in where]})
    unassigned = [r for r in rows if not r["videos"]]
    taught = sum(1 for r in rows if any(v["status"] == "passed" and v["covered"] for v in r["videos"]))
    return {"schema": CHAPTER_SCHEMA, "chapter": (chapter.get("map") or {}).get("chapter_title") or (chapter.get("course") or {}).get("title", ""),
            "teachable": len(rows), "assigned": len(rows) - len(unassigned), "taught_by_a_passed_video": taught,
            "rows": rows, "unassigned": [{k: r[k] for k in ("item_id", "page", "kind", "content")} for r in unassigned],
            "videos": videos}


def _item_order(item_id: str):
    try:
        page, item = item_id.split("-i")
        return int(page.lstrip("p")), int(item)
    except ValueError:
        return (0, 0)
