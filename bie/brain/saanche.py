"""The saancha library (Phase 1, part B1; agreement of 3 November 2026, decision 2: assets are parametric saanche).

One manifest, ``bie/brain/video/engine/saanche.json`` (``bie.saancha-manifest/1``), names every drawing the showing
engine can make: its anchor, its parameters with types, defaults and limits, and its Hindi and English words. This
module is the Python side: the director searches it to plan, the scene-plan compiler (part B2) validates every
``p`` against it, and the CI still sheet draws every entry. The drawn saanche and the Fluent Emoji icons (MIT,
``bie/toolbox/icons.py``) are one searchable library: ``search()`` returns both, each row saying ``draw`` or ``asset``.

A new saancha is a reviewed change to ``draw.mjs`` plus its manifest entry; the tests refuse a registry and manifest
that disagree, and the manifest never names a drawing the engine cannot make.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent / "video" / "engine" / "saanche.json"
TYPES = ("number", "int", "text", "bool", "color", "choice")
_COLOR = re.compile(r"^#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?$")


FAMILIES_DIR = MANIFEST_PATH.parent / "saanche.d"       # one manifest file per family of saanche (families/<name>.mjs)


@lru_cache(maxsize=4)
def manifest(path: str | Path = MANIFEST_PATH) -> dict:
    """The manifest; the main file also takes in every family file of ``saanche.d/`` (a family of drawings built
    together, e.g. for one book, ships its own manifest beside its own ``families/<name>.mjs`` so families never edit
    the same lines). A name defined twice is refused."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    from bie.brain import formats
    formats.check("saancha_manifest", data, where=str(path))
    if Path(path) == MANIFEST_PATH and FAMILIES_DIR.is_dir():
        data = dict(data, saanche=dict(data["saanche"]))
        for fam in sorted(FAMILIES_DIR.glob("*.json")):
            extra = json.loads(fam.read_text(encoding="utf-8"))
            formats.check("saancha_manifest", extra, where=str(fam))
            for name, entry in extra["saanche"].items():
                if name in data["saanche"]:
                    raise formats.FormatError(f"{fam}: saancha '{name}' is already defined")
                data["saanche"][name] = entry
    for name, entry in data["saanche"].items():                 # the schema leaves nested objects loose; check them here
        for key in ("anchor", "what", "tags", "params", "since"):
            if key not in entry:
                raise formats.FormatError(f"{path}: saancha '{name}' misses '{key}'")
        if entry["anchor"] not in ("bottom", "center"):
            raise formats.FormatError(f"{path}: saancha '{name}': anchor must be bottom or center")
        for pname, spec in entry["params"].items():
            if spec.get("type") not in TYPES:
                raise formats.FormatError(f"{path}: {name}.{pname}: type must be one of {', '.join(TYPES)}")
            if "default" not in spec or (spec["type"] == "choice") != ("choices" in spec):
                raise formats.FormatError(f"{path}: {name}.{pname}: a default is needed, and choices exactly for a choice")
    return data


def names(path: str | Path = MANIFEST_PATH) -> list:
    return sorted(manifest(path)["saanche"])


def get(name: str, path: str | Path = MANIFEST_PATH) -> dict | None:
    return manifest(path)["saanche"].get(name)


def problems(name: str, p: dict | None, path: str | Path = MANIFEST_PATH) -> list:
    """Why ``drawSaancha(name, p)`` would be wrong: unknown saancha, unknown parameter, wrong type, out of limits.

    The scene-plan compiler refuses a plan on these, each message naming the exact field, so the director can fix it.
    """
    entry = get(name, path)
    if entry is None:
        close = [n for n in names(path) if n.lower().startswith(name[:3].lower())][:3]
        return [f"no saancha '{name}'" + (f" (near: {', '.join(close)})" if close else "")]
    out = []
    params = entry["params"]
    for key, value in (p or {}).items():
        spec = params.get(key)
        if spec is None:
            out.append(f"{name}: no parameter '{key}' (it has: {', '.join(sorted(params))})")
            continue
        kind = spec["type"]
        if kind in ("number", "int"):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                out.append(f"{name}.{key}: a number is needed, not {value!r}")
            elif kind == "int" and int(value) != value:
                out.append(f"{name}.{key}: a whole number is needed, not {value!r}")
            elif "min" in spec and value < spec["min"] or "max" in spec and value > spec["max"]:
                out.append(f"{name}.{key}: {value} is outside {spec.get('min', '')}..{spec.get('max', '')}")
        elif kind == "bool":
            if not isinstance(value, bool):
                out.append(f"{name}.{key}: true or false is needed, not {value!r}")
        elif kind == "choice":
            if value not in spec["choices"]:
                out.append(f"{name}.{key}: {value!r} is not one of {', '.join(spec['choices'])}")
        elif kind == "color":
            if value and not (isinstance(value, str) and _COLOR.match(value)):
                out.append(f"{name}.{key}: a #rrggbb colour is needed, not {value!r}")
        elif kind == "text":
            if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                out.append(f"{name}.{key}: text or a number is needed, not {value!r}")
    return out


def _hit(words: list, hay: str) -> int:
    return sum(1 for w in words if w and w in hay)


def search(query: str, *, limit: int = 8, icons_limit: int = 4, path: str | Path = MANIFEST_PATH) -> list:
    """The library rows that fit ``query`` (Hindi or English): drawn saanche first, then Fluent Emoji icons.

    A drawn row: {"kind": "draw", "name", "what", "anchor", "params"}; an asset row: {"kind": "asset", "id", ...}
    as ``bie.toolbox.icons.search`` gives it. The director shows BIE's own drawings before fetched pictures
    (library-first, Navin's decision of 29 October 2026).
    """
    words = [w.lower() for w in re.split(r"[\s,/|]+", str(query)) if w]
    rows = []
    for name, entry in manifest(path)["saanche"].items():
        hay = " ".join([name.lower(), entry["what"].lower(), *[t.lower() for t in entry["tags"]]])
        score = _hit(words, hay) + (2 if any(w == name.lower() for w in words) else 0)
        if score:
            rows.append((score, {"kind": "draw", "name": name, "what": entry["what"], "anchor": entry["anchor"],
                                 "params": entry["params"]}))
    rows.sort(key=lambda r: (-r[0], r[1]["name"]))
    out = [row for _, row in rows[:limit]]
    if icons_limit:
        from bie.toolbox import icons
        for row in icons.search(query, limit=icons_limit):
            out.append({"kind": "asset", **row})
    return out
