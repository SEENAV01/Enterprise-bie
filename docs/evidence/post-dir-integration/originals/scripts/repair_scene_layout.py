#!/usr/bin/env python3
"""Bounded content-preserving repair, using real Chromium and explicit API doubles.

Exit 0: locally measured candidate and checked source published.
Exit 2: upstream layout revision required. Exit 3: environment/validation block.
None of these results grants real Remotion rendering or product acceptance.
"""
from pathlib import Path
from dataclasses import replace
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from bie.compiler.layout_repair import repair_and_publish
from bie.compiler.hardened_scene_compile import VERSION
from bie.compiler.qa_scene_compile import CompilerQATarget


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene',type=Path);parser.add_argument('destination',type=Path)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--policy',type=Path,help='Source-bound visual-owner permission. Omitted: reflow only inside existing boxes.')
    parser.add_argument('--width',type=int,default=640);parser.add_argument('--height',type=int,default=360)
    parser.add_argument('--fps',type=int,default=24);parser.add_argument('--browser',default='/usr/bin/chromium')
    parser.add_argument('--motion-preference',choices=['standard','reduced'],default='standard')
    parser.add_argument('--asset-root',type=Path,help='Verified local PCM root for dynamic narration repair')
    parser.add_argument('--screenshots',action='store_true')
    args=parser.parse_args()
    try:
        scene=json.loads(args.scene.read_text());policy=json.loads(args.policy.read_text()) if args.policy else None
        target=replace(CompilerQATarget(),compiler_version=VERSION,width=args.width,height=args.height,fps=args.fps)
        result=repair_and_publish(scene,policy,args.destination,args.evidence,target=target,browser=args.browser,
                                 motion_preference=args.motion_preference,screenshots=args.screenshots,asset_root=args.asset_root)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0 if result['source_published'] else (2 if result['status']=='UPSTREAM_REVISION_REQUIRED' else 3)
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print(json.dumps({'status':'INPUT_OR_PUBLICATION_BLOCKED','error':str(exc),'source_published':False,'accepted':False}));return 3
if __name__=='__main__':raise SystemExit(main())
