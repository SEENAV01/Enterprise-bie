"""The chapter's script: the whole chapter taught once, in one teacher's own words, before any video, note or game is
made (Navin, 22 November 2026).

Navin: "maan lo maine chapter ko poora padh liya hai, mai BIE hun ... mai apni ek script banaunga poore chapter par kyunki
mujhe poora chapter yaad hai; kitab mein jo cheezen hain unhe aapas mein jodke poore chapter ko kaise progress karna hai
link karke poore ek chapter ki script banaunga; phir video maker us script ke hisab se poore chapter ko video ke tukdon
mein baantega". And: "script wo poora gyan hai jo hume bache ko dena hai; notes us gyan ko behtar dhang se organise karke
present karne ka tarika hai" (the script is the knowledge; video, notes and games each present it in their own way and
never write their own story); "chapter 11 ki saari cheezen bache ko samajh aa jaayein, aage wo koi is par based deep book
bhi padhe to wo book use samajh aa jaaye". Card, 22 November 2026: "Poora chapter ek saath".

Input: Section 1's chapter map (``chapter_map.json``), given whole as the chapter file (``chapter_file.markdown``), and,
when the from-run is a naksha run, its two plans (``naksha.json``) as ideas for each heading (not the cut into videos).

How: the script is written heading by heading in the book's order (the opening, 11.1, 11.2 ... 11.10.4). Every call gets
the whole chapter file, the whole script written so far, the terms, analogies and examples already used, this heading's
items and the plan ideas, so one teacher with one memory writes the whole chapter. Each heading's part is checked by code
before the next is written (problems go back, at most ``max_rounds``):

* NCERT line by line: every teachable body item of the heading is in the "teaches" of exactly one point, and the point
  speaks at least one of its key words; no item of another heading, no unknown id.
* Terms: every short form or formula the chapter opens (★) in this heading's items is opened here with its meaning, and
  every other first term is at least said where its line is taught; a term opened earlier is never defined again; a short
  form of a later heading is not used before it is opened (a pointer such as "aage dekhenge" is fine).
* No repetition: no sentence says again what an earlier sentence of the script said; an analogy or an example is used
  once in the chapter; a real-world use is a thing in life, not a study task.
* The teacher's voice: Roman script, sentences under 40 words, a screen line per point (what explains the words), never a
  caution line.

Output: ``script.json`` (the parts, each point with its id "11.6.1-k3": the knowledge points that video, notes and games
will account for), ``SCRIPT.md`` and ``SCRIPT.html`` (Navin's script page: each heading's script beside the NCERT lines
it teaches), ``record.json`` (rounds and problems per heading).
"""
from __future__ import annotations

import html as html_module
import json
import re

from . import chapter_file, studio_naksha
from .studio import parse
from .studio_book import CAUTION
from .studio_film import _content_words, _spoken_words

KINDS = ("explain", "question", "example", "analogy", "real_world", "recall", "activity", "story", "figure", "summary")
MAX_WORDS = 40                 # words in one spoken sentence (Navin's Hinglish rule, Task 045)
SAME_SENTENCE = 0.6            # share of shared words above which a sentence says again what another said
SAME_ANALOGY = studio_naksha.SAME_ANALOGY
SAME_EXAMPLE = 0.6
WORDS_PER_MINUTE = 130         # spoken Hinglish
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
FORWARD = re.compile(r"\b(aage|baad mein|baad me|agle|aane wale|later|next)\b", re.I)
WORD = re.compile(r"[A-Za-z]{3,}")
FILLER = studio_naksha.FILLER | {"hum", "hai", "hain", "toh", "tho", "yeh", "woh", "kya", "nahi", "bhi", "kar", "karta",
                                 "karte", "karti", "hota", "hoti", "hote", "this", "that", "here"}

S = {"type": "string"}


def _obj(properties: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


POINT = _obj({
    "id": S,
    "kind": {"type": "string", "enum": list(KINDS)},
    "teaches": _arr(S),
    "recalls": _arr(S),
    "says": _arr(S),
    "screen": S,
    "terms": _arr(_obj({"term": S, "meaning": S})),
    "outside_book": S,
})
SCHEMA = _obj({"section": S, "points": _arr(POINT), "bridge": S})

RULES = """You are BIE's teacher: the best {subject} teacher for {learners} ({exam}). You have read the whole chapter and
you now write its script: everything the learner must come to know, taught once, in your own words, in the book's order,
each idea linked to what came before. Videos, notes and games are made from this script later (each presents the same
knowledge in its own way), so the script holds the knowledge fully; never write shot directions or "is video mein" in what
you say.

Navin's words for the script (22 November 2026): the teacher explains every single thing of the chapter in his own words,
in the right order, so that the whole chapter makes sense to the learner, and the base is so sound that a deeper book on
the same topic would make sense to them later.

You write the script one heading at a time; this message asks for one heading. You see the whole chapter file (every item
with its id, role, terms, why steps and what comes first), the script written so far, and ideas from the teaching plan.
Continue as the same teacher: same voice, never repeating what the script already said.

Rules:
- NCERT line by line: every item id listed for this heading is in the "teaches" of exactly one point. Teach each line by
  what it does: an in_text_question is posed and answered; reader_talk ("Let us see how this happens") is said in your own
  words; an activity is a task the learner can do or watch; a biography is a short story moment; a figure is walked
  through, label by label (kind "figure"). Use the book's key words when you teach its line.
- Explain, do not restate: the why steps, cause and effect, what must come first. When an earlier point taught what is
  needed, remind in one short sentence and name it in "recalls" (its id); when nothing earlier taught it, teach it briefly
  and say so in outside_book.
- Terms: open each term marked ★ in this heading's items at its first use, with its meaning in simple words ("terms").
  Never define again a term the script already opened: remind in a few words. Do not use a technical term of a later
  heading before it is opened, except as a pointer ("isko aage dekhenge").
- Examples (kind "example"): a concrete case worked through: a named plant or experiment, a number, one molecule followed.
  Analogies (kind "analogy"): at most one per idea, never one the script already used. Real-world uses (kind
  "real_world"): a real thing, place or happening in food, farming, health, weather or technology; never a study task or
  an exam trap; leave it out when there is no honest link, never invent one.
- Depth: NEET depth where the chapter file marks exam high or deep; a sound base everywhere.
- Outside the book is welcome where it makes the concept clearer; name what you added in outside_book.
- "screen": for every point, what the screen shows while it is said (a photo, a diagram, a table, an equation): what
  explains the words. Never a caution line ("assume", "illustrative", "the source does not say") in says or screen.
- Voice: {language} in Roman script with the book's English terms; a warm spoken teacher (questions, "socho", "dekho");
  every sentence under {max_words} words.
- "bridge": one line that leads into the next heading (empty for the last heading).

Ids: points {tag}-k1, {tag}-k2 ... in order. Answer with the JSON object only."""

PROBLEMS_PROMPT = ("BIE's code checked this heading's script and found these problems. Send the whole corrected JSON object "
                   "for this heading again, changing only what the problems need:\n- ")


def tag(section: str) -> str:
    return section or "0"


def headings(chapter: dict) -> list:
    """The body headings in the book's order that have items to teach: [{"number", "title", "items": [ids]}]."""
    wanted = set(studio_naksha.coverable(chapter))
    out = []
    for section in chapter_file.build(chapter)["sections"]:
        if section["zone"] != "body":
            continue
        ids = [row["id"] for row in section["items"] if row["id"] in wanted]
        if ids:
            out.append({"number": section["number"], "title": section["title"] or ("Opening" if not section["number"] else ""),
                        "items": ids, "rows": section["items"]})
    return out


def first_terms(heading: dict) -> list:
    """The terms the chapter opens (★) in this heading's items: [(term, item id)]."""
    return [(t["term"], row["id"]) for row in heading["rows"] for t in row.get("terms") or [] if t.get("first_here")]


def _technical(term: str) -> bool:
    """A short form or formula (PS II, ATP, RuBP, 3-PGA, CO₂, H⁺) in a term of at most three words: it must be opened
    with its meaning and never used before. Section 1 also marks plain words as first terms ("regenerated", "turn"); those
    only need to be said where their line is taught (the Chapter 11 map, 22 November 2026: 39 marked terms in the opening)."""
    term = term.strip()
    return 0 < len(term.split()) <= 3 and (sum(c.isupper() for c in term) >= 2 or any(c.isdigit() or c in "+⁺₀₁₂₃₄₅₆₇₈₉"
                                                                                      for c in term))


def _words(text: str) -> set:
    return {w for w in WORD.findall((text or "").lower()) if w not in FILLER}


def _same(a: set, b: set) -> float:
    return len(a & b) / max(1, len(a | b))


def _overlap(a: set, b: set) -> float:
    return len(a & b) / max(1, min(len(a), len(b)))


def _term_in(term: str, text: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])" + re.escape(_plain(term)) + r"(?![a-z0-9])", _plain(text)))


PLAIN = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "01234567890123456789+-")


def _plain(term: str) -> str:
    """CO₂ and CO2, H⁺ and H+ are one term."""
    return " ".join((term or "").translate(PLAIN).casefold().split())


def _same_term(a: str, b: str) -> bool:
    a, b = _plain(a), _plain(b)
    return bool(a) and bool(b) and (a == b or (len(a) >= 4 and len(b) >= 4 and (a in b or b in a)))


def memory(parts: list) -> dict:
    """What the script so far has used: terms opened, sentences said, analogies and examples, point ids."""
    out = {"terms": {}, "sentences": [], "analogies": [], "examples": [], "points": set()}
    for part in parts:
        for point in part.get("points") or []:
            pid = point.get("id")
            out["points"].add(pid)
            for t in point.get("terms") or []:
                out["terms"].setdefault(_plain(t.get("term") or ""), pid)
            for sentence in point.get("says") or []:
                out["sentences"].append((pid, _words(sentence)))
            if point.get("kind") == "analogy":
                out["analogies"].append((pid, _words(" ".join(point.get("says") or []))))
            if point.get("kind") == "example":
                out["examples"].append((pid, _words(" ".join(point.get("says") or []))))
    return out


def problems(answer, heading: dict, chapter: dict, earlier: list, later_terms: list) -> list:
    """What this heading's part gets wrong, in words the maker can act on. ``earlier``: the parts already written;
    ``later_terms``: the technical terms the chapter opens in later headings."""
    if not isinstance(answer, dict):
        return ["the answer is not one JSON object"]
    items = chapter.get("items") or {}
    number = heading["number"]
    points = [p for p in answer.get("points") or [] if isinstance(p, dict)]
    out = []
    if (answer.get("section") or "") != number:
        out.append(f"section must be {number!r}")
    if not points:
        return out + ["no points"]
    ids = [p.get("id") for p in points]
    if ids != [f"{tag(number)}-k{n}" for n in range(1, len(points) + 1)]:
        out.append(f"point ids must be {tag(number)}-k1, {tag(number)}-k2 ... in order")
    before = memory(earlier)
    taught = {}
    for p in points:
        pid = p.get("id")
        for iid in p.get("teaches") or []:
            if iid not in items:
                out.append(f"{pid}: teaches {iid!r}, which is not an item of the chapter file")
            elif iid not in heading["items"]:
                out.append(f"{pid}: teaches {iid}, which is not an item of this heading ({number or 'the opening'}); "
                           "teach only this heading's items")
            elif iid in taught:
                out.append(f"{iid} is taught twice ({taught[iid]} and {pid}); teach it once")
            else:
                taught[iid] = pid
                words = _content_words(items[iid].get("content", ""))
                if words and not words & _spoken_words(" ".join(p.get("says") or [])):
                    out.append(f"{pid}: teaches {iid}, but none of its key words is said there: "
                               f"{items[iid].get('content', '')[:110]}")
        if not p.get("says"):
            out.append(f"{pid}: says nothing")
        for k, sentence in enumerate(p.get("says") or [], 1):
            if DEVANAGARI.search(sentence or ""):
                out.append(f"{pid} sentence {k}: write it in Roman script")
            if len((sentence or "").split()) > MAX_WORDS:
                out.append(f"{pid} sentence {k}: {len(sentence.split())} words; keep every sentence under {MAX_WORDS}")
            if CAUTION.search(sentence or ""):
                out.append(f"{pid} sentence {k}: a caution line never reaches the learner; say it as a teacher")
        if not (p.get("screen") or "").strip():
            out.append(f"{pid}: needs its screen line (what the screen shows while this is said)")
        elif CAUTION.search(p.get("screen") or ""):
            out.append(f"{pid}: the screen line has a caution line; show what explains the words")
        for r in p.get("recalls") or []:
            if r not in before["points"]:
                out.append(f"{pid}: recalls {r!r}, which is not a point of an earlier heading")
        if p.get("kind") == "real_world":
            task = studio_naksha.STUDY_TASK.search(" ".join(p.get("says") or []))
            if task:
                out.append(f"{pid}: this real-world point is a study task ({task.group(0)!r}); name where the learner meets "
                           "it in life, or leave the point out")
    missing = [iid for iid in heading["items"] if iid not in taught]
    if missing:
        out.append(f"{len(missing)} items of this heading are in no point's teaches: " + ", ".join(missing))
    # terms: opened here when the chapter opens them here; never defined twice; not used before they are opened
    opened_here = {}
    for p in points:
        for t in p.get("terms") or []:
            key = _plain(t.get("term") or "")
            if not key:
                continue
            if key in before["terms"]:
                out.append(f"{p.get('id')}: the term {t.get('term')!r} was opened in {before['terms'][key]}; remind in a few "
                           "words, do not define it again")
            opened_here.setdefault(key, p.get("id"))
    said_by = {p.get("id"): " ".join(p.get("says") or []) for p in points}
    for term, iid in first_terms(heading):
        if iid not in taught or any(_same_term(term, k) for k in opened_here) or any(_same_term(term, k) for k in before["terms"]):
            continue
        if _technical(term):
            out.append(f"{taught[iid]}: open the term {term!r} (first met in {iid}) with its meaning in terms")
        elif not _term_in(term, said_by.get(taught[iid], "")):
            out.append(f"{taught[iid]}: the book's term {term!r} (first met in {iid}) is neither said nor opened; use it "
                       "where you teach that line (open it in terms when the learner needs its meaning)")
    seen_terms = set(before["terms"]) | set()
    for p in points:
        seen_terms |= {_plain(t.get("term") or "") for t in p.get("terms") or []}
        for sentence in p.get("says") or []:
            if FORWARD.search(sentence or ""):
                continue
            for term in later_terms:
                if _term_in(term, sentence) and not any(_same_term(term, k) for k in seen_terms):
                    out.append(f"{p.get('id')}: uses {term!r} before the chapter opens it (a later heading); explain without "
                               "it, or point ahead (\"isko aage dekhenge\")")
                    break
    # no repetition: sentences, analogies, examples
    said = list(before["sentences"])
    for p in points:
        for k, sentence in enumerate(p.get("says") or [], 1):
            words = _words(sentence)
            if len(words) >= 6:
                for other, other_words in said:
                    if len(other_words) >= 6 and _same(words, other_words) >= SAME_SENTENCE:
                        out.append(f"{p.get('id')} sentence {k} says again what {other} said; say something new or "
                                   "remind in a few words")
                        break
            said.append((p.get("id"), words))
    for kind, used, limit in (("analogy", before["analogies"], SAME_ANALOGY), ("example", before["examples"], SAME_EXAMPLE)):
        used = list(used)
        for p in points:
            if p.get("kind") != kind:
                continue
            words = _words(" ".join(p.get("says") or []))
            for other, other_words in used:
                if words and other_words and _overlap(words, other_words) >= limit:
                    out.append(f"{p.get('id')}: this {kind} repeats {other}'s; choose another")
                    break
            used.append((p.get("id"), words))
    return out


def script_so_far(parts: list, chapter: dict) -> str:
    """The script written so far, as the next call reads it."""
    if not parts:
        return "(nothing yet: this is the first heading)"
    out = []
    for part in parts:
        out.append(f"### {part.get('section') or 'Opening'}")
        for p in part.get("points") or []:
            terms = "; ".join(f"{t.get('term')} = {t.get('meaning')}" for t in p.get("terms") or [])
            out.append(f"[{p.get('id')} · {p.get('kind')}] " + " ".join(p.get("says") or [])
                       + (f"  (terms: {terms})" if terms else ""))
        if part.get("bridge"):
            out.append(f"(bridge) {part['bridge']}")
    used = memory(parts)
    out += ["", "Terms already opened: " + ", ".join(sorted(used["terms"])) if used["terms"] else ""]
    return "\n".join(out)


def plan_ideas(naksha: dict | None, number: str) -> str:
    """The teaching plan's ideas for one heading (both shapes when both exist): student questions, openings, analogies,
    examples, real-world uses and pictures. Ideas only: the cut into videos comes later."""
    rows = []
    for shape, plan in sorted((naksha or {}).items()):
        for f in (plan or {}).get("films") or [] if isinstance(plan, dict) else []:
            if (f.get("section") or "") != number:
                continue
            rows.append(f"- plan {shape} · question: {f.get('question')} · opens with: {f.get('opens_with')} · story: "
                        + " → ".join(f.get("story") or [])
                        + (f" · analogy: {(f.get('analogy') or {}).get('picture')}" if (f.get("analogy") or {}).get("picture") else "")
                        + (f" · examples: {'; '.join(f.get('examples') or [])}" if f.get("examples") else "")
                        + (f" · real world: {'; '.join(f.get('real_world') or [])}" if f.get("real_world") else "")
                        + (" · pictures: " + "; ".join(s.get("shows", "") for s in f.get("saman") or []) if f.get("saman") else ""))
    return "\n".join(rows) if rows else "(no plan ideas for this heading)"


def messages(chapter: dict, heading: dict, parts: list, *, course: dict, naksha: dict | None = None,
             language: str = "Hinglish", next_title: str = "") -> list:
    system = RULES.format(subject=course.get("subject") or "the subject", learners=course.get("learners") or "the learners",
                          exam=course.get("exam") or "their exam", language=language or "Hinglish", max_words=MAX_WORDS,
                          tag=tag(heading["number"]))
    items = chapter.get("items") or {}
    stars = [f"{term} (in {iid})" for term, iid in first_terms(heading)]
    lines = "\n".join(f"- {iid}: {items[iid].get('content', '')[:300]}" for iid in heading["items"])
    user = (f"THE CHAPTER FILE\n\n{chapter_file.markdown(chapter)}\n\nTHE SCRIPT SO FAR\n\n{script_so_far(parts, chapter)}\n\n"
            f"IDEAS FROM THE TEACHING PLAN FOR THIS HEADING (use what serves; not the cut into videos)\n\n"
            f"{plan_ideas(naksha, heading['number'])}\n\n"
            f"NOW WRITE THE SCRIPT OF THIS HEADING: {heading['number'] or 'the opening'} {heading['title']}\n"
            f"Its items (each in exactly one point's teaches):\n{lines}\n"
            f"Terms the chapter opens here: {', '.join(stars) if stars else '(none)'}\n"
            f"The next heading: {next_title or '(none: this is the last heading)'}")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def write(client, model: str, chapter: dict, *, course: dict, naksha: dict | None = None, language: str = "Hinglish",
          max_rounds: int = 3, on_part=None) -> dict:
    """The whole chapter's script, heading by heading; ``on_part(record)`` is called after each heading (to save it)."""
    heads = headings(chapter)
    later = {}
    for n, heading in enumerate(heads):
        later[n] = [t for h in heads[n + 1:] for t, _ in first_terms(h) if _technical(t)]
    parts, rounds, usage, left = [], [], {"input_tokens": 0, "output_tokens": 0}, {}
    for n, heading in enumerate(heads):
        nxt = heads[n + 1] if n + 1 < len(heads) else None
        convo = messages(chapter, heading, parts, course=course, naksha=naksha, language=language,
                         next_title=f"{nxt['number']} {nxt['title']}" if nxt else "")
        answer, found, these = None, ["no answer yet"], []
        for number in range(1, max_rounds + 1):
            reply = client.chat(model=model, messages=convo, schema=SCHEMA)
            for key in usage:
                usage[key] += int((reply.get("usage") or {}).get(key) or 0)
            answer = parse(reply.get("content", ""))
            found = problems(answer, heading, chapter, parts, later[n])
            these.append({"round": number, "problems": found})
            if not found:
                break
            convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                             {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
        part = answer if isinstance(answer, dict) else {"section": heading["number"], "points": [], "bridge": ""}
        part = dict(part, section=heading["number"], title=heading["title"])
        parts.append(part)
        rounds.append({"section": heading["number"], "rounds": these})
        if found:
            left[heading["number"] or "opening"] = found
        record = {"parts": parts, "rounds": rounds, "usage": usage, "problems": left}
        if on_part:
            on_part(record)
    return {"parts": parts, "rounds": rounds, "usage": usage, "problems": left}


def counts(chapter: dict, parts: list) -> dict:
    wanted = studio_naksha.coverable(chapter)
    taught = {i for part in parts for p in part.get("points") or [] for i in p.get("teaches") or []}
    sentences = [s for part in parts for p in part.get("points") or [] for s in p.get("says") or []]
    words = sum(len(s.split()) for s in sentences)
    return {"headings": len(parts), "points": sum(len(part.get("points") or []) for part in parts),
            "sentences": len(sentences), "words": words, "minutes": round(words / WORDS_PER_MINUTE),
            "covered": sum(1 for i in wanted if i in taught), "coverable": len(wanted),
            "analogies": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "analogy"),
            "examples": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "example"),
            "real_world": sum(1 for part in parts for p in part.get("points") or [] if p.get("kind") == "real_world"),
            "outside_book": sum(1 for part in parts for p in part.get("points") or [] if (p.get("outside_book") or "").strip())}


KIND_WORDS = {"explain": "samjhana", "question": "sawaal", "example": "example", "analogy": "analogy",
              "real_world": "asli duniya", "recall": "yaad", "activity": "activity", "story": "kahani", "figure": "figure",
              "summary": "saar"}


def markdown(chapter: dict, record: dict) -> str:
    items = chapter.get("items") or {}
    title = (chapter.get("map") or {}).get("chapter_title") or (chapter.get("course") or {}).get("title", "")
    c = counts(chapter, record.get("parts") or [])
    out = [f"# Chapter ki script · {title}", "",
           f"{c['headings']} headings · {c['points']} gyan-bindu · {c['sentences']} lines · lagbhag {c['minutes']} minute bolna · "
           f"NCERT items {c['covered']}/{c['coverable']}", ""]
    for part in record.get("parts") or []:
        out += [f"## {part.get('section') or 'Shuruaat'} {part.get('title') or ''}".rstrip(), ""]
        for p in part.get("points") or []:
            out.append(f"**{p.get('id')}** · {KIND_WORDS.get(p.get('kind'), p.get('kind'))} · " + " ".join(p.get("says") or []))
            if p.get("terms"):
                out.append("  - terms: " + "; ".join(f"{t.get('term')} = {t.get('meaning')}" for t in p["terms"]))
            out.append(f"  - screen: {p.get('screen')}")
            if p.get("teaches"):
                out.append("  - NCERT: " + "; ".join(f"{i} {items.get(i, {}).get('content', '')[:80]}" for i in p["teaches"]))
            if (p.get("outside_book") or "").strip():
                out.append(f"  - kitaab se bahar: {p['outside_book']}")
        if part.get("bridge"):
            out += ["", f"_→ {part['bridge']}_"]
        left = (record.get("problems") or {}).get(part.get("section") or "opening")
        if left:
            out += ["", f"Code ki kamiyan bachi: {len(left)}"]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def html(chapter: dict, record: dict) -> str:
    """SCRIPT.html, Navin's script page (a review page, never the learner's): each heading's script beside the NCERT lines
    it teaches, readable on his tablet."""
    e = html_module.escape
    items = chapter.get("items") or {}
    title = (chapter.get("map") or {}).get("chapter_title") or (chapter.get("course") or {}).get("title", "")
    c = counts(chapter, record.get("parts") or [])
    left_total = sum(len(v) for v in (record.get("problems") or {}).values())
    parts = [f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Chapter ki script · {e(title)}</title><style>
body{{font:16px/1.6 system-ui,sans-serif;margin:0;padding:16px;background:#faf8f3;color:#222}}main{{max-width:1100px;margin:auto}}
h1{{font-size:22px;margin:.2em 0}}.sum{{color:#555}}details.h{{background:#fff;border:1px solid #ddd6c8;border-radius:10px;margin:8px 0;
padding:6px 12px}}details.h>summary{{cursor:pointer;font-weight:600}}.pt{{display:grid;grid-template-columns:3fr 2fr;gap:12px;
border-top:1px solid #eee;padding:10px 0}}@media (max-width:720px){{.pt{{grid-template-columns:1fr}}}}
.tag{{display:inline-block;font-size:12px;border-radius:6px;padding:0 6px;margin-right:6px;background:#eef2e8;color:#2f4d1f}}
.k-analogy,.k-example,.k-real_world{{background:#fbf3df;color:#6b4a07}}.k-question{{background:#e7eefb;color:#1d3d7a}}
.k-recall{{background:#f1f1f1;color:#555}}.says{{margin:4px 0}}.k{{color:#555;font-size:14px}}.k b{{color:#333}}
.book{{background:#f6f3ec;border-radius:8px;padding:6px 10px;font-size:14px;color:#444}}.book div{{margin:3px 0}}
.left{{color:#7a3413;font-size:14px}}.bridge{{color:#2f4d1f;font-style:italic;margin:6px 0}}.id{{color:#888;font-size:12px}}
</style></head><body><main>
<p class="sum">BIE · chapter ki script (review page, learner ko nahi dikhta)</p><h1>{e(title)}</h1>
<p>{c['headings']} headings · {c['points']} gyan-bindu · {c['sentences']} lines · lagbhag {c['minutes']} minute bolna ·
NCERT items {c['covered']}/{c['coverable']} · analogy {c['analogies']} · example {c['examples']} · asli duniya {c['real_world']} ·
kitaab se bahar {c['outside_book']} · code ki kamiyan {left_total}</p>"""]
    for part in record.get("parts") or []:
        points = part.get("points") or []
        left = (record.get("problems") or {}).get(part.get("section") or "opening") or []
        words = sum(len(s.split()) for p in points for s in p.get("says") or [])
        parts.append(f'<details class="h"><summary>{e(part.get("section") or "Shuruaat")} {e(part.get("title") or "")} · '
                     f'{len(points)} gyan-bindu · lagbhag {round(words / WORDS_PER_MINUTE)} min'
                     + (f' · <span class="left">{len(left)} kamiyan bachi</span>' if left else "") + "</summary>")
        for p in points:
            terms = "; ".join(f"<b>{e(t.get('term') or '')}</b> = {e(t.get('meaning') or '')}" for t in p.get("terms") or [])
            book = "".join(f'<div><span class="id">{e(i)}</span> {e(items.get(i, {}).get("content", ""))}</div>'
                           for i in p.get("teaches") or [])
            parts.append(
                f'<div class="pt"><div><span class="tag k-{e(p.get("kind") or "")}">{e(KIND_WORDS.get(p.get("kind"), p.get("kind") or ""))}</span>'
                f'<span class="id">{e(p.get("id") or "")}</span>'
                f'<div class="says">{e(" ".join(p.get("says") or []))}</div>'
                f'<div class="k"><b>Screen par:</b> {e(p.get("screen") or "")}</div>'
                + (f'<div class="k"><b>Terms:</b> {terms}</div>' if terms else "")
                + (f'<div class="k"><b>Kitaab se bahar:</b> {e(p.get("outside_book"))}</div>' if (p.get("outside_book") or "").strip() else "")
                + (f'<div class="k"><b>Yaad:</b> {e(", ".join(p.get("recalls") or []))}</div>' if p.get("recalls") else "")
                + f'</div><div class="book">{book or "<span class=k>(NCERT line nahi: jodne wali baat)</span>"}</div></div>')
        if part.get("bridge"):
            parts.append(f'<div class="bridge">→ {e(part["bridge"])}</div>')
        if left:
            parts.append('<div class="left">Code ki kamiyan: ' + e(" | ".join(left[:8])) + "</div>")
        parts.append("</details>")
    parts.append("</main></body></html>")
    return "\n".join(parts)


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=1)
