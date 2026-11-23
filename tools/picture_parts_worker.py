#!/usr/bin/env python3
"""Cut the moving parts of a film's pictures (``bie/brain/picture_parts.py``), in the studio machine's voice environment,
which has torch and transformers:

    <voice-venv>/bin/python -B tools/picture_parts_worker.py --request request.json --result result.json

request.json: {"revision": ..., "threads": 2, "out": <folder>, "shots": [{"id": ..., "image": <png>, "parts": [{"id": ...,
"inside": [[x, y]], "box": [x0, y0, x1, y1], "moves": true}]}]}. Each sound part is written as <out>/<shot>-<part>.png
(the part's crop, transparent outside it), each plate as <out>/<shot>-plate.png; result.json lists them with their boxes
and every cut that failed with its reason. The model is loaded once for the whole film."""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--request", type=Path, required=True)
    p.add_argument("--result", type=Path, required=True)
    args = p.parse_args(argv)
    request = json.loads(args.request.read_text(encoding="utf-8"))
    out = Path(request["out"])
    out.mkdir(parents=True, exist_ok=True)
    result = {"shots": [], "error": None}
    try:
        sys.path.insert(0, str(ROOT))
        from PIL import Image
        from bie.brain import picture_parts
        t0 = time.monotonic()
        cutter = picture_parts.Sam2Cutter(request.get("revision") or picture_parts.REVISION, request.get("threads"))
        result["load_s"] = round(time.monotonic() - t0, 1)
        for shot in request.get("shots") or []:
            t1 = time.monotonic()
            row = {"id": shot["id"], "layers": [], "plate": None}
            try:
                done = picture_parts.cut_shot(Image.open(shot["image"]), shot.get("parts") or [], cutter)
                for got in done["layers"]:
                    entry = {k: got.get(k) for k in ("id", "box", "centre", "area", "score", "problems")}
                    if got.get("image") is not None:
                        name = f"{shot['id']}-{got['id']}.png"
                        got["image"].save(out / name)
                        entry["file"] = str(out / name)
                    row["layers"].append(entry)
                if done["plate"] is not None:
                    done["plate"].save(out / f"{shot['id']}-plate.png")
                    row["plate"] = str(out / f"{shot['id']}-plate.png")
            except Exception as exc:                 # one picture failing leaves the others cut
                row["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            row["seconds"] = round(time.monotonic() - t1, 2)
            result["shots"].append(row)
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
        result["trace"] = traceback.format_exc()[-1200:]
    args.result.write_text(json.dumps(result, indent=1), encoding="utf-8")
    return 0 if not result["error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
