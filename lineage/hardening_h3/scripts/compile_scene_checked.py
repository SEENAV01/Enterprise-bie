#!/usr/bin/env python3
"""Publish Scene IR source only after capability/source and real AST gates pass."""
from pathlib import Path
from dataclasses import asdict
import argparse, json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from bie.compiler.hardened_scene_compile import publish_h3_scene

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene",type=Path);parser.add_argument("destination",type=Path)
    parser.add_argument("--motion-preference", choices=("standard","reduced"), default="standard")
    args=parser.parse_args()
    try:
        receipt=publish_h3_scene(json.loads(args.scene.read_text()),args.destination,motion_preference=args.motion_preference)
        print(json.dumps(asdict(receipt),indent=2));return 0
    except (ValueError, TypeError, OSError, KeyError) as exc:
        print(json.dumps({"source_gate_passed":False,"accepted":False,"error":str(exc)}));return 2
if __name__ == "__main__":raise SystemExit(main())
