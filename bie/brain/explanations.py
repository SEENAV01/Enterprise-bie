"""The explanation library (Task 045d; Navin, 24 October 2026).

Every term meaning, everyday image, analogy and why chain that Navin's verdict locks is kept in
``rulebook/explanations.json`` and reused for the same concept in later books, so the writer layer (understanding,
plan, script) needs less AI over time, toward BIE's own model later. The page maker gets the matching entries as
the unpack to reuse; the script maker gets them as the opening to speak. Nothing is added by a model: entries come
from ``tools/lock_explanations.py`` after Navin's verdict on a real run, or from Navin himself.

Since 29 October 2026 (Navin: "V1 ke sabhi examples lock ho ... cheejen khud ke paas hone se AI par nirbharta kam
hogi") the library also holds **locked real-world examples** (``examples``: the place, actors, goods, numbers, steps
and the naming sentence of an economics concept's example, S1-16). The understanding section reads the library FIRST:
an item whose term is locked gets the locked example from code and the AI is not asked for it; the run report counts
library hits against AI examples. The example's narration wording is locked separately, only after the narration
work has made it natural (``narration_locked``); ``locked_version`` records the library version at the lock.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent / "rulebook" / "explanations.json"
SCHEMA = "bie.brain.explanations/1"


def term_pattern(term: str, aliases=()) -> str:
    """A term and its aliases as one word-boundary regex (a trailing s/es is allowed)."""
    names = sorted({term.lower(), *(a.lower() for a in aliases)}, key=len, reverse=True)
    return r"(?<![a-z])(?:" + "|".join(re.escape(n) for n in names) + r")(?:e?s)?(?![a-z])"


@dataclass(frozen=True)
class Entry:
    key: str
    term: str
    subject: str
    plain_meaning: str
    everyday_image: str
    why_chain: tuple
    analogy: str
    status: str
    source: str
    from_run: str
    concepts: tuple
    aliases: tuple = ()

    def pattern(self) -> str:
        """The term and its aliases as one word-boundary regex (a trailing s/es is allowed)."""
        return term_pattern(self.term, self.aliases)

    def line(self) -> str:
        why = " → ".join(f"{s['step']} [{s['basis']}]" for s in self.why_chain)
        return (f"{self.term}: yaani {self.plain_meaning}; image: {self.everyday_image}"
                + (f"; why: {why}" if why else "") + (f"; analogy: {self.analogy}" if self.analogy else "")
                + f" (locked, {self.source})")


@dataclass(frozen=True)
class Example:
    """A locked real-world example (Navin, 29 October 2026): the concept applied in a place with actors, goods, numbers
    that change, steps and the sentence that names the term after the story. ``narration`` is the spoken wording, locked
    only after the narration work makes it natural; until then ``narration_locked`` is False and the maker speaks the
    locked facts in its own words."""
    key: str
    term: str
    subject: str
    family: str
    content_type: str
    example: dict
    status: str
    source: str
    from_run: str
    concepts: tuple
    aliases: tuple = ()
    narration: dict | None = None
    narration_locked: bool = False
    locked_version: str = ""

    def pattern(self) -> str:
        return term_pattern(self.term, self.aliases)

    def line(self) -> str:
        ex = self.example
        numbers = "; ".join(f"{n.get('what', '')} {n.get('before', '')} → {n.get('after', '')}".strip() for n in ex.get("numbers") or [])
        steps = " → ".join(st.get("step", "") for st in ex.get("steps") or [])
        return (f"{self.term}: place {ex.get('place', '')}; actors {', '.join(ex.get('actors') or [])}; goods {', '.join(ex.get('goods') or [])}; "
                f"numbers {numbers}; steps {steps}; term after: {ex.get('term_after', '')}; real life: {ex.get('real_life_link', '')} "
                f"(locked, {self.source})")


@dataclass(frozen=True)
class Library:
    version: str
    entries: tuple
    examples: tuple = ()

    def lookup_examples(self, text: str, *, subject: str = "") -> list:
        """The locked examples whose term appears in ``text`` (word boundary, case-insensitive; subject recorded, not filtered)."""
        low = (text or "").lower()
        return [ex for ex in self.examples if ex.status == "locked" and re.search(ex.pattern(), low)]

    def example_lines(self, text: str, *, subject: str = "") -> str:
        """Prompt lines for the locked examples found in ``text``, or ""."""
        return "\n".join("  locked real-world example | " + e.line() for e in self.lookup_examples(text, subject=subject))

    def lookup(self, text: str, *, subject: str = "") -> list:
        """The locked entries whose term appears in ``text`` (word boundary, case-insensitive)."""
        low = (text or "").lower()
        found = []
        for entry in self.entries:      # subject is recorded, not filtered on: the same term may serve another subject
            if entry.status == "locked" and re.search(entry.pattern(), low):
                found.append(entry)
        return found

    def source_lines(self, text: str, *, subject: str = "") -> str:
        """Prompt lines for the matching entries, or ""."""
        found = self.lookup(text, subject=subject)
        return "\n".join("  locked explanation | " + e.line() for e in found)


def _example(raw: dict) -> Example:
    return Example(key=raw["key"], term=raw["term"], subject=raw.get("subject", ""), family=raw.get("family", ""),
                   content_type=raw.get("content_type", ""), example=dict(raw.get("example") or {}), status=raw.get("status", "locked"),
                   source=raw.get("source", ""), from_run=raw.get("from_run", ""), concepts=tuple(raw.get("concepts") or []),
                   aliases=tuple(raw.get("aliases") or []), narration=raw.get("narration"), narration_locked=bool(raw.get("narration_locked")),
                   locked_version=str(raw.get("locked_version", "")))


def _entry(raw: dict) -> Entry:
    return Entry(key=raw["key"], term=raw["term"], subject=raw.get("subject", ""), plain_meaning=raw["plain_meaning"],
                 everyday_image=raw.get("everyday_image", ""), why_chain=tuple(raw.get("why_chain") or []),
                 analogy=raw.get("analogy", ""), status=raw.get("status", "locked"), source=raw.get("source", ""),
                 from_run=raw.get("from_run", ""), concepts=tuple(raw.get("concepts") or []), aliases=tuple(raw.get("aliases") or []))


@lru_cache(maxsize=4)
def load(path: str = str(PATH)) -> Library:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{path}: not an explanation library ({data.get('schema')})")
    return Library(version=str(data["version"]), entries=tuple(_entry(e) for e in data["entries"]),
                   examples=tuple(_example(e) for e in data.get("examples") or []))


def lock_from_items(chapter: dict, item_ids, *, by: str, run: str, path: str = str(PATH)) -> list:
    """Add the unpack of the named items of a passed run to the library as locked entries (Navin's verdict).

    Every term of each item's unpack becomes one entry (the why chain of the item goes with the first term). An
    existing key is replaced, so a later verdict wins. Returns the entries written. Bumps the file's version.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    by_key = {e["key"]: e for e in data["entries"]}
    subject = (chapter.get("course") or {}).get("subject", "")
    written = []
    for iid in item_ids:
        item = chapter["items"][iid]
        unpack = item.get("unpack") or {}
        for n, term in enumerate(unpack.get("terms") or []):
            key = re.sub(r"\s+", " ", term["term"].strip().lower())
            entry = {"key": key, "term": term["term"].strip(), "subject": subject, "plain_meaning": term["plain_meaning"],
                     "everyday_image": term.get("everyday_image", ""),
                     "why_chain": list(unpack.get("why_chain") or []) if n == 0 else [],
                     "analogy": "", "aliases": [], "status": "locked", "source": by, "from_run": f"{run}:{iid}",
                     "concepts": [naksha_name for naksha_name in _concept_names(chapter, iid)]}
            by_key[key] = entry
            written.append(entry)
    data["entries"] = list(by_key.values())
    data["version"] = _bump(str(data["version"]))
    data.setdefault("changes", []).insert(0, f"{data['version']}: {len(written)} entries locked by {by} from {run}")
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    load.cache_clear()
    return written


def example_key(item: dict) -> str:
    """The term a locked example is filed under: the item's first unpack term, else its first concept word of content."""
    terms = (item.get("unpack") or {}).get("terms") or []
    if terms and (terms[0].get("term") or "").strip():
        return re.sub(r"\s+", " ", terms[0]["term"].strip().lower())
    return ""


def lock_examples_from_items(chapter: dict, item_ids, *, by: str, run: str, path: str = str(PATH)) -> list:
    """Lock the real-world examples (S1-16) of the named items of a passed run (Navin's verdict, 29 October 2026).

    One example per item, filed under the item's first unpack term (the other terms are aliases); the narration wording is
    NOT locked here (``narration_locked`` False: that waits for the narration work). An existing key is replaced, so a later
    verdict wins. Returns the examples written. Bumps the file's version and records it on each example (``locked_version``).
    """
    from . import soul
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    by_key = {e["key"]: e for e in data.get("examples") or []}
    course = chapter.get("course") or {}
    subject = course.get("subject", "")
    try:
        from . import shots
        family = shots.subject_family(subject)
    except Exception:       # pragma: no cover - the family is a record, never a blocker
        family = ""
    version = _bump(str(data["version"]))
    written = []
    for iid in item_ids:
        item = chapter["items"][iid]
        example = soul.real_world_of(item.get("unpack"))
        key = example_key(item)
        if not key or not soul.real_world_filled(example):
            raise ValueError(f"{iid}: no real-world example to lock (an unpack with a term and a filled real_world_example is needed)")
        terms = [t["term"].strip() for t in (item.get("unpack") or {}).get("terms") or [] if (t.get("term") or "").strip()]
        row = {"key": key, "term": terms[0], "aliases": terms[1:], "subject": subject, "family": family,
               "content_type": item.get("content_type", ""), "example": copy.deepcopy(example), "status": "locked", "source": by,
               "from_run": f"{run}:{iid}", "concepts": _concept_names(chapter, iid), "narration": None, "narration_locked": False,
               "locked_version": version}
        by_key[key] = row
        written.append(row)
    data["examples"] = list(by_key.values())
    data["version"] = version
    data.setdefault("changes", []).insert(0, f"{version}: {len(written)} real-world examples locked by {by} from {run} (narration wording not locked)")
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    load.cache_clear()
    return written


def item_text(item: dict) -> str:
    """The text a locked example is matched against: the item's own unpack terms (the concept the item opens), never its
    content, so an item that only mentions a locked term in passing keeps its own example."""
    return " | ".join(t.get("term", "") for t in (item.get("unpack") or {}).get("terms") or [])


def apply_examples(items: list, found: list, *, needs_example) -> dict:
    """Library first (Navin, 29 October 2026): every item that needs a real-world example and whose text names a locked
    example's term gets that example from the library (the maker's own is replaced) and is marked ``example_source``
    ``library:<key>``; an item the maker filled itself is marked ``ai``. Returns {"library": n, "ai": m}."""
    from . import soul
    counts = {"library": 0, "ai": 0}
    for item in items or []:
        if not needs_example(item):
            continue
        text = item_text(item).lower()
        hit = next((ex for ex in found if re.search(ex.pattern(), text)), None)
        if hit is not None:
            item.setdefault("unpack", soul.empty_unpack())
            item["unpack"]["real_world_example"] = copy.deepcopy(hit.example)
            item["example_source"] = f"library:{hit.key}"
            counts["library"] += 1
        elif soul.real_world_filled(soul.real_world_of(item.get("unpack"))):
            item["example_source"] = "ai"
            counts["ai"] += 1
    return counts


def _concept_names(chapter: dict, iid: str) -> list:
    return [c["name"] for c in (chapter.get("map") or {}).get("concepts") or [] if iid in (c.get("item_ids") or [])]


def _bump(version: str) -> str:
    head, _, tail = version.rpartition(".")
    return f"{head}.{int(tail) + 1}" if tail.isdigit() and head else version + ".1"
