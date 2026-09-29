"""Read-only file census CLI. It neither runs candidate code nor publishes releases."""
import argparse,json,sys
from pathlib import Path
from .common import inventory,ContractError
p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);args=p.parse_args()
try:
    value={'status':'REVIEW_REQUIRED','files':inventory(args.root),'product_accepted':False}
    print(json.dumps(value,sort_keys=True));raise SystemExit(3)
except (ContractError,OSError,ValueError) as e:
    print(json.dumps({'status':'BLOCKED','error':str(e),'product_accepted':False}),file=sys.stderr);raise SystemExit(4)
