"""Read-only failure classification. CLI cannot supply keys or run arbitrary code.

Exit0: no repair required (requires operator API authority);3: review/routing;
2: invalid/missing evidence;4: output exists. Use the API for registered validators.
"""
from pathlib import Path
import argparse,sys,json
from ..release_v2.contracts import ContractError,canonical_bytes
from .codec import load_snapshot,load_batch,load_policy
from .planner import classify,route_summary

def read(path):
    with Path(path).open('rb') as f:b=f.read(4*1024*1024+1)
    if len(b)>4*1024*1024:raise ContractError('REPAIR_CLI_LIMIT')
    return b

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',required=True);p.add_argument('--batch',required=True);p.add_argument('--policy',required=True);p.add_argument('--artifact-root',required=True);p.add_argument('--as-of',required=True,type=int);p.add_argument('--output')
    a=p.parse_args(argv)
    try:
        policy=load_policy(read(a.policy));plan=classify(load_batch(read(a.batch)),load_snapshot(read(a.snapshot)),a.artifact_root,policy,as_of=a.as_of)
        data=canonical_bytes(dict(classification=plan.to_dict(),routing=route_summary(plan,policy),code_execution_enabled=False))
        if a.output:
            with Path(a.output).open('xb') as f:f.write(data+b'\n')
        print(data.decode());return 0 if plan.status=='NO_REPAIR_NEEDED' else 3
    except FileExistsError:print('REPAIR_OUTPUT_EXISTS',file=sys.stderr);return 4
    except (ContractError,OSError,ValueError,TypeError) as e:print(e.code if isinstance(e,ContractError) else 'REPAIR_INPUT_ERROR',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
