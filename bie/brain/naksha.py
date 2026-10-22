"""Naksha · the compact chapter map that every later section shares.

Section 1 keeps its full chapter map (every item with its teacher questions and answers) as the record. From
it BIE builds the naksha once: a small, versioned map with a stable id for every teachable item, its content
type, its required questions (kya, kyun, kaise ...), its page and its links (prerequisite, part of, cause and
effect, compares with, ...). Later sections never get the whole naksha; a task card carries only the slice its
unit needs (``slice_rows``): its own items and one row for each concept they connect to.

Ids are the chapter map's item ids ("p003-i4") and concept ids; they never change once Section 1 has passed a
page, and a resumed run keeps them. The naksha's sha256 is recorded on every card built from it.
"""
from __future__ import annotations

import hashlib
import json
import re

from . import content_types as ct

SCHEMA = "bie.brain.naksha/1"
SHORT = 100
# Measured: 155,907 characters of chapter-map JSON were 45,479 input tokens (run 39627682253, connect step,
# GPT-6.1 Sol tokenizer). Other tokenizers differ a little; the ledger always has the real count.
CHARS_PER_TOKEN = 3.43
LINKS = {"part_of": "part", "type_of": "kind", "depends_on": "pre", "causes": "cause", "contrasts_with": "compare",
         "compares_with": "compare", "example_of": "example", "sequence_next": "seq", "located_in": "place",
         "function_of": "function", "tested_by": "test"}
EXAM = {"high": "h", "medium": "m", "low": "l"}


def short(text: str, limit: int = SHORT) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit // 2 else cut).rstrip(" ,;:") + "…"


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")


def estimate_tokens(value) -> int:
    text = value if isinstance(value, str) else canonical(value).decode("utf-8")
    return round(len(text) / CHARS_PER_TOKEN)


def item_type(item: dict, concept_type: str | None, types) -> str:
    """The item's type id; an item from a run before 22 October is converted with the legacy mapping."""
    value = item.get("content_type") or ct.NONE
    if value in types.types or value == ct.NONE:
        return value
    new = types.from_legacy(value)
    if new == ct.NONE and value == "example" and concept_type:
        return item_type({"content_type": concept_type}, None, types)
    return new


def in_naksha(item: dict) -> bool:
    return bool(item.get("teachable")) or item.get("kind") == "question"


def build(chapter: dict, types=None) -> dict:
    types = types or ct.load()
    m = chapter.get("map") or {}
    concept_type = {}
    for concept in m.get("concepts") or []:
        for iid in concept.get("item_ids") or []:
            concept_type.setdefault(iid, concept.get("content_type"))
    items, kept = [], set()
    for iid, item in chapter["items"].items():
        if not in_naksha(item):
            continue
        kind = item_type(item, concept_type.get(iid), types)
        items.append([iid, kind, item["page"], short(item.get("content", "")), ",".join(types.required_words(kind)),
                      EXAM.get(item.get("exam_importance"), "")])
        kept.add(iid)
    concepts = [[c["concept_id"], c["name"], item_type({"content_type": c.get("content_type")}, None, types),
                 [i for i in c.get("item_ids") or [] if i in kept]] for c in m.get("concepts") or []]
    links = []
    for iid, item in chapter["items"].items():
        parent = item.get("parent_item_id") or ""
        if iid in kept and parent in kept:
            links.append([iid, "part", parent])
        for tested in item.get("tests_item_ids") or []:
            if iid in kept and tested in kept:
                links.append([iid, "test", tested])
    for rel in m.get("relations") or []:
        links.append([rel["from_concept"], LINKS.get(rel["relation"], rel["relation"]), rel["to_concept"]])
    for link in m.get("question_links") or []:
        for cid in link.get("tests_concepts") or []:
            links.append([link["question_item_id"], "test", cid])
    for ref in m.get("cross_references") or []:
        if ref["from_item_id"] in kept and ref["resolved_item_id"] in chapter["items"]:
            links.append([ref["from_item_id"], "ref", ref["resolved_item_id"]])
    course = chapter.get("course") or {}
    body = {
        "naksha": SCHEMA,
        "chapter": {"title": course.get("title", ""), "subject": course.get("subject", ""), "exam": course.get("exam", ""),
                    "language": course.get("language", ""), "source_sha256": chapter.get("source_sha256", ""),
                    "pages": chapter.get("page_count") or len(chapter.get("pages") or []),
                    "rulebook": chapter.get("rulebook_version", ""), "content_types": types.version},
        "columns": {"items": ["id", "type", "page", "short", "required_questions", "exam"],
                    "concepts": ["id", "name", "type", "item_ids"], "links": ["from", "link", "to"],
                    "prerequisites": ["name", "needed_for", "basis"]},
        "items": items,
        "concepts": concepts,
        "links": links,
        "order": list(m.get("teaching_order") or []),
        "prerequisites": [[p["name"], list(p.get("needed_for") or []), p.get("basis", "")]
                          for p in m.get("prerequisites_to_teach") or []],
    }
    body["sha256"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def size(naksha: dict) -> dict:
    raw = canonical(naksha)
    return {"items": len(naksha["items"]), "concepts": len(naksha["concepts"]), "links": len(naksha["links"]),
            "bytes": len(raw), "chars": len(raw.decode("utf-8")), "tokens_estimate": estimate_tokens(naksha),
            "chars_per_token": CHARS_PER_TOKEN}


class Index:
    """Look-ups over one naksha: rows by id, the concepts of an item, the links of a node."""

    def __init__(self, naksha: dict):
        self.naksha = naksha
        self.items = {row[0]: row for row in naksha["items"]}
        self.concepts = {row[0]: row for row in naksha["concepts"]}
        self.concepts_of = {}
        for cid, _, _, item_ids in naksha["concepts"]:
            for iid in item_ids:
                self.concepts_of.setdefault(iid, []).append(cid)
        self.out, self.into = {}, {}
        for src, link, dst in naksha["links"]:
            self.out.setdefault(src, []).append((link, dst))
            self.into.setdefault(dst, []).append((link, src))

    def pages_of(self, cid: str) -> str:
        pages = sorted({self.items[i][2] for i in self.concepts[cid][3] if i in self.items})
        if not pages:
            return ""
        return str(pages[0]) if len(pages) == 1 else f"{pages[0]}-{pages[-1]}"

    def concept_row(self, cid: str):
        _, name, kind, _ = self.concepts[cid]
        return [cid, kind, self.pages_of(cid), short(name)]


def slice_rows(naksha: dict, item_ids, *, index: Index | None = None) -> list:
    """The card's ``context.map_slice``: one [id, type, page, short] row per own item, then one row per concept those
    items belong to or connect to (prerequisite, part, kind, cause, compare, sequence, example), never their items."""
    index = index or Index(naksha)
    rows, seen = [], set()
    for iid in item_ids:
        if iid in index.items and iid not in seen:
            _, kind, page, text, _, _ = index.items[iid]
            rows.append([iid, kind, str(page), text])
            seen.add(iid)
    own_concepts = []
    for iid in item_ids:
        for cid in index.concepts_of.get(iid, []):
            if cid not in own_concepts:
                own_concepts.append(cid)
    related = list(own_concepts)
    for cid in own_concepts:
        for link, other in index.out.get(cid, []) + index.into.get(cid, []):
            if link in ("pre", "part", "kind", "cause", "compare", "seq", "example") and other in index.concepts \
                    and other not in related:
                related.append(other)
    for iid in item_ids:
        for link, other in index.out.get(iid, []):
            if other in index.items and other not in seen:
                _, kind, page, text, _, _ = index.items[other]
                rows.append([other, kind, str(page), text])
                seen.add(other)
    rows += [index.concept_row(cid) for cid in related if cid in index.concepts]
    return rows


def concept_slice(naksha: dict, *, index: Index | None = None) -> list:
    """The concept layer only (for the lesson plan): one [concept id, type, pages, name] row per concept."""
    index = index or Index(naksha)
    return [index.concept_row(cid) for cid in index.concepts]
