#!/usr/bin/env python3
"""The picture cupboard (almaari): keep the best pictures BIE has made, so later films use them again.

Navin approved this on 21 November 2026 ("Haan, BIE mein banao"): a kept picture is used again whenever a film needs
that scene, and a new one is drawn only when no kept picture fits or the kept one is wrong. This tool copies chosen
pictures out of finished studio runs into a cupboard folder and writes its ``library.json``; a studio job whose
from-run folder holds that cupboard lets the maker use them (``visual.library``, tools/vm_studio.py).

    python3 tools/picture_library.py --out <folder> \
        --keep "<run folder>|q14|s4|thylakoid-closed-sac|closed thylakoid sac" ...

Each --keep is ``run folder|question id|shot id|picture id|scale``. The entry takes the shot's visual type and picture
description from the run's film, and its labelled places from the pins the film placed on that picture. Its set is the
run it came from: close-ups of one structure in one film come from one set ("ATP synthase close up: ..." groups them).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def entry(run: Path, qid: str, shot_id: str, picture_id: str, scale: str, note: str = "") -> tuple[dict, Path]:
    """(library entry, picture file) for one shot of a finished run."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,60}", picture_id):
        raise ValueError(f"picture id {picture_id!r}: lowercase letters, digits and dashes")
    record = json.loads((run / "films" / f"{qid}.json").read_text(encoding="utf-8"))
    shots = {s.get("id"): s for s in (record.get("film") or {}).get("shots") or []}
    if shot_id not in shots:
        raise KeyError(f"{run.name}: no shot {shot_id} in {qid}")
    shot = shots[shot_id]
    name = (record.get("images") or {}).get(shot_id) or f"{qid}-{shot_id}.png"
    picture = run / "films" / "img" / name
    if not picture.exists():
        raise FileNotFoundError(picture)
    places, seen = [], set()
    for sentence in shot.get("sentences") or []:
        for pin in sentence.get("pins") or []:
            label = (pin.get("label") or "").strip()
            if label and label.lower() not in seen and "x" in pin and "y" in pin:
                seen.add(label.lower())
                places.append({"label": label, "x": round(float(pin["x"])), "y": round(float(pin["y"]))})
    visual = shot.get("visual") or {}
    return ({"id": picture_id, "type": visual.get("type") or "cutaway", "scale": scale,
             "shows": (visual.get("image_prompt") or "").strip(), "places": places[:8],
             "file": f"library/{picture_id}{picture.suffix}", "from": f"{run.name} {qid} {shot_id}", "set": run.name,
             "note": note}, picture)


def build(out: Path, keeps: list[str], approved: str = "") -> dict:
    """Write ``out/library.json`` and copy each kept picture to ``out/library/``; an id kept twice keeps the last."""
    (out / "library").mkdir(parents=True, exist_ok=True)
    old = out / "library.json"
    pictures = {p["id"]: p for p in (json.loads(old.read_text(encoding="utf-8")).get("pictures") or [])} if old.exists() else {}
    for keep in keeps:
        parts = keep.split("|")
        if len(parts) not in (5, 6):
            raise ValueError(f"--keep {keep!r}: run|qid|shot|id|scale[|note]")
        made, picture = entry(Path(parts[0]), parts[1], parts[2], parts[3], parts[4], parts[5] if len(parts) == 6 else "")
        shutil.copyfile(picture, out / made["file"])
        pictures[made["id"]] = made
    library = {"approved": approved, "pictures": list(pictures.values())}
    old.write_text(json.dumps(library, ensure_ascii=False, indent=1), encoding="utf-8")
    return library


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--keep", action="append", default=[])
    parser.add_argument("--approved", default="")
    args = parser.parse_args()
    library = build(Path(args.out), args.keep, args.approved)
    print(json.dumps({"pictures": [p["id"] for p in library["pictures"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
