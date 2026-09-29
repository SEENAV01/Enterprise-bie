"""Standalone stdlib unittest collector/runner for an explicitly trusted checkout.

Launched with python -I. Never used as a sandbox for untrusted repositories.
"""
import argparse,hashlib,inspect,json,os,pathlib,sys,unittest

def walk(suite):
    for t in suite:
        if isinstance(t,unittest.TestSuite):yield from walk(t)
        else:yield t

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--directory',required=True)
    p.add_argument('--output',required=True);p.add_argument('--run',action='store_true');a=p.parse_args()
    root=pathlib.Path(a.root);sys.path.insert(0,str(root));sys.dont_write_bytecode=True
    suite=unittest.defaultTestLoader.discover(str(root/a.directory),pattern='test_*.py');cases=[]
    for t in walk(suite):
        method=getattr(t,getattr(t,'_testMethodName',''),None)
        source=inspect.getsourcefile(method) if method else None
        if source is None:raise ValueError('case source unavailable')
        path=pathlib.Path(source).resolve();rel=path.relative_to(root).as_posix()
        cases.append(dict(test_id=t.id(),source=rel,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    if not cases or len({c['test_id'] for c in cases})!=len(cases):raise ValueError('case census invalid')
    failures=errors=skipped=0;ran=0;ids=[]
    if a.run:
        class Results(unittest.TextTestResult):
            def startTest(self,test):ids.append(test.id());super().startTest(test)
        result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2,resultclass=Results).run(suite)
        failures=len(result.failures);errors=len(result.errors);skipped=len(result.skipped);ran=result.testsRun
    data=dict(cases=cases,executed=a.run,run=ran,failures=failures,errors=errors,skipped=skipped,executed_ids=ids,
              passed=a.run and ran==len(cases) and not (failures or errors or skipped))
    with open(a.output,'x') as f:json.dump(data,f,sort_keys=True)
    return 0 if not a.run or data['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
