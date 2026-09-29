"""Read-only math/parser audit; never import a callback selected in input JSON.

Other native-object adapters use the typed Python API. stdout contains a report;
exit 3 means review, 1 blocker, 2 malformed input. No output file is overwritten.
"""
from pathlib import Path
import argparse,json,sys
from .common import Binding,ArtifactRef,read_json,SnapshotStore,ContractError,fields
from .mathematics import MathPolicy,evaluate_math
from .parser import ParserPolicy,evaluate_parser

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('math','parser'));p.add_argument('--root',type=Path,required=True)
    p.add_argument('--request',type=Path,required=True)
    args=p.parse_args()
    try:
        raw=args.request.read_bytes()
        if len(raw)>65536:raise ValueError('request size')
        def pairs(v):
            d={}
            for k,x in v:
                if k in d:raise ValueError('duplicate key')
                d[k]=x
            return d
        d=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError('nonfinite')))
        fields(d,('binding','artifact','policy'))
        b=Binding(**d['binding']);ref=ArtifactRef(**d['artifact']);kw=dict(d['policy']);kw['required_ids']=tuple(kw['required_ids'])
        policy=MathPolicy(**kw)if args.mode=='math'else ParserPolicy(**kw)
        evaluator=evaluate_math if args.mode=='math'else evaluate_parser
        report,details=evaluator(ref,args.root,b,policy)
        print(json.dumps({'report':report.to_dict(),'details':details},sort_keys=True,ensure_ascii=False))
        return 1 if report.status=='BLOCKED'else 3
    except (ContractError,ValueError,TypeError,KeyError,OSError)as exc:
        print(json.dumps({'status':'INVALID_INPUT','code':getattr(exc,'code',type(exc).__name__),'release_authorized':False}),file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())
