#!/usr/bin/env python3
"""Publish Scene IR source only after capability/source and real AST gates pass."""
from pathlib import Path
from dataclasses import asdict, replace
import argparse, json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from bie.compiler.hardened_scene_compile import publish_h3_scene

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene",type=Path);parser.add_argument("destination",type=Path)
    parser.add_argument("--motion-preference", choices=("standard","reduced"), default="standard")
    parser.add_argument("--layout-policy",type=Path,help="Explicit H4 repair contract; preserves legacy H3 default without this flag")
    parser.add_argument("--layout-evidence",type=Path)
    parser.add_argument("--browser",default="/usr/bin/chromium")
    parser.add_argument('--width',type=int,default=640)
    parser.add_argument('--height',type=int,default=360)
    parser.add_argument('--fps',type=int,default=24)
    args=parser.parse_args()
    try:
        from bie.compiler.qa_scene_compile import CompilerQATarget
        from bie.compiler.hardened_scene_compile import VERSION
        target=replace(CompilerQATarget(),compiler_version=VERSION,width=args.width,height=args.height,fps=args.fps)
        if args.layout_policy is not None:
            if args.layout_evidence is None:
                raise ValueError("--layout-evidence required with --layout-policy")
            from bie.compiler.layout_repair import repair_and_publish
            result=repair_and_publish(json.loads(args.scene.read_text()),json.loads(args.layout_policy.read_text()),args.destination,args.layout_evidence,browser=args.browser,motion_preference=args.motion_preference,target=target)
            print(json.dumps(result,indent=2));return 0 if result["source_published"] else 2
        if args.layout_evidence is not None:
            raise ValueError("--layout-evidence requires --layout-policy")
        receipt=publish_h3_scene(json.loads(args.scene.read_text()),args.destination,motion_preference=args.motion_preference,target=target)
        print(json.dumps(asdict(receipt),indent=2));return 0
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(json.dumps({"source_gate_passed":False,"accepted":False,"error":str(exc)}));return 2
if __name__ == "__main__":raise SystemExit(main())
