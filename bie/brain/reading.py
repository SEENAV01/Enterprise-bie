"""Reading the printed page by code, before any AI reads it (Navin, 21 November 2026: "book ko dekh bhi sake book
understanding ke liye ... jisse book achhe se samjh aati hai"; his card the same evening: "Mukabla nahi, BIE banao").

The text layer (``bie.document_intelligence.real_pdf_text_runtime``) gives one block per printed line, in top-then-left
order, and stays the pipeline's source anchor (its block ids). The Chapter 11 audit (NCERT Class 11 Biology,
Photosynthesis, 21 November 2026) found what that order loses on a real book, and this module puts it right from the
glyphs themselves (pdfplumber: every character with its place and size), with no AI:

1. Subscripts and superscripts. The small "2" of CO2 is printed a little lower than its line, so the text layer makes it
   a line of its own ("2 2 2 2" under an equation) and leaves "CO )" behind: 19 lines of the chapter lost their CO2 or
   H2O, 19 the 3 and 4 of C3 and C4. Each small digit or sign goes back after the glyph it follows, written as a
   subscript or superscript (CO₂, C₄, H⁺, NADP⁺); a line that was only such marks is absorbed into its line.
2. Two columns on one line. Where printed lines hold two columns (the unit page's chapter list beside its paragraph,
   the In and Out of a table), they are cut at the white gutter that at least ``GUTTER_LINES`` lines share. A table
   keeps its rows (cells joined by " | "); two text columns are read one after the other, and a side column of short
   entries (a list beside a paragraph) is an ``aside`` read after the paragraph.
3. Figure words in the text. A word of a drawn figure (the Z scheme's "Photosystem II", "LHC", "NADPH") that shares a
   line with the running text is cut off and kept as a ``label``: the figure's words, never part of a sentence. Figures
   are found from the page's own drawing (curves, rects, rules and picture pieces), leaving out the running-head band,
   page frames and the pictures many pages repeat (watermark, background).

Every piece has a kind: ``text`` (running text), ``heading`` (a numbered section heading such as "11.6.1 Splitting of
Water", or a title in large type), ``equation`` (a line with an arrow), ``caption``, ``table``, ``aside``, ``label`` or
``running`` (the running head and the edition line at the foot). What the reader did to a page is in
``PageReading.notes``. A page whose lines do not match the text layer's blocks one to one is left as the layer gave it.
"""
from __future__ import annotations

import io
import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass

MARKS = set("0123456789+-−–")
MARK_LETTERS = set("nxi")      # (CH₂O)ₙ, Pᵢ: a small letter, only on a line of marks
SUB = str.maketrans("0123456789+-−–nxi", "₀₁₂₃₄₅₆₇₈₉₊₋₋₋ₙₓᵢ")
SUP = str.maketrans("0123456789+-−–nxi", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁻ⁿˣⁱ")
SMALL = 0.86            # a mark is at most this share of its line's type size (7.6 under 9.1; 6.1 under 10.5)
MARK_SPACE = 1.0        # points of white after a mark that are a word space (the glyphs around a mark nearly touch)
GAP = 12.0              # points of white inside a line that may be a gutter (a justified word space stays under ~7)
GUTTER_LINES = 3        # lines that must share a gutter before a line is cut there
ASIDE_WIDTH = 0.33      # share of the page width: a side column narrower than this can be an aside (two text columns are wider)
TABLE_CELL = 30         # characters: a row whose every cell is this short is a table row
LABEL_CHARS = 45        # a cut-off piece inside a figure longer than this, in the text's type size, is still text
LINE_LABEL_CHARS = 25   # the same for a whole line ("⊳ Example 3.1 Rain is falling vertically with" is text)
FIGURE_PAD = 12.0       # points around a figure's drawing where its labels sit
FIGURE_JOIN = 20.0      # drawing parts closer than this are one figure
FORMULA_BOX = 36.0      # points: a drawn box lower than this is the band behind an equation (Chapter 11, pages 5 and 9)
CAPITALS = 1.3          # a title's big capitals are at least this much larger than its small capitals
CAPITAL_SPACE = 2.5     # points of white between a big capital and a small one that are a word space
CAPTION_GAP = 8.0       # points between a caption's lines
ARROW_WORD = 12         # characters: a word printed over an equation's arrow ("Light") belongs to that arrow
PRIVATE = re.compile(r"[\ue000-\uf8ff]")   # a font's private glyphs (the extender of a long arrow): no text
HEAD_SHARE, FOOT_SHARE = 0.14, 0.92     # the running head sits above 14% of the page, the edition line below 92%
CAPTION = re.compile(r"^(?:Figure|Fig\.|Table)\s+[0-9]")
ARROW = re.compile(r"[→⟶⇌]")
LIST_MARK = re.compile(r"^\s*(?:[•●▪◦■□➢➤✓\-–*]|\(?(?:[0-9]{1,2}|[ivx]{1,4}|[a-h])[.)])\s*$")
KINDS = ("text", "heading", "equation", "caption", "table", "aside", "label", "running")
SECTION = re.compile(r"^\d{1,2}(?:\.\d{1,2}){1,3}\.?\s+\S")      # "11.6.1 Splitting of Water", "11.2 EARLY EXPERIMENTS"
TITLE = 1.25            # a line this much larger than the text is a title ("CHAPTER 11", "PLANT PHYSIOLOGY")
HEADING_CHARS = 90
# The parts of a chapter after its sections (NCERT prints them in capitals): their lines are summary or exercises, not teaching.
ZONES = {"SUMMARY": "summary", "EXERCISES": "exercise", "EXERCISE": "exercise", "QUESTIONS": "exercise",
         "POINTS TO PONDER": "points_to_ponder"}
SECTION_NUMBER = re.compile(r"^\d{1,2}(?:\.\d{1,2}){1,3}\.?$")


def _upper_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0


@dataclass
class Glyph:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    size: float
    space_after: bool = False
    mark: bool = False          # a subscript or superscript put back by the reader
    source: str = ""            # the line a glyph came from, when two lines were joined (small capitals)

    @property
    def middle(self):
        return (self.top + self.bottom) / 2


@dataclass
class Line:
    id: str
    text: str
    glyphs: list
    x0: float
    top: float
    x1: float
    bottom: float
    changed: bool = False

    @property
    def size(self):
        return statistics.median(g.size for g in self.glyphs) if self.glyphs else 0.0

    @property
    def middle(self):
        return (self.top + self.bottom) / 2


@dataclass(frozen=True)
class Piece:
    id: str
    text: str
    box: tuple              # (x0, top, x1, bottom) as fractions of the page, like the text layer's boxes
    kind: str = "text"


@dataclass
class PageReading:
    number: int
    pieces: list
    absorbed: dict          # {block id of a marks-only line: block id of the line it went back into}
    notes: list
    repaired: bool = True


def _glyphs(chars, text: str) -> list:
    """The line's glyphs (pdfplumber leaves spaces out of a line's chars), each knowing whether the line's text has a
    space after it."""
    out = [Glyph(c["text"], float(c["x0"]), float(c["x1"]), float(c["top"]), float(c["bottom"]), float(c["size"]))
           for c in chars if str(c["text"]).strip()]
    at = 0
    for glyph in out:
        found = text.find(glyph.text, at)
        if found < 0:
            break
        at = found + len(glyph.text)
        glyph.space_after = text[at:at + 1] == " "
    return out


def text_of(glyphs) -> str:
    """The glyphs as text: in order along the line; a space where the printed line had one, none before a put-back mark
    and one after it where white follows (CO₂ and, CO₂), C₆H₁₂O₆)."""
    ordered = sorted(glyphs, key=lambda g: g.x0)
    out = []
    for a, b in zip(ordered, ordered[1:] + [None]):
        out.append(PRIVATE.sub("", a.text))
        if b is None:
            break
        if b.mark:
            continue
        if a.mark:
            if b.x0 - a.x1 > MARK_SPACE:
                out.append(" ")
        elif a.source != b.source:
            if b.x0 - a.x1 > CAPITAL_SPACE:
                out.append(" ")
        elif a.space_after:
            out.append(" ")
    return "".join(out).strip()


def page_lines(page, number: int) -> list:
    """The page's lines exactly as the text layer builds them (same pdfplumber calls, same order, same ids)."""
    raw = page.within_bbox(page.bbox).dedupe_chars().extract_text_lines(strip=True, return_chars=True)
    rows = []
    for index, line in enumerate(raw):
        text = str(line.get("text", "")).strip()
        if text:
            rows.append((float(line["top"]), float(line["x0"]), float(line["bottom"]), float(line["x1"]), text, index,
                         line.get("chars") or []))
    rows.sort(key=lambda r: r[:6])
    return [Line(f"p{number:04d}-b{n:04d}", text, _glyphs(chars, text), x0, top, x1, bottom)
            for n, (top, x0, bottom, x1, text, _, chars) in enumerate(rows, 1)]


# --- 1. subscripts and superscripts

def _marks_only(line: Line, body: float) -> bool:
    return (bool(line.glyphs) and all(g.text in MARKS or g.text in MARK_LETTERS for g in line.glyphs)
            and any(g.text in MARKS for g in line.glyphs) and line.size <= SMALL * body + 0.05)


def _touches(mark: Glyph, glyph: Glyph) -> bool:
    """The mark begins where the glyph ends, and the two overlap in height (the 2 of CO₂ hangs from its O)."""
    return -1.5 <= mark.x0 - glyph.x1 <= 3 and glyph.bottom >= mark.top - 1 and glyph.top <= mark.bottom + 1


def _host(mark: Glyph, lines: list):
    """The line a mark belongs to: among the lines it sits beside, one with a glyph ending just where the mark begins
    (the O of CO₂), else the nearest."""
    best, distance, touching = None, None, False
    for line in lines:
        height = line.bottom - line.top
        if not (line.x0 - 3 <= mark.x0 <= line.x1 + 3) or not (line.top - 0.5 * height <= mark.middle <= line.bottom + 0.5 * height):
            continue
        if mark.size > SMALL * line.size + 0.05:
            continue
        d = abs(mark.middle - line.middle)
        touches = any(_touches(mark, g) and not g.mark for g in line.glyphs)
        if (touches and not touching) or (touches == touching and (distance is None or d < distance)):
            best, distance, touching = line, d, touches
    return best


def _as_mark(glyph: Glyph, lower: bool) -> Glyph:
    return Glyph(glyph.text.translate(SUB if lower else SUP), glyph.x0, glyph.x1, glyph.top, glyph.bottom, glyph.size,
                 mark=True)


def attach_marks(lines: list, body: float) -> dict:
    """Every small digit or sign back after the glyph it follows; returns {marks-only line id: host line id}."""
    hosts = [line for line in lines if not _marks_only(line, body)]
    host_ids = {line.id for line in hosts}
    for line in hosts:                                   # marks the text layer left inside their own line
        full = [g for g in line.glyphs if g.text not in MARKS]
        if not full:
            continue
        size = statistics.median(g.size for g in full)
        middle = statistics.median(g.middle for g in full)
        height = statistics.median(g.bottom - g.top for g in full)
        moved = []
        for i, g in enumerate(line.glyphs):
            if g.text in MARKS and g.size <= SMALL * size + 0.05 and abs(g.middle - middle) > 0.15 * height:
                touching = any(_touches(g, o) for o in line.glyphs if o is not g)
                other = None if touching else _host(g, [h for h in hosts if h is not line])
                if other is not None and any(_touches(g, o) for o in other.glyphs):
                    moved.append(i)          # the 2 of a CO on the line above, grouped with a side column's line
                    other.glyphs.append(_as_mark(g, g.middle > other.middle))
                    other.changed = True
                else:
                    line.glyphs[i] = _as_mark(g, g.middle > middle)
                line.changed = True
        for i in reversed(moved):
            del line.glyphs[i]
    absorbed = {}
    for line in lines:
        if line.id in host_ids:
            continue
        placed = [(g, _host(g, hosts)) for g in line.glyphs]
        if not any(host for _, host in placed):
            continue                                       # a page number or a year: not the marks of a line
        for g, host in placed:
            if host is not None:
                host.glyphs.append(_as_mark(g, g.middle > host.middle))
                host.changed = True
        line.glyphs = [g for g, host in placed if host is None]
        if not line.glyphs:
            absorbed[line.id] = next(host.id for _, host in placed if host is not None)
        else:
            line.text = text_of(line.glyphs)
    for line in lines:
        if line.changed and line.glyphs:
            line.text = text_of(line.glyphs)
    return absorbed


def join_capitals(lines: list) -> dict:
    """A title set in small capitals ("C 11" over "HAPTER", "P H P" over "HOTOSYNTHESIS IN IGHER LANTS") comes from
    the text layer as two lines, the big capitals and the small ones; they are one line ("CHAPTER 11",
    "PHOTOSYNTHESIS IN HIGHER PLANTS"). Returns {small-capitals line id: line id it joined}."""
    absorbed = {}
    for big in lines:
        if not big.glyphs or big.id in absorbed or not all(g.text.isupper() or g.text.isdigit() for g in big.glyphs):
            continue
        for small in lines:
            if small is big or not small.glyphs or small.id in absorbed or big.size < CAPITALS * small.size:
                continue
            if any(g.text.isalpha() and not g.text.isupper() for g in small.glyphs):
                continue
            if not (small.top >= big.top - 2 and small.bottom <= big.bottom + 2) or small.x1 < big.x0 - 3 or small.x0 > big.x1 + 3:
                continue
            for g in big.glyphs:
                g.source = g.source or big.id
            for g in small.glyphs:
                g.source = small.id
            big.glyphs += small.glyphs
            big.x0, big.x1 = min(big.x0, small.x0), max(big.x1, small.x1)
            big.changed = True
            small.glyphs = []
            absorbed[small.id] = big.id
        if big.changed:
            big.text = text_of(big.glyphs)
    return absorbed


# --- 3. figures (found first: a figure's words decide where a line is cut)

def _union(boxes) -> tuple:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def repeated_pictures(pdf) -> set:
    """Picture boxes that sit at the same place on at least three pages (a watermark, a page background)."""
    seen = Counter()
    for page in pdf.pages:
        for box in {tuple(round(float(i[k])) for k in ("x0", "top", "x1", "bottom")) for i in page.images}:
            seen[box] += 1
    return {box for box, count in seen.items() if count >= 3}


def figure_regions(page, repeated=frozenset()) -> list:
    """Boxes (x0, top, x1, bottom in points, ruled) of the page's figures: its curves, rects, rules and picture pieces,
    clustered, leaving out the running-head band, page frames and pictures many pages repeat. ``ruled`` is True for a
    box drawn only with straight rules and frames: a table."""
    width, height = float(page.width), float(page.height)
    objs, drawn = [], []
    for kind in ("curves", "rects", "lines", "images"):
        for o in getattr(page, kind):
            box = (float(o["x0"]), float(o["top"]), float(o["x1"]), float(o["bottom"]))
            if box[3] <= HEAD_SHARE * height or box[1] >= FOOT_SHARE * height:
                continue
            if kind == "images" and (tuple(round(v) for v in box) in repeated
                                     or (box[2] - box[0]) * (box[3] - box[1]) > 0.5 * width * height):
                continue
            if (box[2] - box[0]) > 0.8 * width or (box[3] - box[1]) > 0.8 * height:
                continue
            objs.append((box, kind in ("curves", "images")))
    clusters = []
    for box, curved in objs:
        near = [c for c in clusters if box[0] <= c[0][2] + FIGURE_JOIN and c[0][0] <= box[2] + FIGURE_JOIN
                and box[1] <= c[0][3] + FIGURE_JOIN and c[0][1] <= box[3] + FIGURE_JOIN]
        count = 1 + sum(c[1] for c in near)
        clusters = [c for c in clusters if c not in near] + [
            (_union([box] + [c[0] for c in near]), count, curved or any(c[2] for c in near))]
    out = []
    for box, count, curved in clusters:
        area = (box[2] - box[0]) * (box[3] - box[1])
        if box[3] - box[1] < FORMULA_BOX:
            continue                     # the tinted band behind an equation, not a figure
        if (count >= 3 and area >= 1500) or area >= 4000:
            out.append(box + (not curved,))     # (x0, top, x1, bottom, ruled): only straight rules and boxes is a table
    return out


def _inside(box, regions, pad: float = FIGURE_PAD, ruled=None) -> bool:
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return any(r[0] - pad <= cx <= r[2] + pad and r[1] - pad <= cy <= r[3] + pad for r in regions
               if ruled is None or bool(r[4] if len(r) > 4 else False) == ruled)


# --- 2. gutters

def _gaps(line: Line) -> list:
    """The wide white gaps inside the line, leaving out the one after a list mark ("•   Living", "1.   Parenchyma")."""
    ordered = sorted(line.glyphs, key=lambda g: g.x0)
    gaps = [(a.x1, b.x0) for a, b in zip(ordered, ordered[1:]) if b.x0 - a.x1 >= GAP]
    if gaps and (LIST_MARK.match(text_of([g for g in ordered if g.x1 <= gaps[0][0] + 0.01]))
                 or SECTION_NUMBER.match(text_of([g for g in ordered if g.x1 <= gaps[0][0] + 0.01]))):
        gaps = gaps[1:]                 # "11.5   WHAT IS LIGHT REACTION?": a heading's number, not a column
    return gaps


def gutters(lines: list) -> list:
    """[(x0, x1)]: the white bands inside lines that at least ``GUTTER_LINES`` lines share (a sweep along the page,
    one point at a time)."""
    cover = Counter()
    for line in lines:
        for a, b in _gaps(line):
            cover.update(range(math.ceil(a), math.floor(b) + 1))
    bands, start = [], None
    for x in range(0, (max(cover) + 2) if cover else 0):
        if cover.get(x, 0) >= GUTTER_LINES and start is None:
            start = x
        elif cover.get(x, 0) < GUTTER_LINES and start is not None:
            if x - 1 - start >= 2:
                bands.append((float(start), float(x - 1)))
            start = None
    return bands


def _cut(glyphs, edges) -> list:
    parts = [[] for _ in range(len(edges) + 1)]
    for g in glyphs:
        parts[sum(1 for e in edges if (g.x0 + g.x1) / 2 > e)].append(g)
    return [p for p in parts if p]


def _extent(glyphs) -> tuple:
    return (min(g.x0 for g in glyphs), min(g.top for g in glyphs), max(g.x1 for g in glyphs), max(g.bottom for g in glyphs))


def _crosses(parts, divide: float) -> bool:
    """Does any part of a line run across the column divide?"""
    return any(min(g.x0 for g in p) < divide - 1 and max(g.x1 for g in p) > divide + 1 for p in parts)


def _running_key(text: str) -> str:
    """A head or foot line without its numbers: "PHOTOSYNTHESIS IN HIGHER PLANTS 139" and "... 141" are one running head;
    a line of only numbers (a page number, the edition "2024-25") has the empty key."""
    return re.sub(r"[^a-z]+", " ", text.lower()).strip()


def running_texts(pdf) -> set:
    """The keys of head and foot lines that repeat on at least three pages (running heads, book and part names)."""
    seen = Counter()
    for number, page in enumerate(pdf.pages, 1):
        height = float(page.height)
        keys = {_running_key(l.text) for l in page_lines(page, number)
                if l.top < HEAD_SHARE * height or l.top > FOOT_SHARE * height}
        seen.update(k for k in keys if k)
    return {k for k, count in seen.items() if count >= 3}


def read_page(page, number: int, blocks, *, repeated=frozenset(), running_texts=frozenset()) -> PageReading:
    """The page read by code. ``blocks`` are the text layer's (id, text[, box]) for this page. Pieces keep every id, add
    ``<id>.2`` (``.3`` ...) for the further parts of a cut line, and leave out absorbed marks-only lines."""
    width, height = float(page.width), float(page.height)
    lines = page_lines(page, number)
    if [(l.id, l.text) for l in lines] != [(b[0], b[1]) for b in blocks]:
        return PageReading(number, [Piece(b[0], b[1], tuple(b[2]) if len(b) > 2 else (0, 0, 1, 1)) for b in blocks], {},
                           ["text layer and characters differ: page kept as the text layer gave it"], repaired=False)

    def norm(box):
        return (round(box[0] / width, 4), round(box[1] / height, 4), round(box[2] / width, 4), round(box[3] / height, 4))

    sizes = Counter(round(g.size, 1) for line in lines for g in line.glyphs)
    body = sizes.most_common(1)[0][0] if sizes else 10.0
    notes = []
    absorbed = attach_marks(lines, body)
    capitals = join_capitals(lines)
    absorbed.update(capitals)
    if capitals:
        notes.append(f"{len(capitals)} titles in small capitals joined")
    lines = [l for l in lines if l.glyphs]
    starts = Counter(round(l.x0) for l in lines if abs(l.size - body) <= 0.3)
    margins = [x for x, count in starts.items() if count >= 3]
    marked = sum(1 for l in lines if l.changed)
    if marked:
        notes.append(f"{marked} lines got back their subscripts or superscripts ({len(absorbed)} marks-only lines absorbed)")
    running = {l.id for l in lines if (l.top < HEAD_SHARE * height or l.top > FOOT_SHARE * height)
               and (_running_key(l.text) in running_texts or not _running_key(l.text))}
    regions = figure_regions(page, repeated)
    bands = gutters([l for l in lines if l.id not in running])

    # Where the right column starts beside each gutter (the x most of its lines start at), and how far down it runs.
    starts_at = {}
    for band in bands:
        firsts, tops = Counter(), []
        for line in lines:
            if line.id in running:
                continue
            for a, b in _gaps(line):
                if min(b, band[1]) - max(a, band[0]) >= 2:
                    firsts[round(b)] += 1
                    tops.append((line.top, line.bottom))
        if firsts:
            x, count = firsts.most_common(1)[0]
            if count >= GUTTER_LINES:
                starts_at[band] = (float(x), min(t for t, _ in tops) - 20, max(b for _, b in tops) + 20)

    # Cut each line at a shared gutter, where one side of a gap is a figure's and the other is not, and where a word
    # starts exactly at the right column's start although the left entry ran close to it (no wide gap).
    parts_of = {}
    for line in lines:
        if line.id in running:
            parts_of[line.id] = [line.glyphs]
            continue
        cuts = []
        for a, b in _gaps(line):
            middle = (a + b) / 2
            left = [g for g in line.glyphs if (g.x0 + g.x1) / 2 < middle]
            right = [g for g in line.glyphs if (g.x0 + g.x1) / 2 > middle]
            if any(min(b, gb) - max(a, ga) >= 2 for ga, gb in bands) or (
                    _inside(_extent(left), regions) != _inside(_extent(right), regions)):
                cuts.append(middle)
        ordered = sorted(line.glyphs, key=lambda g: g.x0)
        for band, (start, top, bottom) in starts_at.items():
            if not top <= line.top <= bottom or any(band[0] - 2 <= c <= start + 2 for c in cuts):
                continue
            for prev, g in zip(ordered, ordered[1:]):
                if abs(g.x0 - start) <= 1.5 and (prev.space_after or g.x0 - prev.x1 >= 2) and ordered[0].x0 < band[0]:
                    cuts.append((prev.x1 + g.x0) / 2)
                    break
        parts_of[line.id] = _cut(line.glyphs, sorted(cuts)) if cuts else [line.glyphs]

    def kind_of(glyphs, text, line_id, whole=False):
        if line_id in running:
            return "running"
        box = _extent(glyphs)
        size = statistics.median(g.size for g in glyphs)
        small = size < 0.95 * body
        if CAPTION.match(text) and size <= body - 0.2:
            return "caption"
        if ARROW.search(text):
            return "equation"
        if whole and text.strip() in ZONES:
            return "heading"
        if whole and len(text) <= HEADING_CHARS and (size >= TITLE * body or (
                SECTION.match(text) and (size > body + 0.4 or _upper_share(text) >= 0.6))):
            return "heading"
        if _inside(box, regions, pad=2.0, ruled=True):
            return "table"
        at_margin = whole and not small and any(abs(box[0] - m) <= 2 for m in margins)
        if _inside(box, regions, ruled=False) and not at_margin and (
                small or len(text) <= (LINE_LABEL_CHARS if whole else LABEL_CHARS)):
            return "label"
        return "text"

    entries = []                # (line, piece, side box)
    for line in lines:
        parts = parts_of[line.id]
        texts = [line.text] if len(parts) == 1 else [text_of(p) for p in parts]
        if len(parts) >= 2 and all(len(t) <= TABLE_CELL for t in texts) and line.id not in running:
            entries.append((line, Piece(line.id, " | ".join(texts), norm(_extent(line.glyphs)), "table")))
            continue
        for k, (glyphs, text) in enumerate(zip(parts, texts)):
            pid = line.id if k == 0 else f"{line.id}.{k + 1}"
            entries.append((line, Piece(pid, text, norm(_extent(glyphs)), kind_of(glyphs, text, line.id, len(parts) == 1))))
    rows = [i for i, (line, piece) in enumerate(entries) if piece.kind == "table" and len(parts_of[line.id]) > 1
            and " | " in piece.text]
    for i in reversed(rows):            # a row of short cells with no such row next to it is one line, not a table
        line, piece = entries[i]
        if any(j in rows and abs(entries[j][0].top - line.top) <= 40 for j in (i - 1, i + 1)):
            continue
        if _inside(_extent(line.glyphs), regions, ruled=True):
            continue
        if any(min(b, gb) - max(a, ga) >= 2 for a, b in _gaps(line) for ga, gb in bands):
            parts = parts_of[line.id]    # two columns that happen to be short here: their parts, not a table row
            entries[i:i + 1] = [(line, Piece(line.id if k == 0 else f"{line.id}.{k + 1}", text_of(p), norm(_extent(p)),
                                             kind_of(p, text_of(p), line.id))) for k, p in enumerate(parts)]
            continue
        parts_of[line.id] = [line.glyphs]
        entries[i] = (line, Piece(line.id, line.text, norm(_extent(line.glyphs)), kind_of(line.glyphs, line.text, line.id, True)))

    # Text columns: around each gutter, the lines that do not cross it are read left column first, right column next;
    # a side of short entries beside longer text is an aside, read after the text.
    ordered, used = [], set()
    flow = [e for e in entries if e[1].kind != "running"]
    for band in bands:
        middle = starts_at[band][0] - 1 if band in starts_at else (band[0] + band[1]) / 2
        cut_rows = [i for i, (line, piece) in enumerate(flow) if i not in used and len(parts_of[line.id]) > 1
                    and any(min(band[1], b) - max(band[0], a) >= 2 for a, b in _gaps(line))]
        if not cut_rows or flow[cut_rows[0]][1].kind == "table":
            continue
        start, end = min(cut_rows), max(cut_rows)
        while start > 0 and not _crosses(parts_of[flow[start - 1][0].id], middle) and flow[start - 1][1].kind != "table":
            start -= 1
        while end < len(flow) - 1 and not _crosses(parts_of[flow[end + 1][0].id], middle) and flow[end + 1][1].kind != "table":
            end += 1
        zone = [i for i in range(start, end + 1) if i not in used]
        if not zone:
            continue
        left = [i for i in zone if (flow[i][1].box[0] + flow[i][1].box[2]) / 2 * width < middle]
        right = [i for i in zone if i not in left]
        for idx in (left, right):          # a side that is mostly a figure's words: its short words are the figure's too
            kinds = [flow[i][1].kind for i in idx]
            if kinds.count("label") * 2 >= len(kinds):
                for i in idx:
                    line, piece = flow[i]
                    if piece.kind == "text" and len(piece.text) <= LABEL_CHARS:
                        flow[i] = (line, Piece(piece.id, piece.text, piece.box, "label"))
        texts = {side: [flow[i][1] for i in idx if flow[i][1].kind == "text"] for side, idx in (("l", left), ("r", right))}
        if not texts["l"] or not texts["r"]:
            used.update(zone)
            ordered.append((zone[0], left + right))
            continue
        def narrow(ps):
            return (max(p.box[2] for p in ps) - min(p.box[0] for p in ps)) <= ASIDE_WIDTH
        short = {side: statistics.median(len(p.text) for p in ps) <= TABLE_CELL and narrow(ps) for side, ps in texts.items()}
        order = left + right
        if short["l"] and not short["r"]:
            order = right + left
        for side, idx in (("l", left), ("r", right)):
            if short[side] and not short["r" if side == "l" else "l"]:
                for i in idx:
                    line, piece = flow[i]
                    if piece.kind == "text":
                        flow[i] = (line, Piece(piece.id, piece.text, piece.box, "aside"))
        used.update(zone)
        ordered.append((zone[0], order))
        notes.append(f"two columns read one after the other ({len(left)} + {len(right)} lines)")
    out, done = [], set()
    starts = {start: order for start, order in ordered}
    for i in range(len(flow)):
        if i in starts:
            for j in starts[i]:
                out.append(flow[j][1])
                done.add(j)
        if i in used or i in done:
            continue
        out.append(flow[i][1])
    pieces = [e[1] for e in entries if e[1].kind == "running" and e[0].top < HEAD_SHARE * height] + out + [
        e[1] for e in entries if e[1].kind == "running" and e[0].top >= HEAD_SHARE * height]
    pieces = [Piece(p.id, PRIVATE.sub("", p.text).strip(), p.box, p.kind) for p in pieces]
    merged = []
    for piece in pieces:       # "Light" printed over the arrow of the equation under it: CO₂ + H₂O —Light→ ...
        if (merged and piece.kind == "equation" and merged[-1].kind in ("text", "label")
                and len(merged[-1].text) <= ARROW_WORD and " " not in merged[-1].text
                and -14 / height <= piece.box[1] - merged[-1].box[3] <= 14 / height
                and merged[-1].box[0] >= piece.box[0] and merged[-1].box[2] <= piece.box[2]):
            word = merged.pop()
            absorbed[word.id] = piece.id
            piece = Piece(piece.id, ARROW.sub(lambda m: f"—{word.text}{m.group(0)}", piece.text, count=1), piece.box,
                          piece.kind)
        merged.append(piece)
    size_of = {}
    for line in lines:
        for k, part in enumerate(parts_of[line.id]):
            size_of[line.id if k == 0 else f"{line.id}.{k + 1}"] = statistics.median(g.size for g in part)
    for caption in [p for p in merged if p.kind == "caption"]:     # a caption's further lines are the caption
        current = caption
        while True:
            below = [p for p in merged if p is not current and p.kind in ("text", "aside", "label")
                     and -2 <= (p.box[1] - current.box[3]) * height <= CAPTION_GAP
                     and (caption.box[0] * width - 12 <= p.box[0] * width <= caption.box[2] * width)
                     and p.box[2] * width <= caption.box[2] * width + 12
                     and abs(size_of.get(p.id, 0) - size_of.get(caption.id, 0)) <= 0.3]
            if not below:
                break
            nxt = below[0]
            at = merged.index(current)
            joined = Piece(current.id, current.text + " " + nxt.text,
                           (current.box[0], current.box[1], max(current.box[2], nxt.box[2]), nxt.box[3]), "caption")
            merged[at] = joined
            merged.remove(nxt)
            absorbed[nxt.id] = current.id
            current = joined
    for heading in [p for p in merged if p.kind == "heading"]:      # a heading set on two lines is one heading
        at = merged.index(heading)
        if at + 1 < len(merged):
            nxt = merged[at + 1]
            if (nxt.kind == "text" and _upper_share(nxt.text) >= 0.8 and len(nxt.text) <= 60
                    and -2 <= (nxt.box[1] - heading.box[3]) * height <= 6
                    and abs(size_of.get(nxt.id, 0) - size_of.get(heading.id, 0)) <= 0.3):
                merged[at] = Piece(heading.id, heading.text + " " + nxt.text,
                                   (heading.box[0], heading.box[1], max(heading.box[2], nxt.box[2]), nxt.box[3]), "heading")
                del merged[at + 1]
                absorbed[nxt.id] = heading.id
    labels = [p for p in merged if p.kind == "label"]
    rest = [p for p in merged if p.kind != "label"]
    at = next((i + 1 for i, p in enumerate(rest) if p.kind == "caption"), None)
    if at is None:
        at = len(rest) - sum(1 for p in rest if p.kind == "running" and p.box[1] >= HEAD_SHARE)
    pieces = rest[:at] + labels + rest[at:]
    for kind, words in (("label", "figure words kept out of the text"), ("table", "table rows kept as rows"),
                        ("equation", "equations"), ("aside", "side-column lines")):
        count = sum(1 for p in pieces if p.kind == kind)
        if count:
            notes.append(f"{count} {words}")
    return PageReading(number, pieces, absorbed, notes)


def read(pdf_bytes: bytes, blocks_by_page: dict) -> dict:
    """{page number: PageReading}; ``blocks_by_page`` is {page: [(id, text, box)]} from the text layer."""
    import pdfplumber

    out = {}
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        repeated, heads = repeated_pictures(pdf), running_texts(pdf)
        for number, blocks in blocks_by_page.items():
            out[number] = read_page(pdf.pages[number - 1], number, blocks, repeated=repeated, running_texts=heads)
    return out


def chapter_structure(pages) -> dict:
    """The chapter's printed structure from the reader's headings, by code: ``headings`` in reading order (the numbered
    sections "11.6", "11.6.1" ... and the zones SUMMARY, EXERCISES) and ``of_block``: {block id: {"section", "title",
    "zone"}} for every block (section "" before the first numbered heading: the unit page, the chapter's opening;
    zone "body", "summary", "exercise" or "points_to_ponder")."""
    current = {"section": "", "title": "", "zone": "body"}
    headings, of_block = [], {}
    for page in pages:
        for block in page.blocks:
            kind = getattr(block, "kind", "text") or "text"
            text = " ".join((block.text or "").split())
            if kind == "heading" and SECTION.match(text):
                number = text.split()[0].rstrip(".")
                current = {"section": number, "title": text[len(text.split()[0]):].strip(), "zone": "body"}
                headings.append({"block_id": block.id, "page": page.number, "number": number, "title": current["title"],
                                 "level": number.count("."), "zone": "body"})
            elif kind == "heading" and text in ZONES:
                current = {"section": current["section"], "title": text.title(), "zone": ZONES[text]}
                headings.append({"block_id": block.id, "page": page.number, "number": "", "title": text.title(), "level": 0,
                                 "zone": ZONES[text]})
            if kind != "running":
                of_block[block.id] = dict(current)
    return {"headings": headings, "of_block": of_block}

