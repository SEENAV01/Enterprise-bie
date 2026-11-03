"""The Money v2 gold example as files (Claude's demo, not BIE output; agreement of 3 November 2026): writes
script.json, the show-spec and the asset library for the showing engine, at ₹0 with no AI call.

    python -B tools/gold_money_v2.py --out <folder> [--width 1920 --height 1080] [--durations tts_durations.json]

writes <out>/script.json, <out>/video_specs/v2_gold.json, <out>/assets/ (the Fluent Emoji things the plan uses,
licence-checked and credited through the asset library) and <out>/GOLD.md. With --durations (the voice step's seconds
per sentence) the timing is real; without it every sentence is estimated from its length.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.assets import AssetLibrary  # noqa: E402
from bie.brain import formats  # noqa: E402
from bie.brain.gold.money_v2 import ASSETS_USED, build_script, gold_spec  # noqa: E402
from bie.toolbox import icons  # noqa: E402

FLUENT = {name: "fl:" + name.replace("_", "-") for name in ASSETS_USED}


def resolve_assets(out: Path, *, opener=None) -> dict:
    """The plan's asset names -> served paths, through the asset library (licences recorded, credits ready)."""
    library = AssetLibrary(out / "assets")
    paths = icons.add_to_library(sorted(set(FLUENT.values())), library, opener=opener)
    library.save()
    return {name: paths[icon_id] for name, icon_id in FLUENT.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--durations", type=Path, help="seconds per sentence key (the voice step's durations.json)")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "video_specs").mkdir(exist_ok=True)
    script = build_script()
    (a.out / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=1), encoding="utf-8")
    durations = json.loads(a.durations.read_text(encoding="utf-8")) if a.durations else None
    assets = resolve_assets(a.out)
    spec = gold_spec(durations=durations, width=a.width, height=a.height, assets=assets)
    formats.check("show_spec", spec, where="video_specs/v2_gold.json")
    (a.out / "video_specs" / "v2_gold.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    lines = sum(len(s["lines"]) for s in script)
    (a.out / "GOLD.md").write_text(
        "# Money v2 gold example (Claude's demo, not BIE output)\n\n"
        f"- {lines} narration lines, {len(spec['subs'])} spoken sentences, {spec['duration']:.1f} s"
        + (" (real voice durations)" if durations else " (estimated timings: no voice durations given)") + ".\n"
        f"- {len(spec['scenes'])} scenes, {sum(len(s['els']) for s in spec['scenes'])} elements, "
        f"{len(assets)} fetched things (Fluent Emoji, MIT), the rest drawn by the engine's saanche.\n"
        "- Render: `python -B tools/render_spec.py chunk --spec video_specs/v2_gold.json --assets assets ...` "
        "or the `BIE Task046c Render` workflow.\n", encoding="utf-8")
    print(f"gold v2: {lines} lines, {len(spec['scenes'])} scenes, {spec['duration']:.1f} s, {len(assets)} assets -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
