"""Task 046 one-shot test (26 October 2026): one shot, two routes, judged side by side with the benchmark.

    python -B tools/oneshot.py prompts --shots <shot list json> --shot b37.2 --out <prompts.json>
        Route 2's image prompts for the VM's image job (bie/brain/video/still_prompt.py; no text in the picture).
    python -B tools/oneshot.py route1 --shots <shot list json> --shot b37.2 --plate <folder with plate-1080p.mp4 and
            anchors.json> --out <folder> --dist <preview build folder>
        Route 1: the Blender plate (from .github/workflows/task046-oneshot.yml) with BIE's labels and caption on top.
    python -B tools/oneshot.py route2 --shots <shot list json> --shot b37.2 --still <picture> --out <folder> --dist <...>
        Route 2: the AI still moved in 2.5D by code (depth map, push, particles, glow) with BIE's labels and caption.

Each route writes clip-1080p.mp4, review-720p.mp4, three stills for the look check (look-f0030.jpg, look-f0075.jpg,
look-f0120.jpg), spec.json and route.json (what was made, how long it took). Labels and captions are BIE's code (VG-02).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOOK_FRAMES = (30, 75, 120)      # after the 10-frame fade-in, the middle of the push, near its end


def shot_from(path: str | Path, shot_id: str) -> dict:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    for shot in plan.get("shots") or []:
        if shot["shot_id"] == shot_id:
            return shot
    raise SystemExit(f"{shot_id} is not in {path}")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def finish(spec: dict, out: Path, assets: Path, dist: str, started: float, extra: dict) -> dict:
    """Render the spec at 1080p through BIE's preview path, make the 720p review copy and the look-check stills."""
    from bie.brain.video import compose, render
    compose.write(spec, out / "spec.json")
    t = time.time()
    render.mp4(spec, out / "clip-1080p.mp4", dist=dist, assets=assets)
    render_seconds = round(time.time() - t, 1)
    ffmpeg("-i", str(out / "clip-1080p.mp4"), "-vf", "scale=1280:720", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out / "review-720p.mp4"))
    for f in LOOK_FRAMES:
        ffmpeg("-i", str(out / "clip-1080p.mp4"), "-vf", f"select=eq(n\\,{f - 1})", "-frames:v", "1", "-q:v", "2", str(out / f"look-f{f:04d}.jpg"))
    record = dict(extra, frames=spec["scenes"][0]["duration"], fps=spec["fps"], size=[spec["width"], spec["height"]],
                  compose_render_seconds=render_seconds, total_seconds=round(time.time() - started, 1),
                  labels_missing=spec.get("labels_missing", []), look_frames=list(LOOK_FRAMES))
    (out / "route.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    return record


def route1(args) -> dict:
    from bie.brain.video import compose
    started = time.time()
    shot = shot_from(args.shots, args.shot)
    out = Path(args.out)
    assets = out / "assets"
    (assets / "plate").mkdir(parents=True, exist_ok=True)
    plate = Path(args.plate)
    ffmpeg("-i", str(plate / "plate-1080p.mp4"), str(assets / "plate" / "f%04d.png"))
    count = len(list((assets / "plate").glob("f*.png")))
    anchors = json.loads((plate / "anchors.json").read_text(encoding="utf-8"))["points"]
    spec = compose.plate_spec(shot, pattern="assets/plate/f%04d.png", count=count, anchors=anchors)
    record = finish(spec, out, assets, args.dist, started, {"route": 1, "shot": shot["shot_id"], "plate": str(plate / "plate-1080p.mp4")})
    shutil.rmtree(assets, ignore_errors=True)
    return record


def route2(args) -> dict:
    from PIL import Image
    from bie.brain.video import compose
    from bie.toolbox.adapters import depth
    started = time.time()
    shot = shot_from(args.shots, args.shot)
    out = Path(args.out)
    assets = out / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    image = Image.open(args.still).convert("RGB")
    w, h = image.size
    if abs(w / h - 16 / 9) > 0.01:                  # crop the picture to 16:9 around its centre (the layout asked for 16:9)
        if w / h > 16 / 9:
            nw = round(h * 16 / 9)
            image = image.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = round(w * 9 / 16)
            image = image.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    image.save(assets / "still.png")
    t = time.time()
    info = depth.estimate(assets / "still.png", assets / "depth.png")
    depth_seconds = round(time.time() - t, 1)
    layout = depth.layout_anchors(assets / "depth.png", shot.get("labels") or [], shot.get("member") or "")
    spec = compose.parallax_spec(shot, still="assets/still.png", depth="assets/depth.png", layout=layout, count=args.frames)
    shutil.copy2(assets / "depth.png", out / "depth.png")
    record = finish(spec, out, assets, args.dist, started, {"route": 2, "shot": shot["shot_id"], "still": str(args.still),
                                                            "still_size": [w, h], "depth": info, "depth_seconds": depth_seconds,
                                                            "layout": layout})
    shutil.rmtree(assets, ignore_errors=True)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompts")
    p.add_argument("--shots", required=True)
    p.add_argument("--shot", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--count", type=int, default=4)
    for name in ("route1", "route2"):
        r = sub.add_parser(name)
        r.add_argument("--shots", required=True)
        r.add_argument("--shot", required=True)
        r.add_argument("--out", required=True)
        r.add_argument("--dist", required=True)
        if name == "route1":
            r.add_argument("--plate", required=True)
        else:
            r.add_argument("--still", required=True)
            r.add_argument("--frames", type=int, default=135)
    args = parser.parse_args(argv)
    if args.cmd == "prompts":
        from bie.brain.video import still_prompt
        data = still_prompt.shot_prompts(shot_from(args.shots, args.shot), count=args.count)
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"prompts": len(data["prompts"]), "out": args.out}))
        return 0
    Path(args.out).mkdir(parents=True, exist_ok=True)
    record = route1(args) if args.cmd == "route1" else route2(args)
    print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
