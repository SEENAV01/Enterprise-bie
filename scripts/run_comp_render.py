#!/usr/bin/env python3
"""Run BUILD-007/008 from a JSON request using the real local Remotion backend.

Source must come from compile_scene_checked.py and is revalidated before render.
No dependency install or test-runner injection is performed by this entry point.
Exit 0: technically verified artifact; 1: logged execution failure; 2: invalid input.
Product acceptance remains false regardless of exit status.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.compiler.build_common import BuildError
from bie.compiler.full_render import full_render
from bie.compiler.checked_scene_compile import verify_checked_workspace
from bie.compiler.smoke_render import smoke_render
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="JSON matching RenderRequest; relative workspace resolved beside JSON")
    parser.add_argument("--mode", required=True, choices=("smoke", "full"))
    parser.add_argument("--first-frame", type=int, default=0)
    parser.add_argument("--frame-count", type=int, default=None)
    args = parser.parse_args()
    try:
        raw = json.loads(args.request.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise BuildError("request must be an object")
        raw["composition"] = CompositionDescriptor(**raw["composition"])
        workspace = Path(raw["workspace"])
        if not workspace.is_absolute():
            raw["workspace"] = str((args.request.resolve().parent / workspace).resolve())
        request = RenderRequest(**raw)
        verify_checked_workspace(Path(request.workspace), expected_scene_fingerprint=request.scene_fingerprint, render_request=request)
        if args.mode == "full":
            if args.first_frame != 0 or args.frame_count is not None:
                raise BuildError("full mode does not permit a frame subset")
            receipt = full_render(request)
        else:
            if args.frame_count is None:
                raise BuildError("smoke mode requires explicit --frame-count")
            receipt = smoke_render(request, first_frame=args.first_frame, frame_count=args.frame_count)
        print(json.dumps(asdict(receipt), indent=2))
        return 0 if receipt.passed else 1
    except (BuildError, OSError, TypeError, ValueError, KeyError) as exc:
        print(json.dumps({"passed": False, "accepted": False, "error": str(exc)}), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
