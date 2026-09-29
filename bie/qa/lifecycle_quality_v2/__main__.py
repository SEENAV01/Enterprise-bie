"""Read-only journal inspection. No repair execution, imports or release from JSON."""
import argparse,json,sqlite3
from pathlib import Path
from .common import Binding,strict_json,ContractError
from .durable import LeaseJournal,LeasePolicy

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('journal',type=Path);p.add_argument('--context',type=Path,required=True);a=p.parse_args()
    try:
        if not a.journal.is_file():raise ContractError('H6_JOURNAL_NOT_FOUND')
        if a.journal.is_symlink():raise ContractError('H6_JOURNAL_LINK')
        # Export via a temporary copy so inspection never changes the original DB/WAL.
        import tempfile
        c=strict_json(a.context.read_bytes())
        with tempfile.TemporaryDirectory(prefix='h6-read-') as d:
            path=Path(d)/'journal.sqlite'
            src=sqlite3.connect('file:'+str(a.journal.resolve())+'?mode=ro',uri=True)
            dest=sqlite3.connect(path)
            try:
                tables={row[0] for row in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {'meta','jobs','events','outbox'}<=tables:raise ContractError('H6_JOURNAL_SCHEMA_MISSING')
                src.backup(dest)
            finally:src.close();dest.close()
            result=LeaseJournal(path,Binding(**c['binding']),LeasePolicy(**c['policy'])).export()
        print(json.dumps(result,indent=2));return 0
    except (ContractError,ValueError,TypeError,OSError,KeyError,sqlite3.Error) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e),'product_accepted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
