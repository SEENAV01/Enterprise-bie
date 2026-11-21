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


NOT_TAUGHT = ("running", "label")     # the code reader's running heads and a figure's words (bie.brain.reading)
OWN_LINE = ("heading", "caption", "table", "aside", "equation")    # kinds that are a book line of their own, never inside a sentence
ENTRY = re.compile(r"^(?:Chapter\s+\d+|\d+\.\d+|\d+\.\s|[•●▪-]\s)")    # a side column's new entry ("Chapter 12", "11.3")


def _kind(block) -> str:
    return getattr(block, "kind", "text") or "text"


def teachable(pages) -> dict:
    """{block id: text} for every block long enough to carry a teachable idea (not a running head, a heading or a figure's
    words)."""
    out = {}
    for page in pages:
        for block in page.blocks:
            text = " ".join((block.text or "").split())
            if len(text) >= TEACHABLE_CHARS and _kind(block) not in NOT_TAUGHT + ("heading",):
                out[block.id] = text
    return out


def all_blocks(pages) -> dict:
    return {block.id: " ".join((block.text or "").split()) for page in pages for block in page.blocks}


# --- the book's own lines for one question (Navin, 20 November 2026, on the Q14 film: "video ki script jo teacher samjha
# raha hai usse har baat cover honi chahiye"; "tum mujhe batao is video se NCERT ka konsa text clear hota hai"). A question's
# blocks are lines of the page; its book lines are the whole sentences those blocks belong to, so a film can be checked
# sentence by sentence and Navin can find each one on its printed page.

LONE_MARK = re.compile(r"^[0-9+\-– ]{1,4}$")            # a block that is only a subscript or charge (the 0 of CF0, the 2 of CO2)
FOOTER = re.compile(r"^[0-9][0-9\-–/ ]*$")              # a printed edition or page line such as "2024-25"
HEADER_NUMBER = re.compile(r"^([0-9]{1,4})\s+[A-Z]|[A-Z]\s+([0-9]{1,4})$")
CAPTION = re.compile(r"^(Figure|Fig\.|Table)\s+[0-9]")
SENTENCE_END = re.compile(r"(?<=[.?!])\s+(?=[A-Z0-9(\"'“])")


def printed_page(page) -> str:
    """The page number printed in the page's running head ("PHOTOSYNTHESIS IN HIGHER PLANTS 141" -> "141"), else the
    PDF page number."""
    for block in page.blocks[:2]:
        text = " ".join((block.text or "").split())
        found = HEADER_NUMBER.search(text) if text.upper() == text else None
        if found:
            return found.group(1) or found.group(2)
    return str(page.number)


def _running_head(page, index: int, text: str) -> bool:
    return (index < 2 and text.upper() == text and bool(HEADER_NUMBER.search(text))) or (
        index == len(page.blocks) - 1 and bool(FOOTER.match(text)))


def _pieces(page) -> list:
    """(block, text) for the page's blocks, with each lone subscript put back after the term it belongs to: the text
    layer gives the 0 of CF0 as its own block, sitting inside the line's height, at the term's place along the line."""
    out = [[block, " ".join((block.text or "").split())] for block in page.blocks]
    for index, (block, piece) in enumerate(out):
        if not LONE_MARK.match(piece or "x") or " " in piece.strip():
            continue
        middle = (block.box[1] + block.box[3]) / 2
        for back in range(index - 1, max(-1, index - 3), -1):
            line, text = out[back]
            x0, y0, x1, y1 = line.box
            if not (y0 <= middle <= y1 + 0.004) or x1 <= x0 or LONE_MARK.match(text or "x"):
                continue
            guess = (block.box[0] - x0) / (x1 - x0) * len(text)
            ends = [m.end() for m in re.finditer(r"[A-Z][A-Za-z]*", text)]
            best = min(ends, key=lambda e: abs(e - guess), default=None)
            if best is not None and abs(best - guess) <= 5:
                out[back][1] = text[:best] + piece.strip() + text[best:]
                out[index][1] = ""
            break
    return [(block, piece) for block, piece in out]


def book_lines(pages, block_ids) -> list:
    """The question's book lines: every whole sentence (across lines and page breaks) most of whose letters lie in the
    question's blocks, in reading order, as [{"n", "text", "page", "blocks"}]. Running heads, footers, lone subscripts
    and a figure's words are left out; a heading, a figure caption, a table (one line), a side-column entry and an
    equation are lines of their own and never cut the sentence they sit inside. A block id a question names also stands for the further
    parts the code reader cut from that printed line (``<id>.2``), and an id the reader absorbed stands for the block it
    went into (``Page.absorbed``): a plan made before the reader keeps its lines."""
    wanted = set(block_ids or [])
    if not wanted:
        return []
    wanted |= {host for page in pages for gone, host in getattr(page, "absorbed", ()) if gone in wanted}
    wanted |= {block.id for page in pages for block in page.blocks if block.id.split(".")[0] in wanted}
    text, owner, page_of, order, captions = "", [], {}, {}, []
    for page in pages:
        printed = printed_page(page)
        for index, (block, piece) in enumerate(_pieces(page)):
            order[block.id] = len(order)
            if not piece or LONE_MARK.match(piece) or _running_head(page, index, piece) or _kind(block) in NOT_TAUGHT:
                continue
            page_of[block.id] = printed
            if CAPTION.match(piece) or _kind(block) in OWN_LINE:
                if block.id in wanted:
                    last = captions[-1] if captions else None
                    if (last and _kind(block) in ("table", "aside") and last[2] == _kind(block)
                            and order[last[0][-1]] == order[block.id] - 1
                            and not (_kind(block) == "aside" and ENTRY.match(piece))):
                        last[0].append(block.id)         # one table, or one side-column entry, is one book line
                        last[1] += (" / " if _kind(block) == "table" else " ") + piece
                    else:
                        captions.append([[block.id], piece, _kind(block)])
                continue
            if text:
                joint = "" if text.endswith("-") and piece[:1].islower() else " "
                text += joint
                owner.extend([None] * len(joint))
            text += piece
            owner.extend([block.id] * len(piece))
    found, start = [], 0
    for end in [m.start() for m in SENTENCE_END.finditer(text)] + [len(text)]:
        ids = [o for o in owner[start:end] if o]
        sentence = re.sub(r"\s+([,.;:?!])", r"\1", text[start:end].strip())
        if ids and sum(1 for o in ids if o in wanted) * 2 > len(ids) and len(sentence) >= 12:
            found.append((list(dict.fromkeys(o for o in ids if o in wanted)), sentence))
        start = end + 1
    found += [(bids, piece) for bids, piece, _ in captions]
    found.sort(key=lambda item: order.get(item[0][0], 0))
    return [{"n": n, "text": sentence, "page": page_of.get(blocks[0], ""), "blocks": blocks}
            for n, (blocks, sentence) in enumerate(found, 1)]


# --- the page that opens a unit (Navin, 21 November 2026, on film Q01 of Photosynthesis: "Ise unit ka overview naam se bna
# do jisme us unit ke sbhi chapters mein hum kya samjhenge jaisa overview mil jaaye"; card: "Sirf Unit page se banao").
# A chapter PDF may begin with its unit's opening page ("UNIT 4 / PLANT PHYSIOLOGY / Chapter 11 ... Chapter 12 ...
# Chapter 13" beside a paragraph on the whole unit). That page is no chapter question's matter: its blocks leave every
# chapter question and make one short film of their own, the unit's overview, made only from that page.

UNIT_SPELLED = re.compile(r"^(?:UNIT(\d{1,2})|U(\d{1,2})NIT)")       # the text layer may split small caps: "U 4" + "NIT"
CHAPTER_MENTION = re.compile(r"\bChapter\s+(\d{1,2})\b")
UNIT_TITLE = re.compile(r"^[A-Z][A-Z ,&\-]{3,}$")


def unit_pages(pages) -> dict:
    """{page number: {"unit", "title", "chapters"}} for each page that opens a unit: its first blocks spell UNIT and a
    number, and it names at least two chapters."""
    found = {}
    for page in pages:
        texts = [" ".join((block.text or "").split()) for block in page.blocks]
        head = re.sub(r"\s+", "", " ".join(texts[:3])).upper()
        spelled = UNIT_SPELLED.match(head)
        chapters = list(dict.fromkeys(m.group(1) for t in texts for m in CHAPTER_MENTION.finditer(t)))
        if not spelled or len(chapters) < 2:
            continue
        title = next((t for t in texts[:5] if UNIT_TITLE.match(t) and t.replace(" ", "") not in ("UNIT", "NIT")), "")
        found[page.number] = {"unit": spelled.group(1) or spelled.group(2), "title": title.title(), "chapters": chapters}
    return found


def with_unit_overview(plan: dict, pages) -> dict:
    """The question plan with the unit's opening page moved into its own overview question (id ``u<unit>``, first in the
    list): every point's blocks from that page leave the chapter questions (a point left with none is dropped, and so
    is a question left with no point) and become the overview's points, with one more point for the page's remaining
    lines (the unit's name and its chapters). Running it again changes nothing; a plan without such a page is returned
    as it is."""
    units = unit_pages(pages)
    if not units or not isinstance(plan, dict):
        return plan
    number = min(units)
    unit = units[number]
    page_blocks = [(block, " ".join((block.text or "").split())) for page in pages if page.number in units
                   for block in page.blocks]
    on_page = {block.id for block, text in page_blocks if text and not FOOTER.match(text)}
    qid = f"u{unit['unit']}"
    questions = [dict(q) for q in plan.get("questions") or [] if isinstance(q, dict)]
    overview = next((q for q in questions if q.get("id") == qid), None)
    moved, kept_questions = [], []
    for q in questions:
        if q is overview:
            continue
        points = []
        for p in q.get("points") or []:
            ids = list(p.get("block_ids") or [])
            away = [i for i in ids if i in on_page]
            if away:
                moved.append({"block_ids": away, "point": p.get("point", ""), "kind": p.get("kind", "facts_numbers")})
            stay = [i for i in ids if i not in on_page]
            if stay:
                points.append(dict(p, block_ids=stay))
        if points:
            kept_questions.append(dict(q, points=points))
    if overview is None and not moved:
        return plan
    if overview is None:
        chapters = ", ".join(f"Chapter {c}" for c in unit["chapters"])
        name = f"Unit {unit['unit']}" + (f" ({unit['title']})" if unit["title"] else "")
        overview = {"id": qid, "pillar": "unit", "overview": True, "unit": unit,
                    "question": f"{name} ke chapters mein hum kya samjhenge?",
                    "hook": f"{chapters}: ek hi unit ke chapter, ek hi badi kahani.",
                    "points": [], "film": {"length": "short", "showing_moment": ""},
                    "game_stage": {"mechanic": "sort_groups", "idea": ""}}
    overview = dict(overview, points=list(overview.get("points") or []) + moved)
    used = {i for p in overview["points"] for i in p.get("block_ids") or []}
    rest = [block.id for block, text in page_blocks if block.id in on_page and block.id not in used]
    if rest:
        overview["points"].append({"block_ids": rest, "kind": "classification",
                                   "point": f"Unit {unit['unit']} {unit['title']} ke chapters: "
                                            + ", ".join(f"Chapter {c}" for c in unit["chapters"])})
    out = dict(plan, questions=[overview] + kept_questions)
    out["unit_overview"] = qid
    return out


TERM = re.compile(r"[A-Za-z0-9+]+")


def _norm_term(token: str) -> str:
    return re.sub(r"[0-9+\-]", "", token).casefold()


def is_term(token: str) -> bool:
    """A short form or formula a learner must meet in the book's own spelling: ATP, CO2, G3P, RuBP, H+ (not Pi, not words)."""
    uppers = sum(c.isupper() for c in token)
    return len(token) >= 2 and (uppers >= 2 or (uppers >= 1 and any(c.isdigit() or c == "+" for c in token)))


def chapter_terms(pages) -> list:
    """Every token of the chapter and every run of 2 or 3 neighbouring tokens joined, without digits and charges (the
    text layer splits subscripts off: "CO 2", "H O"), so a term is found however the PDF split it."""
    known = set()
    for page in pages:
        for block in page.blocks:
            tokens = [_norm_term(t) for t in TERM.findall(block.text or "")]
            tokens = [t for t in tokens if t]
            for n in (1, 2, 3):
                for i in range(len(tokens) - n + 1):
                    known.add("".join(tokens[i:i + n]))
    return sorted(known)


def unknown_terms(text: str, known) -> list:
    """The short forms and formulas in ``text`` that the chapter never uses (G3P in a chapter that says PGA)."""
    known = known if isinstance(known, (set, frozenset)) else set(known or [])
    out = []
    for token in TERM.findall(text or ""):
        if is_term(token) and _norm_term(token) and _norm_term(token) not in known and token not in out:
            out.append(token)
    return out


def chapter_text(pages) -> str:
    lines = []
    for page in pages:
        lines.append(f"--- page {page.number} ---")
        for block in page.blocks:
            text = " ".join((block.text or "").split())
            if text:
                kind = _kind(block)
                lines.append(f"[{block.id}] {text}" if kind == "text" else f"[{block.id}] ({KIND_WORDS.get(kind, kind)}) {text}")
    return "\n".join(lines)


KIND_WORDS = {"heading": "heading", "equation": "equation", "caption": "figure caption", "table": "table row", "aside": "side column",
              "label": "a figure's words, not running text", "running": "running head or page line"}


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
    if isinstance(answer, dict):
        answer = with_unit_overview(answer, pages)     # the unit's opening page gets its own overview film
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
