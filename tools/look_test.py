"""The look test: the same shots of finished films drawn again in another cutaway style, so Navin can put them side by
side (Navin, 22 November 2026: "visuals ... abhi alag se dekhein, tabhi paas karunga").

    python -B tools/look_test.py --from-run <films run: folder or https URL> --shots a15:s4,a16:s3 --style matte --out prompts.json

Writes a ``bie.image-prompts/1`` file for the VM's ``image`` section (at most 4 prompts per job): each prompt is the shot's
own picture prompt and its film's look, written by the film maker, with the chosen style (``studio_film.CUTAWAY_STYLES``)
in place of the film's. Nothing in the prompt is written by hand.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from bie.brain import studio_film  # noqa: E402

MAX_PROMPTS = 4


def prompts(from_run: str, shots: list, style: str) -> dict:
    from vm_studio import read_json
    if style not in studio_film.CUTAWAY_STYLES:
        raise ValueError(f"style: one of {', '.join(studio_film.CUTAWAY_STYLES)}")
    if not 1 <= len(shots) <= MAX_PROMPTS:
        raise ValueError(f"shots: 1 to {MAX_PROMPTS}")
    out = []
    for qid, sid in shots:
        film = read_json(from_run, f"films/{qid}.json")["film"]
        shot = next((s for s in film.get("shots") or [] if s.get("id") == sid), None)
        if shot is None:
            raise ValueError(f"{qid} has no shot {sid}")
        if (shot.get("visual") or {}).get("type") != "cutaway":
            raise ValueError(f"{qid} {sid} is not a cutaway; the look test changes cutaways only")
        out.append({"id": f"{qid}-{sid}-{style}".lower(), "prompt": studio_film.image_prompt(shot, film.get("look", ""), style)})
    return {"schema": "bie.image-prompts/1", "note": f"look test, style {style}", "prompts": out}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from-run", required=True)
    parser.add_argument("--shots", required=True, help="qid:shot pairs, for example a15:s4,a16:s3")
    parser.add_argument("--style", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    shots = [tuple(pair.split(":", 1)) for pair in args.shots.split(",") if ":" in pair]
    data = prompts(args.from_run, shots, args.style)
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(data['prompts'])} prompts, style {args.style}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
