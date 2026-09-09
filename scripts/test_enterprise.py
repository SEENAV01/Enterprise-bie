"""Run every imported and new enterprise test against the canonical bie tree.

Historical ZIP contents are immutable. Tests are loaded with unique module names
so identically named files in different batches do not replace each other.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, io, json, sys, time, traceback, unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'bie'
sys.dont_write_bytecode=True
# Working imports are normalized to bie.*; historical snapshots never enter sys.path.
sys.path.insert(0, str(ROOT))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='validation/enterprise_tests.json')
    parser.add_argument('--batch',help='Optional single original batch directory name')
    args=parser.parse_args()
    paths=sorted((ROOT/'tests/imported').glob('*/tests/**/test*.py'))
    if args.batch:paths=[p for p in paths if p.relative_to(ROOT/'tests/imported').parts[0]==args.batch]
    paths += sorted((ROOT/'tests').glob('test*.py'))
    if not args.batch:
        paths += sorted((ROOT/'tests/reasoning').rglob('test*.py'))
        paths += sorted((ROOT/'tests/assembly').rglob('test*.py'))
    if not paths:raise SystemExit('No tests discovered')
    results=[];start=time.monotonic()
    for path in paths:
        rel=path.relative_to(ROOT).as_posix()
        name='bie_test_'+hashlib.sha256(rel.encode()).hexdigest()[:20]
        log=io.StringIO()
        try:
            spec=importlib.util.spec_from_file_location(name,path)
            module=importlib.util.module_from_spec(spec)
            sys.modules[name]=module
            spec.loader.exec_module(module)
            suite=unittest.defaultTestLoader.loadTestsFromModule(module)
            result=unittest.TextTestRunner(stream=log,verbosity=1).run(suite)
            item={'path':rel,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful() and result.testsRun>0}
        except Exception:
            item={'path':rel,'tests':0,'failures':0,'errors':1,'skipped':0,'passed':False}
            log.write(traceback.format_exc())
        if not item['passed']:
            item['log']=log.getvalue();print(rel+' FAILED')
        results.append(item)
    summary={'scope':'Canonical enterprise regression and integration tests; no production or real-book acceptance claimed',
             'python':sys.version.split()[0],'test_files':len(results),
             'tests_run':sum(r['tests'] for r in results),'failed_files':sum(not r['passed'] for r in results),
             'failures':sum(r['failures'] for r in results),'errors':sum(r['errors'] for r in results),
             'skipped':sum(r['skipped'] for r in results),'duration_seconds':round(time.monotonic()-start,3),
             'passed':all(r['passed'] for r in results)}
    output=Path(args.output)
    if not output.is_absolute():output=ROOT/output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps({'summary':summary,'results':results},indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    return 0 if summary['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
