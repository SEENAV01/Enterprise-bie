"""Pick the tools that compute and draw one capability (Task 046a).

``resolve(capability, subject=..., level=..., path="web")`` returns a ``Resolution``: the drawing tools for the
requested render path (``web``: BIE's blocks in Remotion/three.js; ``offline``: Blender or Manim), the compute
libraries that make the data, and the asset sources, each list best first. Order: a tool made for the subject's
family before a general one, then the proven status (used on a real book > demo proven > wrapped > installed), then
the tool's own rank. When the requested path has no drawer, the other path is the fallback and the resolution says
so. When nothing can draw the capability, the resolution is ``missing`` and a line goes into the missing-capability
log (JSON lines), which feeds seekh → BIE and the Task 046 merge path: an AI writes the new block once, BIE tests it,
Navin approves it.

``match(text)`` reads a Task 045d unpack's ``visual_verb`` (or any scene words) and names the capabilities it points to.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import registry as registry_module
from .registry import STATUS_RANK, Toolbox

RENDER_PATHS = ("web", "offline")
DRAW_ROLE = {"web": "draw", "offline": "offline_render"}


@dataclass
class Resolution:
    capability: str
    subject: str = ""
    level: str = ""
    requested_path: str = "web"
    path: str = "web"
    draw: list = field(default_factory=list)
    compute: list = field(default_factory=list)
    assets: list = field(default_factory=list)
    makers: list = field(default_factory=list)
    fallback: str = ""
    missing: bool = False
    reason: str = ""

    @property
    def tool_ids(self) -> list:
        return self.draw + self.compute + self.assets + self.makers

    def to_dict(self) -> dict:
        return asdict(self)


class MissingLog:
    """Missing capabilities as JSON lines: one line per resolve that found nothing to draw."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def add(self, record: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def rows(self) -> list:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def summary(self) -> list:
        """(capability, subject, count, reasons) for each missing pair, most frequent first."""
        counts = {}
        for row in self.rows():
            key = (row.get("capability", ""), row.get("subject", ""))
            entry = counts.setdefault(key, {"capability": key[0], "subject": key[1], "count": 0, "reasons": set()})
            entry["count"] += 1
            entry["reasons"].add(row.get("reason", ""))
        out = sorted(counts.values(), key=lambda e: (-e["count"], e["capability"], e["subject"]))
        return [dict(e, reasons=sorted(e["reasons"])) for e in out]


def default_log() -> MissingLog | None:
    path = os.environ.get("BIE_TOOLBOX_MISSING_LOG")
    return MissingLog(path) if path else None


def _order(tools, subject: str):
    def key(t):
        family = 0 if subject and subject in t.subjects else (1 if "all_subjects" in t.subjects else 2)
        return (family, -STATUS_RANK[t.status], t.rank, t.id)
    return sorted(tools, key=key)


def _fits(tool, subject: str, level: str) -> bool:
    if not tool.usable:
        return False
    if level and tool.levels and level not in tool.levels:
        return False
    return True


def resolve(capability: str, *, subject: str = "", level: str = "", path: str = "web", toolbox: Toolbox | None = None,
            log: MissingLog | None = None, context: str = "") -> Resolution:
    if path not in RENDER_PATHS:
        raise ValueError(f"path must be one of {', '.join(RENDER_PATHS)}")
    box = toolbox or registry_module.load()
    result = Resolution(capability=capability, subject=subject, level=level, requested_path=path, path=path)
    if capability not in box.capabilities:
        result.missing, result.reason = True, "not in the capability vocabulary (bie/toolbox/capabilities.json)"
    else:
        candidates = [t for t in box.for_capability(capability) if _fits(t, subject, level)]
        blocked = [t.id for t in box.for_capability(capability) if not t.usable]
        for attempt in (path,) + tuple(p for p in RENDER_PATHS if p != path):
            drawers = [t for t in candidates if t.role == DRAW_ROLE[attempt] and t.path == attempt]
            if drawers:
                result.path = attempt
                result.draw = [t.id for t in _order(drawers, subject)]
                if attempt != path:
                    result.fallback = f"no {path} tool draws {capability}; using the {attempt} path"
                break
        result.compute = [t.id for t in _order([t for t in candidates if t.role == "compute"], subject)]
        result.assets = [t.id for t in _order([t for t in candidates if t.role == "asset"], subject)]
        if result.path == "web":       # offline tools that build inputs once for the web blocks (route C: Blender → glTF)
            result.makers = [t.id for t in _order([t for t in candidates if t.role == "offline_render"], subject)]
        if not result.draw:
            result.missing = True
            result.reason = "no tool draws it on any path" + (f" (blocked: {', '.join(blocked)})" if blocked else "")
    if result.missing:
        target = log if log is not None else default_log()
        if target is not None:
            target.add({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "capability": capability, "subject": subject,
                        "level": level, "path": path, "reason": result.reason, "context": context[:300],
                        "registry_version": box.version})
    return result


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def match(text: str, *, toolbox: Toolbox | None = None, limit: int = 3) -> list:
    """Capabilities whose words appear in ``text`` (a visual_verb or a shot description), best first."""
    box = toolbox or registry_module.load()
    said = _norm(text)
    scored = []
    for cap in box.capabilities.values():
        hits = [v for v in cap.verbs if re.search(r"(?<![a-z])" + re.escape(_norm(v)) + r"(?![a-z])", said)]
        if cap.id.replace("_", " ") in said or cap.id in said:
            hits.append(cap.id)
        if hits:
            scored.append((len(hits), max(len(h) for h in hits), cap.id))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]))
    return [cid for _, _, cid in scored[:limit]]
