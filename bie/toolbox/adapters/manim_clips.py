"""Manim as BIE's offline renderer for maths and physics clips (Task 046a).

``render(scene, params, out)`` writes the scene's parameters to a JSON file, runs Manim in its own process and moves
the finished MP4 to ``out``. Manim needs Cairo and Pango on the machine (apt: libcairo2-dev libpango1.0-dev) and is
installed with ``pip install -e '.[toolbox-manim]'``.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .base import Unavailable

SCENES = Path(__file__).resolve().parents[1] / "manim_scenes.py"


def render(scene: str, params: dict, out: str | Path, *, width: int = 1280, height: int = 720, fps: int = 30, timeout: int = 900) -> dict:
    if importlib.util.find_spec("manim") is None:
        raise Unavailable("Manim is not installed: pip install -e '.[toolbox-manim]' (needs Cairo and Pango)")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bie-manim-") as work:
        work = Path(work)
        (work / "params.json").write_text(json.dumps(params), encoding="utf-8")
        cmd = [sys.executable, "-m", "manim", "render", "-r", f"{width},{height}", "--fps", str(fps), "--format", "mp4",
               "--media_dir", str(work / "media"), "-o", "clip", "--disable_caching", str(SCENES), scene]
        try:
            done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=work,
                                  env={**__import__("os").environ, "BIE_MANIM_PARAMS": str(work / "params.json")})
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Manim did not finish in {timeout} s") from None
        found = sorted((work / "media").rglob("clip.mp4"))
        if done.returncode != 0 or not found:
            raise RuntimeError("Manim failed: " + (done.stderr or done.stdout)[-800:])
        shutil.move(str(found[0]), out)
    import manim
    return {"scene": scene, "out": str(out), "bytes": out.stat().st_size, "width": width, "height": height, "fps": fps,
            "manim": manim.__version__}
