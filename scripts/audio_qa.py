#!/usr/bin/env python3
"""Audit a published AUDIO MIX output. Exit 0 PASS, 3 REVIEW, 2 FAIL/BLOCKED.

A diagnostic REVIEW report is written; it is NOT a release authorization.
No paid provider, GitHub write, or code execution from source text.
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--caption-intent',type=Path);p.add_argument('--standalone-fixture',action='store_true');a=p.parse_args()
    if a.standalone_fixture:sys.path.append(str(ROOT/'dependency_snapshot'))
    try:
        from bie.audio.common import strict_json
        from bie.audio.qa_source import load_published_mix
        from bie.audio.qa_pipeline import audit_mix
        from bie.audio.qa_io import publish_qa
        if a.output.absolute().is_relative_to(a.input.absolute()):raise ValueError('QA_OUTPUT_INSIDE_SOURCE')
        mixed,sync,files=load_published_mix(a.input)
        intent=strict_json(a.caption_intent.read_text()) if a.caption_intent else None
        stems=tuple(b for n,b in sorted(files.items()) if n.startswith('inputs/') and n.endswith('.wav'))
        report,captions=audit_mix(mixed,sync,asset_wavs=stems,intent=intent)
        publish_qa(report,captions,a.output)
        print(json.dumps({'status':report['status'],'checks':{c['task_id']:c['status'] for c in report['checks']},
            'report_fingerprint':report['fingerprint'],'product_accepted':False},indent=2))
        return 0 if report['status']=='PASS' else 3 if report['status']=='REVIEW' else 2
    except (ValueError,TypeError,OSError,KeyError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e),'product_accepted':False}),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
