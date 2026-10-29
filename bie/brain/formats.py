"""The video path's formats, locked (Task 046 Part C, work D; Navin's verdict brief, 29 October 2026).

Every hand-over between two sections of the video path is one JSON file with a ``schema`` field ``"<id>/<version>"`` and
one definition here: the chapter map (Section 1 → everything after), the lesson plan (Section 2 → the director, the game,
the notes), the canvas plan of a part in mode B and the world plan of a part in mode C (the director → the compilers),
the video spec (the compilers → the render), the render outputs (summary, join, cost: the render → the review page) and
the review records (the page tool → Navin, the game and the notes). A validator runs at every section boundary: a value
of the wrong shape stops the run with a ``FormatError`` that names the file, the format and the field.

Reserved for Task 047 (voice): every beat may carry ``audio`` = {"file", "duration", "words": [{"w", "start", "end"}]};
``voice_of`` turns the beats that have it into the ``voice`` that ``timing.build`` reads, so the animation lands on the
real spoken words the day the voice section writes them, with no change of format.

The change rule (``docs/bie/CONTRACTS.md`` section 6): a format changes only by bumping its version here, adding the
migration step that brings an older file up (``MIGRATIONS``), and re-checking ``tests/fixtures/passed_outputs/``
(``tests/test_task046c_formats.py`` does the recheck). A reader always ``accept``s a file (migrate, then check); a writer
always ``stamp``s and ``check``s it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from bie.model_gateway.schema_validation import SchemaValidationError, validate as _validate


class FormatError(ValueError):
    """A hand-over file of the wrong shape: the message names the file, the format and the field."""


# ---------------------------------------------------------------- schema pieces (the gateway validator's dialect)

S = {"type": "string"}
N = {"type": "number"}
B = {"type": "boolean"}


def A(items: dict) -> dict:
    return {"type": "array", "items": items}


def O(properties: dict, required=None) -> dict:
    """An object whose listed keys must be present; unknown keys are allowed, so a file written by a newer BIE still reads."""
    return {"type": "object", "required": list(properties) if required is None else list(required), "properties": properties}


COURSE = O({"title": S, "subject": S, "learners": S, "language": S, "level": S}, required=["title", "subject", "learners"])

# -- the chapter map (Section 1)
TEACHER_QUESTION = O({"depth": N, "ask": S, "question": S, "answer": S, "basis": S}, required=["question", "answer", "basis"])
ITEM = O({"item_id": S, "kind": S, "content": S, "teachable": B, "page": N, "teacher_understanding": A(TEACHER_QUESTION),
          "unpack": {}, "exam_importance": S, "content_type": S},                  # unpack: a dict since Task 045d, None before
         required=["item_id", "content", "teachable"])          # what every reader needs; the rest is typed when present
CONCEPT = O({"concept_id": S, "name": S, "item_ids": A(S), "content_type": S}, required=["concept_id", "name", "item_ids"])
PREREQUISITE = O({"name": S, "why_needed": S, "needed_for": A(S), "basis": S}, required=["name"])
CHAPTER_MAP = O({"schema": S, "course": COURSE, "level": S, "source_sha256": S, "page_count": N, "rulebook_version": S,
                 "pages": A(O({"page": N, "status": S}, required=["page"])),
                 "items": {"type": "object"},
                 "map": O({"chapter_title": S, "concepts": A(CONCEPT), "prerequisites_to_teach": A(PREREQUISITE)}, required=[]),
                 "map_status": S},
                required=["schema", "course", "source_sha256", "pages", "items", "map", "map_status"])

# -- the lesson plan (Section 2)
WORD = O({"w": S, "start": N, "end": N})
AUDIO = O({"file": S, "duration": N, "words": A(WORD)})            # reserved for Task 047: written by the voice section
BEAT = O({"beat_id": S, "part_id": S, "step": N, "purpose": S, "say": S, "covers_item_ids": A(S), "answers": A(S), "on_screen": S,
          "basis": {"type": "string", "enum": ["book", "outside", "mixed"]}, "source": S, "subtitle": S, "voice": S, "audio": AUDIO},
         required=["beat_id", "part_id", "step", "purpose", "say", "covers_item_ids", "answers", "on_screen", "basis", "source"])
PLAN_VIDEO = O({"video_id": S, "title": S, "kind": S, "concept_ids": A(S), "prerequisites_taught": A(S)}, required=["video_id", "title"])
SCRIPT_VIDEO = O({"video_id": S, "title": S, "status": S, "kind": S, "rounds": N, "parts": A({"type": "object"}),
                  "card_parts": A(O({"part_id": S, "type": S, "item_ids": A(S)})), "beats": A(BEAT)},
                 required=["video_id", "title", "status", "card_parts", "beats"])
LESSON_PLAN = O({"schema": S, "course": COURSE, "source_sha256": S, "rulebook_version": S, "maker_route": S, "plan_status": S,
                 "plan": O({"videos": A(PLAN_VIDEO), "chapter_flow": S}, required=["videos"]),
                 "videos": A(SCRIPT_VIDEO), "quality": {"type": "object"}},
                required=["schema", "course", "rulebook_version", "plan_status", "plan", "videos", "quality"])

# -- the director's plans (Section 3c): a part in mode B on the canvas, a part in mode C in a world
PLAN_BEAT = O({"beat_id": S, "say": S, "caption": S}, required=["beat_id", "say"])
CANVAS_B_PLAN = O({"schema": S, "id": S, "part_id": S, "theme": S, "grid": A(N), "beats": A(PLAN_BEAT), "touches": B,
                   "nodes": A(O({"id": S, "kind": S, "cue": A({})}, required=["id", "kind"])), "graph": {"type": "object"},
                   "focus": A({"type": "object"})},
                  required=["id", "part_id", "beats", "nodes"])
WORLD_C_PLAN = O({"schema": S, "id": S, "part_id": S, "world_width": N, "beats": A(PLAN_BEAT), "kit": S,
                  "elements": A(O({"id": S, "kind": S, "cue": A({})}, required=["id", "kind"])),     # a static element has no cue
                  "camera": A(O({"cue": A({})}, required=[]))},
                 required=["id", "part_id", "beats", "kit", "elements", "camera"])

# -- the video spec (the compilers → the render)
CAPTION = O({"at": N, "until": N, "text": S, "beat_id": S}, required=["at", "until", "text"])
LAYER = O({"id": S, "type": S, "at": N}, required=["id", "type"])
SCENE = O({"id": S, "duration": N, "layers": A(LAYER), "camera": A({"type": "object"}), "captions": A(CAPTION)},
          required=["id", "duration", "layers"])
VIDEO_SPEC = O({"schema": S, "fps": N, "width": N, "height": N, "captions": B, "scenes": A(SCENE)})

# -- the canvas section's summary (canvas.json)
CANVAS_PART = O({"id": S, "part_id": S, "mode": S, "status": S, "seconds": N, "beats": N}, required=["id", "part_id", "mode", "status"])
CANVAS_VIDEO = O({"video_id": S, "title": S, "parts": A(CANVAS_PART), "status": S, "seconds": N}, required=["video_id", "parts", "status"])
CANVAS_SUMMARY = O({"schema": S, "course": COURSE, "rulebook_version": S, "maker_route": S, "videos": A(CANVAS_VIDEO),
                    "missing_kits": A(S), "quality": {"type": "object"}},
                   required=["schema", "course", "maker_route", "videos", "missing_kits", "quality"])

# -- the render outputs (tools/render_spec.py)
RENDER_COST = O({"schema": S, "chunks": N, "frames": N, "video_seconds": N, "video_minutes": N, "render_seconds": N,
                 "seconds_per_video_second": N, "wall_clock_minutes_parallel": N, "machine_minutes": N, "inr_at_list_price": N},
                required=["chunks", "frames", "video_seconds", "video_minutes", "machine_minutes", "inr_at_list_price"])
RENDER_JOIN = O({"schema": S, "video": S, "review": S, "review_bytes": N, "video_bytes": N, "seconds": N, "chunks": N},
                required=["video", "review", "review_bytes", "video_bytes", "seconds", "chunks"])
RENDER_SUMMARY = O({"schema": S, "run_id": S, "sha": S, "run_url": S, "cost": {"type": "object"}, "join": {"type": "object"}})

# -- the review records (tools/task046c_page.py, tools/task046c_chapter_page.py; bie/brain/coverage.py)
COVERED_BEAT = O({"beat_id": S, "purpose": S, "how": S, "basis": S, "scene": S, "time": S, "say": S}, required=["beat_id", "purpose", "how", "basis"])
COVERAGE_ROW = O({"item_id": S, "page": N, "kind": S, "content": S, "beats": A(COVERED_BEAT), "how": S, "questions": N,
                  "questions_answered": N, "covered": B})
REVIEW_RECORD = O({"schema": S, "video_id": S, "title": S, "status": S, "assigned": N, "covered": N, "beats": N, "beats_timed": N,
                   "rows": A(COVERAGE_ROW), "uncovered": A({"type": "object"}), "outside_beats": A(COVERED_BEAT),
                   "beats_beyond_scope": A({"type": "object"}), "questions": N, "questions_answered": N, "basis": {"type": "object"}})
CHAPTER_REVIEW_RECORD = O({"schema": S, "chapter": S, "teachable": N, "assigned": N, "taught_by_a_passed_video": N,
                           "rows": A(O({"item_id": S, "page": N, "kind": S, "content": S,
                                        "videos": A(O({"video_id": S, "status": S, "covered": B}))})),
                           "unassigned": A({"type": "object"}),
                           "videos": A(O({"video_id": S, "status": S, "assigned": N, "covered": N, "uncovered": A(S), "beats": N}))})


# ---------------------------------------------------------------- the formats

def _chapter_map_extra(value: dict) -> list:
    """Every item (keyed by its id) has the item shape; a passed map names its concepts; a map that failed is written too
    (a resume continues it) and may be empty."""
    for iid, item in (value.get("items") or {}).items():
        try:
            _validate(item, ITEM, path=f"$.items.{iid}")
        except SchemaValidationError as exc:
            return [str(exc)]
        if item.get("item_id") != iid:
            return [f"$.items.{iid}.item_id: {item.get('item_id')!r} is not its key"]
    if value.get("map_status") == "passed" and not (value.get("map") or {}).get("concepts"):
        return ["$.map.concepts: missing (map_status is passed)"]
    return []


def _lesson_plan_extra(value: dict) -> list:
    """Every beat's part is a card part of its video (or "" for the hook and the recap), every passed video has beats."""
    for n, video in enumerate(value.get("videos") or []):
        parts = {p["part_id"] for p in video.get("card_parts") or []}
        for m, beat in enumerate(video.get("beats") or []):
            if beat.get("part_id") and beat["part_id"] not in parts:
                return [f"$.videos[{n}].beats[{m}].part_id: {beat['part_id']!r} is not a card part of {video.get('video_id')}"]
        if video.get("status") == "passed" and not video.get("beats"):
            return [f"$.videos[{n}].beats: a passed script has beats"]
    return []


def _video_spec_extra(value: dict) -> list:
    """Scene ids are unique and every caption ends after it starts, inside its scene."""
    seen = set()
    for n, scene in enumerate(value.get("scenes") or []):
        if scene.get("id") in seen:
            return [f"$.scenes[{n}].id: {scene.get('id')!r} is used twice"]
        seen.add(scene.get("id"))
        for m, cap in enumerate(scene.get("captions") or []):
            if not (0 <= cap["at"] < cap["until"] <= scene["duration"]):
                return [f"$.scenes[{n}].captions[{m}]: at {cap['at']}, until {cap['until']} is outside the scene's {scene['duration']} frames"]
    return []


@dataclass(frozen=True)
class Format:
    id: str
    version: int
    schema: dict
    file: str
    written_by: str
    read_by: tuple
    note: str = ""
    since: str = ""
    extra: object = None          # a callable(value) -> [problem]: what a JSON shape cannot say

    @property
    def tag(self) -> str:
        return f"{self.id}/{self.version}"


FORMATS = {
    "chapter_map": Format("bie.brain.chapter-map", 2, CHAPTER_MAP, "chapter_map.json",
                          "Section 1 (bie/brain/understanding.py, run_chapter)",
                          ("Section 2 lesson", "Section 3c canvas", "the game (Task 049)", "the notes (Task 050)", "the review pages"),
                          "items keyed by item id (page, kind, content, teachable, teacher questions, unpack); map.concepts assign items to concepts",
                          "2026-10-24 (/2: the unpack of Task 045d); locked 2026-10-29", extra=_chapter_map_extra),
    "lesson_plan": Format("bie.brain.lesson", 3, LESSON_PLAN, "lesson_plan.json",
                          "Section 2 (bie/brain/lesson.py, run_lesson)",
                          ("Section 3c canvas", "the game (Task 049)", "the notes (Task 050)", "the review pages (coverage)"),
                          "plan.videos (concept_ids) and videos[].beats (say, covers_item_ids, answers, basis, source; audio reserved for the voice)",
                          "2026-10-29 (/3: every beat carries source, S2-10; audio reserved for Task 047); earlier files are migrated",
                          extra=_lesson_plan_extra),
    "canvas_b_plan": Format("bie.brain.canvas-b-plan", 1, CANVAS_B_PLAN, "plans/<part>.plan.json",
                            "Section 3c, mode B (bie/brain/canvas_director.py)", ("bie/brain/canvas.py compile_plan", "the review page"),
                            "nodes with cues [beat_id, word]; the beats are the part's beats of the lesson plan", "2026-10-29"),
    "world_c_plan": Format("bie.brain.world-c-plan", 1, WORLD_C_PLAN, "plans/<part>.plan.json",
                           "Section 3c, mode C (bie/brain/canvas_director.py)", ("bie/brain/video/world.py compile_world", "the review page"),
                           "elements of a kit with cues; a camera path", "2026-10-29"),
    "video_spec": Format("bie.video-spec", 1, VIDEO_SPEC, "video_specs/<video>.json",
                         "the compilers (bie/brain/canvas.py, bie/brain/video/world.py) through the canvas section",
                         ("tools/render_spec.py (chunks, measure)", "bie/brain/video/render.py", "the review page (captions → beat times)"),
                         "scenes in part order; every caption carries its beat_id", "2026-10-29 (was bie.brain.canvas-plan/1; migrated)",
                         extra=_video_spec_extra),
    "canvas_summary": Format("bie.brain.canvas", 1, CANVAS_SUMMARY, "canvas.json",
                             "Section 3c (bie/brain/canvas_director.py)", ("the review page", "the render workflow"),
                             "one row per video with its parts (mode, status, seconds), the missing kits, the quality numbers", "2026-10-28"),
    "render_cost": Format("bie.render.cost", 1, RENDER_COST, "cost.json", "tools/render_spec.py measure", ("summary", "the review page"),
                          "frames, minutes, machine minutes, rupees at the list price", "2026-10-29"),
    "render_join": Format("bie.render.join", 1, RENDER_JOIN, "join.json", "tools/render_spec.py join", ("summary", "the review page"),
                          "the joined MP4 and the ≤ 720p review copy with their sizes", "2026-10-29"),
    "render_summary": Format("bie.render-spec.summary", 1, RENDER_SUMMARY, "summary.json", "tools/render_spec.py summary",
                             ("the review page",), "the run, the sha, the cost and the join", "2026-10-28"),
    "review_record": Format("bie.brain.coverage", 1, REVIEW_RECORD, "<page>.coverage.json",
                            "tools/task046c_page.py (bie/brain/coverage.py video_coverage)", ("Navin", "the game (Task 049)", "the notes (Task 050)"),
                            "which book lines the video taught, by which beats, when and how", "2026-10-29"),
    "chapter_review_record": Format("bie.brain.coverage.chapter", 1, CHAPTER_REVIEW_RECORD, "<page>.coverage.json",
                                    "tools/task046c_chapter_page.py (bie/brain/coverage.py chapter_coverage)", ("Navin",),
                                    "every teachable line → the video that teaches it", "2026-10-29"),
}

# The fields the game (Task 049) and the notes (Task 050) read, so the formats are locked for them too.
READERS = {
    "game (Task 049; bie/brain/game.py, game_build.py)": {
        "chapter_map": ["items.<id>.item_id", "items.<id>.content", "items.<id>.content_type", "items.<id>.teachable", "items.<id>.teacher_understanding"],
        "lesson_plan": ["videos[*].video_id", "videos[*].beats[*].covers_item_ids", "videos[*].beats[*].say"],
        "review_record": ["rows[*].item_id", "rows[*].beats[*].beat_id", "rows[*].beats[*].time"],
    },
    "notes (Task 050; bie/brain/notes.py)": {
        "chapter_map": ["map.concepts[*].item_ids", "items.<id>.kind", "items.<id>.content", "items.<id>.teacher_understanding"],
        "lesson_plan": ["videos[*].video_id", "videos[*].title", "videos[*].beats[*].say", "videos[*].beats[*].covers_item_ids",
                        "videos[*].beats[*].source"],
        "review_record": ["rows[*].item_id", "rows[*].how", "outside_beats[*].beat_id"],
    },
}


def tag(name: str) -> str:
    return FORMATS[name].tag


def parse_tag(value) -> tuple:
    """("id", version) of a value's schema field; ("", 0) when it has none."""
    text = (value or {}).get("schema") if isinstance(value, dict) else None
    if not isinstance(text, str) or "/" not in text:
        return "", 0
    ident, _, version = text.rpartition("/")
    return ident, int(version) if version.isdigit() else 0


# ---------------------------------------------------------------- migrations: an older file brought up, never a hand edit

def _lesson_2_to_3(value: dict) -> dict:
    for video in value.get("videos") or []:
        for beat in video.get("beats") or []:
            beat.setdefault("source", "")
    return value


def _spec_from_canvas_plan(value: dict) -> dict:
    return value                                   # the same shape under its own name; captions may lack beat_id (matched by order)


MIGRATIONS = {
    "lesson_plan": {("bie.brain.lesson", 2): _lesson_2_to_3, ("bie.brain.lesson", 1): _lesson_2_to_3, ("", 0): _lesson_2_to_3},
    "video_spec": {("bie.brain.canvas-plan", 1): _spec_from_canvas_plan, ("bie.render-spec", 1): _spec_from_canvas_plan},
}


def migrate(name: str, value: dict) -> dict:
    """The value at the current version: a file of an older version goes through its steps; one with no schema field (the
    plans and the render outputs before 29 October 2026, a hand-built lesson in a test) is taken as the version before the
    stamp existed, brought up by the ("", 0) step when the format has one, and stamped."""
    fmt = FORMATS[name]
    ident, version = parse_tag(value)
    if not ident:
        step = MIGRATIONS.get(name, {}).get(("", 0))
        return stamp(name, step(value) if step else value)
    if (ident, version) == (fmt.id, fmt.version):
        return value
    step = MIGRATIONS.get(name, {}).get((ident, version))
    if step is None:
        raise FormatError(f"{fmt.file} ({fmt.tag}): schema {ident}/{version} is not a version this BIE can migrate")
    return stamp(name, step(value))


# ---------------------------------------------------------------- stamp, check, accept

def stamp(name: str, value: dict) -> dict:
    value["schema"] = FORMATS[name].tag
    return value


def problems(name: str, value) -> list:
    """The first field that is wrong, as one problem ("$.videos[2].beats[3].basis: enum"), or []."""
    try:
        _validate(value, FORMATS[name].schema)
    except SchemaValidationError as exc:
        return [str(exc)]
    ident, version = parse_tag(value)
    fmt = FORMATS[name]
    if ident and (ident, version) != (fmt.id, fmt.version):
        return [f"$.schema: {ident}/{version} is not {fmt.tag}"]
    return list(fmt.extra(value)) if fmt.extra else []


def check(name: str, value, *, where: str = "") -> dict:
    """A writer's check: the value must already be the current version; the wrong shape stops the run naming the field."""
    found = problems(name, value)
    if found:
        fmt = FORMATS[name]
        raise FormatError(f"{where or fmt.file} ({fmt.tag}): {found[0]}")
    return value


def accept(name: str, value, *, where: str = "") -> dict:
    """A reader's check: an older file is migrated first, then checked."""
    return check(name, migrate(name, value), where=where)


# ---------------------------------------------------------------- the voice fields, reserved for Task 047

def voice_of(beats) -> dict:
    """{beat_id: {"duration", "words"}} from the beats that carry ``audio`` (the voice section's output), the shape
    ``timing.build`` reads; {} until the voice exists, so timing falls back to the text."""
    out = {}
    for b in beats or []:
        audio = b.get("audio") if isinstance(b, dict) else None
        if audio and audio.get("words") and audio.get("duration"):
            out[b["beat_id"]] = {"duration": float(audio["duration"]),
                                 "words": [{"w": w["w"], "start": float(w["start"]), "end": float(w["end"])} for w in audio["words"]]}
    return out


# ---------------------------------------------------------------- a table for the docs

def describe() -> str:
    """The formats as a Markdown table (CONTRACTS.md section 6 is kept in step with it by a test)."""
    lines = ["| Hand-over | Schema | File | Written by | Read by | Holds | Since |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for name, f in FORMATS.items():
        lines.append(f"| {name} | `{f.tag}` | `{f.file}` | {f.written_by} | {'; '.join(f.read_by)} | {f.note} | {f.since} |")
    return "\n".join(lines)
