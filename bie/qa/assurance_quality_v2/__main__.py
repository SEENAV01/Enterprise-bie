"""Read-only correction-inspection CLI. No signing, native execution or publication."""
from pathlib import Path
import argparse,json,sys
from .common import strict_object,Binding,ArtifactRef,ContractError
from .memory import CorrectionPlan,inspect_correction

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('request',type=Path);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args()
    try:
        raw=strict_object(a.request.read_bytes())
        if set(raw)!= {'plan','binding'}:raise ContractError('H8_CLI_FIELDS')
        q=raw['plan']
        for key in ('source','before','after','validation'):q[key]=ArtifactRef(**q[key])
        for key in ('required_cases','target_cases','rerun_gates'):q[key]=tuple(q[key])
        plan=CorrectionPlan(**q);inspect_correction(a.root,plan,Binding(**raw['binding']))
        print(json.dumps({'status':'REVIEW_REQUIRED','inspected':True,'product_accepted':False}));return 3
    except (ContractError,OSError,ValueError,TypeError,KeyError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'product_accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
