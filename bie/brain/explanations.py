"""The explanation library (Task 045d; Navin, 24 October 2026).

Every term meaning, everyday image, analogy and why chain that Navin's verdict locks is kept in
``rulebook/explanations.json`` and reused for the same concept in later books, so the writer layer (understanding,
plan, script) needs less AI over time, toward BIE's own model later. The page maker gets the matching entries as
the unpack to reuse; the script maker gets them as the opening to speak. Nothing is added by a model: entries come
from ``tools/lock_explanations.py`` after Navin's verdict on a real run, or from Navin himself.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent / "rulebook" / "explanations.json"
SCHEMA = "bie.brain.explanations/1"


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
        names = sorted({self.term.lower(), *(a.lower() for a in self.aliases)}, key=len, reverse=True)
        return r"(?<![a-z])(?:" + "|".join(re.escape(n) for n in names) + r")(?:e?s)?(?![a-z])"

    def line(self) -> str:
        why = " → ".join(f"{s['step']} [{s['basis']}]" for s in self.why_chain)
        return (f"{self.term}: yaani {self.plain_meaning}; image: {self.everyday_image}"
                + (f"; why: {why}" if why else "") + (f"; analogy: {self.analogy}" if self.analogy else "")
                + f" (locked, {self.source})")


@dataclass(frozen=True)
class Library:
    version: str
    entries: tuple

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
    return Library(version=str(data["version"]), entries=tuple(_entry(e) for e in data["entries"]))


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


def _concept_names(chapter: dict, iid: str) -> list:
    return [c["name"] for c in (chapter.get("map") or {}).get("concepts") or [] if iid in (c.get("item_ids") or [])]


def _bump(version: str) -> str:
    head, _, tail = version.rpartition(".")
    return f"{head}.{int(tail) + 1}" if tail.isdigit() and head else version + ".1"
