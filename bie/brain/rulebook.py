"""The vision rulebook: Navin's vision as versioned rules that every BIE section and reviewer loads.

A rule is an instruction for the section that makes the work (``rule``) and a yes/no question for
the reviewer (``check``). Rulebook files live in ``bie/brain/rulebook/*.json``; the rulebook version
recorded with every output is the files' own version strings plus a hash of their bytes, so a
changed rule can never pass silently as the old one. Only ``locked`` rules (approved by Navin) are
used; ``proposed`` rules wait for his approval. Companion data files in the same folder (for example
``content_types.json``, schema ``bie.brain.content-types/1``; the level profiles, the teacher example bank and the
explanation library of Task 045d, the visual level ladder of Task 046) carry no rules but count in the version and the
hash, because the sections read them too. ``visual_grammar.json`` (Task 046) is a rules file: the eleven visual grammar
rules VG-01 to VG-11 for the director and the visual section, and the wording rule W-01 with its word list.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

RULEBOOK_DIR = Path(__file__).resolve().parent / "rulebook"
STATUSES = ("locked", "proposed", "retired")
DATA_SCHEMAS = ("bie.brain.content-types/1", "bie.brain.simple-hindi/1", "bie.brain.level-profiles/1",
                "bie.brain.teacher-examples/1", "bie.brain.explanations/1", "bie.brain.visual-levels/1")


class RulebookError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    sections: tuple
    status: str
    rule: str
    check: str

    def applies_to(self, section: str) -> bool:
        return "*" in self.sections or section in self.sections


@dataclass(frozen=True)
class Rulebook:
    rules: tuple
    version: str
    digest: str

    def for_section(self, section: str):
        return tuple(r for r in self.rules if r.status == "locked" and r.applies_to(section))

    def instructions(self, section: str) -> str:
        """The rules for ``section`` as numbered instructions for the maker."""
        return "\n".join(f"[{r.id}] {r.rule}" for r in self.for_section(section))

    def checklist(self, section: str):
        """(rule id, yes/no question) pairs for the reviewer of ``section``."""
        return tuple((r.id, r.check) for r in self.for_section(section) if r.check and r.check != "n/a")

    def reviewer_instructions(self) -> str:
        """How every reviewer works (rules written for "review" itself; the section's rules arrive as its checklist)."""
        return "\n".join(f"[{r.id}] {r.rule}" for r in self.rules if r.status == "locked" and "review" in r.sections)


def _parse(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RulebookError(f"{path.name}: unreadable rulebook ({exc})") from None
    if isinstance(data, dict) and data.get("schema") in DATA_SCHEMAS and data.get("version") and "rules" not in data:
        return str(data["version"]), []
    if not isinstance(data, dict) or not isinstance(data.get("rules"), list) or not data.get("version"):
        raise RulebookError(f"{path.name}: needs 'version' and a 'rules' list")
    rules = []
    for raw in data["rules"]:
        if not isinstance(raw, dict):
            raise RulebookError(f"{path.name}: every rule must be an object")
        missing = [k for k in ("id", "sections", "status", "rule", "check") if not raw.get(k)]
        if missing:
            raise RulebookError(f"{path.name}: rule {raw.get('id', '?')} is missing {', '.join(missing)}")
        if raw["status"] not in STATUSES:
            raise RulebookError(f"{path.name}: rule {raw['id']} has unknown status {raw['status']!r}")
        if not isinstance(raw["sections"], list) or not all(isinstance(s, str) and s for s in raw["sections"]):
            raise RulebookError(f"{path.name}: rule {raw['id']} needs a list of sections")
        rules.append(Rule(raw["id"], tuple(raw["sections"]), raw["status"], raw["rule"].strip(), raw["check"].strip()))
    return str(data["version"]), rules


def load(directory: str | Path = RULEBOOK_DIR) -> Rulebook:
    directory = Path(directory)
    files = sorted(directory.glob("*.json"))
    if not files:
        raise RulebookError(f"no rulebook files in {directory}")
    versions, rules, digest = [], [], hashlib.sha256()
    for path in files:
        version, file_rules = _parse(path)
        versions.append(f"{path.stem}@{version}")
        rules.extend(file_rules)
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    ids = [r.id for r in rules]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise RulebookError("duplicate rule ids: " + ", ".join(duplicates))
    return Rulebook(rules=tuple(rules), version="+".join(versions), digest=digest.hexdigest())
