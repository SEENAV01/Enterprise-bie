"""Operator CLI. JSON roots/limits come from explicit CLI arguments, not candidates."""
from pathlib import Path
import argparse,json,sys
from ..models import BenchmarkError,strict_loads,canonical_json
from ..av.custody import Limits
from .contracts import ExecutionContext
from .ledger import AdoptionStore

def read(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file():raise BenchmarkError('CLI_INPUT_UNSAFE')
    with p.open('rb') as f:b=f.read(2_000_001)
    if len(b)>2_000_000:raise BenchmarkError('CLI_JSON_LIMIT')
    try:return strict_loads(b.decode('utf-8'))
    except UnicodeError as exc:raise BenchmarkError('CLI_JSON_ENCODING') from exc

def main(argv=None):
    parser=argparse.ArgumentParser(description='Section17 governed AV metric execution; never product acceptance')
    parser.add_argument('--db',required=True)
    sub=parser.add_subparsers(dest='action',required=True)
    run=sub.add_parser('run')
    for name in ('campaign','campaign-sha256','context','reference','candidate','code-sha256','artifact-root'):
        run.add_argument('--'+name,required=True)
    run.add_argument('--limits')
    get=sub.add_parser('get');get.add_argument('--run-id',required=True);get.add_argument('--campaign-sha256',required=True)
    recover=sub.add_parser('recover');recover.add_argument('--run-id',required=True)
    recover.add_argument('--context-sha256',required=True);recover.add_argument('--operator-reason',required=True)
    args=parser.parse_args(argv)
    try:
        with AdoptionStore(args.db) as store:
            if args.action=='run':
                limits=Limits(**read(args.limits)) if args.limits else Limits()
                r=store.execute(read(args.campaign),read(args.context),read(args.reference),read(args.candidate),
                    expected_campaign_sha256=args.campaign_sha256,expected_code_sha256=args.code_sha256,
                    execution_context=ExecutionContext(args.artifact_root,limits))
            elif args.action=='get':r=store.get(args.run_id,expected_campaign_sha256=args.campaign_sha256)
            else:r=store.recover(args.run_id,expected_context_sha256=args.context_sha256,operator_reason=args.operator_reason)
        print(canonical_json(r));return 0 if r['status']=='MEASURED' and r['score_exact']=='1' else 2
    except BenchmarkError as exc:
        print(canonical_json({'status':'BLOCKED','reason':exc.code,'release_authorized':False,'product_accepted':False}));return 2
    except Exception:
        print(canonical_json({'status':'BLOCKED','reason':'OPERATOR_EXECUTION_FAILED','release_authorized':False,'product_accepted':False}));return 2

if __name__=='__main__':raise SystemExit(main())
