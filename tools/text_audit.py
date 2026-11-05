"""Measure the texts of a video as drawn: texts under the readable floor and texts that cover each other (Task 048).

Navin, 3 November 2026: "minimum on-screen text size readable on a phone", "label overlap in every mode". Renders the spec
in the same preview page the stills and the MP4 use, measures every sampled frame (``bie/brain/video/preview/audit.mjs``) and
writes the record of ``bie.brain.video.text_audit``. At ₹0: no AI call.

    python -B tools/text_audit.py --spec video_spec.json [--assets assets/] [--dist <preview build>] [--every 30] --out audit.json

also writes the measurements themselves next to the record (``audit.frames.jsonl``), so the record can be read again with
``--frames`` (no render) when the rules of the record change. The record carries ``gate`` (``text_audit.gate``, the box
rule's last check, Navin 5 November 2026): the render workflow publishes no review copy for a video that fails it.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bie.brain import formats  # noqa: E402
from bie.brain.video import render, text_audit, timing  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--assets", type=Path)
    ap.add_argument("--dist", type=Path, help="a preview build to reuse (built here when missing)")
    ap.add_argument("--every", type=int, default=30, help="sample every N frames (30 = once a second)")
    ap.add_argument("--from", dest="first", type=int)
    ap.add_argument("--to", dest="last", type=int)
    ap.add_argument("--frames", type=Path, help="measurements written before (no render)")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    spec = json.loads(a.spec.read_text(encoding="utf-8"))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    if a.frames:
        frames = text_audit.read_jsonl(a.frames)
    else:
        dist = a.dist or Path(tempfile.mkdtemp(prefix="bie-audit-dist-"))
        frames = render.audit(spec, dist=dist, assets=a.assets, every=a.every, first=a.first, last=a.last)
        a.out.with_suffix(".frames.jsonl").write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in frames),
                                                       encoding="utf-8")
    record = text_audit.summarize(frames, floor=spec.get("min_text_px") or text_audit.FLOOR_PX,
                                  fps=spec.get("fps") or timing.FPS, every=a.every,
                                  captions=text_audit.caption_texts(spec))
    record["spec"] = str(a.spec)
    # the box rule's last check: a show-spec's frames mark the plan's own words (the show engine), an older VideoSpec's do not
    record["gate"] = text_audit.gate(record, plan_marks=str(spec.get("schema", "")).startswith("bie.show-spec"))
    formats.check("text_audit", record, where=str(a.out))
    a.out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{a.spec.name}: {record['frames_sampled']} frames, smallest text {record['min_px']} px, "
          f"{record['small_count']} texts under {record['floor_px']} px ({record['lasting_small_count']} lasting), "
          f"{record['overlap_count']} overlapping pairs "
          f"({record['lasting_overlap_count']} lasting), {record['caption_overlap_count']} under the caption; "
          f"overlaps {record['overlap_seconds']} s in all, longest {record['longest_overlap_s']} s; gate "
          + ("passed" if record["gate"]["passed"] else
             f"FAILED ({record['gate']['long_overlaps']} overlaps over {record['gate']['long_s']:.0f} s, "
             f"{record['gate']['small_plan_texts']} plan texts under {record['floor_px']} px)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
