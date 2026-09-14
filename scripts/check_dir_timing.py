"""Run recovered DIR and new timing tests; write transparent local evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests/director'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'verification/dir_timing_tests.json')
    args=parser.parse_args()
    reports=[]
    started=time.monotonic()
    for path in sorted((ROOT/'tests/director').glob('test_*.py')):
        spec=importlib.util.spec_from_file_location(path.stem,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[path.stem]=module
        spec.loader.exec_module(module)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        stream=io.StringIO()
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        reports.append({'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
            'skipped':len(result.skipped),'passed':result.wasSuccessful(),'log':stream.getvalue()})
    summary={key:sum(r[key] for r in reports) for key in ('tests','failures','errors','skipped')}
    summary.update(test_files=len(reports),passed=all(r['passed'] for r in reports),
        original_dir_tests=sum(r['tests'] for r in reports if '/test_time_' not in r['file']),
        timing_unit_tests=sum(r['tests'] for r in reports if r['file'].split('/')[-1] in [f'test_time_{i:03}.py' for i in range(1,6)]),
        cross_contract_tests=sum(r['tests'] for r in reports if r['file'].endswith('test_time_contracts.py')),
        python=platform.python_version(),duration_seconds=round(time.monotonic()-started,3))
    report={'executed_at_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Local recovered DIR + new TIME unit/cross-contract suite; not canonical integration or product acceptance',
        'accepted':False,'summary':summary,'files':reports}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(summary))
    for row in reports:
        if not row['passed']:
            print(row['log'])
    return 0 if summary['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
