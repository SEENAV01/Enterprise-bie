"""Python side of the preview renderer: bundle once, then take stills or a quick MP4 of a VideoSpec.

Needs Node with react, react-dom and playwright (Chromium) on NODE_PATH, plus esbuild (``ESBUILD`` or on PATH)
and ffmpeg for MP4s. In GitHub Actions the workflow installs them; in the cloud workspace they are present.
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIEW = HERE / "preview"


class RenderError(RuntimeError):
    pass


def _node_env():
    env = dict(os.environ)
    if "NODE_PATH" not in env:
        try:
            env["NODE_PATH"] = subprocess.check_output(["npm", "root", "-g"], text=True).strip()
        except (OSError, subprocess.CalledProcessError):
            pass
    return env


TOOLBOX_FILES = ("toolbox.html", "toolbox.js", "toolbox.css")
ENGINE_FILES = ("engine.html", "engine.js")


def needs_toolbox(spec: dict) -> bool:
    """True when a scene uses a toolbox block (Task 046a), which only the toolbox bundle can draw."""
    return any(layer.get("type") == "block" for scene in spec.get("scenes", []) for layer in scene.get("layers", []))


def needs_engine(spec: dict) -> bool:
    """True for a show-spec (bie.show-spec/1, Phase 1): the showing engine's own page draws it."""
    if str(spec.get("schema", "")).startswith("bie.show-spec"):
        return True
    scenes = spec.get("scenes") or []
    return bool(scenes and "els" in scenes[0] and "subs" in spec)


def total_frames(spec: dict) -> int:
    """Frames of either spec shape: a show-spec carries seconds, a VideoSpec carries per-scene frames."""
    if "duration" in spec:
        return int(round(float(spec["duration"]) * (spec.get("fps") or 30)))
    return sum(int(s.get("duration") or 0) for s in spec.get("scenes") or [])


def build_preview(dist: str | Path, *, toolbox: bool = False, engine: bool = False) -> Path:
    dist = Path(dist)
    if (dist / "bundle.js").exists() and (not toolbox or (dist / "toolbox.js").exists()) and (not engine or (dist / "engine.js").exists()):
        return dist
    flags = (["--toolbox"] if toolbox else []) + (["--engine"] if engine else [])
    try:
        run = subprocess.run(["node", str(PREVIEW / "build.mjs"), str(dist)] + flags,
                             capture_output=True, text=True, env=_node_env(), timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RenderError(f"preview build could not run: {exc}") from None
    if run.returncode != 0:
        raise RenderError("preview build failed: " + (run.stderr or run.stdout)[-800:])
    return dist


def _workdir(dist: Path, assets: str | Path | None) -> Path:
    work = Path(tempfile.mkdtemp(prefix="bie-preview-"))
    for name in ("index.html", "bundle.js") + TOOLBOX_FILES + ENGINE_FILES:
        if (dist / name).exists():
            shutil.copy2(dist / name, work / name)
    if assets and Path(assets).exists():
        shutil.copytree(assets, work / "assets", dirs_exist_ok=True)
    return work


def _page(toolbox: bool, engine: bool = False) -> list:
    if engine:
        return ["--page", "engine.html"]
    return ["--page", "toolbox.html"] if toolbox else []


def stills(spec: dict, frames, *, dist: str | Path, assets: str | Path | None = None, out_dir: str | Path | None = None,
           toolbox: bool | None = None):
    """PNG bytes of the given frames of ``spec`` (a VideoSpec), in order."""
    toolbox = needs_toolbox(spec) if toolbox is None else toolbox
    engine = needs_engine(spec)
    dist = build_preview(dist, toolbox=toolbox, engine=engine)
    work = _workdir(dist, assets)
    try:
        (work / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        target = Path(out_dir) if out_dir else work / "stills"
        try:
            run = subprocess.run(["node", str(PREVIEW / "stills.mjs"), "--dist", str(work), "--spec", str(work / "spec.json"),
                                  "--frames", ",".join(str(int(f)) for f in frames), "--out", str(target)] + _page(toolbox, engine),
                                 capture_output=True, text=True, env=_node_env(), timeout=600)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RenderError(f"stills could not run: {exc}") from None
        if run.returncode != 0:
            raise RenderError("stills failed: " + (run.stderr or run.stdout)[-800:])
        return [(target / f"frame-{int(f):06d}.png").read_bytes() for f in frames]
    finally:
        shutil.rmtree(work, ignore_errors=True)


def audit(spec: dict, *, dist: str | Path, assets: str | Path | None = None, every: int = 30, first: int | None = None,
          last: int | None = None, toolbox: bool | None = None, timeout: int = 3600) -> list:
    """The text measurements of every ``every``-th frame of ``spec`` (``preview/audit.mjs``; ``text_audit.summarize`` reads them)."""
    toolbox = needs_toolbox(spec) if toolbox is None else toolbox
    engine = needs_engine(spec)
    dist = build_preview(dist, toolbox=toolbox, engine=engine)
    work = _workdir(dist, assets)
    try:
        (work / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        cmd = ["node", str(PREVIEW / "audit.mjs"), "--dist", str(work), "--spec", str(work / "spec.json"),
               "--out", str(work / "audit.jsonl"), "--every", str(int(every))] + _page(toolbox, engine)
        if first is not None:
            cmd += ["--from", str(int(first))]
        if last is not None:
            cmd += ["--to", str(int(last))]
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, env=_node_env(), timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RenderError(f"text audit could not run: {exc}") from None
        if run.returncode != 0:
            raise RenderError("text audit failed: " + (run.stderr or run.stdout)[-800:])
        lines = (work / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]
    finally:
        shutil.rmtree(work, ignore_errors=True)


def mp4(spec: dict, out: str | Path, *, dist: str | Path, assets: str | Path | None = None, audio: str | Path | None = None,
        timeout: int = 7200, toolbox: bool | None = None):
    toolbox = needs_toolbox(spec) if toolbox is None else toolbox
    engine = needs_engine(spec)
    dist = build_preview(dist, toolbox=toolbox, engine=engine)
    work = _workdir(dist, assets)
    try:
        (work / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        args = ["node", str(PREVIEW / "stills.mjs"), "--dist", str(work), "--spec", str(work / "spec.json"),
                "--mp4", str(Path(out).resolve())] + _page(toolbox, engine)
        if audio:
            args += ["--audio", str(Path(audio).resolve())]
        try:
            run = subprocess.run(args, capture_output=True, text=True, env=_node_env(), timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RenderError(f"mp4 could not run: {exc}") from None
        if run.returncode != 0:
            raise RenderError("mp4 failed: " + (run.stderr or run.stdout)[-800:])
        return Path(out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def mp4_range(spec: dict, out: str | Path, first: int, last: int, *, dist: str | Path, assets: str | Path | None = None,
              timeout: int = 7200, toolbox: bool | None = None):
    """Frames [first, last) of ``spec`` as one MP4 part (Task 046: a long video rendered in chunks on several runners)."""
    toolbox = needs_toolbox(spec) if toolbox is None else toolbox
    engine = needs_engine(spec)
    dist = build_preview(dist, toolbox=toolbox, engine=engine)
    work = _workdir(dist, assets)
    try:
        (work / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        args = ["node", str(PREVIEW / "stills.mjs"), "--dist", str(work), "--spec", str(work / "spec.json"),
                "--mp4", str(Path(out).resolve()), "--from", str(int(first)), "--to", str(int(last))] + _page(toolbox, engine)
        try:
            run = subprocess.run(args, capture_output=True, text=True, env=_node_env(), timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RenderError(f"mp4 chunk could not run: {exc}") from None
        if run.returncode != 0:
            raise RenderError("mp4 chunk failed: " + (run.stderr or run.stdout)[-800:])
        return Path(out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def small_jpeg(png: bytes, width: int = 960, quality: int = 85) -> bytes:
    """A smaller JPEG of a still, so a reviewer can look at several frames in one request."""
    from PIL import Image

    image = Image.open(io.BytesIO(png)).convert("RGB")
    if image.width > width:
        image = image.resize((width, round(image.height * width / image.width)))
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()
