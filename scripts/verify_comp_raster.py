#!/usr/bin/env python3
"""Diagnostic counterfactual PNG checks of an existing BIE Scene IR.

Executes generated components through explicit React/Remotion API doubles in
real Chromium. Never grants actual-render or product acceptance.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import replace
import argparse,json
from bie.compiler.qa_scene_compile import CompilerQATarget
from bie.compiler.hardened_scene_compile import compile_h3_scene,VERSION
from bie.compiler.raster_browser import measure_raster_scene

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--width',type=int,default=640);parser.add_argument('--height',type=int,default=360);parser.add_argument('--fps',type=int,default=24)
    parser.add_argument('--browser',default='/usr/bin/chromium');a=parser.parse_args()
    target=CompilerQATarget(width=a.width,height=a.height,fps=a.fps,compiler_version=VERSION)
    raw=json.loads(a.scene.read_text(encoding='utf-8'));compiled=compile_h3_scene(raw,target=target)
    result=measure_raster_scene(compiled,target,a.out,browser=a.browser)
    print(json.dumps({'passed':result['passed'],'scope':result['scope'],'frames':result['frame_count'],'findings':result['findings'],'accepted':False,'release_authorized':False},ensure_ascii=False))
    return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
