"""Run all recovered DIR, TIME and SYNC tests with per-file evidence."""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.util,io,json,platform,sys,time,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'tests/director'))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=ROOT/'verification/dir_sync_tests.json')
    args=parser.parse_args(); records=[]; start=time.monotonic()
    for p in sorted((ROOT/'tests/director').glob('test_*.py')):
        spec=importlib.util.spec_from_file_location(p.stem,p); module=importlib.util.module_from_spec(spec)
        sys.modules[p.stem]=module; spec.loader.exec_module(module)
        log=io.StringIO(); result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
        records.append({'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'passed':result.wasSuccessful(),'log':log.getvalue()})
    summary={k:sum(r[k] for r in records) for k in ('tests','failures','errors','skipped')}
    summary.update(test_files=len(records),passed=all(r['passed'] for r in records),python=platform.python_version(),
        previous_dir_tests=sum(r['tests'] for r in records if not Path(r['file']).name.startswith('test_sync_')),
        sync_unit_tests=sum(r['tests'] for r in records if Path(r['file']).name in [f'test_sync_{i:03}.py' for i in range(1,6)]),
        sync_cross_contract_tests=sum(r['tests'] for r in records if r['file'].endswith('test_sync_contracts.py')),
        duration_seconds=round(time.monotonic()-start,3))
    report={'executed_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Local DIR/TIME/SYNC source and contract verification, not canonical integration or real-book/media acceptance',
        'accepted':False,'summary':summary,'files':records}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(summary))
    for r in records:
        if not r['passed']: print(r['log'])
    return 0 if summary['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
