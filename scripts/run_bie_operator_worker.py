"""One controlled local operator job; no Android/HTTP worker-control endpoint."""
import argparse, sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from apps.operator.worker_execution import execute_worker

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True);p.add_argument('--run-id',required=True)
    a=p.parse_args()
    result=execute_worker(a.data_root,a.run_id)
    print(json.dumps(result,sort_keys=True));return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception:
        print('Controlled worker action failed; no release authorized.',file=sys.stderr)
        raise SystemExit(2)
