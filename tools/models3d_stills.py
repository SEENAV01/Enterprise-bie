"""The 3D model still sheets: every 3D model of ``engine/three/models3d.json`` in two or three parameter states and camera
angles, rendered by the showing engine's 3D bundle (the same page the chunks render), as PNG sheets.

    python -B tools/models3d_stills.py --out <folder> [--dist <built preview>] [--width 1280]

Each state is one frame (``models3d-<model>-<n>.png``, its state named at the top) and every four frames make a sheet
(``models3d-sheet-<nn>.png``); ``INDEX.md`` says what is where. Needs three.js on NODE_PATH (``tools/toolbox_setup.py``),
like the show lane. A review sees every model moving through its states, not a test count.
"""
from __future__ import annotations

import argparse
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain.video import models3d, render  # noqa: E402

TOP = {"angle": 0, "height": 18, "dist": 0, "tx": 0, "ty": 0, "tz": 0}
STATES = {
    "factory": [({}, None, "4 machines running, belt at rate 1"),
                ({"running": 1, "workers": 8, "rate": 0.3, "output": 2, "target": 12, "smoke": 0.2}, {"angle": -26},
                 "1 of 4 running, 8 workers crowd, output under target"),
                ({"overtime": True, "light": "night", "machines": 6, "running": 6, "workers": 6, "rate": 2.5, "output": 24, "stock": 0.9,
                  "target": 15, "smoke": 1}, {"angle": 38, "height": 12}, "night overtime: 6 machines, fast belt, full godown")],
    "port": [({}, None, "a ship at the berth, cranes loading exports"),
             ({"ships": 3, "arrive": 0.55, "flow": "import", "exports": 4, "imports": 30, "trucks": 3}, {"angle": -22},
              "3 ships coming in, imports landing"),
             ({"light": "evening", "cargo": 1, "exports": 36, "imports": 2}, {"angle": 55, "height": 8, "dist": 20}, "evening, exports piled up")],
    "city": [({"size": 0.25, "traffic": 0.1}, None, "a small town"),
             ({"size": 1, "traffic": 0.9, "smog": 0.8}, {"angle": 10}, "a big city: jam and smog"),
             ({"size": 0.85, "light": "night", "lights": 0.8, "traffic": 0.5}, {"angle": 60, "height": 14, "dist": 26}, "night, windows lit")],
    "farm": [({"harvest": 0.1, "workers": 1}, None, "sown, one worker"),
             ({"harvest": 0.6, "workers": 10, "workplot": 1, "rain": 0.7}, {"angle": -20}, "rain, 10 workers crowd plot 1"),
             ({"harvest": 1, "drought": 0.5, "sacks": 20, "tractor": True, "plots": 5, "hillPlots": 2, "crops": "wheat;rice;wheat;wheat;none"},
              {"angle": 30, "height": 12, "dist": 24}, "ripe, dry year, sacks, hillside plots")],
    "vault": [({"open": 0}, None, "vault shut"), ({"open": 1, "level": 0.9}, {"angle": 4}, "open, reserves full"),
              ({"open": 1, "level": 0.2, "reserve": "notes"}, {"angle": 30, "height": 3, "dist": 13}, "open, few notes left")],
    "exchange": [({"trend": 0.8}, None, "the market rising"), ({"trend": -0.9, "crowd": 1}, {"angle": -24}, "the market falling, a busy floor")],
    "globe": [({"routes": "india-europe;china-usa", "volumes": "4;1"}, None, "two routes, goods moving"),
              ({"routes": "brazil-china;australia-japan;gulf-india", "volumes": "2;1;3", "highlight": "china", "face": "china"}, {"height": 5},
               "three routes, china pulsing")],
    "utilityHill": [({}, None, "the utility hill with 5 slices"),
                    ({"drop": 0.5, "planes": True, "show": 3}, {"angle": 60, "height": 6}, "slices falling to the floor"),
                    ({"drop": 1, "flatten": 1, "show": 3}, TOP, "top view: the indifference map")],
    "containerCube": [({"side": 1, "units": 1}, None, "1 m cube: 1 unit, 6 m2"),
                      ({"side": 2, "units": 8, "grid": True, "compare": True}, None, "2 m cube: 8 units"),
                      ({"side": 2, "faces": 1, "explode": 0.8, "grid": True}, {"angle": 50}, "faces apart: 6 x 4 m2")],
}


def states() -> list:
    """[(model, n, p, cam3d key or None, label)] for every model of the manifest (a model without states shows its defaults)."""
    out = []
    for name in models3d.names():
        for n, (p, cam, label) in enumerate(STATES.get(name) or [({}, None, "defaults")], 1):
            out.append((name, n, p, cam, label))
    return out


def sheet_spec(rows: list, width: int) -> dict:
    """One show-spec whose second ``i`` shows state ``i`` (its place or model, with its state named at the top)."""
    scenes = []
    for i, (name, n, p, cam, label) in enumerate(rows):
        entry = models3d.get(name)
        place = entry.get("role") == "place"
        w, h = (1920, 1080) if place else (1700, 1000)
        el = {"kind": "model3d", "id": "m", "model": name, "p": p, "steps": [], "x": 960, "y": 540 if place else 580, "w": w, "h": h,
              "s": 1, "z": 0, "t0": float(i), "t1": None, "enter": "none", "keys": [], "place": place,
              "cam3d": [dict(cam, t=float(i), d=0.001)] if cam else []}
        scenes.append({"id": f"s{i + 1}", "t0": float(i), "t1": float(i + 1), "bg": "paper", "cam": [], "els": [
            el, {"text": f"{name} · {label}", "size": 36, "style": "pill", "x": 960, "y": 52, "t0": float(i), "t1": None, "z": 40}]})
    return {"schema": "bie.show-spec/1", "fps": 30, "width": width, "height": round(width * 9 / 16), "duration": float(len(rows)),
            "subs": [], "assets": {}, "scenes": scenes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dist", type=Path, help="an already built engine preview (CI reuses the lane's build)")
    ap.add_argument("--width", type=int, default=1280)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    rows = states()
    spec = sheet_spec(rows, a.width)
    dist = a.dist or Path(tempfile.mkdtemp()) / "dist"
    frames = [i * 30 + 21 for i in range(len(rows))]           # 0.7 s into each state: the processes are moving
    pngs = render.stills(spec, frames, dist=dist)
    lines = [f"# 3D model still sheets ({len(models3d.names())} models, {len(rows)} states, {models3d.manifest()['licence']})\n"]
    names = []
    for (name, n, _, _, label), png in zip(rows, pngs):
        fname = f"models3d-{name}-{n}.png"
        (a.out / fname).write_bytes(png)
        names.append(fname)
        lines.append(f"- `{fname}`: {name}, {label}")
    try:
        from PIL import Image
        for k in range(0, len(pngs), 4):
            ims = [Image.open(io.BytesIO(p)).convert("RGB") for p in pngs[k:k + 4]]
            W, H = ims[0].size
            sheet = Image.new("RGB", (W * 2, H * 2), "white")
            for j, im in enumerate(ims):
                sheet.paste(im, ((j % 2) * W, (j // 2) * H))
            sname = f"models3d-sheet-{k // 4 + 1:02d}.png"
            sheet.save(a.out / sname)
            lines.append(f"- `{sname}`: {', '.join(names[k:k + 4])}")
    except ImportError:                                             # the frames alone still show every state
        pass
    (a.out / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"3D model stills: {len(rows)} states of {len(models3d.names())} models -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
