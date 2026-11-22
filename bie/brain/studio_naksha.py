"""The chapter's teaching naksha: how the whole chapter is taught, film by film, before any film is written (Navin,
21 November 2026, after the Chapter 11 audit: "pdhana kaise hai decide ho jiske adhaar par pure chapter par script bane
taaki progression na tute dohrav na ho sab kuchh ek jaisa na lage aur ncert cover bhi ho jaaye line by line bina
hallucination ke"; cards the same evening: the naksha on the book's own headings, made two ways to compare, "Logic pehle
option ka use karo aur implement 3 ke jaise aur keval option 1 ke tarike se bhi alag se implement karke dikhao phir choose
karunga", and "Naksha pehle").

Input: Section 1's chapter map (``chapter_map.json``, both eyes, every item placed in its printed section with its role)
given whole to the maker as the chapter file (``chapter_file.markdown``: "codex ko ek output file do jisse wo asani se
content ko samjh paaye"). Output: two naksha, each checked by code:

* shape **A** ("logic of option 1, made like option 3"): the book's headings are the course's chapters; inside each heading
  1 to 4 films, each answering one student question its lines raise; a film never mixes two headings.
* shape **B** ("only option 1"): one film per heading; a heading with sub-headings gets one film per sub-heading (and one
  for its own opening lines when they carry teaching).

Every film of either shape names the items it teaches (each teachable body item in exactly one film: NCERT line by line),
the earlier films it builds on and the items it only recalls (progression, no re-teaching), its prerequisite, how it
opens, its story in steps, its one analogy (never used by another film), examples, real-world uses, the terms it opens,
what it adds from outside the book (marked), and its list of things to show (saman ki list: what each picture must show to
explain the teacher's line; a new picture unless the very same thing is shown again; Navin: "teacher jo bol raha hai
usko samjhane ke liye uske hisab se alag kuchh banana pade to banaya jaaye"). Exercises go to practice, the summary to
recaps. Code checks all of it and sends the exact problems back.

The films stage then makes each film from its naksha row (``questions.json`` of this run: films ``a01``... and
``b01``...), with the rows before it as what the learner already knows.
"""
from __future__ import annotations

import json
import re

from . import chapter_file
from .studio import parse

SHAPES = ("A", "B")
COVER_ROLES = ("teach", "in_text_question", "reader_talk", "activity", "biography", "")
KINDS = ("photo", "cutaway", "diagram", "molecule", "graph", "table")
MIN_MINUTES, MAX_MINUTES = 2, 12
MAX_FILMS_PER_HEADING_A = 4
SAME_ANALOGY = 0.5            # share of shared words above which two analogies are one analogy told twice
FILLER = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with", "like", "as", "is", "are", "jaise", "ki",
          "ka", "ke", "ek", "se", "mein", "aur", "hai", "hain", "wala", "wali", "jo", "par"}
# a "real-world use" that is really a study task (the first naksha of Chapter 11, 22 November 2026: "Incomplete Z-scheme
# diagrams mein arrows identify karna", "NEET numerical traps", "Interpreting experimental controls")
STUDY_TASK = re.compile(r"\b(diagrams?|identif\w*|labels?|labell?ing|trace|tracing|interpret\w*|distinguish\w*|"
                        r"differentiat\w*|neet|numericals?|exams?|traps?|stoichiometr\w*|padhna|likhna|worksheet)\b", re.I)

S = {"type": "string"}
N = {"type": "number"}


def _obj(properties: dict) -> dict:
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def _arr(items: dict) -> dict:
    return {"type": "array", "items": items}


FILM = _obj({
    "id": S, "section": S, "title": S, "question": S,
    "teaches": _arr(S), "recalls": _arr(S), "builds_on": _arr(S),
    "prerequisite": S, "opens_with": S, "story": _arr(S),
    "analogy": _obj({"for": S, "picture": S, "why_it_fits": S}),
    "examples": _arr(S), "real_world": _arr(S), "terms": _arr(S),
    "outside_book": _arr(_obj({"what": S, "why": S})),
    "saman": _arr(_obj({"id": S, "shows": S, "kind": {"type": "string", "enum": list(KINDS)}, "for_items": _arr(S),
                        "why": S, "reuse_of": S})),
    "minutes": N,
})
SCHEMA = _obj({
    "shape": {"type": "string", "enum": list(SHAPES)},
    "chapter_flow": S,
    "films": _arr(FILM),
    "practice": _arr(_obj({"item": S, "films": _arr(S)})),
    "recap": _arr(_obj({"item": S, "film": S})),
})

RULES = """You are BIE's teacher-planner: the best {subject} teacher for {learners} ({exam}), planning how to teach one whole
chapter in films before a single film is written. BIE has read the chapter with both eyes (the printed text and each
page's image) and gives you the chapter file: the book's own sections in order, every item with its id, its role in the
book, its content type, its exam weight, the terms it opens, its why steps and what must come first; then the concepts
and how they hang together. Plan from that file only; what you add from outside the book is welcome where it makes the
concept clearer, and you name it under outside_book.

Navin's rules for the plan (21 November 2026):
- NCERT line by line, no hallucination: every item whose role is teach, in_text_question, reader_talk, activity or
  biography and whose zone is the body is in the "teaches" list of exactly one film (a figure's labels and a table's rows
  go with their figure or table); an exercise item is in "practice"
  (with the films that prepare for it), a summary item in "recap" (with the film that recaps it). Headings and captions
  need no film of their own; their items go with the film of their section. Use only ids from the file.
- Progression, no repetition: films follow the book's order. A film builds on the films before it ("builds_on") and may
  remind the learner of an earlier item in one sentence ("recalls", only items taught in an earlier film); it never
  teaches again what an earlier film taught. The journey from the leaf into the cell and the chloroplast is told once in
  the chapter, in the film that first needs it; a later film opens where its own concept lives.
- Not everything the same: every film opens differently ("opens_with": a question, a puzzle, a scene from the learner's
  life, an experiment, a number), has at most one analogy and never one another film uses (a dam, a kitchen, a battery, a
  factory, a relay race: once each in the whole chapter), and its own examples and real-world uses (NEET depth where it
  matters).
- "examples" (at least one per film, never the same as another film's): a concrete case the teacher works through while
  teaching this film's lines: a named plant or experiment, a number worked out, one molecule followed step by step (the
  book's own example first; one from outside the book is also named under outside_book).
- "real_world": where the learner meets this concept in life, food, farming, health, the weather or technology: a real
  thing, place or happening (greenhouse tomatoes given extra CO2, a potted plant drooping in the heat, sugarcane and
  maize as C4 crops). A study skill, a diagram task or an exam trap is not a real-world use: it belongs in practice.
  Leave real_world empty when the film's lines have no honest real-world link; never invent one.
- Each line is taught by what it does: an in_text_question is posed and answered; reader_talk ("Let us see how this
  happens") is said in the teacher's own words; an activity becomes a task the learner can do or watch; a biography is a
  short story moment.
- Terms: every term marked ★ in a film's items is opened in that film, at the moment it is first needed ("terms").
- Saman ki list (what the screen needs): for each film, the pictures it needs to explain what the teacher says, each with
  what it shows, its kind (photo, cutaway, diagram, molecule, graph, table), the items it serves and why it explains them.
  Make a new picture for what a line needs; name an earlier film's picture in "reuse_of" only when the very same thing is
  shown again (a reminder). No two films open on the same picture.
- Length follows the content: 2 to 12 minutes; a process or structure gets time, a light point a short film.
- The unit's opening page, when the chapter file begins with one (UNIT, its name and its chapters), is the first film:
  the unit's overview, made only from that page's items.

{shape_rules}

Ids: films {prefix}01, {prefix}02 ... in teaching order; saman ids s1, s2 ... inside each film. Write titles, questions,
openings and story steps in {language} (Roman script), with the book's English terms. Answer with the JSON object only."""

SHAPE_RULES = {
    "A": """Shape A (the book's headings, films by student question): each numbered heading of the book (11.1, 11.6, 11.6.1 ...)
is a chapter of the course; inside it make 1 to 4 films, each answering one question a student would ask about that
heading's lines ("question": in the learner's words). A film's items all come from one heading ("section" = that heading's
number, or "" for the chapter's opening before the first heading). Together the films of a heading teach all its lines.""",
    "B": """Shape B (one heading, one film): one film per numbered heading of the book ("section" = its number, or "" for the
chapter's opening); a heading that has sub-headings (11.6 with 11.6.1, 11.6.2, 11.6.3) gets one film per sub-heading,
and one film of its own only when its own lines before the first sub-heading carry teaching. "question" is the heading's
own question in the learner's words. Two films never share a section.""",
}

PROBLEMS_PROMPT = ("BIE's code checked your naksha and found these problems. Send the whole corrected JSON object again, "
                   "changing only what the problems need:\n- ")


def coverable(chapter: dict) -> list:
    """The ids every naksha must teach: body items whose role needs teaching (a heading or caption goes with its section)."""
    items = chapter.get("items") or {}
    return [iid for iid in chapter_file._order(items)
            if items[iid].get("zone", "body") == "body" and items[iid].get("teachable")
            and (items[iid].get("role") or "") in COVER_ROLES and items[iid].get("kind") not in ("heading", "caption")
            and not (items[iid].get("kind") in chapter_file.PART_KINDS and items[iid].get("parent_item_id"))]


def zone_items(chapter: dict, zone: str) -> list:
    items = chapter.get("items") or {}
    return [iid for iid in chapter_file._order(items) if items[iid].get("zone") == zone and items[iid].get("teachable")]


def sections(chapter: dict) -> list:
    """The numbered headings in book order, with "" (the opening) first."""
    return [""] + [h["number"] for h in chapter.get("ncert_sections") or [] if h.get("number")]


def messages(chapter: dict, shape: str, *, course: dict, language: str = "Hinglish") -> list:
    prefix = shape.lower()
    system = RULES.format(subject=course.get("subject") or "the subject", learners=course.get("learners") or "the learners",
                          exam=course.get("exam") or "their exam", shape_rules=SHAPE_RULES[shape], prefix=prefix,
                          language=language or "Hinglish")
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Make the shape {shape} naksha for this chapter.\n\n" + chapter_file.markdown(chapter)}]


def _words(text: str) -> set:
    return {w for w in re.findall(r"[a-zA-Zऀ-ॿ]{3,}", (text or "").lower()) if w not in FILLER}


def problems(answer, chapter: dict, shape: str) -> list:
    """What the naksha gets wrong, in words the maker can act on."""
    if not isinstance(answer, dict):
        return ["the answer is not one JSON object"]
    items = chapter.get("items") or {}
    order = {iid: n for n, iid in enumerate(chapter_file._order(items))}
    films = [f for f in answer.get("films") or [] if isinstance(f, dict)]
    out = []
    if answer.get("shape") != shape:
        out.append(f"shape must be {shape!r}")
    if not films:
        return out + ["no films"]
    prefix = shape.lower()
    ids = [f.get("id") for f in films]
    if ids != [f"{prefix}{n:02d}" for n in range(1, len(films) + 1)]:
        out.append(f"film ids must be {prefix}01, {prefix}02 ... in teaching order")
    heading_index = {s: n for n, s in enumerate(sections(chapter))}
    taught, where = {}, {}
    for f in films:
        fid = f.get("id")
        for iid in f.get("teaches") or []:
            if iid not in items:
                out.append(f"{fid}: teaches {iid!r}, which is not an item of the chapter file")
                continue
            if iid in taught:
                out.append(f"{iid} is taught twice ({taught[iid]} and {fid}); teach it once and recall it later")
            taught.setdefault(iid, fid)
            section = items[iid].get("ncert_section", "")
            if section != (f.get("section") or ""):
                out.append(f"{fid}: {iid} belongs to section {section or 'the opening'!r}, not {f.get('section') or 'the opening'!r}")
            if items[iid].get("zone", "body") != "body":
                out.append(f"{fid}: {iid} is a {items[iid].get('zone')} item: put it in "
                           f"{'practice' if items[iid].get('zone') == 'exercise' else 'recap'}, not in teaches")
        if (f.get("section") or "") not in heading_index:
            out.append(f"{fid}: section {f.get('section')!r} is not a heading of the book")
        if not f.get("teaches"):
            out.append(f"{fid}: teaches nothing")
        minutes = f.get("minutes")
        if not isinstance(minutes, (int, float)) or not MIN_MINUTES <= minutes <= MAX_MINUTES:
            out.append(f"{fid}: minutes must be between {MIN_MINUTES} and {MAX_MINUTES}")
        if not f.get("opens_with") or len(f.get("story") or []) < 2:
            out.append(f"{fid}: needs opens_with and a story of at least two steps")
        if not f.get("saman"):
            out.append(f"{fid}: needs its saman ki list (what the screen must show)")
        if not [x for x in f.get("examples") or [] if str(x).strip()]:
            out.append(f"{fid}: needs at least one example (a concrete case the teacher works through)")
        for use in f.get("real_world") or []:
            task = STUDY_TASK.search(str(use))
            if task:
                out.append(f"{fid}: real_world {str(use)[:80]!r} is a study task ({task.group(0)!r}), not a use in life: name "
                           "where the learner meets this concept (food, farming, health, weather, technology), or leave it "
                           "empty; study tasks go to practice")
        for s in f.get("saman") or []:
            bad = [i for i in s.get("for_items") or [] if i not in (f.get("teaches") or []) and i not in (f.get("recalls") or [])]
            if bad:
                out.append(f"{fid} {s.get('id')}: serves {bad}, which this film neither teaches nor recalls")
        before = {o.get("id") for o in films[:films.index(f)]}
        for b in f.get("builds_on") or []:
            if b not in before:
                out.append(f"{fid}: builds_on {b!r}, which is not an earlier film")
        for r in f.get("recalls") or []:
            if taught.get(r) is None or taught.get(r) == fid:
                out.append(f"{fid}: recalls {r!r}, which no earlier film teaches")
    missing = [iid for iid in coverable(chapter) if iid not in taught]
    if missing:
        out.append(f"{len(missing)} items are in no film's teaches: " + ", ".join(missing[:40]))
    # the book's order: a film's section never comes before an earlier film's section
    places = [heading_index.get(f.get("section") or "", 0) for f in films]
    for n in range(1, len(films)):
        if places[n] < places[n - 1]:
            out.append(f"{films[n].get('id')} (section {films[n].get('section')!r}) comes after a later section's film: "
                       "follow the book's order")
            break
    for f in films:
        firsts = [order.get(i, 0) for i in f.get("teaches") or [] if i in order]
        if firsts != sorted(firsts):
            out.append(f"{f.get('id')}: list teaches in the book's order")
    if shape == "A":
        counts = {}
        for f in films:
            counts[f.get("section") or ""] = counts.get(f.get("section") or "", 0) + 1
        out += [f"section {s or 'opening'!r} has {n} films; shape A makes 1 to {MAX_FILMS_PER_HEADING_A} per heading"
                for s, n in counts.items() if n > MAX_FILMS_PER_HEADING_A]
    else:
        seen = {}
        for f in films:
            if (f.get("section") or "") in seen:
                out.append(f"{f.get('id')} and {seen[f.get('section') or '']} share section {f.get('section')!r}: "
                           "shape B makes one film per heading")
            seen.setdefault(f.get("section") or "", f.get("id"))
    # not everything the same: one analogy per film, never another film's; every film opens on its own picture
    analogies = []
    for f in films:
        picture = (f.get("analogy") or {}).get("picture") or ""
        words = _words(picture)
        if not words:
            continue
        for other, other_words in analogies:
            if len(words & other_words) / max(1, min(len(words), len(other_words))) >= SAME_ANALOGY:
                out.append(f"{f.get('id')}: its analogy ({picture!r}) repeats {other}'s; choose another or none")
                break
        analogies.append((f.get("id"), words))
    examples = {}
    for f in films:
        for example in f.get("examples") or []:
            key = " ".join(sorted(_words(str(example))))
            if key and key in examples and examples[key] != f.get("id"):
                out.append(f"{f.get('id')}: example {str(example)[:80]!r} repeats {examples[key]}'s; give this film its own")
            examples.setdefault(key, f.get("id"))
    openings = {}
    for f in films:
        first = next(iter(f.get("saman") or []), None)
        if not first:
            continue
        if first.get("reuse_of"):
            out.append(f"{f.get('id')}: its opening picture reuses {first.get('reuse_of')!r}; open on a picture of its own")
        key = " ".join(sorted(_words(first.get("shows") or "")))
        if key and key in openings:
            out.append(f"{f.get('id')} opens on the same picture as {openings[key]}; give each film its own opening")
        openings.setdefault(key, f.get("id"))
    for p in answer.get("practice") or []:
        if p.get("item") not in items:
            out.append(f"practice names {p.get('item')!r}, which is not an item")
        bad = [x for x in p.get("films") or [] if x not in ids]
        if bad:
            out.append(f"practice {p.get('item')}: films {bad} are not films of this naksha")
    left = [i for i in zone_items(chapter, "exercise") if i not in {p.get("item") for p in answer.get("practice") or []}]
    if left:
        out.append(f"{len(left)} exercise items are in no practice row: " + ", ".join(left[:20]))
    left = [i for i in zone_items(chapter, "summary") if i not in {r.get("item") for r in answer.get("recap") or []}]
    if left:
        out.append(f"{len(left)} summary items are in no recap row: " + ", ".join(left[:20]))
    return out


def plan(client, model: str, chapter: dict, shape: str, *, course: dict, language: str = "Hinglish", max_rounds: int = 3) -> dict:
    convo = messages(chapter, shape, course=course, language=language)
    rounds, usage, answer, found = [], {"input_tokens": 0, "output_tokens": 0}, None, ["no answer yet"]
    for number in range(1, max_rounds + 1):
        reply = client.chat(model=model, messages=convo, schema=SCHEMA)
        for key in usage:
            usage[key] += int((reply.get("usage") or {}).get(key) or 0)
        answer = parse(reply.get("content", ""))
        found = problems(answer, chapter, shape)
        rounds.append({"round": number, "problems": found})
        if not found:
            break
        convo = convo + [{"role": "assistant", "content": reply.get("content", "")},
                         {"role": "user", "content": PROBLEMS_PROMPT + "\n- ".join(found)}]
    return {"shape": shape, "answer": answer, "problems": found, "rounds": rounds, "usage": usage}


def questions(chapter: dict, naksha: dict) -> list:
    """The films of one naksha as the films stage's questions: each film's items become its points (their blocks give
    the book lines), and the film carries its naksha row and what the films before it taught."""
    items = chapter.get("items") or {}
    films = [f for f in (naksha or {}).get("films") or [] if isinstance(f, dict)]
    out = []
    for n, f in enumerate(films):
        points = [{"block_ids": list(items[i].get("block_ids") or []), "point": items[i].get("content", "")[:200],
                   "kind": items[i].get("content_type") or "facts_numbers", "item_id": i}
                  for i in f.get("teaches") or [] if i in items]
        before = [{"id": o.get("id"), "title": o.get("title"), "question": o.get("question"),
                   "taught": [items[i].get("content", "")[:120] for i in o.get("teaches") or [] if i in items][:8],
                   "analogy": (o.get("analogy") or {}).get("picture", ""),
                   "opening": next((s.get("shows") for s in o.get("saman") or []), "")} for o in films[:n]]
        out.append({"id": f.get("id"), "pillar": f.get("section") or "opening", "question": f.get("question") or f.get("title"),
                    "hook": f.get("opens_with", ""), "points": points,
                    "film": {"length": "long" if (f.get("minutes") or 0) >= 4 else "short",
                             "showing_moment": next((s.get("shows") for s in f.get("saman") or []), "")},
                    "game_stage": {"mechanic": "choose_and_see", "idea": ""},
                    "naksha": dict(f, before=before, after=[f"{o.get('id')}: {o.get('title')}" for o in films[n + 1:]])})
    return out


def markdown(chapter: dict, records: list) -> str:
    """NAKSHA.md for Navin: the two shapes side by side, film by film."""
    items = chapter.get("items") or {}
    out = [f"# Padhane ka naksha · {(chapter.get('map') or {}).get('chapter_title') or chapter.get('course', {}).get('title', '')}",
           "", "BIE ka naksha (review page, learner ko nahi dikhta). Do roop: A = har heading ke andar sawaal-wise films; "
           "B = ek heading, ek film.", ""]
    for record in records:
        answer = record.get("answer") or {}
        films = answer.get("films") or []
        minutes = sum(f.get("minutes") or 0 for f in films)
        out += [f"## Roop {record['shape']}: {len(films)} films, lagbhag {minutes:g} minute"
                + (f" · {len(record['problems'])} problems left" if record.get("problems") else ""), "",
                answer.get("chapter_flow", ""), ""]
        for f in films:
            out += [f"### {f.get('id')} · {f.get('section') or 'shuruaat'} · {f.get('title')} ({f.get('minutes')} min)", "",
                    f"- **Sawaal:** {f.get('question')}", f"- **Shuruaat:** {f.get('opens_with')}",
                    f"- **Kahani:** " + " → ".join(f.get("story") or [])]
            if (f.get("analogy") or {}).get("picture"):
                out.append(f"- **Analogy:** {f['analogy']['picture']} ({f['analogy'].get('for', '')}): {f['analogy'].get('why_it_fits', '')}")
            if f.get("builds_on"):
                out.append(f"- **Pehle ki films par:** {', '.join(f['builds_on'])}")
            if f.get("recalls"):
                out.append(f"- **Yaad dilayegi:** {', '.join(f['recalls'])}")
            out.append(f"- **NCERT items ({len(f.get('teaches') or [])}):** " + "; ".join(
                f"{i} {items.get(i, {}).get('content', '')[:70]}" for i in (f.get("teaches") or [])[:6])
                + (" …" if len(f.get("teaches") or []) > 6 else ""))
            if f.get("terms"):
                out.append(f"- **Terms:** {', '.join(f['terms'])}")
            if f.get("examples"):
                out.append(f"- **Examples:** {'; '.join(f['examples'])}")
            if f.get("real_world"):
                out.append(f"- **Asli duniya mein:** {'; '.join(f['real_world'])}")
            if f.get("outside_book"):
                out.append(f"- **Kitaab se bahar:** {'; '.join(o.get('what', '') for o in f['outside_book'])}")
            out.append("- **Saman ki list:** " + "; ".join(
                f"{s.get('id')} {s.get('kind')}: {s.get('shows')}" + (f" (dobara: {s['reuse_of']})" if s.get("reuse_of") else "")
                for s in f.get("saman") or []))
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def compare(chapter: dict, records: list) -> dict:
    """The two shapes heading by heading (for NAKSHA.html): per shape its totals and, for every heading of the book, its
    films; ``differs`` marks the headings where the shapes cut the lines differently."""
    wanted = coverable(chapter)
    wanted_set = set(wanted)
    shapes = {}
    for record in records:
        films = [f for f in (record.get("answer") or {}).get("films") or [] if isinstance(f, dict)]
        taught = {i for f in films for i in f.get("teaches") or []}
        shapes[record["shape"]] = {
            "films": len(films), "minutes": sum(f.get("minutes") or 0 for f in films),
            "problems": list(record.get("problems") or []), "rounds": len(record.get("rounds") or []),
            "covered": sum(1 for i in wanted if i in taught), "coverable": len(wanted),
            "with_examples": sum(1 for f in films if f.get("examples")),
            "with_real_world": sum(1 for f in films if f.get("real_world")),
            "flow": (record.get("answer") or {}).get("chapter_flow", ""), "by_section": {}}
        for f in films:
            shapes[record["shape"]]["by_section"].setdefault(f.get("section") or "", []).append(f)
    titles = {h.get("number"): h.get("title") for h in chapter.get("ncert_sections") or [] if h.get("number")}
    rows = []
    for number in sections(chapter):
        cells = {shape: data["by_section"].get(number, []) for shape, data in shapes.items()}
        if not any(cells.values()):
            continue
        cuts = {shape: frozenset(frozenset(i for i in f.get("teaches") or [] if i in wanted_set) for f in films)
                for shape, films in cells.items()}
        rows.append({"number": number, "title": titles.get(number, "") if number else "Shuruaat (pehli heading se pehle)",
                     "films": cells, "differs": len(set(cuts.values())) > 1})
    return {"shapes": shapes, "sections": rows}


def html(chapter: dict, records: list) -> str:
    """NAKSHA.html for Navin (a review page, never the learner's): the two shapes heading by heading on one screen, so he
    can compare them on his tablet before choosing (Navin, 21 November 2026: "dikhao phir choose karunga")."""
    import html as html_module
    e = html_module.escape
    data = compare(chapter, records)
    title = (chapter.get("map") or {}).get("chapter_title") or chapter.get("course", {}).get("title", "")
    parts = [f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Padhane ka naksha · {e(title)}</title><style>
body{{font:16px/1.55 system-ui,sans-serif;margin:0;padding:16px;background:#faf8f3;color:#222}}main{{max-width:1100px;margin:auto}}
h1{{font-size:22px;margin:.2em 0}}h2{{font-size:18px;margin:1.4em 0 .4em}}.sum{{color:#555}}
.tot{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:10px 0}}
.box{{background:#fff;border:1px solid #ddd6c8;border-radius:10px;padding:10px 12px}}.box b{{font-size:18px}}
details.h{{background:#fff;border:1px solid #ddd6c8;border-radius:10px;margin:8px 0;padding:6px 12px}}
details.h>summary{{cursor:pointer;font-weight:600}}.diff{{display:inline-block;font-size:12px;border-radius:6px;padding:0 6px;
margin-left:6px;background:#fdeee6;color:#7a3413}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0}}
@media (max-width:720px){{.two{{grid-template-columns:1fr}}}}.col h3{{font-size:14px;margin:4px 0;color:#2f4d1f}}
.film{{border-top:1px solid #eee;padding:8px 0}}.film .t{{font-weight:600}}.k{{color:#555;font-size:14px}}
.k b{{color:#333}}details.more>summary{{cursor:pointer;font-size:14px;color:#2f4d1f}}.none{{color:#999;font-size:14px}}
</style></head><body><main>
<p class="sum">BIE · padhane ka naksha (review page, learner ko nahi dikhta)</p><h1>{e(title)}</h1>
<p>Do roop: <b>A</b> = har heading ke andar sawaal-wise films · <b>B</b> = ek heading, ek film.</p><div class="tot">"""]
    for shape, s in data["shapes"].items():
        parts.append(f'<div class="box">Roop {e(shape)}: <b>{s["films"]} films · lagbhag {s["minutes"]:g} min</b><br>'
                     f'<span class="k">NCERT items {s["covered"]}/{s["coverable"]} · examples wali films {s["with_examples"]} · '
                     f'asli duniya wali films {s["with_real_world"]} · code ki kamiyan {len(s["problems"])} · '
                     f'{s["rounds"]} round</span></div>')
    parts.append("</div><h2>Har heading par dono roop</h2>")
    for row in data["sections"]:
        counts = " · ".join(f"{shape}: {len(films)} film, {sum(f.get('minutes') or 0 for f in films):g} min"
                            for shape, films in row["films"].items())
        parts.append(f'<details class="h"><summary>{e(row["number"] + " " if row["number"] else "")}{e(row["title"])} · '
                     f'{e(counts)}{"<span class=diff>yahan farq hai</span>" if row["differs"] else ""}</summary><div class="two">')
        for shape, films in row["films"].items():
            parts.append(f'<div class="col"><h3>Roop {e(shape)}</h3>')
            if not films:
                parts.append('<div class="none">is heading ki koi film nahi</div>')
            for f in films:
                analogy = (f.get("analogy") or {}).get("picture") or ""
                lines = [f'<div class="film"><div class="t">{e(f.get("id") or "")} · {e(f.get("title") or "")} '
                         f'({f.get("minutes")} min)</div>',
                         f'<div class="k"><b>Sawaal:</b> {e(f.get("question") or "")}</div>',
                         f'<div class="k"><b>Shuruaat:</b> {e(f.get("opens_with") or "")}</div>']
                if analogy:
                    lines.append(f'<div class="k"><b>Analogy:</b> {e(analogy)}</div>')
                if f.get("examples"):
                    lines.append(f'<div class="k"><b>Examples:</b> {e("; ".join(f["examples"]))}</div>')
                if f.get("real_world"):
                    lines.append(f'<div class="k"><b>Asli duniya mein:</b> {e("; ".join(f["real_world"]))}</div>')
                lines.append(f'<div class="k"><b>NCERT items:</b> {len(f.get("teaches") or [])} · <b>tasveerein:</b> '
                             f'{len(f.get("saman") or [])}</div><details class="more"><summary>kahani aur saman</summary>'
                             f'<div class="k"><b>Kahani:</b> {e(" → ".join(f.get("story") or []))}</div>'
                             + "".join(f'<div class="k">• {e(s.get("id") or "")} {e(s.get("kind") or "")}: {e(s.get("shows") or "")}'
                                       + (f' (dobara: {e(s["reuse_of"])})' if s.get("reuse_of") else "") + "</div>"
                                       for s in f.get("saman") or [])
                             + (f'<div class="k"><b>Kitaab se bahar:</b> '
                                f'{e("; ".join(o.get("what", "") for o in f.get("outside_book") or []))}</div>'
                                if f.get("outside_book") else "")
                             + "</details></div>")
                parts.append("".join(lines))
            parts.append("</div>")
        parts.append("</div></details>")
    parts.append("<h2>Poore chapter ka flow</h2>")
    parts += [f'<div class="box"><b>Roop {e(shape)}</b><div class="k">{e(s["flow"])}</div></div>'
              for shape, s in data["shapes"].items()]
    parts.append("</main></body></html>")
    return "\n".join(parts)


def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=1)
