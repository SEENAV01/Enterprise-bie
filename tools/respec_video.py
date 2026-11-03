"""Compile a canvas run's plans again with the current code: a new video spec, at ₹0 and with no AI call.

Task 048 plumbing (render and player). Navin, 3 November 2026: "fix only these general issues (minimum on-screen text size
readable on a phone, no world for a place that is not that world, label overlap in every mode)". A fix in the compilers or the
blocks shows on the same plans the director already made, without asking the maker again: this tool reads the plans of a
canvas run (``plans/<part>.plan.json``, in the order of ``canvas.json``), compiles each with the code of this checkout
(``canvas.compile_plan`` for a canvas part, ``world.compile_world`` for a world part), adds the credit card, checks the spec
like the director does (format, licences) and writes it for the render workflow. A part the current code refuses is listed with
its reason (it needs the director again); the video's spec is still written from the parts that compile, and the record says
which are missing.

    python -B tools/respec_video.py --run <canvas run folder> --video v4 [--video v8] --out <folder>

writes ``<out>/video_specs/<video>.json``, ``<out>/assets/`` (the run's asset library, plus any icon the compiler needs) and
``<out>/RESPEC.json`` ({videos: [{video_id, parts: [{id, mode, status, problem}], compiled, refused, scenes, seconds}]}).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import canvas, formats  # noqa: E402
from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.brain.video import timing, world  # noqa: E402
from bie.toolbox import icons  # noqa: E402
from bie.toolbox import licence as licence_policy  # noqa: E402


def paths_for(plan: dict, library: AssetLibrary, *, opener=None) -> dict:
    """icon id → ``assets/...`` path for the compiler and the renderer (the director's own step: icons into the library)."""
    ids = world.icons_in(plan) if "elements" in plan else canvas.icons_in(plan)
    index_ids = [i for i in ids if not str(i).startswith("asset:")]
    paths = icons.add_to_library(index_ids, library, opener=opener) if index_ids else {}
    paths.update({i: "assets/" + library.assets[i.split(":", 1)[1]].path for i in ids
                  if str(i).startswith("asset:") and i.split(":", 1)[1] in library.assets})
    return paths


def compile_part(plan: dict, library: AssetLibrary, *, opener=None) -> dict:
    """The scene of one plan with the current code (raises the compiler's PlanError when the code refuses it)."""
    paths = paths_for(plan, library, opener=opener)
    if "elements" in plan:
        scene, _ = world.compile_world(plan, icon_paths=paths)
    else:
        scene, _ = canvas.compile_plan(plan, icon_paths=paths)
    return scene


def respec(run: Path, video_id: str, out: Path, *, opener=None) -> dict:
    summary = json.loads((run / "canvas.json").read_text(encoding="utf-8"))
    video = next((v for v in summary.get("videos") or [] if v.get("video_id") == video_id), None)
    if video is None:
        raise SystemExit(f"{run}/canvas.json has no video {video_id}")
    library = AssetLibrary(out / "assets")
    rows, scenes = [], []
    for part in video.get("parts") or []:
        row = {"id": part["id"], "mode": part.get("mode", "")}
        path = run / "plans" / f"{part['id']}.plan.json"
        if part.get("status") != "passed" or not path.exists():
            row.update(status="no_plan", problem=f"the run has no passed plan for {part['id']}")
            rows.append(row)
            continue
        plan = json.loads(path.read_text(encoding="utf-8"))
        try:
            scenes.append(compile_part(plan, library, opener=opener))
            row["status"] = "compiled"
        except (canvas.PlanError, ValueError, KeyError) as exc:
            row.update(status="refused", problem=str(exc)[:400])
        rows.append(row)
    credits = library.credits(library.used_in(scenes))
    if scenes and credits:
        scenes.append(canvas.credits_scene(credits, scene_id=f"{video_id}_credits"))
    result = {"video_id": video_id, "parts": rows, "compiled": sum(1 for r in rows if r["status"] == "compiled"),
              "refused": sum(1 for r in rows if r["status"] == "refused"), "scenes": len(scenes),
              "seconds": round(sum(s["duration"] for s in scenes) / timing.FPS, 1)}
    if scenes:
        spec = canvas.video_spec(scenes)
        problems = licence_policy.lesson_spec_check(spec) + library.lesson_check(sorted(library.assets))
        if problems:
            result.update(status="stopped_by_licence", licence_problems=problems)
        else:
            formats.check("video_spec", spec, where=f"video_specs/{video_id}.json")
            canvas.write_spec(spec, out / "video_specs" / f"{video_id}.json")
            result["status"] = "spec_written"
    else:
        result["status"] = "no_scene"
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True, type=Path, help="a canvas run folder (canvas.json, plans/, assets/)")
    ap.add_argument("--video", action="append", required=True)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    if (a.run / "assets").is_dir() and not (a.out / "assets").exists():
        shutil.copytree(a.run / "assets", a.out / "assets")
    record = {"schema": "bie.respec/1", "run": str(a.run), "videos": [respec(a.run, v, a.out) for v in a.video]}
    (a.out / "RESPEC.json").write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    for v in record["videos"]:
        print(f"{v['video_id']}: {v['status']}, {v['compiled']} compiled, {v['refused']} refused, {v['seconds']} s")
        for r in v["parts"]:
            if r["status"] != "compiled":
                print(f"  {r['id']} {r['status']}: {r.get('problem', '')[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
