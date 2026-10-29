"""Render a video spec (the canvas director's ``video_specs/<video>.json``) through BIE's preview renderer, in chunks on
several runners, join the chunks into one MP4 and measure the speed (Task 046 Part C, PR 4: render speed).

    python -B tools/render_spec.py chunk --spec <video_spec.json> --out <dir> --chunk 2 --chunks 6 [--assets <dir>] [--dist <dir>]
    python -B tools/render_spec.py join --out <dir> --chunks 6 [--review 720] [--audio narration.wav]
    python -B tools/render_spec.py measure --out <dir>
    python -B tools/render_spec.py bench --spec <video_spec.json> [--frames 60] [--assets <dir>] [--dist <dir>] --out <dir> [--label before]
    python -B tools/render_spec.py summary --out <dir> [--run-id .. --sha .. --run-url ..]
    python -B tools/render_spec.py fixture --out <dir>          (the kit's two test fixtures as one ~70 s spec: the pipeline's own proof)

``chunk`` renders frames [i*N/chunks, (i+1)*N/chunks) with the preview renderer (Chromium + ffmpeg, SwiftShader WebGL, the
toolbox bundle) to part-<i>.mp4 and writes its timing. ``join`` concatenates the parts (and muxes a narration when given) and
writes the ≤ 720p review copy. ``measure`` sums the chunk timings into cost.json: render seconds per second of video, the
wall-clock of the parallel render, machine minutes and rupees at the GitHub Actions list price (the public repository runs
free). ``bench`` times the first frames of a spec on this machine, so a speed change is measured before and after on the
same frames. Inputs (``--spec``) may be local files or https URLs.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats  # noqa: E402
from bie.brain.video import render  # noqa: E402

LIST_PRICE_USD_PER_MINUTE = 0.008        # GitHub-hosted Linux runner, 2 vCPU, list price (the public repository is billed nothing)
USD_TO_INR = 84.0


def read_json(source: str) -> dict:
    if source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def chunk_range(total: int, chunk: int, chunks: int) -> tuple:
    """Frames [first, last) of chunk ``chunk`` of ``chunks``: equal parts, the last one shorter; every frame once."""
    per = -(-total // chunks)
    return min(total, chunk * per), min(total, (chunk + 1) * per)


def total_frames(spec: dict) -> int:
    return sum(int(s["duration"]) for s in spec["scenes"])


def timing_row(spec: dict, first: int, last: int, seconds: float, **extra) -> dict:
    video_seconds = (last - first) / spec["fps"]
    return {"frames": [first, last], "video_seconds": round(video_seconds, 2), "render_seconds": round(seconds, 1),
            "seconds_per_frame": round(seconds / max(1, last - first), 3),
            "seconds_per_video_second": round(seconds / max(0.01, video_seconds), 2),
            "machine": os.environ.get("RUNNER_NAME") or os.uname().nodename, "cpus": os.cpu_count(), **extra}


def cmd_chunk(args) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    spec = formats.accept("video_spec", read_json(args.spec), where=args.spec)
    first, last = chunk_range(total_frames(spec), args.chunk, args.chunks)
    dist = render.build_preview(Path(args.dist) if args.dist else out / "_dist", toolbox=True)
    assets = Path(args.assets) if args.assets else (out / "assets" if (out / "assets").exists() else None)
    started = time.time()
    render.mp4_range(spec, out / f"part-{args.chunk:02d}.mp4", first, last, dist=dist, assets=assets)
    row = timing_row(spec, first, last, time.time() - started, chunk=args.chunk, chunks=args.chunks)
    (out / f"part-{args.chunk:02d}.json").write_text(json.dumps(row, indent=1), encoding="utf-8")
    print(json.dumps(row))
    return 0


def ffprobe_seconds(path: Path) -> float:
    done = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True)
    return round(float(done.stdout.strip() or 0), 2)


def cmd_join(args) -> int:
    out = Path(args.out)
    parts = [out / f"part-{i:02d}.mp4" for i in range(args.chunks)]
    missing = [str(p) for p in parts if not p.exists()]
    if missing:
        raise SystemExit("missing parts: " + ", ".join(missing))
    listing = out / "parts.txt"
    listing.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    silent = out / "video_silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(silent)], check=True)
    final = out / "video.mp4"
    if args.audio and Path(args.audio).exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(args.audio), "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "128k", "-shortest", str(final)], check=True)
    else:
        shutil.copy(silent, final)
    review = out / f"review-{args.review}p.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-vf", f"scale=-2:{args.review}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "26", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(review)], check=True)
    info = {"video": str(final), "review": str(review), "review_bytes": review.stat().st_size, "video_bytes": final.stat().st_size,
            "seconds": ffprobe_seconds(final), "chunks": args.chunks}
    formats.check("render_join", formats.stamp("render_join", info), where=str(out / "join.json"))
    (out / "join.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info))
    return 0


def measure(rows: list) -> dict:
    video_seconds = sum(r["video_seconds"] for r in rows)
    render_seconds = sum(r["render_seconds"] for r in rows)
    wall = max(r["render_seconds"] for r in rows)
    machine_minutes = render_seconds / 60
    frames = sum(r["frames"][1] - r["frames"][0] for r in rows)
    return {"chunks": len(rows), "frames": frames, "video_seconds": round(video_seconds, 2), "video_minutes": round(video_seconds / 60, 2),
            "render_seconds": round(render_seconds, 1), "seconds_per_frame": round(render_seconds / max(1, frames), 3),
            "seconds_per_video_second": round(render_seconds / max(0.01, video_seconds), 2),
            "wall_clock_minutes_parallel": round(wall / 60, 1), "machine_minutes": round(machine_minutes, 1),
            "usd_at_list_price": round(machine_minutes * LIST_PRICE_USD_PER_MINUTE, 3),
            "inr_at_list_price": round(machine_minutes * LIST_PRICE_USD_PER_MINUTE * USD_TO_INR, 2),
            "list_price_usd_per_minute": LIST_PRICE_USD_PER_MINUTE, "usd_to_inr": USD_TO_INR,
            "note": "GitHub-hosted ubuntu runner, 2 vCPU, software WebGL (SwiftShader), no GPU; the public repository bills Rs 0",
            "rows": rows}


def cmd_measure(args) -> int:
    out = Path(args.out)
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("part-*.json"))]
    if not rows:
        raise SystemExit("no chunk timings")
    cost = measure(rows)
    formats.check("render_cost", formats.stamp("render_cost", cost), where=str(out / "cost.json"))
    (out / "cost.json").write_text(json.dumps(cost, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in cost.items() if k != "rows"}))
    return 0


def trim_spec(spec: dict, frames: int) -> dict:
    """The first ``frames`` frames of a spec (whole scenes cut at the limit), for a timing on the same frames before and after."""
    trimmed = copy.deepcopy(spec)
    left = frames
    scenes = []
    for sc in trimmed["scenes"]:
        if left <= 0:
            break
        sc["duration"] = min(int(sc["duration"]), left)
        left -= sc["duration"]
        scenes.append(sc)
    trimmed["scenes"] = scenes
    return trimmed


def bench(spec: dict, frames: int, *, dist, assets, out: Path, label: str) -> dict:
    """Time the first ``frames`` frames of ``spec`` on this machine (the same frames before and after a speed change)."""
    trimmed = trim_spec(spec, frames)
    total = total_frames(trimmed)
    started = time.time()
    render.mp4(trimmed, out / f"bench-{label}.mp4", dist=dist, assets=assets, toolbox=True)
    return timing_row(trimmed, 0, total, time.time() - started, label=label,
                      blocks=sorted({l.get("block", l.get("type", "")) for s in trimmed["scenes"] for l in s["layers"]}))


def fixture_spec(out: Path, *, opener=None) -> dict:
    """The kit's demand-pull canvas (B) and world (C) fixtures as one video spec with the credits card: a ~70 s video the
    render pipeline proves itself on (test inputs of the economy kit, not lesson content)."""
    from bie.brain import canvas
    from bie.brain.assets import AssetLibrary
    from bie.brain.video import world
    from bie.toolbox import icons
    fixtures = ROOT / "tests" / "fixtures" / "task046c"
    out.mkdir(parents=True, exist_ok=True)
    library = AssetLibrary(out / "assets")
    plan = json.loads((fixtures / "demand_pull_touches.plan.json").read_text(encoding="utf-8"))
    paths = icons.add_to_library(canvas.icons_in(plan), library, opener=opener)
    scene_b, _ = canvas.compile_plan(plan, icon_paths=paths)
    scene_c, _ = world.compile_world(json.loads((fixtures / "demand_pull_world.world.json").read_text(encoding="utf-8")))
    library.save()
    scenes = [scene_b, scene_c, canvas.credits_scene(library.credits(sorted(library.assets)))]
    spec = canvas.video_spec(scenes)
    canvas.write_spec(spec, out / "video_spec.json")
    return spec


def cmd_fixture(args) -> int:
    spec = fixture_spec(Path(args.out))
    print(json.dumps({"frames": total_frames(spec), "seconds": round(total_frames(spec) / spec["fps"], 1), "scenes": len(spec["scenes"])}))
    return 0


def cmd_bench(args) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    spec = formats.accept("video_spec", read_json(args.spec), where=args.spec)
    dist = render.build_preview(Path(args.dist) if args.dist else out / "_dist", toolbox=True)
    assets = Path(args.assets) if args.assets else None
    row = bench(spec, args.frames, dist=dist, assets=assets, out=out, label=args.label)
    path = out / "bench.json"
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    rows.append(row)
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(json.dumps(row))
    return 0


def cmd_summary(args) -> int:
    out = Path(args.out)
    cost = json.loads((out / "cost.json").read_text(encoding="utf-8")) if (out / "cost.json").exists() else {}
    join = json.loads((out / "join.json").read_text(encoding="utf-8")) if (out / "join.json").exists() else {}
    summary = {"schema": "bie.render-spec.summary/1", "run_id": args.run_id, "sha": args.sha, "run_url": args.run_url,
               "cost": {k: v for k, v in cost.items() if k != "rows"}, "join": join}
    formats.check("render_summary", summary, where=str(out / "summary.json"))
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    lines = ["# Render", ""]
    if cost:
        lines += [f"- {cost['video_minutes']} minutes of video in {cost['chunks']} chunks: {cost['wall_clock_minutes_parallel']} minutes wall-clock "
                  f"(parallel), {cost['machine_minutes']} machine minutes, {cost['seconds_per_frame']} s per frame, "
                  f"{cost['seconds_per_video_second']} render seconds per video second; ₹{cost['inr_at_list_price']} at the list price (billed ₹0)."]
    if join:
        lines += [f"- video.mp4 {join['video_bytes'] / 1e6:.1f} MB, review-{args.review}p.mp4 {join['review_bytes'] / 1e6:.1f} MB, {join['seconds']} s."]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("chunk")
    k.add_argument("--spec", required=True)
    k.add_argument("--out", required=True)
    k.add_argument("--chunk", type=int, required=True)
    k.add_argument("--chunks", type=int, required=True)
    k.add_argument("--assets", default="")
    k.add_argument("--dist", default="")
    j = sub.add_parser("join")
    j.add_argument("--out", required=True)
    j.add_argument("--chunks", type=int, required=True)
    j.add_argument("--review", type=int, default=720)
    j.add_argument("--audio", default="")
    m = sub.add_parser("measure")
    m.add_argument("--out", required=True)
    b = sub.add_parser("bench")
    b.add_argument("--spec", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--frames", type=int, default=60)
    b.add_argument("--assets", default="")
    b.add_argument("--dist", default="")
    b.add_argument("--label", default="now")
    su = sub.add_parser("summary")
    su.add_argument("--out", required=True)
    su.add_argument("--run-id", default="")
    su.add_argument("--sha", default="")
    su.add_argument("--run-url", default="")
    su.add_argument("--review", type=int, default=720)
    fx = sub.add_parser("fixture")
    fx.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    return {"chunk": cmd_chunk, "join": cmd_join, "measure": cmd_measure, "bench": cmd_bench, "summary": cmd_summary,
            "fixture": cmd_fixture}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
