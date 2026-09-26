"""Execute every supplied Section 15 test; preserve failures and source identity."""
import hashlib, io, json, os, platform, sys, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=Path(os.environ['BIE_GAME_EVIDENCE']);OUT.mkdir(parents=True,exist_ok=True)

def main():
    source={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for base in ('bie','tests','scripts') for p in sorted((ROOT/base).rglob('*.py'))}
    (OUT/'SOURCE_INVENTORY.json').write_text(json.dumps(source,indent=2)+'\n')
    report={'schema_version':'bie.game.section15.linux-verification/1','platform':platform.platform(),
            'tested_commit':os.environ.get('GITHUB_SHA'),'source_inventory_sha256':hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
            'product_accepted':False,'groups':[]}
    started=time.monotonic()
    for path in sorted((ROOT/'tests').rglob('test*.py')):
        module='.'.join(path.relative_to(ROOT).with_suffix('').parts)
        log=io.StringIO();begin=time.monotonic()
        suite=unittest.defaultTestLoader.loadTestsFromName(module)
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
        row={'module':module,'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
             'skips':len(result.skipped),'passed':result.wasSuccessful() and result.testsRun>0 and not result.skipped,
             'seconds':round(time.monotonic()-begin,3)}
        report['groups'].append(row)
        (OUT/(module+'.log')).write_text(log.getvalue(),encoding='utf-8')
        print(json.dumps(row),flush=True)
        if not row['passed']:print(log.getvalue(),flush=True)
        (OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    report['tests_run']=sum(r['run'] for r in report['groups'])
    report['passed']=all(r['passed'] for r in report['groups'])
    report['seconds']=round(time.monotonic()-started,3)
    (OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='groups'}),flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
