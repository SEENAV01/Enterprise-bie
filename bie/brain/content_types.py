"""Content types in code: the type map (``rulebook/content_types.json``) and BIE's own type proposal per block.

Before the maker AI reads a page, BIE's code proposes a content type for every native text block from the
detection hints in the type map (keywords, patterns, and a little list context: a numbered or bulleted list
takes the type of the line that introduces it, "There are four types of tissues" → classification). The
proposal is evidence, not a verdict. The maker sees it on its task card and decides; the code compares the
maker's type with its own, every difference is recorded in the process record, and a strong proposal that
the maker contradicts without a reason (``type_note``) goes back to the maker as a problem.

The type also decides which teacher questions an item must answer (``required_asks``) and the teaching
pattern of its lesson, so Sections 1 and 2 read both from here.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent / "rulebook" / "content_types.json"
NONE = "none"
# Most specific first: used only to break a tie between two equally strong proposals.
PRECEDENCE = ("figure", "definition", "classification", "comparison", "timeline", "process", "cause_effect", "structure",
              "facts_numbers")
LIST_MARKER = re.compile(r"^\s*(?:\(?(?:\d{1,2}|[ivx]{1,4}|[a-hA-H])[.)]|[•●▪◦\-–*])\s*\S")
LEAD_IN_TYPES = ("classification", "process", "structure", "comparison", "timeline")
NUMBERED_LIST_HINT = r"^\s*\(?[0-9ivx]+[.)]\s+\w+"     # the process hint that on its own only says "numbered list"
PATTERN_MARK = "pattern "       # evidence: "pattern 'types of'" (the matched words) or "'types of'" (a keyword)
LIST_MARK = " (numbered list)"
ROLE_KINDS = ("question", "answer_option")      # a PYQ and its options: a role, linked to the items they test
PART_KINDS = ("table_row", "diagram_label")     # a row or a label follows the type of its table or diagram


@dataclass(frozen=True)
class TypeSpec:
    id: str
    name: str
    required_asks: tuple
    questions: tuple            # (ask, word, question)
    teaching_pattern: tuple
    keywords: tuple
    patterns: tuple


@dataclass(frozen=True)
class ContentTypes:
    version: str
    types: dict
    legacy: dict
    words: dict                 # Hinglish question word -> English asks

    @property
    def ids(self):
        return tuple(self.types)

    def required_asks(self, type_id: str) -> tuple:
        spec = self.types.get(type_id)
        return spec.required_asks if spec else ()

    def word(self, ask: str) -> str:
        """The Hinglish question word for an English ask ("how" -> "kaise")."""
        for word, asks in self.words.items():
            if ask in asks:
                return word
        return ask

    def required_words(self, type_id: str) -> tuple:
        return tuple(dict.fromkeys(self.word(a) for a in self.required_asks(type_id)))

    def pattern(self, type_id: str) -> tuple:
        spec = self.types.get(type_id)
        return spec.teaching_pattern if spec else ()

    def from_legacy(self, old: str) -> str:
        """The new type id for a Section 1 type of 21 October; roles (example, question, other) give ``none``."""
        new = self.legacy.get(old, old)
        return new if new in self.types else NONE


def _keyword_regex(word: str):
    flags = 0 if word.isupper() else re.IGNORECASE
    head = r"\b" if word[:1].isalnum() else ""
    tail = r"\b" if word[-1:].isalnum() else ""
    return re.compile(head + re.escape(word) + tail, flags)


@lru_cache(maxsize=4)
def load(path: str = str(PATH)) -> ContentTypes:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    types = {}
    for raw in data["types"]:
        hints = raw.get("detection_hints") or {}
        types[raw["id"]] = TypeSpec(
            id=raw["id"], name=raw["name"], required_asks=tuple(raw["required_asks"]),
            questions=tuple((q["ask"], q["word"], q["question"]) for q in raw["typical_questions"]),
            teaching_pattern=tuple(raw["teaching_pattern"]),
            keywords=tuple((k, _keyword_regex(k)) for k in hints.get("keywords", [])),
            patterns=tuple((p, re.compile(p, re.IGNORECASE | re.MULTILINE)) for p in hints.get("patterns", [])))
    legacy = {k: v for k, v in (data.get("legacy_types") or {}).items() if not k.startswith("_")}
    words = {w: tuple(spec["asks"]) for w, spec in data["question_words"].items()}
    return ContentTypes(version=str(data["version"]), types=types, legacy=legacy, words=words)


@dataclass(frozen=True)
class Proposal:
    type: str | None
    strength: str               # "strong", "weak" or "none"
    evidence: tuple = field(default_factory=tuple)

    @property
    def strong(self) -> bool:
        return self.strength == "strong"


SILENT = Proposal(None, "none")


def _clean(text: str) -> str:
    # The text layer carries bullets as private-use or symbol glyphs; they are list markers, not words.
    return "".join("•" if unicodedata.category(ch) in ("Co", "So") else ch for ch in text)


def is_list_item(text: str) -> bool:
    return bool(LIST_MARKER.match(_clean(text)))


def score(text: str, types: ContentTypes | None = None) -> dict:
    """{type id: (points, evidence)} for one piece of text: a pattern is worth 2 points, a keyword 1."""
    types = types or load()
    text = _clean(text)
    found = {}
    for spec in types.types.values():
        evidence, points = [], 0
        for source, regex in spec.patterns:
            match = regex.search(text)
            if match:
                points += 2
                evidence.append(PATTERN_MARK + repr(match.group(0).strip()[:40]) + (LIST_MARK if source == NUMBERED_LIST_HINT else ""))
        for word, regex in spec.keywords:
            if regex.search(text):
                points += 1
                evidence.append(repr(word))
        if points:
            found[spec.id] = (points, tuple(evidence))
    return found


def propose(text: str, types: ContentTypes | None = None) -> Proposal:
    """BIE's proposal for one piece of text, ignoring context. Strong = a pattern or two keywords of one type."""
    types = types or load()
    found = score(text, types)
    if is_list_item(text) and "process" in found:
        # A numbered list line alone says "list", not "process"; the line that introduces the list decides.
        points, evidence = found["process"]
        kept = tuple(e for e in evidence if not e.endswith(LIST_MARK))
        points -= 2 * (len(evidence) - len(kept))
        if points > 0:
            found["process"] = (points, kept)
        else:
            del found["process"]
    if not found:
        return SILENT
    top = max(points for points, _ in found.values())
    tied = sorted((t for t, (p, _) in found.items() if p == top), key=PRECEDENCE.index)
    evidence = found[tied[0]][1]
    strength = "strong" if top >= 2 else "weak"
    if len(tied) > 1 and strength == "strong":
        strength = "weak"           # two types equally likely: a hint for the maker, never a correction
        evidence = tuple(f"{t}: {', '.join(found[t][1])}" for t in tied)
    return Proposal(tied[0], strength, evidence)


def _marker_style(text: str) -> str:
    head = _clean(text).lstrip()[:3]
    if head[:1].isdigit():
        return "number"
    if head[:1].lower() in "ivx" and head[1:2] in ".)":
        return "roman"
    if head[:1].isalpha() or head[:1] == "(":
        return "letter"
    return "bullet"


def _lead_in(text: str, proposal: Proposal) -> bool:
    if not proposal.strong or proposal.type not in LEAD_IN_TYPES:
        return False
    return proposal.type in ("classification", "process") or _clean(text).rstrip().endswith((":", ":-", "-", "–"))


def propose_blocks(blocks, types: ContentTypes | None = None) -> dict:
    """{block id: Proposal} for a page's native text blocks in reading order, with list context.

    A list line takes the type of the line that introduces its list (a strong classification or process line,
    or a structure, comparison or timeline line ending in a colon), unless its own text is strong. The list
    ends at the first line that is not a list line or that uses another marker (1. 2. then bullets).
    """
    types = types or load()
    out, lead, style = {}, None, None
    for block in blocks:
        own = propose(block.text, types)
        if is_list_item(block.text):
            current = _marker_style(block.text)
            if style is None:
                style = current
            elif current != style:
                lead = None
            if lead is not None and not own.strong:
                own = Proposal(lead[0], "strong", (f"list under {lead[1]!r}",))
        else:
            lead = (own.type, block.text.strip()[:60]) if _lead_in(block.text, own) else None
            style = None
        out[block.id] = own
    return out


def propose_item(item: dict, block_proposals: dict) -> Proposal:
    """The code's proposal for one maker item: the strongest proposal among its blocks (image-only items: none)."""
    proposals = [block_proposals[b] for b in item.get("block_ids") or [] if b in block_proposals]
    strong = [p for p in proposals if p.strong]
    if strong:
        kinds = sorted({p.type for p in strong}, key=PRECEDENCE.index)
        if len(kinds) == 1:
            return strong[0]
        return Proposal(kinds[0], "weak", (f"its blocks point to {', '.join(kinds)}",))
    weak = [p for p in proposals if p.type]
    return weak[0] if weak else SILENT


def compare(items, block_proposals: dict) -> list:
    """One row per item: the maker's type, the code's proposal and how they relate.

    status: agree · explained (different, and the maker gave a type_note) · disagree (a strong proposal differs
    and the maker gave no reason: goes back to the maker) · differs_weak (only a weak hint differs: recorded) ·
    code_silent (no hint on the item's blocks, for example image-only items) · role (a question or an answer
    option) · follows_parent (a table row or diagram label: its table or diagram is compared instead).
    """
    rows = []
    for item in items:
        mine = propose_item(item, block_proposals)
        theirs = item.get("content_type")
        if item.get("kind") in ROLE_KINDS:
            status = "role"
        elif item.get("kind") in PART_KINDS:
            status = "follows_parent"
        elif mine.type is None:
            status = "code_silent"
        elif mine.type == theirs:
            status = "agree"
        elif (item.get("type_note") or "").strip():
            status = "explained"
        elif mine.strong and item.get("teachable"):
            status = "disagree"
        else:
            status = "differs_weak"
        rows.append({"item_id": item["item_id"], "ai_type": theirs, "code_type": mine.type, "strength": mine.strength,
                     "evidence": list(mine.evidence)[:4], "status": status, "type_note": item.get("type_note", "")})
    return rows


def summary(rows) -> dict:
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return dict(sorted(counts.items()))
