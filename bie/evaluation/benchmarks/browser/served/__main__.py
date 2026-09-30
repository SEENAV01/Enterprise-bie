"""Export/verify stored browser evidence. Run/get/recover use the existing browser CLI."""
import argparse
from ...models import BenchmarkError,canonical_json
from ..ledger import BrowserStore
from .export import export_run,verify_export

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['export','verify'])
    p.add_argument('--archive',required=True);p.add_argument('--db');p.add_argument('--run-id');a=p.parse_args()
    try:
        if a.action=='verify':r=verify_export(a.archive)
        else:
            if not a.db or not a.run_id:raise BenchmarkError('HTTP_EXPORT_ARGUMENTS_REQUIRED')
            with BrowserStore(a.db) as store:r=export_run(store,a.run_id,a.archive)
        print(canonical_json(r));return 0
    except (BenchmarkError,OSError) as exc:
        print(canonical_json({'status':'BLOCKED','error_code':exc.code if isinstance(exc,BenchmarkError) else 'HTTP_EXPORT_IO_ERROR'}));return 2
if __name__=='__main__':raise SystemExit(main())
