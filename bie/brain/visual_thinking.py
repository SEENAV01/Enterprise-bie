"""Dikhane ki soch: the visual-idea step before layout (Task 046 Part D1; Navin's verdict on the Money videos, 30 October 2026).

Navin: "jo bola ja rha hai screen ke visuals se wo baat clear ho ... visuals tarike se user ko teacher ki baat aankhon ke jariye
dimag tak pahunchate ho, is parkar se naration ka scene plan bnana hai"; "agar puri video mein sirf text hi text screen par dikha
to video, video nhi ek book ban jaayegi"; page 2: "dekho kaise icons ka use kiya ja rha hai khud samjh aa rha hai ki neeche likhe
text ka matlb kya hai". The 195 Money plans of 29 October showed one setup (a bank, four people, text on boards: 137 of 195 plans
in the two world kits, 27 distinct icons of 4,213) and lost the book's own pictures (the six Evolution-of-Money drawings, the two
page-4 timelines, the five-currency panel, the coin-limit table were covered in words, never drawn).

This module adds, before any layout:

- **the idea of every beat** (the maker's strict answer, ``IDEAS_SCHEMA``): its key idea, its relation from the closed list of
  ``rulebook/visual_verbs.json`` (reject, accept, compulsory, limit, more_less, count, sequence, cause_effect, compare,
  part_whole, place, change, promise, question; ``other`` with a note, which is logged so Navin can add an entry), the things,
  people and places it names, what is seen and on which word;
- **the picture type of a part, decided by code first** (``book_pictures``, ``picture_of``): a book diagram or table the part
  covers is drawn as itself (a timeline with the book's years and labels, a table row by row, a panel of items as a gallery
  of icon cards, a flow of boxes and arrows), then the card part's type is the hint, and the maker decides only where code
  cannot; the picture node is placed by code (``picture_node``) and the maker builds around it;
- **the needs list** (``resolve_needs``): the maker names things in words; code finds them in the full icon index (aliases,
  Hindi words, emoji names: ``toolbox.icons.search``) and in the lesson's asset library; whatever is not found goes to
  ``needs.json`` (the thing, its beats, its kind, the sources tried) for the fetch step in GitHub Actions;
- **the dikhane ki list** (``dikhane_list``): per video, beat → what is seen → on which word → how (code or maker), written
  to ``visual_ideas/<video>.json`` (``bie.brain.visual-ideas/1``) and shown on a page BEFORE the render;
- **the code checks of Part D** (``beat_cover_problems``, ``text_only_problems``, ``phrase_problems``, ``caution_problems``,
  ``book_picture_problems``): every beat shows at least one non-text thing cued on its words; no text-only screen longer than
  ``TEXT_ONLY_LIMIT_S``; screen text is a name or a short natural phrase, never a sentence; every book picture the part covers
  is drawn; a caution or fact-check line never reaches the screen (a background check); and the per-video ``report``.
"""
from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from . import formats
from .common import S, arr, obj
from .video import saanche, world
from .runner import NOTES_SCHEMA
from ..toolbox import icons

VERBS_PATH = Path(__file__).resolve().parent / "rulebook" / "visual_verbs.json"
SCHEMA = formats.tag("visual_ideas")
NEEDS_SCHEMA = formats.tag("needs")
VERSION = "visual-ideas/1"
TEXT_ONLY_LIMIT_S = 10.0                 # Navin, 30 October 2026: a screen of text alone is a book, not a video
PHRASE_WORDS = 8                         # screen text is a name or a short natural phrase; a sentence lives in the narration
PICTURE_TYPES = ("timeline", "gallery", "table", "flow", "tree", "chart", "map", "things")
BOOK_PICTURE_KINDS = ("diagram", "table")
BOOK_CHILD_KINDS = ("diagram_label", "table_row", "caption")
# Canvas and world element kinds the learner sees as a thing (not text): what a beat must show (D1 check 1).
NON_TEXT_CANVAS = ("icon", "crowd", "picture", "mark", "arrow", "value", "table", "tree", "highlight", "action")
NON_TEXT_WORLD = ("shop", "bank", "price_tag", "crowd", "coin_rain", "balance", "pull_arrow", "teller", "shopkeeper", "action")
TEXT_CANVAS = ("text", "callout")
TEXT_WORLD = ("board", "label", "title")
# A caution, caveat or fact-check line (Navin, 30 October 2026: "background mein ek check hai, visuals par to yeh cheejen na dikhe").
CAUTION = re.compile(r"illustrative|imagined|imaginary|hypothetical|काल्पनिक|मान\s*लीजिए|मान\s*लो|assum(?:e|ed|ption)|not (?:given|supplied|"
                     r"provided|verified)|no (?:numerical )?(?:data|source|ratio)|source[- ]?(?:evidence|less)|outside (?:clarification|fact|"
                     r"label|the book)|fact[- ]?check|verified|caveat|clarification|standard textbook|textbook mechanism|दावा नहीं|"
                     r"(?:data|आँकड़े|आंकड़े|dates?) (?:नहीं|not)", re.IGNORECASE)
SENTENCE_END = re.compile(r"[।.!?]\s*$")
YEAR = re.compile(r"(?<!\d)(\d{3,4})\s*(CE|BCE|BC|AD)?(?!\d)")
CENTURY = re.compile(r"(\d{1,2})(?:st|nd|rd|th)\s*c(?:entury|\.)?\s*(BCE|BC|CE|AD)?", re.IGNORECASE)
PANEL = re.compile(r"^\s*(\d+)\s*[.)]\s*([^|]+?)\s*(?:\||$)")
NOUN = re.compile(r"[A-Za-z][A-Za-z'-]{1,}|[ऀ-ॿ]{2,}")
# Card rule 8 stays (Navin, 30 October 2026: historical figures are his decision): no portrait is ever asked for or fetched.
PORTRAIT = re.compile(r"portrait|photo of (?:a |the )?(?:person|man|woman|king|queen|ruler|leader|people|him|her)\b|face of|painting of|"
                      r"statue of|likeness|पोर्ट्रेट|तस्वीर", re.IGNORECASE)


class IdeaError(ValueError):
    pass


# ---------------------------------------------------------------- the rulebook of visual verbs

@lru_cache(maxsize=2)
def load_verbs(path: str = str(VERBS_PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def relations(verbs: dict | None = None) -> tuple:
    return tuple(r["id"] for r in (verbs or load_verbs())["relations"])


def relation_entry(relation: str, verbs: dict | None = None) -> dict:
    return next((r for r in (verbs or load_verbs())["relations"] if r["id"] == relation), {})


def guess_relation(say: str, verbs: dict | None = None) -> str:
    """The relation a beat's words suggest (code's own reading, offered to the maker and used when the maker says 'other')."""
    low = (say or "").lower()
    best, hits = "other", 0
    for r in (verbs or load_verbs())["relations"]:
        n = sum(1 for w in r.get("words") or [] if w and w.lower() in low)
        if n > hits:
            best, hits = r["id"], n
    return best


def verbs_text(verbs: dict | None = None) -> str:
    """The relations and how each is shown, for the maker's card."""
    return "\n".join(f"- {r['id']}: {r['show']}" + (f" (saanche: {', '.join(r['templates'])})" if r.get("templates") else "")
                     for r in (verbs or load_verbs())["relations"])


# ---------------------------------------------------------------- the maker's strict answer

TEMPLATE_CHOICES = ("none",) + tuple(saanche.TEMPLATE_NAMES) + ("other",)     # Task 046 Part D2: the kriya ka saancha of the beat
STRONG_PROCESSES = saanche.STRONG             # the recipes whose words, when a beat says them, need the recipe or a reason (rulebook)
IDEA = obj({"beat_id": S, "idea": S, "relation": S, "relation_note": S, "things": arr(S), "people": arr(S), "places": arr(S),
            "shows": S, "on_word": S, "image_wanted": S, "template": {"type": "string", "enum": list(TEMPLATE_CHOICES)}, "template_note": S})
IDEAS_SCHEMA = obj({"notes": NOTES_SCHEMA, "beats": arr(IDEA), "picture_type": {"type": "string", "enum": list(PICTURE_TYPES)},
                    "picture_note": S})            # the enum: the live run of 31 October 2026 wrote the card type there in 21 of 36 parts

ROLE = """You are BIE's visual thinker for one part of a video lesson of {subject} for {learners} ({exam}). The script is written and
passed; you do not change a word. Before any layout, say for EVERY beat what the learner should SEE so that the spoken point is
clear through the eyes (Navin, 30 October 2026: "jo bola ja rha hai screen ke visuals se wo baat clear ho"; a screen of text alone
is a book, not a video). Code then finds the things in BIE's icon index and asset library, places the book's own pictures, and
checks the layout.

Course: "{title}" · learner language: {language}.

For each beat give:
- idea: the key idea in a few words (what the teacher is making the learner understand right now).
- relation: ONE id from this list, how the idea relates its things (or "other" with relation_note; an "other" is logged so Navin can
  add it):
{verbs}
- things, people, places: the concrete nouns THIS beat names or implies, as plain English or Hindi words a picture can show:
  exactly the beat's own things, never a thing from an example, a card or another part (Navin, 2 November 2026: "jis cheej ka
  jikar hai wohi cheej dikhe"). Every thing you list is a promise: it must appear on screen in this beat. A real person is never
  drawn (card rule 8): name the role or the object, not the person.
- shows: what is seen, in at most {phrase_words} words, as a picture description of this beat's own things and what happens to
  them. Never a sentence for the screen: the sentence is the narration.
- on_word: the word of this beat (exactly as written) on which the picture should appear ("" = the beat's start).
- image_wanted: a real object of this beat that an icon cannot show and a photograph or museum image can, as search words; ""
  when an icon is enough. Never a person's portrait (card rule 8).
- template: when the beat tells a PROCESS the learner should see happen (Navin, 1 November 2026: "process show nahi ho rahi hai"),
  the recipe that shows it, or "compose" when no recipe fits but the motion parts do (the layout step writes the parts); "none"
  when the beat tells no process; "other" only when a motion part BIE lacks is needed (template_note names it: it goes to the
  missing-capability log). The actors, things and numbers always come from this beat. The recipes:
{templates}
  The motion parts every process is made of:
{parts}
- template_note: for "other" the process in a few words; for "none" on a beat that names a process word, why no saancha.
{picture_line}
Reply with the JSON object only."""

PICTURE_BY_CODE = ("Code has already decided this part's picture ({ptype}: {ptitle}) from the book's own {source}; it is placed at the top "
                   "of the canvas. Set picture_type to \"{ptype}\" and use picture_note for what the beats add around it.")
PICTURE_BY_MAKER = ("picture_type: the one picture this part needs most, from timeline, gallery (a row of icon cards), table, flow, tree, chart, "
                    "map or things (the things themselves with the relation's mark, arrow, meter or scale); the card part's type is "
                    "\"{card_type}\". picture_note: one line on why.")


def check_ideas(stub: dict, value: dict, *, picture: dict | None = None, verbs: dict | None = None) -> list:
    """The code check of the maker's ideas: every beat once, a known relation (or 'other' with a note), at least one noun, a short
    'shows' that is not a sentence, an on_word that is in the beat."""
    verbs = verbs or load_verbs()
    known = set(relations(verbs))
    beats = {b["beat_id"]: b.get("say", "") for b in stub["beats"]}
    seen, problems = [], []
    for row in value.get("beats") or []:
        bid = row.get("beat_id", "")
        if bid not in beats:
            problems.append(f"beat {bid!r} is not a beat of this part")
            continue
        seen.append(bid)
        if row.get("relation") not in known:
            problems.append(f"beat {bid}: relation {row.get('relation')!r} is not in the list ({', '.join(sorted(known))}); use 'other' with a note")
        elif row.get("relation") == "other" and not (row.get("relation_note") or "").strip():
            problems.append(f"beat {bid}: relation 'other' needs relation_note (what relation the picture shows)")
        named = [str(n).strip() for key in ("things", "people", "places") for n in (row.get(key) or []) if str(n).strip()]
        nouns = [n for n in named if _is_thing(n)]
        if not nouns:
            grammar = [n for n in named if not _is_thing(n)]
            problems.append(f"beat {bid}: name at least one thing, person or place the learner sees (a picture needs a thing)"
                            + (f"; {', '.join(repr(g) for g in grammar[:3])} {'is' if len(grammar) == 1 else 'are'} only grammar, not a thing" if grammar else ""))
        shows = (row.get("shows") or "").strip()
        if not shows:
            problems.append(f"beat {bid}: shows is empty: say what is seen")
        elif len(shows.split()) > PHRASE_WORDS * 2:
            problems.append(f"beat {bid}: shows is {len(shows.split())} words; describe the picture in at most {PHRASE_WORDS * 2}")
        word = (row.get("on_word") or "").strip()
        if word and word not in beats[bid]:
            problems.append(f"beat {bid}: on_word {word!r} is not written in that beat")
        template = row.get("template") or "none"
        if template not in TEMPLATE_CHOICES:
            problems.append(f"beat {bid}: template {template!r} is not one of {', '.join(TEMPLATE_CHOICES)}")
        elif template == "other" and not (row.get("template_note") or "").strip():
            problems.append(f"beat {bid}: template 'other' needs template_note (which process the beat shows), so BIE can learn it")
        elif template == "none" and not (row.get("template_note") or "").strip():
            named = saanche.guess_template(beats[bid])
            if named in STRONG_PROCESSES:
                problems.append(f"beat {bid} names a process ({named}: '{saanche.process_word(named, beats[bid])}'); pick the "
                                f"template {named!r} so the learner sees it happen, or say in template_note why not")
    missing = [b for b in beats if b not in seen]
    if missing:
        problems.append("every beat needs its idea; missing: " + ", ".join(missing))
    dup = sorted({b for b in seen if seen.count(b) > 1})
    if dup:
        problems.append("a beat appears twice: " + ", ".join(dup))
    ptype = (value.get("picture_type") or "").strip()
    if ptype not in PICTURE_TYPES and ptype in CARD_HINT:     # a card part's type ("definition") is read as its picture ("things")
        ptype = CARD_HINT[ptype]
    if ptype and ptype not in PICTURE_TYPES:
        problems.append(f"picture_type {ptype!r} is not one of {', '.join(PICTURE_TYPES)}")
    if picture and picture.get("by") == "book" and ptype and ptype != picture["type"]:
        problems.append(f"picture_type: code drew the book's {picture['type']} for this part; set picture_type to {picture['type']!r}")
    return problems


# ---------------------------------------------------------------- the book's own pictures (code first)

def _year_of(text: str):
    """A year from a label ('1661', '7th c.' → 650, '6th c. BCE' → -550, '1540 CE'), or None."""
    m = CENTURY.search(text or "")
    if m:
        n = int(m.group(1))
        year = (n - 1) * 100 + 50
        return -year if (m.group(2) or "").upper() in ("BCE", "BC") else year
    m = YEAR.search(text or "")
    if m:
        year = int(m.group(1))
        return -year if (m.group(2) or "").upper() in ("BCE", "BC") else year
    return None


def _date(year: int) -> str:
    """An ISO-like date for timeline_build (D3 reads negative and short years)."""
    return f"{year:04d}-01-01" if year > 0 else f"-{abs(year):06d}-01-01"


def _cells(content: str) -> list:
    return [c.strip() for c in str(content or "").split("|") if c.strip()]


def _strip_label(cell: str) -> str:
    """'Commodity: Salt' → 'Salt'; 'ASPECT: BASIS OF VALUE' → 'BASIS OF VALUE'."""
    head, sep, rest = cell.partition(":")
    return rest.strip() if sep and len(head) <= 40 and rest.strip() else cell.strip()


def _columns(parent_content: str) -> list:
    m = re.search(r"Columns?:\s*([^.\n]+)", parent_content or "")
    return _cells(m.group(1)) if m else []


def children_of(items: dict, parent_id: str) -> list:
    kids = [i for i in items.values() if i.get("parent_item_id") == parent_id and i.get("kind") in BOOK_CHILD_KINDS]
    return sorted(kids, key=lambda i: (int(re.sub(r"\D", "", i["item_id"].split("-i")[-1]) or 0)))


def timeline_events(parent: dict, kids: list) -> list:
    """[{date, year, label, item_id}] from dated labels ('1661 | Sweden | First banknotes'); from the parent's own text when the
    labels are not dated one by one ('6th c. BCE / Punch-marked → Mauryan / Imperial silver → …')."""
    events = []
    for k in kids:
        cells = _cells(k["content"])
        year = _year_of(cells[0] if cells else k["content"])
        if year is None or not cells or len(cells[0]) > 14:          # a date cell is short ('1661', '7th c.'); a sentence is a description
            continue
        name = cells[1] if len(cells) > 1 else ""
        detail = cells[2] if len(cells) > 2 else ""
        events.append({"date": _date(year), "year": year, "when": cells[0], "name": name, "detail": detail,
                       "label": " — ".join(c for c in cells[1:] if c)[:60], "item_id": k["item_id"]})
    if len(events) >= 2:
        return _with_icons(events)
    # the parent's chain: "A / B → C / D → …" with a date in some stages; the labels below or above the markers are its children
    stages = [re.split(r"\.\s", st, maxsplit=1)[0].strip(" .") for st in re.split(r"\s*(?:→|➔|->)\s*", re.sub(r"^[^:]*:\s*|^[^.]*\.\s*", "", parent.get("content", "")))]
    for st in stages:
        head, _, tail = st.partition("/")
        year = _year_of(head)
        when = head.strip() if year is not None else head.strip()
        name = tail.strip() if tail else head.strip()
        kid = next((k for k in kids if name and name.split()[0].lower() in k.get("content", "").lower()), None)
        events.append({"date": _date(year) if year is not None else "", "year": year, "when": when, "name": name if tail else "",
                       "detail": "", "label": name[:60], "item_id": (kid or parent)["item_id"]})
    dated = [e for e in events if e["year"] is not None]
    return _with_icons(events) if len(events) >= 2 and dated else []


def _with_icons(events: list) -> list:
    for e in events:
        e["icon"] = panel_icon({"caption": e.get("detail", ""), "name": e.get("name", "")}, fallback="tw:1f4c5")
    return events


def gallery_panels(parent: dict, kids: list) -> list:
    """[{n, name, caption, nouns, item_id}] from numbered or columned labels ('1. BARTER | Wheat exchanged for cloth. …',
    '$ | United States Dollar (USD) | …')."""
    panels = []
    for n, k in enumerate(kids, 1):
        cells = _cells(k["content"])
        if not cells:
            continue
        m = PANEL.match(k["content"])
        name = m.group(2).strip() if m else (cells[1] if len(cells) > 1 and len(cells[0]) <= 2 else cells[0])
        caption = cells[1] if m and len(cells) > 1 else (cells[2] if len(cells) > 2 else (cells[1] if len(cells) > 1 else ""))
        caption = re.split(r"\.\s", caption, maxsplit=1)[0].strip(" .")
        nouns = [w for w in re.findall(r"[A-Za-z][A-Za-z-]{2,}", (name + " " + caption))][:6]
        panels.append({"n": int(m.group(1)) if m else n, "name": name[:40], "caption": caption[:60], "nouns": nouns, "item_id": k["item_id"],
                       "numbered": bool(m)})
    return panels if len(panels) >= 2 else []


def table_rows(parent: dict, kids: list) -> dict:
    """{columns, rows: [{cells, item_id}]} from a book table and its rows ('Commodity: Salt | Where it was used: Ancient Rome')."""
    columns = _columns(parent.get("content", ""))
    rows = []
    for k in kids:
        if k.get("kind") != "table_row" or re.search(r"header row", k.get("where_on_page", ""), re.I):
            continue
        cells = [_strip_label(c) for c in _cells(k["content"])]
        if cells:
            rows.append({"cells": cells, "item_id": k["item_id"]})
    if not columns and rows:
        columns = [c.partition(":")[0].strip() for c in _cells(kids[0]["content"])] if ":" in kids[0]["content"] else [f"col {i + 1}" for i in range(len(rows[0]["cells"]))]
    width = max((len(r["cells"]) for r in rows), default=0)
    columns = (columns + [""] * width)[:width] if width else columns
    rows = [dict(r, cells=(r["cells"] + [""] * width)[:width]) for r in rows]
    return {"columns": columns, "rows": rows} if rows and columns else {}


def flow_steps(parent: dict, kids: list) -> dict:
    """{nodes: [{id, label, item_id}], edges: [[a, b]]} from a chain of boxes joined by arrows in the parent's text."""
    text = parent.get("content", "")
    chain = [re.split(r"\.\s", s, maxsplit=1)[0].strip(" .") for s in re.split(r"\s*(?:→|➔|->)\s*", re.sub(r"^[^:]*:\s*", "", text)) if s.strip(" .")]
    if len(chain) < 3:
        return {}
    nodes = [{"id": f"n{i + 1}", "label": re.sub(r"\s*\(.*?\)\s*", " ", step).strip()[:40]} for i, step in enumerate(chain[:8])]
    for node, k in zip(nodes, kids):
        node["item_id"] = k["item_id"]
    return {"nodes": nodes, "edges": [[nodes[i]["id"], nodes[i + 1]["id"]] for i in range(len(nodes) - 1)]}


def book_pictures(items: dict, item_ids) -> list:
    """The book diagrams and tables a part covers (by a parent or any of its labels or rows), each with its picture type and
    the data code drew from the book: [{item_id, kind, type, title, data, children, page}]."""
    wanted = set(item_ids or [])
    parents = {}
    for iid in wanted:
        item = items.get(iid)
        if not item:
            continue
        if item.get("kind") in BOOK_PICTURE_KINDS:
            parents[iid] = item
        elif item.get("kind") in BOOK_CHILD_KINDS and item.get("parent_item_id") in items \
                and items[item["parent_item_id"]].get("kind") in BOOK_PICTURE_KINDS:
            parents[item["parent_item_id"]] = items[item["parent_item_id"]]
    out = []
    for pid, parent in sorted(parents.items()):
        kids = children_of(items, pid)
        covered = [k["item_id"] for k in kids if k["item_id"] in wanted]
        title = re.split(r"[.:]\s", parent.get("content", ""), maxsplit=1)[0].strip()[:60]
        pic = {"item_id": pid, "kind": parent.get("kind"), "page": parent.get("page"), "title": title, "children": [k["item_id"] for k in kids],
               "covered_children": covered}
        if parent.get("kind") == "table":
            data = table_rows(parent, kids)
            pic.update(type="table" if data else "things", data=data)
        else:
            events = timeline_events(parent, kids) if parent.get("content_type") == "timeline" or YEAR.search(parent.get("content", "")) else []
            numbered = sum(1 for k in kids if PANEL.match(k.get("content", "")))
            arrows = re.search(r"→|➔|->", parent.get("content", "")) is not None
            if events:
                pic.update(type="timeline", data={"events": events})
            elif arrows and numbered < 2 and flow_steps(parent, kids):          # boxes joined by arrows, not numbered panels: a flow
                pic.update(type="flow", data=flow_steps(parent, kids))
            else:
                panels = gallery_panels(parent, kids)
                if panels:
                    pic.update(type="gallery", data={"panels": panels})
                else:
                    flow = flow_steps(parent, kids)
                    pic.update(type="flow" if flow else "things", data=flow)
        out.append(pic)
    return out


CARD_HINT = {"timeline": "timeline", "comparison": "table", "process": "flow", "classification": "tree", "structure": "tree",
             "facts_numbers": "things", "cause_effect": "things", "definition": "things", "figure": "gallery", "none": "things"}


def picture_of(items: dict, item_ids, card_type: str = "") -> dict:
    """What this part's picture is, decided by code first: {type, by: book|card|maker, pictures: [...], hint}. ``by == "book"``
    when the part covers a book diagram or table (drawn as itself); ``by == "card"`` names the card type's hint for the
    maker; ``by == "maker"`` when nothing is known."""
    pics = book_pictures(items, item_ids)
    drawn = [p for p in pics if p["type"] != "things"]
    if drawn:
        return {"type": drawn[0]["type"], "by": "book", "pictures": drawn, "hint": CARD_HINT.get(card_type or "", "things")}
    hint = CARD_HINT.get(card_type or "", "")
    return {"type": hint or "things", "by": "card" if hint else "maker", "pictures": [], "hint": hint or "things"}


def panel_icon(panel: dict, *, index=None, fallback: str = "tw:1f5bc") -> str:
    """The icon for a gallery panel or a timeline event: its caption's things first ('Wheat exchanged for cloth' → the sheaf), then
    its name; a frame (a calendar for a date) when the thing has no icon yet (a need)."""
    name = str(panel.get("name") or "")
    named = bool(icons._alias_ids(icons._words(_strip_label(name)))) if name else False    # "Euro", "Japanese Yen": the name says it
    order = ([name] if named else []) + [panel.get("caption", "")] + list(panel.get("nouns") or []) + ([] if named else [name])
    for query in order:
        if not str(query).strip():
            continue
        rows = icons.search(query, limit=1) if index is None else icons.search(query, index, limit=1)
        if rows:
            return rows[0]["id"]
    return fallback


def place_pictures(items: dict, beats: list, card_type: str = "", *, prefix: str = "book") -> tuple:
    """(picture, nodes) for a part: what its picture is (``picture_of``, from the items its own beats cover) and the picture nodes
    code places, one per book picture, in the order the beats reach them; when a part covers two book pictures (v4's two
    page-4 timelines) the first leaves as the second arrives, in the same cells. ``beats``: the part's beats with their
    ``covers_item_ids``."""
    order = [b["beat_id"] for b in beats]
    covers = {}
    for b in beats:
        for iid in b.get("covers_item_ids") or []:
            covers.setdefault(iid, b["beat_id"])
    picture = picture_of(items, sorted(covers), card_type)

    def start(bp):
        hits = [order.index(covers[i]) for i in [bp["item_id"]] + list(bp.get("children") or []) if i in covers]
        return min(hits) if hits else 0
    pics = sorted(picture["pictures"], key=start)
    starts = []
    for bp in pics:                                   # each picture gets its own beats: two never share a start
        starts.append(max(start(bp), (starts[-1] + 1) if starts else 0))
    nodes, slim, placed, stacked = [], [{"beat_id": b["beat_id"], "say": b.get("say", "")} for b in beats], [], 0
    for k, bp in enumerate(pics):
        s0 = starts[k]
        if s0 >= len(order):                          # more pictures than beats: stack it below the earlier one when there is room
            cell = picture_cell(bp)
            if stacked + cell[3] + picture_cell(pics[0])[3] > 7:
                picture.setdefault("not_drawn", []).append(bp["item_id"])
                continue
            stacked += cell[3]
            node = picture_node(bp, slim, {i: order[0] for i in covers}, node_id=f"{prefix}_{bp['item_id'].replace('-', '_')}",
                                cell=[0, picture_cell(pics[0])[3] + stacked - cell[3], 12, cell[3]])
            nodes.append(node)
            placed.append(bp)
            continue
        s1 = starts[k + 1] if k + 1 < len(pics) and starts[k + 1] < len(order) else len(order)
        window = {i: (b if s0 <= order.index(b) < s1 else order[s0]) for i, b in covers.items()}
        node = picture_node(bp, slim[s0:], window, node_id=f"{prefix}_{bp['item_id'].replace('-', '_')}",
                            until_cue=[order[s1], ""] if s1 < len(order) else None)
        nodes.append(node)
        placed.append(bp)
    picture["pictures"] = placed
    return picture, nodes


def picture_cell(picture: dict) -> list:
    """Where code places a book picture on the 12 x 8 grid: a table takes the rows it needs (the picture IS the part), a timeline,
    flow or gallery the top three rows; the maker builds in the rows below."""
    ptype = picture.get("type")
    if ptype == "table":
        rows = len((picture.get("data") or {}).get("rows") or [])
        return [0, 0, 12, 3 if rows <= 3 else 5 if rows <= 6 else 7]
    if ptype in ("flow", "tree"):
        return [0, 0, 12, 4]
    return [0, 0, 12, 3]


def picture_node(picture: dict, beats: list, covers: dict, *, cell=None, node_id: str = "book_picture", until_cue=None) -> dict:
    """The canvas node code places for a book picture: kind 'picture' with the book's data; each event, row or panel appears on
    the beat that covers its item (``covers``: item id → beat id), else on the part's first beat."""
    first = beats[0]["beat_id"] if beats else ""

    order = [b["beat_id"] for b in beats]

    def cue_for(item_id):
        bid = covers.get(item_id)
        return [bid if bid in order else first, ""]
    data = json.loads(json.dumps(picture.get("data") or {}))
    if picture["type"] == "timeline":
        for e in data.get("events", []):
            e["cue"] = cue_for(e.get("item_id"))
    elif picture["type"] == "gallery":
        for p in data.get("panels", []):
            p["cue"] = cue_for(p.get("item_id"))
            p["icon"] = panel_icon(p)
    elif picture["type"] == "table":
        for r in data.get("rows", []):
            r["cue"] = cue_for(r.get("item_id"))
    elif picture["type"] == "flow":
        for n in data.get("nodes", []):
            n["cue"] = cue_for(n.get("item_id"))
    node = {"id": node_id, "kind": "picture", "cell": list(cell or picture_cell(picture)), "cue": [first, ""],
            "picture": {"type": picture["type"], "title": picture.get("title", ""), "item_id": picture["item_id"], **data}}
    if until_cue:
        node["until_cue"] = list(until_cue)
    return node


# ---------------------------------------------------------------- the needs list

# Words that are never a thing a picture can show (a pronoun, a filler, an adverb, a verb form): a "thing" that is only one of these
# is dropped before the search, so the needs list names things, not grammar (the Money dry run, 31 October 2026).
NOT_A_THING = frozenset("""मानिए मान मानो लीजिए लो कितना कितने कितनी यहाँ यहां वहाँ वहां सीधा सीधे पहले बाद इसे उसे इन्हें उन्हें ऐसा ऐसे वैसा
कैसे क्या क्यों कब अब फिर यह वह ये वो इस उस इसका उसका हम आप तुम मैं कोई कुछ सब सभी बहुत ज़्यादा ज्यादा कम सिर्फ़ सिर्फ अगर तब जब
जैसे इसलिए लेकिन मतलब यानी ठीक सही गलत बात तरीका चीज़ चीज here there this that thing things way something""".split())


def _is_thing(noun: str) -> bool:
    from . import soul
    from .video import screen_text
    words = noun.lower().split()
    junk = NOT_A_THING | soul.STOP | soul.HINDI_VERB_WORDS | screen_text.STOP
    if not re.search(r"[a-z\u0900-\u097f]", noun.lower()):     # a year or a number ("1023", "1661") is text on the picture, not a thing
        return False
    return bool(words) and not all(w.strip("।,.!?") in junk for w in words)


def nouns_of(ideas: dict) -> list:
    """The things, people and places the ideas name, once each, in order (never a word that is only grammar)."""
    out = []
    for row in ideas.get("beats") or []:
        for key in ("things", "people", "places"):
            for n in row.get(key) or []:
                n = str(n).strip()
                if n and _is_thing(n) and n.lower() not in {o.lower() for o in out}:
                    out.append(n)
    return out


def resolve_needs(ideas: dict, library=None, *, index=None, per_noun: int = 3) -> dict:
    """{found: {noun: [icon ids]}, images: {noun: [asset ids]}, needs: [{thing, beats, kind, sources_tried}]}: the icon index and
    the asset library are searched for every noun the ideas name; only an icon that is a picture OF the noun counts
    (``icons.fits``; Navin's addendum of 2 November 2026: a near word is not the thing), and a noun with none is a need (the
    general path: the fetch step, then BIE's coder)."""
    found, images, needs = {}, {}, []
    beats_of = {}
    for row in ideas.get("beats") or []:
        for key in ("things", "people", "places"):
            for n in row.get(key) or []:
                beats_of.setdefault(str(n).strip(), []).append(row["beat_id"])
    for noun in nouns_of(ideas):
        rows = [r for r in _search(noun, index) if icons.fits(noun, r)][:per_noun]
        if rows:
            found[noun] = [r["id"] for r in rows]
        hits = library.find([noun]) if library is not None else []
        if hits:
            images[noun] = [a.asset_id for a in hits]
        if not rows and not hits:
            needs.append({"thing": noun, "beats": beats_of.get(noun, []), "kind": "icon",
                          "sources_tried": ["icon-index"] + (["asset-library"] if library is not None else [])})
    for row in ideas.get("beats") or []:                       # the real objects the maker wants a picture of
        want = str(row.get("image_wanted") or "").strip()
        if not want or PORTRAIT.search(want):
            continue
        words = [w for w in want.lower().split() if len(w) > 2]
        hits = library.find(words) if library is not None else []
        hits = [a for a in hits if len(set(words) & {t.lower() for t in a.tags}) >= min(2, len(words))]
        if hits:
            images[want] = [a.asset_id for a in hits[:2]]
        elif want not in {n["thing"] for n in needs}:
            needs.append({"thing": want, "beats": [row["beat_id"]], "kind": "image", "sources_tried": ["asset-library"] if library is not None else []})
    return {"found": found, "images": images, "needs": needs}


def candidates_text(found: dict, by_id: dict | None = None) -> str:
    """The icon candidates per noun for the layout maker's card ('wheat: tw:1f33e ear of rice; fa:solid/wheat-alt wheat alt')."""
    by_id = by_id or icons.by_id()
    lines = []
    for noun, ids in found.items():
        lines.append(f"- {noun}: " + "; ".join(f"{i} ({by_id[i]['name']})" if i in by_id else i for i in ids))
    return "\n".join(lines)


# ---------------------------------------------------------------- the dikhane ki list

def dikhane_list(video_id: str, parts: list) -> dict:
    """The record of a video's visual thinking (``bie.brain.visual-ideas/1``): per part its picture (type, by whom, the book item),
    per beat the idea, relation, nouns, what is seen and on which word; the relations outside the list; the needs."""
    outside, needs, rows = [], [], []
    for part in parts:
        ideas = part.get("ideas") or {}
        for row in ideas.get("beats") or []:
            if row.get("relation") == "other":
                outside.append({"part": part["id"], "beat_id": row["beat_id"], "note": row.get("relation_note", ""), "idea": row.get("idea", "")})
        needs += [dict(n, part=part["id"]) for n in (part.get("needs") or [])]
        rows.append({"id": part["id"], "part_id": part.get("part_id", ""), "mode": part.get("mode", ""), "kit": part.get("kit", ""),
                     "picture": {k: v for k, v in (part.get("picture") or {}).items() if k != "pictures"},
                     "book_pictures": [{"item_id": p["item_id"], "type": p["type"], "title": p["title"], "page": p.get("page")}
                                       for p in (part.get("picture") or {}).get("pictures") or []],
                     "beats": [{"beat_id": r["beat_id"], "idea": r.get("idea", ""), "relation": r.get("relation", ""),
                                "relation_note": r.get("relation_note", ""), "nouns": [n for k in ("things", "people", "places") for n in r.get(k) or []],
                                "shows": r.get("shows", ""), "on_word": r.get("on_word", ""), "image_wanted": r.get("image_wanted", ""),
                                "icons": part.get("icons_by_beat", {}).get(r["beat_id"], []),
                                "template": r.get("template", "none"), "template_note": r.get("template_note", ""),
                                **({"realised": part["realised"][r["beat_id"]]} if r["beat_id"] in (part.get("realised") or {}) else {})}
                               for r in ideas.get("beats") or []],
                     "status": part.get("status", "")})
    return {"schema": SCHEMA, "video_id": video_id, "parts": rows, "relations_outside_list": outside, "needs": needs,
            "verbs_version": load_verbs()["version"]}


def needs_record(run_needs: list, missing: list) -> dict:
    """``needs.json`` (``bie.brain.needs/1``): the things no source had, with their beats and kinds, and the capabilities
    (world kits, blocks) the parts needed and BIE lacks."""
    return {"schema": NEEDS_SCHEMA, "needs": run_needs, "missing_capabilities": missing}


# ---------------------------------------------------------------- the code checks (Part D)

def _cue_beat(cue):
    return cue[0] if isinstance(cue, (list, tuple)) and cue else None


def beat_cover_problems(plan: dict, beats: list, mode: str) -> list:
    """D1 check 1: every beat shows at least one non-text thing cued on its words (an icon, crowd, mark, arrow, value step, table
    row, tree, picture event; in a world a prop, person, price, crowd step or packet) — or the beat is only text."""
    shown = set()
    if mode == "C":
        for e in plan.get("elements") or []:
            kind = e.get("kind")
            if kind in NON_TEXT_WORLD:
                shown.add(_cue_beat(e.get("cue")))
                for st in e.get("steps") or []:
                    shown.add(_cue_beat(st.get("cue")))
                for pk in e.get("packets") or []:
                    shown.add(_cue_beat(pk.get("cue")))
                for key in ("lift", "carry"):
                    if e.get(key):
                        shown.add(_cue_beat(e[key].get("cue")))
                shown.add(_cue_beat(e.get("tilt_cue")))
    else:
        for n in plan.get("nodes") or []:
            kind = n.get("kind")
            if kind in NON_TEXT_CANVAS:
                shown.add(_cue_beat(n.get("cue")))
                for st in n.get("steps") or []:
                    shown.add(_cue_beat(st.get("cue")))
                for r in n.get("rows") or []:
                    shown.add(_cue_beat(r.get("cue")))
                for h in n.get("highlights") or []:
                    shown.add(_cue_beat(h.get("cue")))
                for c in n.get("children") or []:
                    if isinstance(c, dict):
                        shown.add(_cue_beat(c.get("cue")))
                pic = n.get("picture") or {}
                for group in ("events", "panels", "rows", "nodes"):
                    for item in pic.get(group) or []:
                        shown.add(_cue_beat(item.get("cue")))
            if n.get("flow"):
                shown.add(_cue_beat((n["flow"] or {}).get("cue")) or _cue_beat(n.get("cue")))
        g = plan.get("graph") or {}
        for group in ("curves", "guides", "shades", "notes"):
            for item in g.get(group) or []:
                shown.add(_cue_beat(item.get("cue")))
        for d in g.get("dots") or []:
            for st in d.get("steps") or []:
                shown.add(_cue_beat(st.get("cue")))
    missing = [b["beat_id"] for b in beats if b["beat_id"] not in shown]
    if missing:
        return [f"beats {', '.join(missing)} show nothing but text: every beat shows at least one non-text thing (an icon, a mark, an arrow, "
                "a crowd or value step, a table row, a picture event; in a world a prop, a person, a price or a crowd step) cued on a word "
                "of that beat (D1-01)"]
    return []


def text_only_stretches(elements: list, duration: int, fps: int, *, text_kinds=TEXT_CANVAS, non_text_kinds=NON_TEXT_CANVAS) -> list:
    """[(start_frame, end_frame)] stretches where something is on screen but nothing non-text is: a text-only screen."""
    points = sorted({0, duration} | {e.get("at", 0) for e in elements} | {e["until"] for e in elements if "until" in e})
    out, cur = [], None
    for a, b in zip(points, points[1:]):
        visible = [e for e in elements if e.get("at", 0) <= a < e.get("until", 10 ** 9)]
        texty = any(e.get("kind") in text_kinds for e in visible)
        non_text = any(e.get("kind") in non_text_kinds or e.get("block") for e in visible)
        if texty and not non_text:
            cur = [a, b] if cur is None else [cur[0], b]
        else:
            if cur:
                out.append(tuple(cur))
            cur = None
    if cur:
        out.append(tuple(cur))
    return out


def text_only_problems(scene: dict, fps: int, *, limit_s: float = TEXT_ONLY_LIMIT_S) -> tuple:
    """(problems, text_only_seconds) for a compiled canvas scene: the canvas_build elements plus every block layer (a timeline,
    a flow) counted as a non-text thing while it is on screen."""
    elements = []
    for layer in scene.get("layers") or []:
        if layer.get("block") == "canvas_build":
            elements += [dict(e) for e in (layer.get("data") or {}).get("elements") or []]
        elif layer.get("type") == "block":
            elements.append({"kind": "block", "block": layer.get("block"), "at": layer.get("at", 0), **({"until": layer["until"]} if "until" in layer else {})})
    stretches = text_only_stretches(elements, scene.get("duration", 0), fps)
    seconds = sum((b - a) for a, b in stretches) / fps
    longest = max(((b - a) / fps for a, b in stretches), default=0.0)
    problems = []
    if longest > limit_s:
        problems.append(f"the screen shows only text for {longest:.1f} s (limit {limit_s:.0f} s): put the thing the beat names on screen "
                        "(an icon, a picture, a crowd) while it is said (D1-02)")
    return problems, round(seconds, 1)


def phrase_problems(texts: list) -> list:
    """D1 check 3: screen text is a name or a short natural phrase (at most PHRASE_WORDS words), never a sentence (the sentence is the
    narration's). Labels of one or two words pass."""
    problems = []
    for row in texts:
        text = (row.get("text") or "").strip()
        if not text or row.get("role") == "book":          # the book's own words, placed by code: never the maker's sentence
            continue
        for line in [ln.strip() for ln in text.split("\n") if ln.strip()]:
            words = line.split()
            if len(words) > PHRASE_WORDS or (SENTENCE_END.search(line) and len(words) > 3):
                problems.append(f"{row['id']}: '{line[:50]}' is a sentence ({len(words)} words); the screen shows a name or a short phrase of at most "
                                f"{PHRASE_WORDS} words, the sentence stays in the narration and the subtitles (D1-03)")
                break
    return problems


def caution_problems(texts: list) -> list:
    """D1 check 6: a caution, caveat or fact-check line never reaches the screen (Navin: 'background mein ek check hai, visuals par
    to yeh cheejen na dikhe')."""
    out = []
    for row in texts:
        if row.get("role") == "book":
            continue
        text = (row.get("text") or "")
        m = CAUTION.search(text)
        if m:
            out.append(f"{row['id']}: '{text[:50]}' is a caution or fact-check line ('{m.group(0)}'); these stay background checks, never on "
                       "screen: show the thing itself (D1-06)")
    return out


def book_picture_problems(plan: dict, picture: dict) -> list:
    """D1 check 4: every book diagram or table the part covers is drawn (a picture node with its item id)."""
    drawn = {(n.get("picture") or {}).get("item_id") for n in plan.get("nodes") or [] if n.get("kind") == "picture"}
    missing = [p for p in (picture or {}).get("pictures") or [] if p["item_id"] not in drawn]
    return [f"the book's {p['type']} '{p['title']}' ({p['item_id']}, page {p.get('page')}) is covered by this part but not drawn: keep the "
            f"picture node code placed (D1-04)" for p in missing]


def kit_sequence_problems(parts: list) -> list:
    """D1 check 5 (run level): the same world kit never in two consecutive parts."""
    out = []
    for a, b in zip(parts, parts[1:]):
        if a.get("mode") == "C" and b.get("mode") == "C" and a.get("kit") and a.get("kit") == b.get("kit"):
            out.append(f"parts {a['id']} and {b['id']} are both the {a['kit']} world: the second becomes a canvas (D1-05)")
    return out


def report(parts: list) -> dict:
    """Per video: distinct icons, text-only screen time and its share, picture types used, worlds used, relations outside the list."""
    icons_used = sorted({i for p in parts for i in (p.get("icon_ids") or [])})
    total = sum(p.get("seconds") or 0 for p in parts) or 0.0
    text_only = round(sum(p.get("text_only_seconds") or 0 for p in parts), 1)
    return {"distinct_icons": len(icons_used), "icons": icons_used, "text_only_seconds": text_only,
            "text_only_share": round(text_only / total, 3) if total else 0.0,
            "picture_types": sorted({t for p in parts for t in (p.get("picture_types") or [])}),
            "worlds": sorted({p["kit"] for p in parts if p.get("mode") == "C" and p.get("kit")}),
            "book_pictures": len({b["item_id"] for p in parts for b in (p.get("picture") or {}).get("pictures") or []}),   # distinct pictures,
            "book_pictures_drawn": len({i for p in parts for i in (p.get("book_picture_ids") or [])}),                     # each counted once
            "relations_outside_list": sum(1 for p in parts for r in ((p.get("ideas") or {}).get("beats") or []) if r.get("relation") == "other"),
            # Task 046 Part D2: processes shown, meaning realised, layout kept
            "actions": sorted(t for p in parts for t in (p.get("actions") or [])),
            "relations": sum(p.get("relations", 0) for p in parts),
            "relations_realised": sum(p.get("relations_realised", 0) for p in parts),
            "relations_realised_pct": (round(100 * sum(p.get("relations_realised", 0) for p in parts) / sum(p.get("relations", 0) for p in parts), 1)
                                       if sum(p.get("relations", 0) for p in parts) else None),
            "boards_in_world_parts": sum(p.get("boards", 0) for p in parts if p.get("mode") == "C"),
            "overlaps": sum(p.get("overlaps", 0) for p in parts),
            "subtitle_violations": sum(p.get("subtitle_violations", 0) for p in parts),
            "icon_misfits": [m for p in parts for m in (p.get("icon_misfits") or [])],
            # Navin's addendum of 2 November 2026: the things the dikhane ki list names, on screen in their beats
            "mentioned_things": sum((p.get("coverage") or {}).get("mentioned", 0) for p in parts),
            "shown_things": sum((p.get("coverage") or {}).get("shown", 0) for p in parts),
            "coverage_pct": (round(100.0 * sum((p.get("coverage") or {}).get("shown", 0) for p in parts)
                                   / sum((p.get("coverage") or {}).get("mentioned", 0) for p in parts), 1)
                             if sum((p.get("coverage") or {}).get("mentioned", 0) for p in parts) else None),
            "things_not_shown": [dict(t, part=p.get("id")) for p in parts for t in (p.get("coverage") or {}).get("not_shown", [])]}


# ---------------------------------------------------------------- meaning checks (Task 046 Part D2, E)
# Navin's D1 findings 4 and 5: a struck ₹500 with "₹200 ▼" was drawn for change given back (a different thing, not the same
# quantity going down), and "25 paise: no status" was said with no cross on the coin. The dikhane ki list names each beat's
# relation; these checks ask whether an element on that beat realises it.

LEXICON = load_verbs().get("lexicon") or {}
RETURN_WORDS = re.compile(LEXICON.get("return_words", r"(?!x)x"), re.IGNORECASE)
CHANGE_WORDS = re.compile(LEXICON.get("change_words", r"(?!x)x"), re.IGNORECASE)
OLD_DAYS = re.compile(LEXICON.get("old_days", r"(?!x)x"), re.IGNORECASE)
MODERN_ICONS = dict(LEXICON.get("modern_icons") or {})


def gives_back(text: str, value: str) -> bool:
    """The beat gives this value back (a return word right beside the value, or a change word in the beat while the value is an
    amount): then it is a give, not one quantity going down (seekh -> BIE, Part D2 run b: "लौटाया 10 kg ही" repaid grain while the
    board changed the cloth, '2 metres' → '1 metre', and was refused as change given back)."""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(value or ""))
    if not m:
        return False
    number = m.group(0).replace(",", "")
    words = re.findall(r"\S+", text or "")
    for i, w in enumerate(words):
        if number in [n.replace(",", "") for n in re.findall(r"\d[\d,]*(?:\.\d+)?", w)]:
            near = " ".join(words[max(0, i - 3):i + 4])
            if RETURN_WORDS.search(near):
                return True
    return bool(CHANGE_WORDS.search(text or "")) and bool(re.search(r"\d", str(value)))
# what realises a relation on its beat by kinds of elements and mark styles (a process realises relations by its parts:
# saanche.realises, rulebook/saanche.json); a relation not listed is covered by D1-01
REALISE = {
    "reject": {"marks": ("cross",), "kinds": ()},
    "accept": {"marks": ("tick",), "kinds": ()},
    "limit": {"marks": (), "kinds": ("value", "highlight", "board"), "icons": ("fa:solid/gauge-high", "fa:solid/gauge")},
    "count": {"marks": (), "kinds": ("crowd", "value", "picture", "table", "board", "price_tag")},
    "change": {"marks": (), "kinds": ("value", "board", "price_tag"), "steps": 2},
    "sequence": {"marks": (), "kinds": ("arrow", "picture", "pull_arrow", "crowd")},
    "cause_effect": {"marks": (), "kinds": ("arrow", "pull_arrow", "value", "price_tag", "balance", "crowd")},
    "compare": {"marks": (), "kinds": ("table", "picture", "balance"), "icons_min": 2},
}


def _beats_of(item: dict) -> set:
    """Every beat an element (canvas node or world element) does something in: its cue, steps, marks, rows, children, picture
    items, packets, carry, lift and the action's steps."""
    out = {_cue_beat(item.get("cue")), _cue_beat(item.get("tilt_cue"))}
    for key in ("steps", "marks", "rows", "highlights", "packets"):
        out |= {_cue_beat(x.get("cue")) for x in item.get(key) or [] if isinstance(x, dict)}
    out |= {_cue_beat(c.get("cue")) for c in item.get("children") or [] if isinstance(c, dict)}
    for key in ("lift", "carry", "flow"):
        if isinstance(item.get(key), dict):
            out.add(_cue_beat(item[key].get("cue")))
    pic = item.get("picture") or {}
    for group in ("events", "panels", "rows", "nodes", "items"):
        out |= {_cue_beat(x.get("cue")) for x in pic.get(group) or [] if isinstance(x, dict)}
    return out - {None}


def _pictures_of(item: dict) -> list:
    """The picture ids an element draws: its icon, a flow's, a crowd's carried goods, a shop's goods, a balance's pans, an action's
    objects, the panels and events of a picture."""
    ids = [item.get("icon"), (item.get("flow") or {}).get("icon"), (item.get("carry") or {}).get("icon"), item.get("carry_icon"),
           item.get("left_icon"), item.get("right_icon"), (item.get("left") or {}).get("icon"), (item.get("right") or {}).get("icon")]
    ids += [o.get("icon") for o in item.get("objects") or [] if isinstance(o, dict)]
    ids += [g.get("icon") for g in item.get("goods") or [] if isinstance(g, dict)]
    pic = item.get("picture") or {}
    for group in ("panels", "events", "items", "nodes"):
        ids += [x.get("icon") for x in pic.get(group) or [] if isinstance(x, dict)]
    return [i for i in ids if isinstance(i, str) and i]


def _present(item: dict, order: dict, mode: str = "B"):
    """(first, last) beat index an element is on screen in: from its first cued beat to the beat of its until_cue (or the end).
    An element with no cue is drawn from frame 0 (canvas.cue_frame); in a world, the kit's place and the person who works there
    stand for the whole part (world.WHOLE_PART_KINDS)."""
    if not order:
        return None
    last = max(order.values())
    if mode == "C" and item.get("kind") in world.WHOLE_PART_KINDS | set(world.PLACE_KINDS.values()):
        return 0, last
    idx = [order[b] for b in _beats_of(item) | ({_cue_beat(s.get("cue")) for s in item.get("parts") or [] if isinstance(s, dict)} - {None})
           if b in order]
    until = _cue_beat(item.get("until_cue"))
    return (min(idx) if idx else 0), order[until] if until in order else last


def _words(text: str) -> set:
    return {w.lower() for w in re.findall(r"[\w\u0900-\u097f]+", str(text or ""))}


def _draws(item: dict, mode: str, thing: str) -> bool:
    """A world element of a kind that draws the thing (places.json 'draws': a shop draws the shop, the crowd its people), or an
    action whose actor is the thing (an actor is drawn as a person, named by its role, who or label)."""
    words = _words(thing)
    if mode == "C" and words & world.DRAWS.get(item.get("kind"), frozenset()):
        return True
    if item.get("kind") == "action":
        named = set()
        for a in item.get("actors") or []:
            if isinstance(a, dict):
                named |= _words(" ".join(str(a.get(k, "")) for k in ("role", "who", "label")))
        return bool(words & named)
    return False


@lru_cache(maxsize=8192)
def _search(thing: str, index=None) -> tuple:
    """``icons.search`` for a thing, kept for the run (a part's check runs it for every thing in every round)."""
    return tuple(icons.search(thing, limit=12) if index is None else icons.search(thing, index, limit=12))


@lru_cache(maxsize=4)
def _known_icons(index=None) -> dict:
    return icons.by_id() if index is None else icons.by_id(index)


def thing_pictures(thing: str, found: dict | None = None, images: dict | None = None, index=None) -> tuple:
    """(shows, fit): the pictures that count as showing a thing (the icon candidates code offered the maker for it, the
    library's pictures of it, the icons whose names or search terms carry its words) and, of those, the ones that are pictures
    OF it (``icons.fits``, the library's pictures, best first). Only a thing with a fitting picture is asked for; one without
    is a need (the general asset path finds or makes it)."""
    lib = [f"asset:{a}" for a in (images or {}).get(thing, [])]
    by = {r["id"]: r for r in _search(thing, index)}
    known = _known_icons(index)
    offered = list((found or {}).get(thing, []))
    fit = lib + [i for i in dict.fromkeys(offered + list(by)) if icons.fits(thing, by.get(i) or known.get(i) or {"id": i})]
    return set(offered) | set(lib) | set(by), fit


MARK_THINGS = {k: dict(v, key=k, rx=re.compile(v["words"], re.IGNORECASE)) for k, v in (LEXICON.get("mark_things") or {}).items()
               if not k.startswith("_")}
TEXT_THINGS = re.compile(LEXICON.get("text_things", r"(?!x)x"), re.IGNORECASE)
TEXT_HEADS = frozenset(LEXICON.get("text_heads") or ())          # a thing named by these is text or a mark on screen


def is_text_thing(thing: str) -> bool:
    """A thing whose head noun is text or a mark ('₹ symbol', '₹100 amount', '2024 timeline marker'): shown by the words or
    the mark on screen, never asked for as a picture (seekh -> BIE, the addendum proof's run a)."""
    return icons._head(icons._words(thing)) in TEXT_HEADS
GENERIC_TEXT_WORDS = re.compile(r"\b(label|tag|marker|code|badge|stamp|symbol|sign|counter|denomination|example|timeline|dot)s?\b", re.IGNORECASE)


def _texts_of(item: dict) -> list:
    """The words an element puts on screen (its text, label, title, steps, an action's amounts, texts and part texts)."""
    out = [item.get(k) for k in ("text", "label", "title", "root", "sign", "left_label", "right_label")]
    out += [st.get("text") for st in item.get("steps") or [] if isinstance(st, dict)]
    out += [c.get("text") if isinstance(c, dict) else c for c in item.get("children") or []]
    out += [a.get("text") for a in item.get("amounts") or [] if isinstance(a, dict)]
    out += [t.get("text") for t in item.get("texts") or [] if isinstance(t, dict)]
    out += [p.get(k) for p in item.get("parts") or [] if isinstance(p, dict) for k in ("text", "left_text", "right_text", "title")]
    out += [o.get("label") for o in item.get("objects") or [] if isinstance(o, dict)]
    pic = item.get("picture") or {}
    for group in ("panels", "events", "items", "nodes"):
        out += [x.get(k) for x in pic.get(group) or [] if isinstance(x, dict) for k in ("name", "label", "caption")]
    return [str(t) for t in out if t]


def _shows_mark(item: dict, cls: dict) -> bool:
    kind = item.get("kind")
    if kind == "mark" and item.get("mark") in cls.get("marks", ()):
        return True
    if kind in cls.get("kinds", ()):
        return True
    if kind == "action" and set(saanche.parts_of(item)) & set(cls.get("parts", ())):
        return True
    return any(t.strip() in cls.get("texts", ()) for t in _texts_of(item))


def _shows_text(item: dict, thing: str) -> bool:
    """A text thing ('₹100 label', 'number 1', '2024 marker', '₹ symbol') is shown by an element whose words carry its numbers,
    its signs or its words."""
    digits = re.findall(r"\d[\d,]*", thing)
    signs = [c for c in thing if unicodedata.category(c) == "Sc" or c == "%"]     # a currency sign of any currency, a per cent
    words = [w for w in re.findall(r"[A-Za-z\u0900-\u097f]{3,}", GENERIC_TEXT_WORDS.sub(" ", thing))]
    texts = " ".join(_texts_of(item)).lower()
    if digits:
        return all(d.replace(",", "") in texts.replace(",", "") for d in digits)
    if signs:
        return all(c in texts for c in signs)
    return bool(words) and all(w.lower() in texts for w in words)


def coverage_rows(plan: dict, mode: str, ideas: dict | None, *, found: dict | None = None, images: dict | None = None, index=None) -> list:
    """Navin's addendum of 2 November 2026, point 4: every thing the dikhane ki list names for a beat must be on screen in that
    beat. One row per (beat, thing): shown (a picture of it on screen during the beat), by which elements, and whether BIE has a
    picture of it at all (a thing with none is a need: the general asset path finds or makes it)."""
    items = (plan.get("elements") if mode == "C" else plan.get("nodes")) or []
    order = {b["beat_id"]: i for i, b in enumerate(plan.get("beats") or [])}
    spans, present = [], []
    for x in items:
        span = _present(x, order, mode)
        if not span:
            continue
        present.append((x, span))
        pics = set(_pictures_of(x))
        if pics:
            spans.append((x.get("id"), pics, span))
    rows, cache = [], {}
    for idea in (ideas or {}).get("beats") or []:
        bid = idea.get("beat_id")
        if bid not in order:
            continue
        for thing in dict.fromkeys(str(t).strip() for t in idea.get("things") or []):
            if not thing or not _is_thing(thing):
                continue
            here = [x for x, (first, last) in present if first <= order[bid] <= last]
            mark = next((cls for cls in MARK_THINGS.values() if cls["rx"].search(thing)), None)
            if mark:                          # a mark of the visual grammar: a tick, a cross, an arrow, a question mark
                by = [x.get("id") for x in here if _shows_mark(x, mark)]
                rows.append({"beat_id": bid, "thing": thing, "shown": bool(by), "by": by, "has_picture": True, "pictures": ["a mark"],
                             "mark": mark["key"]})
                continue
            if thing not in cache:
                cache[thing] = thing_pictures(thing, found, images, index)
            ids, fit = cache[thing]
            text_thing = is_text_thing(thing)
            if text_thing:
                fit = []                              # text or a mark: never asked for as a picture
            by = [eid for eid, pics, (first, last) in spans if first <= order[bid] <= last and pics & ids]
            by += [x.get("id") for x in here if x.get("id") not in by and _draws(x, mode, thing)]
            if not by and (text_thing or TEXT_THINGS.search(thing)):   # a number, a label, a tag: shown by the words on screen
                by = [x.get("id") for x in here if _shows_text(x, thing)]
            rows.append({"beat_id": bid, "thing": thing, "shown": bool(by), "by": by, "has_picture": bool(fit or by),
                         "pictures": fit[:3]})
    return rows


AUTO_THINGS_MAX = 4
AUTO_SIZES = ((2, 2), (2, 1), (1, 1))      # the area code gives a thing it shows: 2 x 2 cells, else 2 x 1, else one cell


def _free_cell(busy: list, cols: int, rows_n: int):
    """The first free area of the grid (left to right, top to bottom) of the largest of AUTO_SIZES that fits, or None."""
    for w, h in AUTO_SIZES:
        for r in range(0, rows_n - h + 1):
            for c in range(0, cols - w + 1):
                if not any(c < b[0] + b[2] and b[0] < c + w and r < b[1] + b[3] and b[1] < r + h for b in busy):
                    return [c, r, w, h]
    return None


def _under_the_strip(plan: dict, ids: set):
    """The ids among ``ids`` that the compiled plan shows under the subtitle strip (``canvas.subtitle_problems``), or None
    when the plan does not compile."""
    from . import canvas
    try:
        scene, _ = canvas.compile_plan(json.loads(json.dumps(plan)))
    except (canvas.PlanError, KeyError, TypeError, ValueError, IndexError):
        return None
    return {i for i in ids if any(p.startswith(f"{i} sits under") for p in canvas.subtitle_problems(scene))}


def _boxes_meet(a, b) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def lift_from_strip(plan: dict) -> list:
    """Code moves a canvas node out from under the subtitle strip (seekh -> BIE, the addendum proof's run a of 2 November
    2026: 3 parts refused after three rounds only because a node in the bottom rows went under the captions as the camera
    moved): a node the compiled plan shows under the strip goes up one, two or three rows where those cells are free while it
    is on screen, else it gives up its bottom row. Never when the plan does not compile; never into another node. In place;
    returns what was done."""
    nodes = [n for n in plan.get("nodes") or [] if n.get("cell")]
    under = _under_the_strip(plan, {n.get("id") for n in nodes})
    if not under:
        return []
    order = {b["beat_id"]: i for i, b in enumerate(plan.get("beats") or [])}
    fixes = []
    for node in nodes:
        if node.get("id") not in under:
            continue
        span = _present(node, order) or (0, max(order.values(), default=0))
        busy = [m["cell"] for m in nodes if m is not node and (lambda o: o and o[0] <= span[1] and span[0] <= o[1])(_present(m, order))]
        c, r, w, h = node["cell"][:4]
        tries = [[c, r - d, w, h] for d in (1, 2, 3) if r - d >= 0] + ([[c, r, w, h - 1]] if h > 1 else [])
        old = list(node["cell"])
        for cell in tries:
            if any(_boxes_meet(cell, b) for b in busy):
                continue
            node["cell"] = cell
            still = _under_the_strip(plan, {node["id"]})
            if still == set():
                fixes.append(f"{node['id']} moved from cells {old} to {cell}, out from under the subtitle strip")
                break
            node["cell"] = old
            if still is None:
                break
    return fixes


def show_missing_things(plan: dict, mode: str, ideas: dict | None, *, found: dict | None = None, images: dict | None = None) -> list:
    """Code shows on the canvas what it can of a beat's things the maker left out (seekh -> BIE, Navin's addendum of 2 November
    2026: on run c, a third of the things the dikhane ki list named were not on screen): the thing's best picture (or, for a mark
    with an ``auto_icon`` in the lexicon, the first icon that fits those words) in a free area of the grid during its beat (AUTO_SIZES), on its word when the
    beat says it, leaving when the next beat starts; never under the subtitle strip (a place the compiled plan shows there is
    given up for the next free one), never when the plan does not compile. At most AUTO_THINGS_MAX per part; a world is left
    to the maker. In place; returns what was done."""
    if mode != "B":
        return []
    nodes = plan.setdefault("nodes", [])
    beats = plan.get("beats") or []
    order = {b["beat_id"]: i for i, b in enumerate(beats)}
    says = {b["beat_id"]: b.get("say", "") for b in beats}
    cols, rows_n = (plan.get("grid") or [12, 8])[:2]
    taken = {n.get("id") for n in nodes}
    fixes, added = [], 0
    for row in coverage_rows(plan, "B", ideas, found=found, images=images):
        if row["shown"] or not row["has_picture"] or added >= AUTO_THINGS_MAX:
            continue
        thing, bid = row["thing"], row["beat_id"]
        mark = MARK_THINGS.get(row.get("mark")) if row.get("mark") else None
        if mark is not None and not mark.get("auto_icon"):
            continue                                      # a tick, a cross, an arrow says something about another thing: the maker's
        if mark is not None:
            pid = next((r["id"] for r in icons.fitting(mark["auto_icon"], limit=4)), None)
        else:
            pid = next(iter(row["pictures"]), None)
        if not pid:
            continue
        busy = [n["cell"] for n in nodes if n.get("cell") and (_present(n, order) or (0, -1))[0] <= order[bid] <= (_present(n, order) or (0, -1))[1]]
        tokens = [w.strip("।,.!?:;()\"'") for w in says.get(bid, "").split()]
        word = next((w for w in tokens if w and w.lower() in thing.lower().split()), "")
        nxt = next((b["beat_id"] for b in beats if order[b["beat_id"]] == order[bid] + 1), None)
        k = 1
        while f"auto_thing_{k}" in taken:
            k += 1
        nid = f"auto_thing_{k}"
        for _ in range(3):                                # a place under the subtitle strip is given up for the next free one
            spot = _free_cell(busy, cols, rows_n)
            if not spot:
                break
            node = {"id": nid, "kind": "icon", "icon": pid, "cell": spot, "cue": [bid, word], **({"until_cue": [nxt, ""]} if nxt else {})}
            nodes.append(node)
            under = _under_the_strip(plan, {nid})
            if under is None:                             # the plan does not compile with it: leave the plan as the maker made it
                nodes.pop()
                spot = None
                break
            if not under:
                break
            nodes.pop()
            busy.append(spot)
            spot = None
        if not spot:
            continue
        taken.add(nid)
        added += 1
        fixes.append(f"'{thing}' shown in beat {bid} by code ({pid} in cells {spot})")
    return fixes


def coverage_problems(rows: list) -> list:
    """A thing of a beat that BIE has a picture of but the plan does not show during that beat."""
    return [f"beat {r['beat_id']}: '{r['thing']}' is a thing of this beat in the dikhane ki list, but it is not on screen during the "
            f"beat: show it ({', '.join(r['pictures'])}), on screen during that beat (Navin: \"jis cheej ka jikar hai wohi cheej dikhe\")"
            for r in rows if r["has_picture"] and not r["shown"]]


def coverage_summary(rows: list) -> dict:
    """mentioned, shown, coverage % and the things not shown (with whether BIE has a picture of them)."""
    mentioned, shown = len(rows), sum(1 for r in rows if r["shown"])
    return {"mentioned": mentioned, "shown": shown, "coverage_pct": round(100.0 * shown / mentioned, 1) if mentioned else 100.0,
            "not_shown": [{"beat_id": r["beat_id"], "thing": r["thing"], "has_picture": r["has_picture"]} for r in rows if not r["shown"]]}


def relation_rows(plan: dict, mode: str, ideas: dict | None) -> list:
    """Per beat of the dikhane ki list: its relation and whether an element on that beat realises it (and which)."""
    items = plan.get("elements") if mode == "C" else plan.get("nodes")
    items = items or []
    order = {b["beat_id"]: i for i, b in enumerate(plan.get("beats") or [])}
    rows = []
    for idea in (ideas or {}).get("beats") or []:
        rel, bid = idea.get("relation"), idea.get("beat_id")
        rule = REALISE.get(rel)
        if not rule:
            continue
        here = [x for x in items if bid in _beats_of(x)]
        by = []
        for x in here:
            kind = x.get("kind")
            if kind == "mark" and x.get("mark") in rule["marks"]:
                by.append(x.get("id"))
            elif kind == "action" and rel in saanche.realises(x):
                by.append(x.get("id"))
            elif kind in rule["kinds"] and (not rule.get("steps") or len(x.get("steps") or []) >= rule["steps"]):
                by.append(x.get("id"))
            elif kind == "icon" and x.get("icon") in rule.get("icons", ()):
                by.append(x.get("id"))
        chosen = idea.get("template")
        if not by and chosen not in (None, "", "none", "other"):    # the saancha the dikhane ki list itself chose for this beat
            by = [x.get("id") for x in here if x.get("kind") == "action" and x.get("template") == chosen]
        if not by and rel == "compare":                      # a refusal beside an acceptance on the beat: the two compared
            def side(x):
                names = saanche.parts_of(x) if x.get("kind") == "action" else []
                return ("refuse" if "refuse" in names or x.get("mark") == "cross" else
                        "accept" if "accept" in names or x.get("mark") == "tick" else "")
            if {"refuse", "accept"} <= {side(x) for x in here}:
                by = [x.get("id") for x in here if side(x)]
        if not by and rule.get("icons_min") and sum(1 for x in here if x.get("kind") in ("icon", "crowd")) >= rule["icons_min"]:
            by = [x.get("id") for x in here if x.get("kind") in ("icon", "crowd")]
        if not by and rel in ("sequence", "compare"):          # a highlight on the book's timeline, flow, gallery or table
            pics = {x.get("id"): (x.get("picture") or {}).get("type") for x in items if x.get("kind") == "picture"}
            want = ("timeline", "flow", "gallery") if rel == "sequence" else ("table", "gallery")
            by = [x.get("id") for x in here if x.get("kind") in ("highlight", "mark")
                  and any(str(x.get("target", "")).startswith(pid) and ptype in want for pid, ptype in pics.items() if pid)]
        if not by and rel in ("sequence", "cause_effect"):     # a process already playing across the beat shows its steps
            by = [x.get("id") for x in items if x.get("kind") == "action" and rel in saanche.realises(x) and _spans(x, bid, order)]
        rows.append({"beat_id": bid, "relation": rel, "realised": bool(by), "by": by})
    return rows


def _spans(item: dict, bid: str, order: dict) -> bool:
    """An element whose cued beats start before (or at) ``bid`` and end after (or at) it."""
    idx = [order[b] for b in _beats_of(item) if b in order]
    return bool(idx) and bid in order and min(idx) <= order[bid] <= max(idx)


def realise_relations(plan: dict, mode: str, ideas: dict | None) -> list:
    """Code draws what it can of a relation the maker left unshown (seekh -> BIE: 19 of the first Part D2 run's refusals): on the
    canvas, a sequence or cause-effect beat with nothing that shows it gets an arrow from the thing on screen before the beat to
    the thing the beat brings, on that thing's word. In place; returns what was done, for the report."""
    if mode != "B":
        return []
    nodes = plan.setdefault("nodes", [])
    order = {b["beat_id"]: i for i, b in enumerate(plan.get("beats") or [])}
    ids = {n.get("id") for n in nodes}
    shown = ("icon", "crowd", "value", "picture", "table", "tree", "action", "text", "callout")
    fixes = []
    for r in relation_rows(plan, mode, ideas):
        if r["realised"] or r["relation"] not in ("sequence", "cause_effect") or r["beat_id"] not in order:
            continue
        bid = r["beat_id"]
        here = [n for n in nodes if n.get("cell") and n.get("kind") in shown and _cue_beat(n.get("cue")) == bid]
        def still_on(n):
            until = _cue_beat(n.get("until_cue"))
            return until is None or order.get(until, 10 ** 6) > order[bid]
        before = [n for n in nodes if n.get("cell") and n.get("kind") in shown and _cue_beat(n.get("cue")) in order
                  and order[_cue_beat(n.get("cue"))] < order[bid] and still_on(n)]
        if not here or not before:
            continue
        here.sort(key=lambda n: n.get("kind") in ("text", "callout"))            # a picture of the thing first, words last
        src = max(before, key=lambda n: (order[_cue_beat(n.get("cue"))], n.get("cue_fraction") or 0))
        dst = here[0]
        aid = f"auto_arrow_{bid}"
        if aid in ids:
            continue
        nodes.append({"id": aid, "kind": "arrow", "from": src["id"], "to": dst["id"], "cue": list(dst["cue"])})
        ids.add(aid)
        fixes.append(f"arrow {src['id']} → {dst['id']} drawn on beat {bid} ({r['relation']})")
    return fixes


SHOWS = {"reject": "a cross on the thing refused (a mark 'cross' on its icon, or a process with a refuse part)",
         "accept": "a tick on the thing accepted (a mark 'tick', or a process with an accept part)",
         "limit": "a meter or stack that stops at its red line (a process with a meter part and its limit, or a value or highlight in danger tone)",
         "count": "a counted crowd, stack or value whose number is the narration's number (crowd, value, or things appearing one by one)",
         "change": "the old value struck out and the new one in its place (a value or board with two steps), or a process that changes it",
         "sequence": "the steps in order (arrows, a flow or timeline picture, or a process of two or more parts)",
         "cause_effect": "the cause, an arrow, the effect (an arrow, a changing value, or a process)",
         "compare": "the two things side by side (a table, a balance, two icons, or a process with a compare part)"}


def _unit(text: str) -> str:
    """The unit of an amount, singular and plural alike (seekh -> BIE, Part D2 run b: '2 metres' → '1 metre' of cloth is one
    quantity; the plural made it look like two): the words without digits, an English plural s and a Hindi plural ending dropped."""
    words = []
    for w in re.split(r"[\s,]+", str(text or "").lower()):
        w = re.sub(r"[\d.]+", "", w)
        if not w:
            continue
        if re.fullmatch(r"[a-z]{2,}s", w):
            w = w[:-1]
        w = re.sub(r"(?<=[\u0900-\u097f])(ों|े|ा)$", "", w)
        words.append(w)
    return "".join(words)


def struck_problems(plan: dict, mode: str) -> list:
    """D2-E: a struck old value with an up or down arrow shows ONE quantity changing. A value given back is not that quantity
    going down (the D1 v4 render struck the paid amount and showed the change with a down arrow): it travels back in a process
    (a give with its tag). Two numbers of different units are two quantities, not one value changing."""
    says = {b["beat_id"]: b.get("say", "") for b in plan.get("beats") or []}
    items = (plan.get("elements") if mode == "C" else plan.get("nodes")) or []
    change_beats = {b for x in items if x.get("kind") == "action" and "give" in saanche.parts_of(x) for b in _beats_of(x)}
    out = []
    for x in items:
        if x.get("kind") not in ("value", "board", "price_tag"):
            continue
        steps = x.get("steps") or []
        for prev, cur in zip(steps, steps[1:]):
            bid = _cue_beat(cur.get("cue"))
            if gives_back(says.get(bid, ""), cur.get("text", "")) and bid not in change_beats:
                out.append(f"{x.get('id')}: beat {bid} gives '{cur.get('text', '')}' back; that travels back in a process (a give with "
                           f"its tag), not '{prev.get('text', '')}' struck out for '{cur.get('text', '')}'")
                break
            a, b = str(prev.get("text", "")), str(cur.get("text", ""))
            if re.search(r"\d", a) and re.search(r"\d", b) and _unit(a) and _unit(b) and _unit(a) != _unit(b):
                out.append(f"{x.get('id')}: '{a}' struck out for '{b}' are two different quantities; a struck value with an arrow is one "
                           "quantity changing: use two elements, or an action")
                break
    return out


def meaning_problems(plan: dict, mode: str, ideas: dict | None) -> list:
    """The meaning checks of a plan (D2-E): every relation of the dikhane ki list realised on its beat, and the struck-value rule."""
    out = [f"beat {r['beat_id']} is '{r['relation']}' in the dikhane ki list, but nothing on that beat shows it: add {SHOWS[r['relation']]}, "
           "cued on a word of that beat" for r in relation_rows(plan, mode, ideas) if not r["realised"]]
    return out + struck_problems(plan, mode)


def icon_misfits(plan: dict, mode: str) -> list:
    """D2-E (report only): an icon that does not fit the beat's era (the rulebook's modern icons in a beat about the old days)."""
    says = {b["beat_id"]: b.get("say", "") for b in plan.get("beats") or []}
    items = (plan.get("elements") if mode == "C" else plan.get("nodes")) or []
    out = []
    for x in items:
        refs = [x.get("icon"), (x.get("flow") or {}).get("icon"), (x.get("carry") or {}).get("icon")]
        refs += [o.get("icon") for o in x.get("objects") or []] + [g.get("icon") for g in x.get("goods") or []]
        for ref in refs:
            if ref in MODERN_ICONS:
                old = [b for b in _beats_of(x) if OLD_DAYS.search(says.get(b, ""))]
                if old:
                    out.append({"element": x.get("id"), "icon": ref, "name": MODERN_ICONS[ref], "beats": sorted(old),
                                "why": "a modern thing in a beat about the old days"})
    return out
