"""The film-first course studio, stage 1: a chapter's student questions (Navin, 18 November 2026).

Navin's decisions of 18 November 2026 (planning chat, decision cards):
  1. Every point of the book is taught in a video and kept in the notes; the video is made first, its length follows the
     point (a process or a structure gets a long cinematic film, a light point a short one).
  2. Games revise the whole chapter in each subject's own ways; every question gets at least one game stage.
  3. BIE writes each chapter's question list and Navin says yes before that chapter's videos are made.
  4. The frame is the same in every subject; colours and visuals follow the subject.
  5. Everything is made on the VM through Codex on Navin's ChatGPT plan; pictures come from AI (Codex image_gen).
  6. Navin looks at the first chapter before the whole book runs.

This stage reads the chapter's own text blocks (``bie.brain.pages``: the pipeline's source anchors such as
``p0003-b0007``) and asks the maker for the Chapter 17 shape: one big question, 3-5 pillars, and student questions that
together cover every teachable block. Code checks the answer (ids, coverage, counts, kinds, no source names on the
learner's screen) and sends the exact problems back. Each question carries what its film shows, how long it runs and its
game stage, so the later stages (films, games, Living Book) hang on the same question.
"""
from __future__ import annotations

import json
import re

KINDS = ("process", "structure", "classification", "comparison", "timeline", "cause_effect", "facts_numbers", "figure",
         "definition")
MECHANICS = ("drag_to_target", "choose_and_see", "build_sequence", "slider_cause_effect", "assemble_parts",
             "predict_then_run", "sort_groups", "route_flow")
FILM_LENGTHS = ("long", "short")
TEACHABLE_CHARS = 60            # a block shorter than this is a heading, caption or label: it need not have its own point
MIN_QUESTIONS, MAX_QUESTIONS = 4, 30
MIN_POINTS, MAX_POINTS = 1, 8
SOURCE_WORDS = re.compile(r"(?i)\b(according to the (book|text|author)|the book says|book mein|kitab (mein|kehti)|"
                          r"textbook|ncert|campbell|this chapter says|lekhak)\b")
QID = re.compile(r"^q[0-9]{2}$")
PID = re.compile(r"^p[0-9]$")

S = {"type": "string"}


# Navin's decision 4 (18 November 2026): one skeleton for every subject; the colours follow the subject.
SUBJECT_TINTS = (
    (r"biolog|botan|zoolog|life science|jeev|plant|animal|tissue|cell|ncert.*science", "#3f7d4e"),
    (r"geograph|bhugol|climate|monsoon|earth|environment", "#2c6e87"),
    (r"econom|arthshastra|money|bank|finance|budget|commerce", "#9a6b1f"),
    (r"histor|itihas|medieval|ancient|modern india|culture", "#8a3b2e"),
    (r"polit|polity|civics|constitution|governance|samvidhan", "#33508f"),
    (r"physic|bhautik|motion|electric|magnet|optic", "#4b4fa8"),
    (r"chemi|rasayan|reaction|organic", "#7a4a9a"),
    (r"math|ganit|algebra|geometry|calculus|statistic", "#245f9e"),
)


def subject_tint(course: str) -> str:
    text = (course or "").lower()
    for pattern, tint in SUBJECT_TINTS:
        if re.search(pattern, text):
            return tint
    return "#2c6e87"


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


SCHEMA = _obj({
    "chapter_title": S,
    "big_question": S,
    "pillars": _arr(_obj({"id": S, "title": S, "line": S})),
    "questions": _arr(_obj({
        "id": S, "pillar": S, "question": S, "hook": S,
        "points": _arr(_obj({"block_ids": _arr(S), "point": S, "kind": {"type": "string", "enum": list(KINDS)}})),
        "film": _obj({"length": {"type": "string", "enum": list(FILM_LENGTHS)}, "showing_moment": S}),
        "game_stage": _obj({"mechanic": {"type": "string", "enum": list(MECHANICS)}, "idea": S}),
    })),
})

INSTRUCTIONS = """You are BIE's course studio, planning ONE chapter of a book as a film-first course for {course}.
Language of every learner-facing line: {language} (Navin's spoken Hinglish in Roman script unless Hindi is asked; Hindi means
Devanagari).

What the course is (Navin's decisions):
- Every point of the chapter is taught in a video and kept in the notes. Videos come first; games revise; notes support the
  video. So the question list you write is the backbone of the whole course: one question = one film = one notes section.
- Split the chapter the way the approved golden chapter did: ONE big question for the chapter, 3 to 5 pillars (big themes),
  and student questions in the learner's own words, each opening with a curiosity (a real-life puzzle), never a heading.
- Every teachable block of the chapter (listed below with its id) must sit in at least one question. A block may come back
  in a later question only as a reminder. Keep the book's teaching order where one idea needs another first.
- Each question has 1 to 8 points. A point is one teachable idea of the book in one plain line, with the block ids it comes
  from and its kind: process, structure, classification, comparison, timeline, cause_effect, facts_numbers, figure or
  definition.
- film.length: "long" when the question holds a process, a structure to see inside, or a cause and effect to watch
  happen; "short" for light points (a definition, a list, a fact). film.showing_moment: the ONE thing that changes on
  screen and carries the idea (for example "the moist air block climbs the Ghats, cools, and rain starts on the windward
  side").
- game_stage: how the learner revises this question by acting, so that their choice makes something happen on screen
  (mechanics: drag_to_target, choose_and_see, build_sequence, slider_cause_effect, assemble_parts, predict_then_run,
  sort_groups, route_flow). Pick what fits the content; a plain quiz is not a game.
- Ids: pillars p1..p5, questions q01, q02, ... in teaching order.
- Never name the book, the author or the publisher, and never say "the book says": the learner meets the knowledge, not
  the source.

Answer with the JSON object only."""

PROBLEMS_PROMPT = ("BIE's code checked your question list and found these problems. Send the whole corrected JSON object "
                   "again, changing only what the problems need:\n- ")


def teachable(pages) -> dict:
    """{block id: text} for every block long enough to carry a teachable idea."""
    out = {}
    for page in pages:
        for block in page.blocks:
            text = " ".join((block.text or "").split())
            if len(text) >= TEACHABLE_CHARS:
                out[block.id] = text
    return out


def all_blocks(pages) -> dict:
    return {block.id: " ".join((block.text or "").split()) for page in pages for block in page.blocks}


def chapter_text(pages) -> str:
    lines = []
    for page in pages:
        lines.append(f"--- page {page.number} ---")
        for block in page.blocks:
            text = " ".join((block.text or "").split())
            if text:
                lines.append(f"[{block.id}] {text}")
    return "\n".join(lines)


def messages(pages, *, course: str, language: str) -> list:
    return [{"role": "system", "content": INSTRUCTIONS.format(course=course or "learners of this book",
                                                              language=language or "Hinglish")},
            {"role": "user", "content": "The chapter's text blocks, in reading order:\n\n" + chapter_text(pages)}]


def _strings(answer: dict):
    yield answer.get("big_question", "")
    for pillar in answer.get("pillars") or []:
        yield pillar.get("title", "")
        yield pillar.get("line", "")
    for q in answer.get("questions") or []:
        yield q.get("question", "")
        yield q.get("hook", "")
        for point in q.get("points") or []:
            yield point.get("point", "")


def problems(answer, known_ids, teachable_ids) -> list:
    """Everything wrong with a question list, as sentences the maker can act on (empty = passed)."""
    if not isinstance(answer, dict):
        return ["the answer is not a JSON object"]
    out = []
    pillars = answer.get("pillars") or []
    if not 3 <= len(pillars) <= 5:
        out.append(f"there are {len(pillars)} pillars; write 3 to 5")
    pillar_ids = [p.get("id") for p in pillars]
    if len(set(pillar_ids)) != len(pillar_ids) or any(not PID.match(str(i)) for i in pillar_ids):
        out.append("pillar ids must be unique, p1 to p5")
    questions = answer.get("questions") or []
    if not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        out.append(f"there are {len(questions)} questions; write {MIN_QUESTIONS} to {MAX_QUESTIONS}")
    seen_q, covered = set(), set()
    for number, q in enumerate(questions, 1):
        qid = q.get("id")
        if not QID.match(str(qid)) or qid in seen_q:
            out.append(f"question {number}: id must be unique, q01, q02, ...")
        seen_q.add(qid)
        if q.get("pillar") not in pillar_ids:
            out.append(f"{qid}: pillar {q.get('pillar')!r} is not one of the pillars")
        if len((q.get("question") or "").strip()) < 12:
            out.append(f"{qid}: the question is missing or too short")
        if len((q.get("hook") or "").strip()) < 12:
            out.append(f"{qid}: the hook (a real-life puzzle) is missing or too short")
        points = q.get("points") or []
        if not MIN_POINTS <= len(points) <= MAX_POINTS:
            out.append(f"{qid}: {len(points)} points; write {MIN_POINTS} to {MAX_POINTS}")
        for point in points:
            ids = point.get("block_ids") or []
            unknown = [i for i in ids if i not in known_ids]
            if not ids:
                out.append(f"{qid}: a point has no block ids")
            if unknown:
                out.append(f"{qid}: unknown block ids {', '.join(unknown[:5])}")
            if point.get("kind") not in KINDS:
                out.append(f"{qid}: kind {point.get('kind')!r} is not one of {', '.join(KINDS)}")
            covered.update(i for i in ids if i in known_ids)
        film = q.get("film") or {}
        if film.get("length") not in FILM_LENGTHS or len((film.get("showing_moment") or "").strip()) < 12:
            out.append(f"{qid}: film needs length long or short and a showing_moment")
        stage = q.get("game_stage") or {}
        if stage.get("mechanic") not in MECHANICS or len((stage.get("idea") or "").strip()) < 12:
            out.append(f"{qid}: game_stage needs a mechanic from the list and an idea")
    missing = [i for i in teachable_ids if i not in covered]
    if missing:
        out.append(f"{len(missing)} teachable blocks are in no question: " + ", ".join(missing[:25])
                   + (" ..." if len(missing) > 25 else ""))
    named = sorted({m.group(0) for text in _strings(answer) for m in [SOURCE_WORDS.search(text or "")] if m})
    if named:
        out.append("learner lines name the source; remove: " + ", ".join(named))
    return out


def coverage(answer: dict, teachable_ids) -> dict:
    covered = {i for q in answer.get("questions") or [] for p in q.get("points") or [] for i in p.get("block_ids") or []}
    hit = [i for i in teachable_ids if i in covered]
    return {"teachable_blocks": len(teachable_ids), "covered": len(hit),
            "percent": round(100 * len(hit) / len(teachable_ids), 1) if teachable_ids else 100.0,
            "missing": [i for i in teachable_ids if i not in covered]}


def parse(text: str):
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    try:
        return json.loads(text[text.find("{"): text.rfind("}") + 1] if "{" in text else text)
    except ValueError:
        return None


def plan(client, model: str, pages, *, course: str = "", language: str = "Hinglish", max_rounds: int = 3) -> dict:
    """Ask, check, send the problems back; at most ``max_rounds`` maker calls. Returns the record of the stage."""
    known = all_blocks(pages)
    teach = list(teachable(pages))
    convo = messages(pages, course=course, language=language)
    rounds, usage, answer, found = [], {"input_tokens": 0, "output_tokens": 0}, None, ["no answer yet"]
    for number in range(1, max_rounds + 1):
        reply = client.chat(model=model, messages=convo, schema=SCHEMA)
        for key in usage:
            usage[key] += int((reply.get("usage") or {}).get(key) or 0)
        answer = parse(reply.get("content", ""))
        found = problems(answer, known, teach)
        rounds.append({"round": number, "problems": found})
        if not found:
            break
        convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                         {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
    return {"answer": answer, "problems": found, "rounds": rounds, "usage": usage, "teachable": teach,
            "coverage": coverage(answer, teach) if isinstance(answer, dict) else None}


def ask(client, model: str, convo: list, schema: dict, check, *, max_rounds: int = 3,
        problems_prompt: str = "BIE's code checked your answer and found these problems. Send the whole corrected JSON "
                               "object again:\n- ") -> dict:
    """The studio's maker loop for the later stages: ask, let code check, send the exact problems back."""
    rounds, usage, answer, found = [], {"input_tokens": 0, "output_tokens": 0}, None, ["no answer yet"]
    for number in range(1, max_rounds + 1):
        reply = client.chat(model=model, messages=convo, schema=schema)
        for key in usage:
            usage[key] += int((reply.get("usage") or {}).get(key) or 0)
        answer = parse(reply.get("content", ""))
        found = check(answer)
        rounds.append({"round": number, "problems": found})
        if not found:
            break
        convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                         {"role": "user", "content": problems_prompt + "\n- ".join(found)}]
    return {"answer": answer, "problems": found, "rounds": rounds, "usage": usage}


LENGTH_WORD = {"long": "lambi film", "short": "chhoti film"}
MECHANIC_WORD = {"drag_to_target": "kheencho aur dekho", "choose_and_see": "chuno aur nateeja dekho",
                 "build_sequence": "kram lagao", "slider_cause_effect": "slider se kaaran-asar",
                 "assemble_parts": "hisse jodo", "predict_then_run": "pehle andaaza, phir dekho",
                 "sort_groups": "samooh mein baanto", "route_flow": "raasta banao"}


def markdown(record: dict, *, title: str = "") -> str:
    """QUESTIONS.md: the list Navin says yes to (Hinglish, short)."""
    a = record.get("answer") or {}
    cov = record.get("coverage") or {}
    lines = [f"# Sawaal-list · {a.get('chapter_title') or title}", "",
             f"Bada sawaal: **{a.get('big_question', '')}**", "",
             f"Kitab ki baatein jo kisi sawaal mein aayi: {cov.get('covered', 0)} / {cov.get('teachable_blocks', 0)} "
             f"({cov.get('percent', 0)}%)", ""]
    pillars = {p.get("id"): p for p in a.get("pillars") or []}
    for pid, pillar in pillars.items():
        lines += [f"## {pillar.get('title', '')}", "", pillar.get("line", ""), ""]
        for q in [q for q in a.get("questions") or [] if q.get("pillar") == pid]:
            film = q.get("film") or {}
            stage = q.get("game_stage") or {}
            lines += [f"**{q.get('id', '')[1:]} · {q.get('question', '')}**", "",
                      f"- Paheli: {q.get('hook', '')}",
                      f"- Baatein ({len(q.get('points') or [])}): " + "; ".join(p.get("point", "") for p in q.get("points") or []),
                      f"- Film: {LENGTH_WORD.get(film.get('length'), '')}. Screen par: {film.get('showing_moment', '')}",
                      f"- Game: {MECHANIC_WORD.get(stage.get('mechanic'), '')}. {stage.get('idea', '')}", ""]
    if record.get("problems"):
        lines += ["## Code ki jaanch mein bachi kamiyan", ""] + [f"- {p}" for p in record["problems"]]
    return "\n".join(lines).strip() + "\n"
