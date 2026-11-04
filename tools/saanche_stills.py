"""The saancha still sheets (Phase 1, part B1): every drawing of the manifest at its default parameters, as PNG sheets.

    python -B tools/saanche_stills.py --out <folder> [--per-sheet 12] [--dist <built preview>]

Each sheet is one rendered frame of the showing engine (the same page the chunks render), a grid of saanche with
their names at the 36 px floor, written as ``saanche-<nn>.png`` with an ``INDEX.md`` naming what is on which sheet.
CI renders the sheets on every change to the engine or the manifest and publishes them as an artifact, so a review
sees every drawing, not a test count.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import saanche  # noqa: E402
from bie.brain.video import render  # noqa: E402

COLS, ROWS = 4, 3
W, H = 1920, 1080


def sheet_spec(pages: list) -> dict:
    """One show-spec whose scene ``i`` is sheet ``i``: a grid of saanche at defaults, each named below itself."""
    scenes = []
    for i, page in enumerate(pages):
        els = []
        for j, name in enumerate(page):
            entry = saanche.get(name)
            cx = (j % COLS + 0.5) * (W / COLS)
            top = (j // COLS) * (H / ROWS)
            base = top + H / ROWS - 64
            y = base if entry["anchor"] == "bottom" else top + (H / ROWS - 64) * 0.55
            wdef = (entry["params"].get("w") or {}).get("default")
            s = round(min(1.0, (W / COLS) * 0.92 / wdef), 3) if wdef else 1   # a wide one (a world) fits its cell
            els.append({"draw": name, "p": {}, "x": cx, "y": y, "s": s, "z": 20,
                        "t0": 0.0, "t1": None, "enter": "none", "keys": []})
            els.append({"text": name, "size": 36, "style": "tag", "x": cx, "y": base + 34,
                        "t0": 0.0, "t1": None, "z": 40})
        scenes.append({"id": f"sheet{i + 1}", "t0": float(i), "t1": float(i + 1), "bg": "paper",
                       "cam": [], "els": els})
    return {"schema": "bie.show-spec/1", "fps": 30, "width": W, "height": H, "duration": float(len(pages)),
            "subs": [], "scenes": scenes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--per-sheet", type=int, default=COLS * ROWS)
    ap.add_argument("--dist", type=Path, help="an already built engine preview (CI reuses the lane's build)")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    everything = saanche.names()
    pages = [everything[i:i + a.per_sheet] for i in range(0, len(everything), a.per_sheet)]
    spec = sheet_spec(pages)
    dist = a.dist or render.build_preview(Path(tempfile.mkdtemp()) / "dist", engine=True)
    frames = [i * 30 + 15 for i in range(len(pages))]
    pngs = render.stills(spec, frames, dist=dist)
    lines = [f"# Saancha still sheets ({len(everything)} saanche, {saanche.manifest()['licence']})\n"]
    for i, (page, png) in enumerate(zip(pages, pngs)):
        name = f"saanche-{i + 1:02d}.png"
        (a.out / name).write_bytes(png)
        lines.append(f"- `{name}`: {', '.join(page)}")
    (a.out / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"saanche stills: {len(everything)} saanche on {len(pages)} sheets -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
