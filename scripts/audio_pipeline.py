#!/usr/bin/env python3
"""H5 local technical AUDIO lane. No GitHub mutation or live paid calls."""
from pathlib import Path
import argparse
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--standalone-fixture',action='store_true',help='Use pinned canonical dependency snapshots, not enterprise acceptance')
    sub=p.add_subparsers(dest='command',required=True)
    probe=sub.add_parser('probe');probe.add_argument('--output',type=Path,required=True)
    req=sub.add_parser('request');req.add_argument('input',type=Path);req.add_argument('--profile',type=Path,required=True)
    req.add_argument('--run-id',required=True);req.add_argument('--job-id',required=True);req.add_argument('--revision',required=True)
    req.add_argument('--key-id',required=True);req.add_argument('--output',type=Path,required=True)
    req.add_argument('--preparation-profile',choices=('batch001-144','batch001-204'),default='batch001-144')
    run=sub.add_parser('run');verify=sub.add_parser('verify-export')
    for parser in (run,verify):
        for name in ('request','profile','trust'):parser.add_argument('--'+name,type=Path,required=True)
    run.add_argument('--private-key-file',type=Path,required=True);run.add_argument('--root',type=Path,required=True)
    run.add_argument('--output',type=Path,required=True);run.add_argument('--allow-technical-voice',action='store_true')
    run.add_argument('--allow-review-output',action='store_true');verify.add_argument('folder',type=Path)
    a=p.parse_args(argv)
    if a.standalone_fixture:sys.path.append(str(ROOT/'dependency_snapshot'))
    from bie.audio.pipeline_io import read_json,read_private_key,publish_export,verify_export
    from bie.audio.pipeline_profile import probe_profile,validate_profile
    from bie.audio.pipeline_contract import build_request
    from bie.audio.pipeline_durable import execute_durable
    from bie.audio.acoustic_contract import canonical
    from bie.audio.common import AudioError
    try:
        if a.command=='probe':
            v=probe_profile()
            with a.output.open('xb') as f:f.write(canonical(v))
            result={'status':'DISCOVERED_NOT_APPROVED','profile_fingerprint':v['fingerprint'],'product_accepted':False}
        elif a.command=='request':
            profile=read_json(a.profile);validate_profile(profile)
            v=build_request(read_json(a.input),profile_fingerprint=profile['fingerprint'],run_id=a.run_id,
                job_id=a.job_id,revision=a.revision,key_id=a.key_id,preparation_profile=a.preparation_profile)
            with a.output.open('xb') as f:f.write(canonical(v))
            result={'status':'REQUEST_PREPARED_NO_EXECUTION','request_fingerprint':v['fingerprint'],'product_accepted':False}
        else:
            request,profile,trust=map(read_json,(a.request,a.profile,a.trust))
            if a.command=='verify-export':
                result={'status':'VERIFIED_TECHNICAL_EXPORT',**verify_export(a.folder,request,profile,trust)}
            else:
                if not a.allow_technical_voice or not a.allow_review_output:
                    raise AudioError('PIPELINE_TECHNICAL_REVIEW_OPT_IN_REQUIRED')
                # Refuse output overwrite before any potentially expensive work.
                if a.output.exists() or a.output.is_symlink():raise AudioError('PIPELINE_EXPORT_EXISTS')
                signer=read_private_key(a.private_key_file)
                r=execute_durable(request,profile,trust,signer,root=a.root)
                export=publish_export(r,request,profile,trust,a.output,allow_technical_voice=True,allow_review=True)
                result={'status':'TECHNICAL_REVIEW_OUTPUT','cache_hit':r['cache_hit'],
                    'native_pipeline_runs':r['native_pipeline_runs'],'artifact_ref':r['artifact_ref'],
                    'state':r['state'],'export':export,'product_accepted':False}
        print(json.dumps(result,sort_keys=True,indent=2));return 0
    except (ValueError,OSError,RuntimeError,TypeError,KeyError) as exc:
        print(json.dumps({'status':'BLOCKED','error_code':getattr(exc,'code',type(exc).__name__),
            'product_accepted':False}),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
