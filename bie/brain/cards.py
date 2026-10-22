"""Task cards: how BIE tells the AI exactly what to make (docs/roadmap/TASK_CARD.md).

Every maker or reviewer call has the same shape:

1. System message = the fixed prefix of the section and task: a header line (prefix id, rulebook version,
   content-types version, output schema id), the role and the course, the rule texts of the section sorted
   by id, the content types (required questions and teaching patterns), the output schema with sorted keys,
   and how to answer. Nothing that changes per unit goes in, so every call of the same section and task in a
   run sends the same bytes and providers can cache them. The prefix is hashed; the hash is on the card and
   in the process record.
2. User message = the card (compact JSON in schema order), then the source: native text blocks, item lines
   or teacher questions, and page images as image parts.

The card is checked by code before anything is sent (``check``): it must match the schema in
``task_card.schema.json``, its prefix must be the one actually sent, its task must belong to its section, its
rules must be locked rules of that section, every part must ask at least its type's required questions and
every id must exist. After the answer, ``coverage_problems`` checks ``must_cover`` both ways.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from bie.model_gateway.schema_validation import SchemaValidationError, validate

from . import content_types as ct

CARD = "bie.task-card/1"
SCHEMA_PATH = Path(__file__).resolve().parent / "task_card.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
ORDER = tuple(SCHEMA["properties"])
SECTION_TASKS = {
    "understand": ("read_page",),
    "connect": ("build_chapter_map",),
    "lesson": ("plan_videos", "write_script"),
    "director": ("direct_scenes",),
    "visual": ("plan_assets", "choose_asset", "lay_out_scene"),
    "game": ("design_game", "build_mission"),
    "notes": ("write_notes",),
    "review": ("review",),
}
CARD_INTRO = "BIE task card (JSON):"


class CardError(ValueError):
    """A card BIE built is wrong: a bug in BIE, so nothing is sent."""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def types_text(types, *, ids=None, patterns: bool) -> str:
    """The content types as fixed prefix text: what each is, its required and other questions, its teaching pattern."""
    raw = {t["id"]: t for t in json.loads(ct.PATH.read_text(encoding="utf-8"))["types"]}
    lines = []
    for type_id in ids or types.ids:
        spec, info = types.types[type_id], raw[type_id]
        required = ", ".join(f"{a} ({types.word(a)})" for a in spec.required_asks)
        others = ", ".join(f"{a} ({w})" for a, w, _ in spec.questions if a not in spec.required_asks)
        lines.append(f"- {type_id} · {spec.name}: {info['what_it_is']} Required questions: {required}. Other questions: {others}.")
        if patterns:
            lines.append("  Teaching pattern: " + " ".join(f"{n}) {step}." for n, step in enumerate(spec.teaching_pattern, 1)))
    return "\n".join(lines)


@dataclass(frozen=True)
class Prefix:
    prefix_id: str
    section: str
    task: str
    schema_id: str
    rulebook_version: str
    content_types_version: str
    text: str

    @property
    def sha256(self) -> str:
        return sha256(self.text)

    def ref(self) -> dict:
        return {"prefix_id": self.prefix_id, "rulebook_version": self.rulebook_version,
                "content_types_version": self.content_types_version, "schema_id": self.schema_id, "sha256": self.sha256}


def course_line(course) -> str:
    return (f'Course: "{course.title}" · subject: {course.subject} · learners: {course.learners} · exam: {course.exam} · '
            f"learner language: {course.language}.")


def build_prefix(*, section: str, task: str, version: int, schema_id: str, schema: dict, role: str, how: str, rulebook,
                 course, types=None, patterns: bool = False, review: bool = False, checklist: str = "") -> Prefix:
    """The fixed system message of one section and task. ``review`` builds the reviewer's prefix of the same task."""
    types = types or ct.load()
    prefix_id = f"{section}.{task}{'.review' if review else ''}/{version}"
    header = (f"BIE task prefix {prefix_id} · rulebook {rulebook.version} · content types {types.version} · "
              f"schema {schema_id}")
    if review:
        rules = rulebook.reviewer_instructions() + "\n\nCheck against this list (answer every item in \"checklist\" with its rule id):\n" + checklist
    else:
        rules = "\n".join(f"[{r.id}] {r.rule}" for r in sorted(rulebook.for_section(section), key=lambda r: r.id))
    text = "\n\n".join([
        header,
        role.strip() + "\n" + course_line(course),
        ("How you review (BIE's rules):\n" if review else "Navin's rules for this task (follow every one):\n") + rules,
        "BIE's content types (the type of an item decides its required questions and how it is taught, shown, played "
        "and drawn):\n" + types_text(types, patterns=patterns),
        "Output schema (JSON):\n" + json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        "How BIE talks to you: every request is a task card (JSON) followed by its source. The card names the unit, its "
        "parts with their content type and required questions, the ids of the rules above that apply, the output, the "
        "ids you must cover and the context. The card is BIE's instruction; the source is the material.\n" + how.strip(),
    ])
    return Prefix(prefix_id, section, task, schema_id, rulebook.version, types.version, text)


def make(*, prefix: Prefix, chapter_id: str, unit: dict, parts: list, rules: list, mode: str, max_output_tokens: int,
         must_cover: list, claim_field: str, may_skip: list, map_slice: list, before: str, after: str, block_ids: list,
         page_images: list) -> dict:
    """A card with its keys in schema order (what is sent is what is recorded)."""
    card = {
        "card": CARD,
        "card_id": f"{prefix.section}.{prefix.task}@{chapter_id}/{unit['unit_id']}",
        "section": prefix.section,
        "task": prefix.task,
        "prefix": prefix.ref(),
        "unit": {"unit_id": unit["unit_id"], "title": unit.get("title", ""), "pages": list(unit.get("pages") or [])},
        "parts": parts,
        "rules": list(rules),
        "output": {"schema_id": prefix.schema_id, "mode": mode, "max_output_tokens": int(max_output_tokens)},
        "coverage": {"must_cover": list(must_cover), "claim_field": claim_field, "may_skip": list(may_skip)},
        "context": {"map_slice": [[str(x) for x in row] for row in map_slice], "before": before, "after": after},
        "source": {"block_ids": list(block_ids), "page_images": list(page_images)},
    }
    assert tuple(card) == ORDER
    return card


def part(part_id: str, item_ids, type_id: str, focus: str, *, questions=(), types=None) -> dict:
    """One part: its ids, one type and the questions it must answer (always the type's required asks first)."""
    types = types or ct.load()
    asks = list(dict.fromkeys(list(types.required_asks(type_id)) + [q for q in questions if q]))
    return {"part_id": part_id, "item_ids": list(item_ids), "type": type_id, "questions": asks or ["what"],
            "focus": focus.strip() or "-"}


def check(card: dict, *, prefix: Prefix, rulebook, known_ids=None, types=None) -> list:
    """Problems with a card BIE built (empty = the card may be sent)."""
    types = types or ct.load()
    problems = []
    try:
        validate(card, SCHEMA, strict=True)
    except SchemaValidationError as exc:
        return [f"card does not match the task-card schema: {exc}"]
    if card["prefix"] != prefix.ref():
        problems.append("card prefix does not match the prefix that is sent")
    if card["task"] not in SECTION_TASKS.get(card["section"], ()):
        problems.append(f"task {card['task']} does not belong to section {card['section']}")
    locked = {r.id for r in rulebook.for_section(card["section"])}
    stray = [r for r in card["rules"] if r not in locked]
    if stray:
        problems.append(f"rules {stray} are not locked rules of section {card['section']}")
    for p in card["parts"]:
        if p["type"] != ct.NONE:
            missing = [a for a in types.required_asks(p["type"]) if a not in p["questions"]]
            if missing:
                problems.append(f"part {p['part_id']}: a {p['type']} part must ask {missing}")
    if known_ids is not None:
        ids = [i for p in card["parts"] for i in p["item_ids"]] + card["coverage"]["must_cover"] + \
              [s["item_id"] for s in card["coverage"]["may_skip"]] + [row[0] for row in card["context"]["map_slice"]]
        unknown = sorted({i for i in ids if i not in known_ids})
        if unknown:
            problems.append(f"ids not in the chapter: {unknown[:20]}")
    if card["output"]["schema_id"] != prefix.schema_id:
        problems.append("the card's output schema is not the prefix's schema")
    return problems


def require_valid(card: dict, **kwargs) -> dict:
    problems = check(card, **kwargs)
    if problems:
        raise CardError(f"{card.get('card_id', '?')}: " + "; ".join(problems))
    return card


def coverage_problems(card: dict, claimed, *, known=None, rule: str = "") -> list:
    """must_cover checked both ways: every id is claimed; every claimed id is a known id of this unit."""
    must = card["coverage"]["must_cover"]
    allowed = set(must) | {s["item_id"] for s in card["coverage"]["may_skip"]} | set(known or ())
    claimed = list(claimed)
    tag = f" ({rule})" if rule else ""
    problems = []
    missing = [i for i in must if i not in set(claimed)]
    if missing:
        problems.append(f"{len(missing)} ids of must_cover are not claimed in {card['coverage']['claim_field']}{tag}: "
                        + ", ".join(missing[:40]))
    unknown = sorted({i for i in claimed if i not in allowed})
    if unknown:
        problems.append(f"{card['coverage']['claim_field']} claims ids that are not part of this card: {', '.join(unknown[:20])}")
    return problems


def user_message(card: dict, source: str, images=(), closing: str = "Answer the card with one JSON object.") -> list:
    """The user turn: the card, the source text, then the images (each after a one-line label)."""
    parts = [{"type": "text", "text": f"{CARD_INTRO}\n{compact(card)}\n\n{source.strip()}"}]
    for label, image in images:
        if image is not None:
            parts += [{"type": "text", "text": label}, image]
    parts.append({"type": "text", "text": closing})
    return parts


def read_card(text: str) -> dict:
    """The card inside a user message (for the offline fake and for tests)."""
    start = text.index(CARD_INTRO) + len(CARD_INTRO)
    value, _ = json.JSONDecoder().raw_decode(text[start:].lstrip())
    return value


class CardBook:
    """The cards of one run: a card id is used once, and every prefix hash of the run is kept."""

    def __init__(self):
        self.cards, self.prefixes = {}, {}

    def add(self, card: dict) -> dict:
        if card["card_id"] in self.cards:
            raise CardError(f"card id {card['card_id']} is used twice in this run")
        self.cards[card["card_id"]] = card
        self.prefixes.setdefault(card["prefix"]["prefix_id"], card["prefix"]["sha256"])
        return card
