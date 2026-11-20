"""The film-first course studio, stage 4: the Living Book, the chapter's notes (Navin, 18 November 2026).

Navin's order: films first, then games, then the notes, which support the films the way the Monsoon notes supported the
Monsoon film and the Chapter 17 Living Book covered the whole chapter. Per student question the maker writes the note
cards (together they cover every point of the question), a short class moment with Asha, Dev and the Teacher that clears
the usual confusion, one "yaad rakho" line and a check question. Code adds the film's own picture with its pins, the
film's diagram and the film's takeaway lines, checks everything and builds one phone page for the chapter
(``studio_book_player.html``) whose sections link to each question's film and game.
"""
from __future__ import annotations

import json
import re

from .studio import SOURCE_WORDS, ask

S = {"type": "string"}
SPEAKERS = ("Asha", "Dev", "Teacher")
CAUTION = re.compile(r"(?i)\b(illustrative|for illustration|the source does not say|source mein nahi|not in the source)\b")


def _obj(properties: dict) -> dict:
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


SCHEMA = _obj({
    "cards": _arr(_obj({"label": S, "text": S, "covers": _arr({"type": "integer"})})),
    "scene": _arr(_obj({"who": {"type": "string", "enum": list(SPEAKERS)}, "line": S})),
    "remember": S,
    "check": _obj({"question": S, "choices": _arr(S), "correct": {"type": "integer"}, "explanation": S}),
})

INSTRUCTIONS = """You are BIE's notes writer and teacher. Write the Living Book notes for ONE student question of a {course}
chapter. The learner has watched this question's film; the notes are what they read and keep. Learner-facing language:
{language} (Navin's natural spoken Hinglish in Roman script, simple and exact; keep the subject's key terms in English
where learners use them).

- cards: 3 to 8 note cards. label is 2 to 6 words; text is 1 to 3 short sentences that teach one idea completely (what,
  how, why, with the exact terms, numbers and names from the chapter). covers lists the indexes (0-based) of the question's
  points the card teaches; together the cards cover every point. Add what the film could not say: definitions, numbers,
  exceptions, comparisons.
- scene: a class moment of 3 to 6 lines between Asha, Dev (students) and Teacher that clears the most common confusion
  about this question. The students ask or get it wrong; the Teacher fixes it in plain words.
- remember: one line to remember for the exam.
- check: one question that makes the learner think (apply, not recall), 3 or 4 choices, correct = the index (0-based)
  of the right choice, explanation in 1 or 2 lines.
- Never "the book says", never a source name, never a caution line ("assume", "illustrative").

Answer with the JSON object only."""


def messages(question: dict, *, course: str, language: str, chapter: str = "") -> list:
    points = "\n".join(f"{i}. ({p.get('kind')}) {p.get('point')}" for i, p in enumerate(question.get("points") or []))
    user = (f"Chapter: {chapter}\nQuestion {question.get('id')}: {question.get('question')}\nCuriosity: {question.get('hook')}\n"
            f"Points to cover:\n{points}\n"
            + ("\nWhat the film said:\n" + question["film_text"] if question.get("film_text") else "")
            + ("\nThe book's lines for these points:\n" + question["source_text"] if question.get("source_text") else ""))
    return [{"role": "system", "content": INSTRUCTIONS.format(course=course or "school", language=language or "Hinglish")},
            {"role": "user", "content": user}]


def problems(notes, question: dict) -> list:
    if not isinstance(notes, dict):
        return ["the answer is not a JSON object"]
    out, covered = [], set()
    cards = notes.get("cards") or []
    if not 3 <= len(cards) <= 8:
        out.append(f"there are {len(cards)} cards; write 3 to 8")
    for k, card in enumerate(cards, 1):
        covered.update(card.get("covers") or [])
        words = len((card.get("label") or "").split())
        if not 1 <= words <= 7:
            out.append(f"card {k}: label must be 2 to 6 words")
        if len((card.get("text") or "").strip()) < 40:
            out.append(f"card {k}: text is too short to teach the idea")
    missing = [i for i in range(len(question.get("points") or [])) if i not in covered]
    if missing:
        out.append("no card covers the question's points " + ", ".join(map(str, missing)))
    scene = notes.get("scene") or []
    if not 3 <= len(scene) <= 6:
        out.append(f"the scene has {len(scene)} lines; write 3 to 6")
    if scene and not any(line.get("who") == "Teacher" for line in scene):
        out.append("the scene needs the Teacher to clear the confusion")
    if any(line.get("who") not in SPEAKERS for line in scene):
        out.append("scene speakers must be Asha, Dev or Teacher")
    if len((notes.get("remember") or "").strip()) < 15:
        out.append("remember (the one line for the exam) is missing")
    check = notes.get("check") or {}
    choices = [c.strip() for c in check.get("choices") or []]
    if not 3 <= len(choices) <= 4 or len(set(c.lower() for c in choices)) != len(choices) or not all(choices):
        out.append("check needs 3 or 4 different choices")
    if not 0 <= int(check.get("correct", -1)) < len(choices):
        out.append("check.correct must be the index of a choice")
    if len((check.get("question") or "").strip()) < 15 or len((check.get("explanation") or "").strip()) < 20:
        out.append("check needs a full question and an explanation")
    texts = ([c.get("label") for c in cards] + [c.get("text") for c in cards] + [l.get("line") for l in scene]
             + [notes.get("remember"), check.get("question"), check.get("explanation")] + choices)
    for text in texts:
        if text and SOURCE_WORDS.search(text):
            out.append(f"names the source: {text[:60]!r}")
        if text and CAUTION.search(text):
            out.append(f"a caution line reaches the learner: {text[:60]!r}")
    return out


def write(client, model: str, question: dict, *, course: str = "", language: str = "Hinglish", chapter: str = "",
          max_rounds: int = 3) -> dict:
    record = ask(client, model, messages(question, course=course, language=language, chapter=chapter), SCHEMA,
                 lambda notes: problems(notes, question), max_rounds=max_rounds)
    record["notes"] = record.pop("answer")
    return record


def film_figures(film: dict, images: dict) -> dict:
    """From the question's film: the first photo with its pins (at most 6), the first diagram, and the takeaway lines."""
    photo, diagram = None, None
    for shot in film.get("shots") or []:
        visual = shot.get("visual") or {}
        if visual.get("type") == "photo" and photo is None and images.get(shot.get("id")):
            pins, seen = [], set()
            for sentence in shot.get("sentences") or []:
                for pin in sentence.get("pins") or []:
                    if pin.get("label") not in seen and len(pins) < 6:
                        seen.add(pin.get("label"))
                        pins.append({"t": pin.get("label"), "x": pin.get("x"), "y": pin.get("y")})
            photo = {"img": images[shot.get("id")], "pins": pins, "caption": shot.get("key", "")}
        if visual.get("type") == "diagram" and diagram is None and visual.get("svg"):
            diagram = {"svg": visual["svg"], "caption": shot.get("key", "")}
    keys = [s.get("key") for s in film.get("shots") or [] if s.get("key")]
    return {"photo": photo, "diagram": diagram, "keys": keys}


def player_data(sections: list, *, plan: dict, tint: str) -> dict:
    """The JSON the Living Book reads: pillars, and one section per question in plan order."""
    by_q = {s["qid"]: s for s in sections}
    pillars = []
    for pillar in plan.get("pillars") or []:
        items = []
        for q in plan.get("questions") or []:
            if q.get("pillar") == pillar.get("id") and q.get("id") in by_q:
                s = by_q[q["id"]]
                items.append({"qid": q["id"], "question": q.get("question"), "hook": q.get("hook"),
                              "notes": s.get("notes"), "figures": s.get("figures") or {},
                              "film": s.get("film_link", ""), "game": s.get("game_link", "")})
        if items:
            pillars.append({"id": pillar.get("id"), "title": pillar.get("title"), "line": pillar.get("line"), "items": items})
    return {"chapter": plan.get("chapter_title", ""), "big": plan.get("big_question", ""), "tint": tint, "pillars": pillars}


def html(data: dict, template: str) -> str:
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("/*__BOOK__*/null", blob, 1)
