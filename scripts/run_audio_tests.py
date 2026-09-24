#!/usr/bin/env python3
"""Run AUDIO tests with exact pinned DIR dependencies; never write to GitHub."""
from __future__ import annotations
import argparse,hashlib,importlib,io,json,os,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))


def verify_dependencies():
    m=json.loads((ROOT/'DEPENDENCY_SNAPSHOT.json').read_text())
    for row in m['files']:
        p=ROOT/'dependency_snapshot'/row['path']
        if p.is_symlink() or not p.is_file():raise ValueError('DEPENDENCY_PATH_INVALID:'+row['path'])
        b=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        if hashlib.sha256(b).hexdigest()!=row['sha256'] or len(b)!=row['bytes'] or blob!=row['expected_git_blob']:
            raise ValueError('DEPENDENCY_IDENTITY_MISMATCH:'+row['path'])
    return m


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pattern',default='test*.py');parser.add_argument('--output',type=Path);args=parser.parse_args()
    baseline=verify_dependencies();os.environ['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'dependency_snapshot')))
    paths=sorted((ROOT/'tests/audio').glob(args.pattern))
    if not paths:raise SystemExit('NO_TESTS_DISCOVERED')
    total=failures=errors=skips=0;start=time.monotonic();results=[];logs=io.StringIO()
    for p in paths:
        print('RUN '+p.name, file=sys.stderr, flush=True)
        module=importlib.import_module('tests.audio.'+p.stem)
        suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        r=unittest.TextTestRunner(stream=logs,verbosity=2).run(suite)
        results.append({'file':p.relative_to(ROOT).as_posix(),'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped)})
        print(f'FINISHED {p.name}: {r.testsRun} tests, {len(r.failures)} failures, {len(r.errors)} errors', file=sys.stderr, flush=True)
        total+=r.testsRun;failures+=len(r.failures);errors+=len(r.errors);skips+=len(r.skipped)
    payload={'schema_version':'bie.audio.batch-test/1','scope':'AUDIO batch tests with exact DIR dependency closure, NOT the full enterprise regression',
             'baseline_commit':baseline['commit'],'tests':total,'failures':failures,'errors':errors,'skips':skips,'passed':total>0 and failures+errors+skips==0,
             'python':sys.version.split()[0],'duration_seconds':round(time.monotonic()-start,4),'results':results,
             'tested_source':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('bie','tests','scripts','dependency_snapshot') for p in sorted((ROOT/folder).rglob('*.py'))},
             'audio_generation_scope':'see test cases; real local TTS is separately reported','full_enterprise_regression_rerun':False,'product_accepted':False}
    sys.stdout.write(logs.getvalue());print(json.dumps({k:v for k,v in payload.items() if k not in ('results','tested_source')},indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(payload,indent=2)+'\n')
    return 0 if payload['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
