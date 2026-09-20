#!/usr/bin/env python3
"""Regenerate and diagnose explicitly composed frame runtime; NOT a render."""
from pathlib import Path
from dataclasses import asdict
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bie.compiler.qa_scene_compile import CompilerQATarget
from bie.compiler.hardened_scene_compile import compile_h3_scene
from bie.compiler.composition_conformance import verify_composition

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scene',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--width',type=int,default=1280);ap.add_argument('--height',type=int,default=720);ap.add_argument('--fps',type=int,default=12)
    a=ap.parse_args()
    if a.output.exists() or a.output.is_symlink() or any(p.is_symlink() for p in a.output.absolute().parents):
        ap.error('output must be new with no symlink ancestors')
    a.output.mkdir(parents=True)
    report={'scope':'COMPOSITION_DIAGNOSTICS_NOT_ACTUAL_RENDER','passed':False,'accepted':False}
    try:
        if not a.scene.is_file() or a.scene.stat().st_size>4*1024*1024:raise ValueError('bounded scene file required')
        document=json.loads(a.scene.read_text(encoding='utf-8'))
        target=CompilerQATarget(width=a.width,height=a.height,fps=a.fps,compiler_version='1.3.0-comp-h3')
        result=compile_h3_scene(document,target=target)
        (a.output/'SOURCE_RECEIPT.json').write_text(json.dumps(asdict(result.receipt),indent=2))
        report=verify_composition(result,target)
    except (ValueError,OSError,TypeError,KeyError) as exc:report['failure']=str(exc)
    (a.output/'RESULT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
