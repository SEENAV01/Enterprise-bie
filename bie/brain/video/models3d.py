"""The 3D layer's Python side (Navin, 5 November 2026: "3d models objects duniya process bna sakte ho aise format mein
jinme bie scene plan ke hisab se modify karke use kar sake").

A 3D model is a parametric procedural model of the showing engine's 3D layer (``engine/three/``): a place (a factory
floor, a port, a city, a farm, a bank vault, an exchange floor) or a model of an idea (a globe with trade routes, the
utility hill, the container cube), drawn by code from three.js primitives. Its manifest,
``engine/three/models3d.json``, has the saancha manifest's format (``bie.saancha-manifest/1``: parameters with types,
defaults and limits, Hindi and English words), so the same law checks it (``saanche.problems``). A scene plan uses one
as the scene's place (``world3d``: a backdrop under the SVG people, things and words) or as a thing (an ``item`` whose
thing is ``{"model": name, "p": {...}}``), changes its parameters on cue words (``steps``), moves its 3D camera
(``cam3d``) and puts people and words beside its parts (``at: {"of", "spot"}``).

Spots, boxes and zones come from the very description the engine draws (``tools/model3d_measure.mjs``), one Node call
per batch, kept for the life of the process, like ``boxes.py``. Without Node the compiler says so (fail closed).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from bie.brain import saanche
from bie.brain.video import boxes

ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = Path(__file__).resolve().parent / "engine" / "three" / "models3d.json"
TOOL = ROOT / "tools" / "model3d_measure.mjs"
CAM_LIMITS = {"angle": (-1440, 1440), "height": (-100, 300), "dist": (0, 400), "tx": (-300, 300), "ty": (-300, 300),
              "tz": (-300, 300), "fov": (10, 100), "spin": (-90, 90), "d": (0, 30)}
STEP_FIELDS = {"t", "p", "d"}
PLACE_SIZE = (1920, 1080)

_measures: dict = {}
_checks: dict = {}


class ModelsUnavailable(RuntimeError):
    """The 3D measure could not run (no Node, or the tool failed)."""


def manifest() -> dict:
    return saanche.manifest(MANIFEST_PATH)


def names() -> list:
    return sorted(manifest()["saanche"])


def get(name: str) -> dict | None:
    return manifest()["saanche"].get(name)


def size_of(name: str) -> tuple:
    entry = get(name) or {}
    w, h = entry.get("size") or PLACE_SIZE
    return float(w), float(h)


def problems(name, p) -> list:
    """Why a model's parameters are wrong: unknown model, unknown parameter, wrong type, out of limits (the manifest)."""
    if not isinstance(name, str) or get(name) is None:
        return [f"no 3D model '{name}' (models: {', '.join(names())})"]
    if p is not None and not isinstance(p, dict):
        return [f"{name}: p must be an object of parameters, not {p!r}"]
    return saanche.problems(name, p or {}, path=MANIFEST_PATH)


def cam_problems(keys, where: str) -> list:
    """A 3D camera's keys: a list of {t, d?, angle?, height?, dist?, tx?, ty?, tz?, fov?, spin?} with numbers in range."""
    if keys is None:
        return []
    if not isinstance(keys, list):
        return [f"{where}: cam3d must be a list of camera keys, not {keys!r}"]
    out = []
    for i, k in enumerate(keys):
        if not isinstance(k, dict):
            out.append(f"{where}: cam3d key {i + 1} is not an object")
            continue
        for f, v in k.items():
            if f == "t":
                continue
            if f not in CAM_LIMITS:
                out.append(f"{where}: cam3d key {i + 1}: no field '{f}' (fields: t, {', '.join(CAM_LIMITS)})")
            elif isinstance(v, bool) or not isinstance(v, (int, float)):
                out.append(f"{where}: cam3d key {i + 1}: {f} needs a number, not {v!r}")
            elif not CAM_LIMITS[f][0] <= v <= CAM_LIMITS[f][1]:
                out.append(f"{where}: cam3d key {i + 1}: {f} {v} is outside {CAM_LIMITS[f][0]}..{CAM_LIMITS[f][1]}")
        if "t" not in k:
            out.append(f"{where}: cam3d key {i + 1} has no time t")
    return out


def element_problems(el: dict, where: str) -> list:
    """Every problem of one compiled model element: its parameters and each step's, its camera, the kind's own checks."""
    name = el.get("model")
    out = [f"{where}: {p}" for p in problems(name, el.get("p"))]
    if out and (get(name) is None or not isinstance(el.get("p"), dict)):
        return out
    merged = dict(el.get("p") or {})
    for i, st in enumerate(el.get("steps") or []):
        if not isinstance(st, dict) or not isinstance(st.get("p"), dict):
            out.append(f"{where}: step {i + 1} needs p, an object of the parameters that change")
            continue
        extra = sorted(set(st) - STEP_FIELDS)
        if extra:
            out.append(f"{where}: step {i + 1}: no field {', '.join(repr(x) for x in extra)} (a step has t, p and d)")
        d = st.get("d")
        if d is not None and (isinstance(d, bool) or not isinstance(d, (int, float)) or not 0 <= d <= 30):
            out.append(f"{where}: step {i + 1}: d is the seconds the change takes, 0..30, not {d!r}")
        out += [f"{where}: step at {st.get('t')}: {p}" for p in problems(name, st["p"])]
        merged.update(st["p"])
    out += cam_problems(el.get("cam3d"), where)
    if not out:
        try:
            out += [f"{where}: {p}" for p in check(name, el.get("p") or {}) + (check(name, merged) if merged != (el.get("p") or {}) else [])]
        except ModelsUnavailable as exc:
            out.append(f"{where}: not checked: {exc}")
    return sorted(set(out), key=out.index)


# ---------------------------------------------------------------- the measure (Node, the engine's own description)


def _key(v) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)


MEASURED = ("model", "p", "steps", "cam3d", "x", "y", "w", "h", "s", "keys", "t0", "place")


def _call(req: dict) -> dict:
    node = boxes.node_path()
    if not node:
        raise ModelsUnavailable("3D models need Node to measure the engine's description (node not found; set BIE_NODE)")
    try:
        done = subprocess.run([node, str(TOOL)], input=json.dumps(req, ensure_ascii=False), capture_output=True, text=True,
                              timeout=180, cwd=str(ROOT))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ModelsUnavailable(f"the 3D measure did not run: {exc}") from None
    if done.returncode != 0:
        raise ModelsUnavailable(f"the 3D measure failed: {(done.stderr or '')[-400:]}")
    return json.loads(done.stdout or "{}")


def measure_many(pairs) -> list:
    """[(model element, t)] -> [{spots, box, zones, rect} | {error}], measured in one Node call for what is not yet known."""
    keys, need = [], {}
    for el, t in pairs:
        slim = {k: el.get(k) for k in MEASURED if el.get(k) is not None}
        k = _key([slim, round(float(t), 3)])
        keys.append(k)
        if k not in _measures and k not in need:
            need[k] = {"el": slim, "t": round(float(t), 3)}
    if need:
        got = _call({"measures": list(need.values())}).get("measures") or []
        for k, v in zip(need, got):
            _measures[k] = v
    return [_measures[k] for k in keys]


def measure(el: dict, t: float) -> dict:
    return measure_many([(el, t)])[0]


def check(name: str, p: dict) -> list:
    """The kind's own checks (a globe's region names), which the manifest's types cannot see."""
    k = _key([name, p])
    if k not in _checks:
        _checks[k] = (_call({"checks": [{"model": name, "p": p}]}).get("checks") or [[]])[0]
    return list(_checks[k])


def describe(el: dict, t: float) -> dict:
    """The engine's whole description of a model at ``t`` (nodes, spots, camera, light): the determinism tests read it."""
    return (_call({"describe": [{"el": el, "t": t}]}).get("describe") or [{}])[0]


def js_kinds() -> dict:
    return _call({"kinds": True}).get("kinds") or {}


# ---------------------------------------------------------------- the director's library


def library_text() -> str:
    """The 3D models for the director: what each is, its parameters, its spots and how a plan uses it."""
    rows = []
    for name in names():
        e = get(name)
        params = ", ".join(f"{k}:{v['type']}" + (f"[{'|'.join(v['choices'])}]" if v["type"] == "choice" else
                                                  f"[{v.get('min')}..{v.get('max')}]" if v["type"] in ("number", "int") else "")
                           for k, v in e["params"].items())
        rows.append(f"- {name} ({e.get('role', 'model')}, item size {e['size'][0]}x{e['size'][1]}): {e['what']} · p = {{{params}}} · "
                    f"spots: {', '.join(e.get('spots') or [])}")
    rows.append("Use: a scene's place with the scene field world3d {model, p, steps, cam3d}, or a thing with an item step whose thing is "
                "{model, p} (id names it for at); steps [{t, p, d}] change parameters on a cue (numbers glide d seconds); cam3d "
                "[{t, d, angle, height, dist, tx, ty, tz, fov, spin}] moves its camera; at {of, spot, dx, dy, when} puts a person, "
                "text, mark, glow or item beside a spot.")
    return "\n".join(rows)
