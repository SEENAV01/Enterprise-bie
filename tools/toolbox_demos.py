"""Render and check the toolbox proof clips (Task 046a).

    python tools/toolbox_demos.py --batch 1 --out <folder> [--only id,id] [--keep-going]

For every demo of the batch (bie/toolbox/demos.py): compute and fetch its data, render a 3–5 s silent MP4 with BIE's
preview renderer (the toolbox bundle; Manim for the offline demo), take six stills for a contact sheet, check the
clip (not blank, something moves, the right length) and write ``<out>/<demo>/receipt.json`` with the versions of the
tools it proves, compared with the registry. ``<out>/RESULTS.json`` sums up; the exit code is 1 when any demo fails.
Needs the toolbox Python extras, the web packages (tools/toolbox_setup.py) on NODE_PATH, Chromium (Playwright) and ffmpeg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.brain.video import render  # noqa: E402
from bie.toolbox import demos as demo_module  # noqa: E402
from bie.toolbox import registry as registry_module  # noqa: E402
from bie.toolbox.adapters.base import PROGRAMS, PYTHON_TOOLS, installed_version  # noqa: E402

SHEET_AT = (0.06, 0.24, 0.42, 0.6, 0.78, 0.96)
WEB = json.loads((ROOT / "bie" / "toolbox" / "web_packages.json").read_text(encoding="utf-8"))


def npm_version(package: str) -> str | None:
    base = os.environ.get("NODE_PATH", "")
    path = Path(base, *package.split("/"), "package.json")
    try:
        return json.loads(path.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return None


def tool_versions(tool_ids, box) -> dict:
    out = {}
    for tid in tool_ids:
        tool = box.tool(tid)
        if tid in PYTHON_TOOLS or tid in PROGRAMS:
            found = installed_version(tid)
        elif tid in WEB["tool_packages"]:
            found = npm_version(WEB["tool_packages"][tid])
        else:
            found = None                       # an asset source or BIE's own blocks: no package to read
        out[tid] = {"registry": tool.version, "installed": found,
                    "matches": None if found is None else (found == tool.version or found.startswith(tool.version))}
    return out


def ffprobe_seconds(path: Path) -> float:
    done = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True)
    return float(done.stdout.strip() or 0)


def frame_at(path: Path, seconds: float, out: Path) -> bytes:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{seconds:.3f}", "-i", str(path), "-frames:v", "1", str(out)], check=True)
    return out.read_bytes()


def checks(pngs: list) -> dict:
    from PIL import Image, ImageChops, ImageStat
    import io
    images = [Image.open(io.BytesIO(p)).convert("L").resize((480, 270)) for p in pngs]
    spread = [round(ImageStat.Stat(im).stddev[0], 2) for im in images]
    motion = round(ImageStat.Stat(ImageChops.difference(images[0], images[-1])).mean[0], 2)
    steps = [round(ImageStat.Stat(ImageChops.difference(a, b)).mean[0], 2) for a, b in zip(images, images[1:])]
    return {"stddev": spread, "first_last_difference": motion, "step_differences": steps,
            "not_blank": all(s > 8 for s in spread), "moves": motion > 1.5 and max(steps) > 0.5}


def contact_sheet(pngs: list, labels: list, out: Path, title: str):
    from PIL import Image, ImageDraw, ImageFont
    import io
    tw, th, cols = 640, 360, 3
    rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows + 56), (6, 18, 28))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=26)
        small = ImageFont.load_default(size=20)
    except TypeError:
        font = small = ImageFont.load_default()
    draw.text((16, 14), title.replace("→", "->")[:110], fill=(242, 246, 248), font=font)      # the default font has no arrow
    for i, (png, label) in enumerate(zip(pngs, labels)):
        im = Image.open(io.BytesIO(png)).convert("RGB").resize((tw, th))
        x, y = (i % cols) * tw, 56 + (i // cols) * th
        sheet.paste(im, (x, y))
        draw.rectangle([x, y + th - 30, x + 150, y + th], fill=(6, 18, 28))      # bottom-left: titles stay readable
        draw.text((x + 8, y + th - 26), label, fill=(56, 211, 195), font=small)
    sheet.save(out, format="PNG", optimize=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_demo(demo, out: Path, *, dist: Path, opener=None) -> dict:
    folder = out / demo.id
    shutil.rmtree(folder, ignore_errors=True)
    (folder / "assets").mkdir(parents=True)
    work = demo_module.Work(folder=folder, library=AssetLibrary(folder / "assets"), opener=opener)
    started = time.time()
    built = demo.build(work)
    mp4 = folder / "demo.mp4"
    if demo.kind == "manim":
        duration = ffprobe_seconds(mp4)
        pngs = [frame_at(mp4, duration * f, folder / f"still-{i}.png") for i, f in enumerate(SHEET_AT)]
        labels = [f"{duration * f:.1f} s" for f in SHEET_AT]
    else:
        spec = built
        (folder / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        total = sum(s["duration"] for s in spec["scenes"])
        frames = [min(total - 1, int(round(total * f))) for f in SHEET_AT]
        pngs = render.stills(spec, frames, dist=dist, assets=folder / "assets", out_dir=folder / "stills")
        render.mp4(spec, mp4, dist=dist, assets=folder / "assets")
        labels = [f"{f / spec['fps']:.1f} s" for f in frames]
        duration = ffprobe_seconds(mp4)
    contact_sheet(pngs, labels, folder / "contact_sheet.png", f"{demo.id} · {demo.title}")
    found = checks(pngs)
    found["length_ok"] = abs(duration - demo.seconds) <= 0.35 and 3.0 <= duration <= 5.5
    if demo.rules:                                      # Task 046: the benchmark rules the clip serves, read off its stills
        from bie.brain.video import frame_checks
        found["rules"] = frame_checks.demo_rules(pngs, demo.rules, accent=work.notes.get("accent"))
    return {"demo": demo.id, "title": demo.title, "batch": demo.batch, "kind": demo.kind, "tools": list(demo.tools),
            "capabilities": list(demo.capabilities), "seconds": round(duration, 2), "mp4_bytes": mp4.stat().st_size,
            "mp4_sha256": sha(mp4), "checks": found, "notes": work.notes, "render_seconds": round(time.time() - started, 1),
            "assets": [{"id": a.asset_id, "title": a.title, "licence": a.licence, "source": a.source, "credit": a.credit, "tags": a.tags,
                        "author": a.author, "licence_url": a.licence_url, "page_url": a.page_url}
                       for a in work.library.assets.values()],
            "blocks": demo_module.spec_blocks(built if demo.kind != "manim" else None)}


def chromium_path() -> str:
    """Chrome Headless Shell as Playwright installs it (the same Chromium build the preview renderer uses); Remotion's
    renderer needs the headless shell, because full Chrome no longer has the old headless mode."""
    roots = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "", str(Path.home() / ".cache" / "ms-playwright")]
    for root in filter(None, roots):
        found = sorted(Path(root).glob("chromium_headless_shell-*/chrome-*/headless_shell"))
        if found:
            return str(found[-1])
    return ""


def bridge(demo_id: str, out: Path) -> dict:
    """Render an already rendered web demo again with real Remotion (@remotion/bundler + @remotion/renderer) and compare
    the frames with the preview path's frames: the same blocks must give the same picture."""
    from PIL import Image, ImageChops, ImageStat
    folder = out / demo_id
    spec = json.loads((folder / "spec.json").read_text(encoding="utf-8"))
    lite = sorted((folder / "stills").glob("frame-*.png"))
    frames = [int(p.stem.split("-")[1]) for p in lite]
    script = ROOT / "bie" / "brain" / "video" / "remotion" / "render.mjs"
    started = time.time()
    browser = chromium_path()
    if browser:
        # Chromium now needs --enable-unsafe-swiftshader for software WebGL, and Remotion has no option for extra
        # browser flags; a two-line wrapper adds it (the same flag the preview renderer passes).
        wrapper = folder / "headless_shell_webgl.sh"
        wrapper.write_text(f'#!/bin/sh\nexec "{browser}" --enable-unsafe-swiftshader --ignore-gpu-blocklist "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
        browser = str(wrapper)
    done = subprocess.run(["node", str(script), "--spec", str(folder / "spec.json"), "--public", str(folder), "--out", str(folder / "bridge.mp4"),
                           "--frames", ",".join(map(str, frames)), "--stills", str(folder / "bridge_stills")]
                          + (["--browser", browser] if browser else []), capture_output=True, text=True, timeout=3600)
    row = {"demo": demo_id, "renderer": "remotion " + (npm_version("remotion") or "?"), "frames": frames,
           "render_seconds": round(time.time() - started, 1)}
    if done.returncode != 0:
        row.update(passed=False, error=(done.stderr or done.stdout)[-1500:])
        return row
    diffs, pngs = [], []
    for f, path in zip(frames, lite):
        real = folder / "bridge_stills" / f"frame-{f:06d}.png"
        a = Image.open(path).convert("L").resize((480, 270))
        b = Image.open(real).convert("L").resize((480, 270))
        diffs.append(round(ImageStat.Stat(ImageChops.difference(a, b)).mean[0], 2))
        pngs += [path.read_bytes(), real.read_bytes()]
    contact_sheet(pngs, [f"{lbl} {f / spec['fps']:.1f} s" for f in frames for lbl in ("lite", "remotion")],
                  folder / "bridge_sheet.png", f"{demo_id}: preview path (left) and real Remotion (right), same frames")
    seconds = ffprobe_seconds(folder / "bridge.mp4")
    row.update(mean_differences=diffs, seconds=round(seconds, 2), passed=max(diffs) < 8.0 and abs(seconds - sum(s["duration"] for s in spec["scenes"]) / spec["fps"]) < 0.2)
    return row


def claims(box, batch: int, results: list, selected: set | None = None) -> list:
    """Tools the registry calls demo_proven (or better) whose proof demos did not pass in this run of the whole batch (or of
    the group of it that was selected): a status word is a claim, and the demos lane checks it every time."""
    passed = {r["demo"] for r in results if r.get("passed")}
    proven = registry_module.STATUS_RANK["demo_proven"]
    wrong = []
    for tool in box.batch(batch):
        if registry_module.STATUS_RANK.get(tool.status, 0) >= proven:
            failed = [d for d in tool.proof.get("demos", []) if d not in passed and (selected is None or d in selected)]
            if failed:
                wrong.append(f"{tool.id} is {tool.status} but its demo did not pass: {', '.join(failed)}")
    return wrong


def annotate(results: list):
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    for r in results:
        if not r.get("passed"):
            text = str(r.get("error") or r.get("checks") or "failed").replace("%", "%25").replace("\n", "%0A")[:3000]
            print(f"::error title=Toolbox demo {r['demo']}::{text}", flush=True)
    print(f"::notice title=Toolbox demos::{sum(1 for r in results if r.get('passed'))} of {len(results)} passed", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--batch", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", default="")
    parser.add_argument("--dist", type=Path, help="toolbox preview build folder (default <out>/_dist)")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--bridge", default="", help="render this already rendered demo again with real Remotion and compare")
    parser.add_argument("--group", choices=("all", "main", "bench"), default="all",
                        help="bench = the Task 046 benchmark-block clips (ids bench-*), main = the rest; the lane renders the two groups of batch 1 side by side")
    args = parser.parse_args(argv)
    if args.bridge:
        row = bridge(args.bridge, args.out)
        (args.out / args.bridge / "bridge.json").write_text(json.dumps(row, indent=1), encoding="utf-8")
        print(json.dumps({k: row.get(k) for k in ("demo", "passed", "mean_differences", "render_seconds", "error")}), flush=True)
        annotate([row])
        return 0 if row["passed"] else 1
    if args.batch is None:
        parser.error("--batch is required unless --bridge is given")
    box = registry_module.load()
    wanted = [d for d in demo_module.DEMOS if d.batch == args.batch and (not args.only or d.id in args.only.split(","))
              and (args.group == "all" or (args.group == "bench") == d.id.startswith("bench-"))]
    if not wanted:
        print("no demo selected", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    dist = render.build_preview(args.dist or args.out / "_dist", toolbox=True)
    results = []
    for demo in wanted:
        try:
            row = run_demo(demo, args.out, dist=dist)
            row["versions"] = tool_versions(demo.tools, box)
            mismatched = [t for t, v in row["versions"].items() if v["matches"] is False]
            rules_failed = (row["checks"].get("rules") or {}).get("failed") or {}
            row["passed"] = row["checks"]["not_blank"] and row["checks"]["moves"] and row["checks"]["length_ok"] and not mismatched and not rules_failed
            row["lesson_use"] = demo_module.lesson_use(demo.tools, row["assets"], row["blocks"], box=box)   # Task 046a-L
            if mismatched:
                row["error"] = "installed version differs from the registry: " + ", ".join(mismatched)
            elif rules_failed:
                row["error"] = "rule check failed: " + "; ".join(f"{k}: {v}" for k, v in rules_failed.items())
        except Exception as exc:
            row = {"demo": demo.id, "title": demo.title, "batch": demo.batch, "tools": list(demo.tools), "passed": False,
                   "error": f"{type(exc).__name__}: {exc}"[:1500], "trace": traceback.format_exc()[-3000:]}
        (args.out / demo.id).mkdir(parents=True, exist_ok=True)
        (args.out / demo.id / "receipt.json").write_text(json.dumps(row, indent=1, ensure_ascii=False), encoding="utf-8")
        results.append(row)
        print(json.dumps({k: row.get(k) for k in ("demo", "passed", "seconds", "render_seconds", "error")}), flush=True)
        if not row["passed"] and not args.keep_going:
            break
    wrong = [] if args.only else claims(box, args.batch, results, selected={d.id for d in wanted})
    for line in wrong:
        print(("::error title=Toolbox status claim::" if os.environ.get("GITHUB_ACTIONS") == "true" else "CLAIM NOT PROVEN: ") + line, flush=True)
    summary = {"schema": "bie.toolbox.demo-results/1", "batch": args.batch, "registry_version": box.version,
               "passed": all(r["passed"] for r in results) and len(results) == len(wanted) and not wrong, "claims_not_proven": wrong,
               "demos": len(wanted), "rendered": len(results), "failed": [r["demo"] for r in results if not r["passed"]],
               "results": results}
    (args.out / "RESULTS.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    annotate(results)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
