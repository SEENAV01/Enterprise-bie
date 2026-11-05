"""The box rule's Python side (dabba-niyam, Navin 5 November 2026): the boxes of saanche, persons and reserved
background zones, measured by the engine's own drawings (``bie/brain/video/engine/boxes.mjs`` through
``tools/saancha_boxes.mjs``), so the scene-plan compiler and the engine never disagree about where a thing is.

One Node call answers a whole plan (every distinct saancha with its parameters, every person size, every background),
and the answers are kept for the life of the process, so the director's check loop pays for each box once. Node is part
of every place the compiler runs (the VM installs it with the Codex CLI, GitHub runners carry it, the render needs it);
without it the box checks cannot run and the compiler says so (fail closed), never silently passing a plan.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "tools" / "saancha_boxes.mjs"

_items: dict = {}
_persons: dict = {}
_zones: dict = {}
_worlds: dict = {}


class BoxesUnavailable(RuntimeError):
    """The engine's measure could not run (no Node, or the tool failed)."""


def _key(v) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)


def node_path() -> str | None:
    return os.environ.get("BIE_NODE") or shutil.which("node")


def measure(items=(), persons=(), bgs=(), worlds=()) -> None:
    """Measure everything not yet known in one Node call: ``items`` [{draw, p}], ``persons`` [{h, look}],
    ``bgs`` [names], ``worlds`` [world p]."""
    need_items = {}
    for it in items:
        k = _key(it)
        if k not in _items:
            need_items[k] = {"draw": it["draw"], "p": it.get("p") or {}}
    need_persons = {}
    for pr in persons:
        k = _key(pr)
        if k not in _persons:
            need_persons[k] = pr
    need_bgs = sorted({b for b in bgs if b and b not in _zones})
    need_worlds = {}
    for w in worlds:
        k = _key(w)
        if k not in _worlds:
            need_worlds[k] = w
    if not (need_items or need_persons or need_bgs or need_worlds):
        return
    node = node_path()
    if not node:
        raise BoxesUnavailable("the box rule needs Node to measure the engine's drawings (node not found; set BIE_NODE)")
    req = {"items": list(need_items.values()), "persons": list(need_persons.values()), "bgs": need_bgs,
           "worlds": list(need_worlds.values())}
    try:
        done = subprocess.run([node, str(TOOL)], input=json.dumps(req, ensure_ascii=False), capture_output=True,
                              text=True, timeout=120, cwd=str(ROOT))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BoxesUnavailable(f"the box measure did not run: {exc}") from None
    if done.returncode != 0:
        raise BoxesUnavailable(f"the box measure failed: {(done.stderr or '')[-400:]}")
    out = json.loads(done.stdout or "{}")
    for k, v in zip(need_items, out.get("items") or []):
        _items[k] = v
    for k, v in zip(need_persons, out.get("persons") or []):
        _persons[k] = v
    for b in need_bgs:
        _zones[b] = (out.get("zones") or {}).get(b) or []
    for k, v in zip(need_worlds, out.get("worlds") or []):
        _worlds[k] = v


def item(draw: str, p: dict | None = None) -> dict:
    it = {"draw": draw, "p": p or {}}
    measure(items=[it])
    return _items[_key(it)]


def person(h: float = 440, look=None) -> dict:
    pr = {"h": h, "look": look or "villager"}
    measure(persons=[pr])
    return _persons[_key(pr)]


def zones(bg: str | None) -> list:
    if not bg:
        return []
    measure(bgs=[bg])
    return _zones.get(bg) or []


def world_zones(p: dict | None) -> list:
    w = p or {}
    measure(worlds=[w])
    return _worlds[_key(w)]
