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
from functools import lru_cache
from pathlib import Path

from . import formats
from .common import S, arr, obj
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
NON_TEXT_CANVAS = ("icon", "crowd", "picture", "mark", "arrow", "value", "table", "tree", "highlight")
NON_TEXT_WORLD = ("shop", "bank", "price_tag", "crowd", "coin_rain", "balance", "pull_arrow", "teller", "shopkeeper")
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
PORTRAIT = re.compile(r"portrait|photo of (?:a |the )?(?!coin|note|seal)|face of|painting of|statue of|likeness|पोर्ट्रेट|तस्वीर", re.IGNORECASE)


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
    return "\n".join(f"- {r['id']}: {r['show']}" for r in (verbs or load_verbs())["relations"])


# ---------------------------------------------------------------- the maker's strict answer

IDEA = obj({"beat_id": S, "idea": S, "relation": S, "relation_note": S, "things": arr(S), "people": arr(S), "places": arr(S),
            "shows": S, "on_word": S, "image_wanted": S})
IDEAS_SCHEMA = obj({"notes": NOTES_SCHEMA, "beats": arr(IDEA), "picture_type": S, "picture_note": S})

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
- things, people, places: the concrete nouns the beat names or implies, as plain English or Hindi words a picture can show (wheat,
  cloth, salt, coin, ₹500 note, phone, law scroll, Sweden, 1661, farmer, shopkeeper). A real person is never drawn (card rule 8): name
  the role (a king, a ruler) or the object (a coin with a seal), not the person.
- shows: what is seen, in at most {phrase_words} words, as a picture description (a cross on the old coin; a meter filling to ₹1,000
  with a red line; wheat and cloth swapping hands). Never a sentence for the screen: the sentence is the narration.
- on_word: the word of this beat (exactly as written) on which the picture should appear ("" = the beat's start).
- image_wanted: a real object an icon cannot show and a photograph or museum image can (a punch-marked silver coin, a cowrie
  shell, a cheque leaf), as search words; "" when an icon is enough. Never a person's portrait (card rule 8).
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
        nouns = [n for key in ("things", "people", "places") for n in (row.get(key) or []) if str(n).strip()]
        if not nouns:
            problems.append(f"beat {bid}: name at least one thing, person or place the learner sees (a picture needs a thing)")
        shows = (row.get("shows") or "").strip()
        if not shows:
            problems.append(f"beat {bid}: shows is empty: say what is seen")
        elif len(shows.split()) > PHRASE_WORDS * 2:
            problems.append(f"beat {bid}: shows is {len(shows.split())} words; describe the picture in at most {PHRASE_WORDS * 2}")
        word = (row.get("on_word") or "").strip()
        if word and word not in beats[bid]:
            problems.append(f"beat {bid}: on_word {word!r} is not written in that beat")
    missing = [b for b in beats if b not in seen]
    if missing:
        problems.append("every beat needs its idea; missing: " + ", ".join(missing))
    dup = sorted({b for b in seen if seen.count(b) > 1})
    if dup:
        problems.append("a beat appears twice: " + ", ".join(dup))
    ptype = (value.get("picture_type") or "").strip()
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
    for query in [panel.get("caption", "")] + list(panel.get("nouns") or []) + [panel.get("name", "")]:
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

def nouns_of(ideas: dict) -> list:
    """The things, people and places the ideas name, once each, in order."""
    out = []
    for row in ideas.get("beats") or []:
        for key in ("things", "people", "places"):
            for n in row.get(key) or []:
                n = str(n).strip()
                if n and n.lower() not in {o.lower() for o in out}:
                    out.append(n)
    return out


def resolve_needs(ideas: dict, library=None, *, index=None, per_noun: int = 3) -> dict:
    """{found: {noun: [icon ids]}, images: {noun: [asset ids]}, needs: [{thing, beats, kind, sources_tried}]}: the icon index and
    the asset library are searched for every noun the ideas name; a noun found nowhere is a need."""
    found, images, needs = {}, {}, []
    beats_of = {}
    for row in ideas.get("beats") or []:
        for key in ("things", "people", "places"):
            for n in row.get(key) or []:
                beats_of.setdefault(str(n).strip(), []).append(row["beat_id"])
    for noun in nouns_of(ideas):
        rows = icons.search(noun, limit=per_noun) if index is None else icons.search(noun, index, limit=per_noun)
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
                                "icons": part.get("icons_by_beat", {}).get(r["beat_id"], [])}
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
            "book_pictures": sum(len((p.get("picture") or {}).get("pictures") or []) for p in parts),
            "book_pictures_drawn": sum(p.get("book_pictures_drawn") or 0 for p in parts),
            "relations_outside_list": sum(1 for p in parts for r in ((p.get("ideas") or {}).get("beats") or []) if r.get("relation") == "other")}
