"""One controlled local operator job; no Android/HTTP worker-control endpoint."""
import argparse, os, sys, time, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.operator.contracts import Credentials, Principal, PERMISSIONS
from apps.operator.service import Service

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args(); c=Credentials(); principal=Principal('local-operator','local',PERMISSIONS,time.time()+3600)
    c.grant(os.environ.get('BIE_OPERATOR_TOKEN',''),principal)
    result=Service(a.data_root,c).work_once(principal,a.run_id)
    print(json.dumps(result,sort_keys=True));return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception:
        print('Controlled worker action failed; no release authorized.',file=sys.stderr)
        raise SystemExit(2)
