"""Render a composed VideoSpec through BIE's real render path, in chunks, with the placeholder voice (Task 046, Part B).

    python -B tools/render_video.py compose --plan shots/v3.json --beats <lesson_plan.json or fixture> --parts c07.1 --out <dir>
            [--voice espeak|silent] [--route A|C] [--models <folder with <member>.glb>]
    python -B tools/render_video.py chunk --spec <dir>/video_spec.json --out <dir> --chunk 2 --chunks 6 [--dist <dir>]
    python -B tools/render_video.py join --out <dir> --chunks 6 [--review 720]
    python -B tools/render_video.py measure --out <dir> [--route A]
    python -B tools/render_video.py report --out <dir> [--route A]          (frame checks → the 24-rule table with frame numbers)
    python -B tools/render_video.py models --plan <plan> [--parts c07.1] --out <dir>   (route C: Blender → one glTF per member)
    python -B tools/render_video.py bridge --out <dir> [--frames 300] [--dist <dir>]   (real Remotion on the first frames, compared)
    python -B tools/render_video.py summary --out <dir> [--run-id .. --sha .. --run-url ..]

``compose`` writes video_spec.json, shots_frames.json (every shot's frame range), the narration (narration.wav) and the
credits. ``chunk`` renders frames [i*N/chunks, (i+1)*N/chunks) with the preview renderer (Chromium + ffmpeg, SwiftShader
WebGL, the toolbox bundle) to part-<i>.mp4 and writes its timing. ``join`` concatenates the parts, muxes the narration,
and writes the ≤ 720p review copy. ``measure`` sums the chunk timings into cost.json: render seconds per second of video,
machine minutes, rupees at the GitHub Actions list price (the public repo runs free; the list price is what a private one
would pay). Route C: the same spec with the world layer's ``models`` pointing at Blender-made glTF sheets (``--models``).
``report`` takes one still per shot from the finished video, runs ``frame_checks`` and merges the findings into the director's
24-rule table (RULES.md, SHOTS.md, report.json, contact sheets). A plan the director blocked (``render_allowed`` false: W-01 or
another blocking check) is refused unless ``--allow-blocked`` says this is a pipeline check; the output then says ``blocked``.
Inputs (``--plan``, ``--beats``, ``--chapter``) may be local files or https URLs.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import shots as shots_module  # noqa: E402
from bie.brain.video import compose, render, timing, voice as voice_module  # noqa: E402
from run_brain import read_text  # noqa: E402

LIST_PRICE_USD_PER_MINUTE = 0.008          # GitHub-hosted Linux runner, 2 vCPU, list price per minute (private repositories)
USD_TO_INR = 84.0


def _read_json(source: str) -> dict:
    return json.loads(read_text(str(source)))


def _beats_of(source: str, video_id: str) -> list:
    data = _read_json(source)
    if "video" in data and data["video"].get("video_id") == video_id:
        return data["video"]["beats"]
    for v in (data.get("videos") or (data.get("plan") or {}).get("videos") or []):
        if v["video_id"] == video_id:
            return v["beats"]
    raise SystemExit(f"{source}: no beats for {video_id}")


def blocked_reasons(plan: dict) -> list:
    """Why the director does not allow this video to render (W-01 hits and the blocking checks), for the refusal."""
    reasons = [f"W-01 {h['beat_id']}: {h['words']!r}" for h in (plan.get("wording") or {}).get("hits") or []]
    for check in plan.get("checks") or []:
        if isinstance(check, dict) and check.get("blocking") and check.get("rule") != "W-01":
            reasons.append(f"{check.get('rule')}: {check.get('why') or check.get('note') or ''}".strip())
    return reasons or ["the director marked the video not renderable"]


def members_of(plan: dict) -> list:
    """The family members the plan's shots show, in order of first use (the composer's reading of each clause)."""
    out, carried = [], compose.DEFAULT_MEMBER
    for shot in plan["shots"]:
        carried = compose.member_of(shot, carried)
        if carried not in out:
            out.append(carried)
    return out


def route_c_models(spec: dict, models: Path | None, out: Path) -> dict:
    """Route C: every member a scene's shots show gets its Blender-made glTF (``<models>/<member>.glb``) when one exists, copied
    next to the page and named in the world layer's ``data.models``; a member without a model keeps the procedural sheet.
    Returns {member: served path} for the members that got a model."""
    served = {}
    for scene in spec["scenes"]:
        for layer in scene["layers"]:
            if layer.get("block") != "cell_sheet" or layer["data"].get("world"):
                continue
            members = {s.get("member") or layer["data"].get("member", "generic") for s in layer["data"].get("shots") or []} or {layer["data"].get("member", "generic")}
            found = {}
            for member in sorted(members):
                glb = models / f"{member}.glb" if models else None
                if glb and glb.exists():
                    (out / "assets" / "models").mkdir(parents=True, exist_ok=True)
                    shutil.copy(glb, out / "assets" / "models" / f"{member}.glb")
                    found[member] = served[member] = f"assets/models/{member}.glb"       # served next to the page, as the demos do
            if found:
                layer["data"]["models"] = found
    return served


def cmd_compose(args) -> int:
    out = Path(args.out)
    plan = _read_json(args.plan)
    blocked = not plan.get("render_allowed", True)
    if blocked and not args.allow_blocked:
        for line in blocked_reasons(plan):
            print(f"not rendered: {line}", file=sys.stderr)
        print(f"{plan.get('video_id')}: the director blocked this video; fix the script (VM job) or pass --allow-blocked for a pipeline check", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    beats = _beats_of(args.beats, plan["video_id"])
    parts = [p for p in args.parts.split(",") if p]
    seg = compose.segment(plan, parts=parts) if parts else plan
    beat_ids = {b for s in seg["scenes"] for b in s["beat_ids"]}
    seg_beats = [b for b in beats if b["beat_id"] in beat_ids]
    voice = None
    audio = None
    if args.voice == "espeak" and not voice_module.available():
        raise SystemExit("eSpeak NG is not installed (apt-get install espeak-ng); pass --voice silent for the text estimate")
    if args.voice == "espeak":
        voice = voice_module.narrate(seg_beats, out / "voice")
        # the shot list again, on the real spoken seconds: every shot sits on a sound that exists
        chapter = _read_json(args.chapter) if args.chapter else None
        if chapter is not None:
            from bie.brain.understanding import Course
            course = Course(**{k: v for k, v in chapter["course"].items() if k in ("title", "subject", "learners", "exam", "language", "level")})
            video = {"video_id": plan["video_id"], "title": plan.get("title", ""), "beats": seg_beats, "status": "passed"}
            full = shots_module.build_video(video, chapter, course, voice=voice)
            seg = compose.segment(full, scene_ids=[s["scene_id"] for s in full["scenes"]]) if not parts else full
            seg = dict(seg, scenes=[s for s in seg["scenes"] if not parts or s["part_id"] in parts])
            ids = {s["scene_id"] for s in seg["scenes"]}
            seg["shots"] = [s for s in seg["shots"] if s["scene_id"] in ids]
    spec = compose.video_spec(seg, voice=voice and {"provider": voice_module.PROVIDER}, audio="narration.wav" if voice else None)
    if voice:
        scenes = [{"scene_id": s["scene_id"], "beat_ids": s["beat_ids"]} for s in seg["scenes"]]
        tl = timing.build(seg_beats, scenes, voice=voice)
        # the credits scene has no narration; the mix covers the teaching scenes
        voice_module.mix(voice, scenes, tl, out / "narration.wav")
    if args.route == "C":
        route_c_models(spec, Path(args.models) if args.models else None, out)
    problems = compose.check_spec(seg, spec)
    compose.write(spec, out / "video_spec.json")
    (out / "shots_frames.json").write_text(json.dumps(compose.shot_frames(seg, spec), ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "plan.json").write_text(json.dumps(seg, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(s["duration"] for s in spec["scenes"])
    worlds = [l for s in spec["scenes"] for l in s["layers"] if l.get("block") == "cell_sheet"]
    summary = {"video_id": plan["video_id"], "parts": parts, "scenes": len(spec["scenes"]), "shots": len(seg["shots"]), "frames": total,
               "seconds": round(total / spec["fps"], 2), "voice": voice_module.PROVIDER if voice else "silent", "route": args.route,
               "models": sorted({m for l in worlds for m in (l["data"].get("models") or {})}), "members": members_of(seg), "blocked": blocked,
               "blocked_reasons": blocked_reasons(plan) if blocked else [], "check_spec": problems}
    (out / "compose.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not problems else 1


def chunk_range(total: int, chunk: int, chunks: int) -> tuple:
    """Frames [first, last) of chunk ``chunk`` of ``chunks``: equal parts, the last one shorter; every frame once."""
    per = -(-total // chunks)
    return min(total, chunk * per), min(total, (chunk + 1) * per)


def cmd_chunk(args) -> int:
    out = Path(args.out)
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    total = sum(s["duration"] for s in spec["scenes"])
    first, last = chunk_range(total, args.chunk, args.chunks)
    dist = render.build_preview(Path(args.dist) if args.dist else out / "_dist", toolbox=True)
    started = time.time()
    part = out / f"part-{args.chunk:02d}.mp4"
    render.mp4_range(spec, part, first, last, dist=dist, assets=out / "assets" if (out / "assets").exists() else None)
    seconds = time.time() - started
    row = {"chunk": args.chunk, "chunks": args.chunks, "frames": [first, last], "video_seconds": round((last - first) / spec["fps"], 2),
           "render_seconds": round(seconds, 1), "seconds_per_video_second": round(seconds / max(0.01, (last - first) / spec["fps"]), 2),
           "machine": os.environ.get("RUNNER_NAME") or os.uname().nodename, "cpus": os.cpu_count()}
    (out / f"part-{args.chunk:02d}.json").write_text(json.dumps(row, indent=1), encoding="utf-8")
    print(json.dumps(row))
    return 0


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
    narration = out / "narration.wav"
    if narration.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(narration), "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                        "-shortest", str(final)], check=True)
    else:
        shutil.copy(silent, final)
    review = out / f"review-{args.review}p.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(final), "-vf", f"scale=-2:{args.review}", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "26", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(review)], check=True)
    info = {"video": str(final), "review": str(review), "review_bytes": review.stat().st_size, "video_bytes": final.stat().st_size,
            "seconds": _ffprobe(final)}
    (out / "join.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info))
    return 0


def _ffprobe(path: Path) -> float:
    done = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return round(float(done.stdout.strip() or 0), 2)


def cmd_measure(args) -> int:
    out = Path(args.out)
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("part-*.json"))]
    if not rows:
        raise SystemExit("no chunk timings")
    video_seconds = sum(r["video_seconds"] for r in rows)
    render_seconds = sum(r["render_seconds"] for r in rows)
    wall = max(r["render_seconds"] for r in rows)
    machine_minutes = render_seconds / 60
    cost = {"route": args.route, "chunks": len(rows), "video_seconds": round(video_seconds, 2), "render_seconds": round(render_seconds, 1),
            "seconds_per_video_second": round(render_seconds / video_seconds, 2), "wall_clock_minutes_parallel": round(wall / 60, 1),
            "machine_minutes": round(machine_minutes, 1), "usd_at_list_price": round(machine_minutes * LIST_PRICE_USD_PER_MINUTE, 3),
            "inr_at_list_price": round(machine_minutes * LIST_PRICE_USD_PER_MINUTE * USD_TO_INR, 2),
            "list_price_usd_per_minute": LIST_PRICE_USD_PER_MINUTE, "usd_to_inr": USD_TO_INR,
            "note": "GitHub-hosted ubuntu runner, 2 vCPU, software WebGL (SwiftShader), no GPU; the public repository bills Rs 0", "rows": rows}
    (out / "cost.json").write_text(json.dumps(cost, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in cost.items() if k != "rows"}))
    return 0


def cmd_models(args) -> int:
    """Route C: a Blender-made glTF sheet per member the plan shows (bie/toolbox/blender/cell_sheet.py through the adapter)."""
    from bie.toolbox.adapters import blender
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plan = _read_json(args.plan)
    parts = [p for p in args.parts.split(",") if p]
    seg = compose.segment(plan, parts=parts) if parts else plan
    rows = {}
    for member in members_of(seg):
        started = time.time()
        glb = out / f"{member}.glb"
        info = blender.cell_sheet(glb, kind=member, rows=args.rows, cols=args.cols)
        rows[member] = dict(info, seconds=round(time.time() - started, 1), bytes=glb.stat().st_size)
        print(json.dumps({"member": member, **{k: rows[member][k] for k in ("cells", "hairs", "layers", "seconds", "bytes", "blender")}}), flush=True)
    (out / "models.json").write_text(json.dumps({"made_by": "Blender (bpy) through bie.toolbox.adapters.blender.cell_sheet", "rows": args.rows,
                                                 "cols": args.cols, "members": rows}, indent=1), encoding="utf-8")
    return 0


def _still(video: Path, frame: int, fps: int, out: Path) -> bytes:
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{frame / fps:.3f}", "-i", str(video), "-frames:v", "1", str(out)], check=True)
    return out.read_bytes()


def cmd_report(args) -> int:
    from collections import Counter
    from bie.brain.video import frame_checks
    out = Path(args.out)
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    spec = json.loads((out / "video_spec.json").read_text(encoding="utf-8"))
    rows = json.loads((out / "shots_frames.json").read_text(encoding="utf-8"))
    compose_info = json.loads((out / "compose.json").read_text(encoding="utf-8")) if (out / "compose.json").exists() else {}
    join_info = json.loads((out / "join.json").read_text(encoding="utf-8")) if (out / "join.json").exists() else {}
    cost = json.loads((out / "cost.json").read_text(encoding="utf-8")) if (out / "cost.json").exists() else {}
    video = out / "video.mp4"
    fps = spec["fps"]
    rendered = int(round(_ffprobe(video) * fps))                 # a smoke run may hold only the first frames of the spec
    stills = out / "stills"
    stills.mkdir(exist_ok=True)
    frames, not_rendered = [], []
    for r in rows:
        mid = (r["from"] + r["to"]) // 2
        if mid >= rendered:
            not_rendered.append(r["shot_id"])
            continue
        frames.append((mid, _still(video, mid, fps, stills / f"frame-{mid:06d}.png")))
    accents = {}
    for scene in spec["scenes"]:
        world = next((l for l in scene["layers"] if l["id"] == "world"), None)
        if world:
            for ws, r in zip(world["data"]["shots"], [r for r in rows if r["scene_id"] == scene["id"]]):
                accents[r["shot_id"]] = compose.accent_of(ws.get("member", compose.DEFAULT_MEMBER))
    findings = frame_checks.check_frames(frames, rows, accents)
    table = frame_checks.rule_table_with_frames(plan["rule_table"], findings)
    sheets = []
    for i in range(0, len(frames), 16):
        name = f"contact-{i // 16:02d}.png"
        frame_checks.contact_sheet(frames[i:i + 16], out / name, f"{plan['video_id']} · route {args.route} · shots {i + 1}-{min(len(frames), i + 16)} (one still per shot)")
        sheets.append(name)
    total = sum(s["duration"] for s in spec["scenes"])
    seconds = round(sum(r["seconds"] for r in rows), 1)
    split = shots_module.level_split(plan["shots"])                   # the director's own measures, on the segment's shots
    changes = len(shots_module.visual_changes(plan["shots"]))
    report = {"schema": "bie.brain.benchmark-report/1", "video_id": plan["video_id"], "title": plan.get("title", ""), "route": args.route,
              "parts": compose_info.get("parts"), "scenes": len(plan["scenes"]), "shots": len(rows), "frames": total, "seconds": round(total / fps, 2),
              "spoken_seconds": seconds, "voice": compose_info.get("voice"), "models": compose_info.get("models"), "members": compose_info.get("members"),
              "blocked": compose_info.get("blocked", False), "level_seconds": split,
              "main_level": max(split.items(), key=lambda kv: kv[1]["seconds"])[0] if split else None,
              "pace": {"changes": changes, "seconds_per_change": round(seconds / max(1, changes), 2), "band": (plan.get("pace") or {}).get("band"),
                       "target_seconds": (plan.get("pace") or {}).get("target_seconds")},
              "shots_not_rendered": not_rendered, "rule_table": table, "tally": dict(Counter(r["status"] for r in table)), "frames_checked": findings["frames_checked"],
              "frame_findings": {k: len(v) for k, v in findings["findings"].items()}, "cost": {k: v for k, v in cost.items() if k != "rows"},
              "review": Path(join_info["review"]).name if join_info.get("review") else None, "review_bytes": join_info.get("review_bytes"),
              "video_seconds": join_info.get("seconds"), "contact_sheets": sheets}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"# Rule table · {plan['video_id']} · route {args.route}", "", f"{report['tally']}; {findings['frames_checked']} stills read (one per shot).", "",
             "| rule | status | frame | note |", "|---|---|---|---|"]
    lines += [f"| {r['rule']} | {r['status']} | {r['frame'] if r.get('frame') is not None else ''} | {str(r.get('note', '')).replace('|', '/')} |" for r in table]
    (out / "RULES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines = [f"# Shot list · {plan['video_id']} · route {args.route}", "", f"{len(rows)} shots, {seconds} s spoken, {report['frames']} frames; levels: " +
             ", ".join(f"{k} {v['share']:.0%}" for k, v in report["level_seconds"].items()) + f"; one visual change every {report['pace']['seconds_per_change']} s.", "",
             "| shot | frames | s | level | capability | camera | labels | sentence |", "|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r['shot_id']} | {r['from']}–{r['to']} | {r['seconds']} | {r['level']} | {r['capability']} | {r['camera']} | {', '.join(r['labels'])} | {r['sentence'].replace('|', '/')} |" for r in rows]
    (out / "SHOTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    cost_line = (f"{cost['seconds_per_video_second']} render seconds per second of video, {cost['machine_minutes']} machine minutes, "
                 f"Rs {cost['inr_at_list_price']} at the list price (USD {cost['usd_at_list_price']}); billed Rs 0 on the public repository") if cost else "not measured"
    md = [f"# Benchmark render · {plan['video_id']} · route {args.route}", "",
          f"- segment: parts {', '.join(report['parts'] or [])}, {len(rows)} shots, {report['seconds']} s with credits ({seconds} s spoken), {report['frames']} frames at {fps} fps, 1920 × 1080",
          f"- voice: {report['voice']}; models: {', '.join(report['models'] or []) or 'procedural (route A)'}; members shown: {', '.join(report['members'] or [])}",
          f"- levels: " + ", ".join(f"{k} {v['seconds']} s ({v['share']:.0%})" for k, v in report["level_seconds"].items()) + f"; main level {report['main_level']}",
          f"- pace: {report['pace']['changes']} visual changes, one every {report['pace']['seconds_per_change']} s (band {report['pace']['band']})",
          f"- rules: {report['tally']} (RULES.md, frame numbers from {findings['frames_checked']} stills)", f"- cost: {cost_line}",
          f"- review copy: {report['review'] or 'none'}" + (f" ({report['review_bytes'] / 1e6:.1f} MB)" if report.get("review_bytes") else ""), ""]
    (out / "REPORT.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("route", "shots", "seconds", "main_level", "pace", "tally", "frames_checked")}, ensure_ascii=False))
    return 0


def cmd_bridge(args) -> int:
    """The first ``--frames`` frames of the spec rendered by real Remotion (@remotion/bundler + renderer) and by the preview path,
    timed, three stills compared: the same blocks must give the same picture (Task 046a's bridge, on the lesson spec)."""
    from PIL import Image, ImageChops, ImageStat
    from toolbox_demos import chromium_path, contact_sheet
    out = Path(args.out)
    spec = json.loads((out / "video_spec.json").read_text(encoding="utf-8"))
    total = sum(s["duration"] for s in spec["scenes"])
    last = min(total, args.frames)
    probe = [int(last * f) for f in (0.15, 0.5, 0.85)]
    script = ROOT / "bie" / "brain" / "video" / "remotion" / "render.mjs"
    browser = chromium_path()
    if browser:
        wrapper = out / "headless_shell_webgl.sh"
        wrapper.write_text(f'#!/bin/sh\nexec "{browser}" --enable-unsafe-swiftshader --ignore-gpu-blocklist "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
        browser = str(wrapper)
    started = time.time()
    done = subprocess.run(["node", str(script), "--spec", str(out / "video_spec.json"), "--public", str(out), "--out", str(out / "bridge.mp4"),
                           "--from", "0", "--to", str(last), "--frames", ",".join(map(str, probe)), "--stills", str(out / "bridge_stills")]
                          + (["--browser", browser] if browser else []), capture_output=True, text=True, timeout=5400)
    remotion_seconds = time.time() - started
    row = {"renderer": "remotion", "frames": [0, last], "video_seconds": round(last / spec["fps"], 2), "render_seconds": round(remotion_seconds, 1),
           "seconds_per_video_second": round(remotion_seconds / max(0.01, last / spec["fps"]), 2), "probe_frames": probe, "includes_bundling": True}
    if done.returncode != 0:
        row.update(passed=False, error=(done.stderr or done.stdout)[-1500:])
        (out / "bridge.json").write_text(json.dumps(row, indent=1), encoding="utf-8")
        print(json.dumps({k: row.get(k) for k in ("passed", "error")}))
        return 1
    dist = render.build_preview(Path(args.dist) if args.dist else out / "_dist", toolbox=True)
    started = time.time()
    render.mp4_range(spec, out / "preview_sample.mp4", 0, last, dist=dist, assets=out / "assets" if (out / "assets").exists() else None)
    preview_seconds = time.time() - started
    lite = render.stills(spec, probe, dist=dist, assets=out / "assets" if (out / "assets").exists() else None, out_dir=out / "preview_stills")
    diffs, pngs = [], []
    for f, png in zip(probe, lite):
        real = (out / "bridge_stills" / f"frame-{f:06d}.png").read_bytes()
        import io
        a = Image.open(io.BytesIO(png)).convert("L").resize((480, 270))
        b = Image.open(io.BytesIO(real)).convert("L").resize((480, 270))
        diffs.append(round(ImageStat.Stat(ImageChops.difference(a, b)).mean[0], 2))
        pngs += [png, real]
    contact_sheet(pngs, [f"{lbl} {f / spec['fps']:.1f} s" for f in probe for lbl in ("preview", "remotion")], out / "bridge_sheet.png",
                  "route A sample: preview path (left) and real Remotion (right), same frames")
    row.update(passed=max(diffs) < 8.0, mean_differences=diffs,
               preview={"render_seconds": round(preview_seconds, 1), "seconds_per_video_second": round(preview_seconds / max(0.01, last / spec["fps"]), 2)})
    (out / "bridge.json").write_text(json.dumps(row, indent=1), encoding="utf-8")
    print(json.dumps({k: row.get(k) for k in ("passed", "mean_differences", "seconds_per_video_second", "preview")}))
    return 0 if row["passed"] else 1


def cmd_summary(args) -> int:
    """REPORT.md and summary.json over the routes' report.json files (and the bridge), for the blindtest-results folder."""
    out = Path(args.out)
    reports = {p.parent.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(out.glob("*/report.json"))}
    bridge = json.loads((out / "bridge" / "bridge.json").read_text(encoding="utf-8")) if (out / "bridge" / "bridge.json").exists() else None
    lines = ["# Task 046 Part B · benchmark render of v3's epithelium family segment", "",
             f"Run {args.run_id} from {args.sha[:8] if args.sha else '?'}; script from {args.run_url}. Status: IMPLEMENTED (nothing ACCEPTED until Navin's verdict).", "",
             "| route | shots | seconds | main level | one change every | rules pass / partial / fail | render s per video s | machine min | Rs at list price |",
             "|---|---|---|---|---|---|---|---|---|"]
    for route, r in reports.items():
        t, c = r.get("tally", {}), r.get("cost", {})
        lines.append(f"| {route} | {r['shots']} | {r['seconds']} | {r['main_level']} | {r['pace']['seconds_per_change']} s | {t.get('pass', 0)} / {t.get('partial', 0)} / {t.get('fail', 0)} "
                     f"| {c.get('seconds_per_video_second', '?')} | {c.get('machine_minutes', '?')} | {c.get('inr_at_list_price', '?')} |")
    if bridge:
        lines += ["", f"Bridge (real Remotion, first {bridge['video_seconds']} s of route A): {bridge['seconds_per_video_second']} render s per video s "
                  f"(bundling included), frames against the preview path differ by {bridge.get('mean_differences')} (mean grey levels, < 8 passes): "
                  f"{'passed' if bridge.get('passed') else 'FAILED'}."]
    lines += ["", "Per route: review-720p.mp4 (the video), REPORT.md, RULES.md (24 rules with frame numbers), SHOTS.md (shot by shot), cost.json, contact-*.png.", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps({"run_id": args.run_id, "sha": args.sha, "run_url": args.run_url, "routes": reports, "bridge": bridge},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compose")
    c.add_argument("--plan", required=True)
    c.add_argument("--beats", required=True)
    c.add_argument("--chapter", default="", help="chapter map or fixture with items; needed to rebuild the shot list on the voice's seconds")
    c.add_argument("--parts", default="")
    c.add_argument("--out", required=True)
    c.add_argument("--voice", choices=("espeak", "silent"), default="espeak")
    c.add_argument("--route", choices=("A", "C"), default="A")
    c.add_argument("--models", default="")
    c.add_argument("--allow-blocked", action="store_true", help="compose a video the director blocked (W-01 or another blocking check): pipeline checks only")
    mo = sub.add_parser("models")
    mo.add_argument("--plan", required=True)
    mo.add_argument("--parts", default="")
    mo.add_argument("--out", required=True)
    mo.add_argument("--rows", type=int, default=5)
    mo.add_argument("--cols", type=int, default=7)
    k = sub.add_parser("chunk")
    k.add_argument("--spec", required=True)
    k.add_argument("--out", required=True)
    k.add_argument("--chunk", type=int, required=True)
    k.add_argument("--chunks", type=int, required=True)
    k.add_argument("--dist", default="")
    j = sub.add_parser("join")
    j.add_argument("--out", required=True)
    j.add_argument("--chunks", type=int, required=True)
    j.add_argument("--review", type=int, default=720)
    m = sub.add_parser("measure")
    m.add_argument("--out", required=True)
    m.add_argument("--route", default="A")
    r = sub.add_parser("report")
    r.add_argument("--out", required=True)
    r.add_argument("--route", default="A")
    b = sub.add_parser("bridge")
    b.add_argument("--out", required=True)
    b.add_argument("--frames", type=int, default=300)
    b.add_argument("--dist", default="")
    su = sub.add_parser("summary")
    su.add_argument("--out", required=True)
    su.add_argument("--run-id", default="")
    su.add_argument("--sha", default="")
    su.add_argument("--run-url", default="")
    args = parser.parse_args(argv)
    return {"compose": cmd_compose, "chunk": cmd_chunk, "join": cmd_join, "measure": cmd_measure, "report": cmd_report, "models": cmd_models,
            "bridge": cmd_bridge, "summary": cmd_summary}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
