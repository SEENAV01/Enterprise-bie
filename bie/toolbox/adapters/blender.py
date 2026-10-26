"""Blender (headless) as BIE's offline model builder, route C of Task 046 (Task 046a).

Blender runs in its own process, never inside BIE's process: with the ``bpy`` wheel (``pip install -e
'.[toolbox-blender]'``, Python 3.13) through the same interpreter, or with a Blender program named by
``BIE_BLENDER`` (``blender -b --python script -- args``). Scripts live in ``bie/toolbox/blender/``; each prints one
``BIE_BLENDER_RESULT {json}`` line that becomes the asset record.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .base import Unavailable

SCRIPTS = Path(__file__).resolve().parents[1] / "blender"


def command(script: str, args: list) -> list:
    path = str(SCRIPTS / script)
    program = os.environ.get("BIE_BLENDER") or ""
    if program:
        return [program, "-b", "--factory-startup", "--python", path, "--", *args]
    if importlib.util.find_spec("bpy") is not None:
        return [sys.executable, "-B", path, *args]
    found = shutil.which("blender")
    if found:
        return [found, "-b", "--factory-startup", "--python", path, "--", *args]
    raise Unavailable("Blender is not installed: pip install -e '.[toolbox-blender]' (bpy) or set BIE_BLENDER")


def run(script: str, args: list, *, timeout: int = 900) -> dict:
    try:
        done = subprocess.run(command(script, args), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Blender script {script} did not finish in {timeout} s") from None
    lines = [l for l in done.stdout.splitlines() if l.startswith("BIE_BLENDER_RESULT ")]
    if done.returncode != 0 or not lines:
        raise RuntimeError(f"Blender script {script} failed ({done.returncode}): " + (done.stderr or done.stdout)[-600:])
    return json.loads(lines[-1].split(" ", 1)[1])


def cell_sheet(out: str | Path, *, kind: str = "columnar", rows: int = 5, cols: int = 7, seed: int = 7) -> dict:
    """Build an epithelial cell sheet and export it as a .glb file; returns the record (cells, size, Blender version)."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    info = run("cell_sheet.py", ["--out", str(out), "--kind", kind, "--rows", str(rows), "--cols", str(cols), "--seed", str(seed)])
    if not out.exists() or out.read_bytes()[:4] != b"glTF":
        raise RuntimeError("Blender did not write a glTF binary")
    return dict(info, bytes=out.stat().st_size)


def fbx_part(fbx: str | Path, match: str, out: str | Path, *, exclude: str = "", max_objects: int = 400, timeout: int = 1800,
             group: str = "", min_vertices: int = 0) -> dict:
    """Keep the meshes of an FBX (for example a Z-Anatomy body system) whose names match, as a centred .glb; with
    ``group`` (a regular expression on parent names) one joined object per matching parent (a brain's lobes)."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    args = ["--fbx", str(fbx), "--match", match, "--out", str(out), "--max-objects", str(max_objects)]
    if exclude:
        args += ["--exclude", exclude]
    if group:
        args += ["--group", group]
    if min_vertices:
        args += ["--min-vertices", str(min_vertices)]
    info = run("fbx_part.py", args, timeout=timeout)
    if not out.exists():
        raise RuntimeError("Blender did not write the part")
    return dict(info, bytes=out.stat().st_size)


def epithelium_studio(out: str | Path, params: dict | None = None, *, stills: list | None = None, timeout: int = 7200) -> dict:
    """Render an epithelium shot the studio way (Task 046 one-shot test, Route 1): organic Voronoi cells with subsurface
    scattering, nucleus domes, basement membrane and fibres, a capillary behind, key and rim light, mist haze, depth of
    field, a push-in and particles crossing (``bie/toolbox/blender/epithelium_studio.py``; presets in
    ``epithelium_studio.json``). Writes ``frames/f0001.png``…, ``anchors.json`` (per-frame label anchor points) and
    ``record.json`` into ``out``; returns the record (cells, seconds per frame, samples). ``stills``: only these frames."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    args = ["--out", str(out)]
    if params:
        (out / "params.json").write_text(json.dumps(params), encoding="utf-8")
        args += ["--params", str(out / "params.json")]
    if stills:
        args += ["--stills", ",".join(str(int(f)) for f in stills)]
    info = run("epithelium_studio.py", args, timeout=timeout)
    if not (out / "anchors.json").exists():
        raise RuntimeError("the epithelium recipe wrote no anchors.json")
    return info
