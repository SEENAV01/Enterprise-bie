"""Operator CLI: run pinned AV evidence, get receipts, or map native declarations."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from ..models import BenchmarkError,canonical_json
from .custody import read_json,Limits
from .ledger import AVRunStore
from .native import map_render_receipt

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run')
    for name in ('database','campaign','run-id','media','media-sha256','policy','policy-sha256'):run.add_argument('--'+name,required=True)
    run.add_argument('--captions');run.add_argument('--captions-sha256');run.add_argument('--caption-format',choices=['srt','vtt'],default='srt')
    run.add_argument('--deadline',type=float,default=900)
    get=sub.add_parser('get');get.add_argument('--database',required=True);get.add_argument('--run-id',required=True)
    rec=sub.add_parser('recover')
    for n in ('database','run-id','candidate-sha256','policy-sha256','reason'):rec.add_argument('--'+n,required=True)
    native=sub.add_parser('map-native')
    for n in ('native-receipt','av-receipt','contract-file','commit','run-id','input-sha256','recipe-sha256','composition-id'):native.add_argument('--'+n,required=True)
    a=p.parse_args(argv)
    try:
        if a.command=='map-native':
            result=map_render_receipt(read_json(a.native_receipt),read_json(a.av_receipt),expected_commit=a.commit,
                expected_run_id=a.run_id,expected_input_sha256=a.input_sha256,expected_recipe_sha256=a.recipe_sha256,
                expected_composition_id=a.composition_id,contract_path=a.contract_file)
            print(canonical_json(result));return 0
        if a.command in ('get','recover') and not Path(a.database).is_file():raise BenchmarkError('AV_DATABASE_MISSING')
        with AVRunStore(a.database) as store:
            if a.command=='run':
                result=store.execute(campaign_id=a.campaign,run_id=a.run_id,media_path=a.media,media_sha256=a.media_sha256,
                    policy=read_json(a.policy),policy_sha256=a.policy_sha256,caption_path=a.captions,
                    caption_sha256=a.captions_sha256,caption_format=a.caption_format,limits=Limits(deadline_s=a.deadline))
            elif a.command=='get':result=store.get(a.run_id)
            else:result=store.recover(a.run_id,candidate_sha256=a.candidate_sha256,policy_sha256=a.policy_sha256,operator_reason=a.reason)
        print(canonical_json(result));return 0 if result['status']=='DIAGNOSTIC_PASS' else 2
    except (BenchmarkError,OSError) as e:
        print(json.dumps({'status':'BLOCKED','error_code':e.code if isinstance(e,BenchmarkError) else 'OPERATOR_IO_ERROR',
                          'release_authorized':False,'product_accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
