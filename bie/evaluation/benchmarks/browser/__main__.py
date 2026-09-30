"""Observed-browser CLI. Requires a trusted scenario and pinned native Chromium."""
import argparse,json
from pathlib import Path
from dataclasses import asdict
from ..models import BenchmarkError,canonical_json,strict_loads
from .contracts import BrowserExecutionContext,BrowserLimits
from .ledger import BrowserStore

def read(path):
    raw=Path(path).read_bytes()
    if len(raw)>1_000_000:raise BenchmarkError('BROWSER_CLI_INPUT_LIMIT')
    return strict_loads(raw.decode('utf-8'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['run','get','recover'])
    p.add_argument('--db',required=True);p.add_argument('--run-id',required=True)
    p.add_argument('--campaign');p.add_argument('--reference');p.add_argument('--candidate');p.add_argument('--context')
    p.add_argument('--reference-sha');p.add_argument('--candidate-sha');p.add_argument('--reservation-sha');p.add_argument('--reason')
    a=p.parse_args()
    try:
        with BrowserStore(a.db) as store:
            if a.action=='get':r=store.get(a.run_id)
            elif a.action=='recover':r=store.recover(a.run_id,expected_reservation_sha256=a.reservation_sha,reason=a.reason)
            else:
                if not all([a.campaign,a.reference,a.candidate,a.context,a.reference_sha,a.candidate_sha]):
                    raise BenchmarkError('BROWSER_CLI_REQUIRED_ARGUMENTS')
                ctx=read(a.context);ctx['limits']=BrowserLimits(**ctx.get('limits',{}));ctx=BrowserExecutionContext(**ctx)
                r=store.execute(a.run_id,a.campaign,read(a.reference),read(a.candidate),
                    expected_reference_sha256=a.reference_sha,expected_candidate_sha256=a.candidate_sha,context=ctx)
        print(canonical_json(r));return 0 if r['result']['status']=='MEASURED' and r['result']['outcome']=='PASS' else 2
    except (BenchmarkError,TypeError,ValueError,OSError) as exc:
        print(canonical_json({'status':'BLOCKED','error_code':exc.code if isinstance(exc,BenchmarkError) else 'BROWSER_CLI_ERROR','product_accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
