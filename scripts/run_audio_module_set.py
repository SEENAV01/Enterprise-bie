#!/usr/bin/env python3
"""Run an explicit, disjoint AUDIO module set and preserve incremental evidence.

This complements the inherited test runner without modifying it. A partial report
has complete=false and passed=false. Imported canonical fixtures are pinned.
"""
from __future__ import annotations
import argparse,hashlib,importlib,json,os,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.append(str(ROOT/'dependency_snapshot'))

def identity():
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ('bie','scripts','tests','dependency_snapshot','examples')
        for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--modules',nargs='+',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    from scripts.run_audio_tests import verify_dependencies
    baseline=verify_dependencies()
    allowed={x.name for x in (ROOT/'tests/audio').glob('test*.py')}
    if not a.modules or len(set(a.modules))!=len(a.modules) or not set(a.modules)<=allowed:
        raise SystemExit('INVALID_MODULE_SET')
    os.environ['PYTHONPATH']=str(ROOT)+os.pathsep+str(ROOT/'dependency_snapshot')
    os.environ['PYTHONDONTWRITEBYTECODE']='1';before=identity()
    payload={'schema_version':'bie.audio.explicit-module-test/1','complete':False,'passed':False,
        'scope':'AUDIO_MODULES_ONLY_NOT_FULL_ENTERPRISE','baseline_commit':baseline['commit'],
        'selected_modules':a.modules,'tests':0,'failures':0,'errors':0,'skips':0,'results':[],
        'tested_source':before,'python':sys.version.split()[0],'product_accepted':False,'full_enterprise_regression':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    def write():
        tmp=a.output.with_suffix('.tmp');tmp.write_text(json.dumps(payload,indent=2)+'\n');os.replace(tmp,a.output)
    write();started=time.monotonic()
    for name in a.modules:
        print('RUN '+name,flush=True);begin=time.monotonic()
        module=importlib.import_module('tests.audio.'+name[:-3]);suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        r=unittest.TextTestRunner(stream=sys.stdout,verbosity=2).run(suite)
        row={'file':'tests/audio/'+name,'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),
             'seconds':round(time.monotonic()-begin,3)}
        payload['results'].append(row)
        for k in ('tests','failures','errors','skips'):payload[k]+=row[k]
        print('FINISHED '+json.dumps(row),flush=True);write()
    after=identity();payload.update(complete=True,source_unchanged_during_tests=before==after,
        duration_seconds=round(time.monotonic()-started,3))
    payload['passed']=payload['tests']>0 and sum(payload[k] for k in ('failures','errors','skips'))==0 and before==after
    write();print(json.dumps({k:v for k,v in payload.items() if k not in ('results','tested_source')},indent=2),flush=True)
    return 0 if payload['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
