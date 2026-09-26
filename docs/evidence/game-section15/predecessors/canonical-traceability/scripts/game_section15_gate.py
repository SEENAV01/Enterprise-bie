"""Run all adopted GAME tests and bind the result to exact canonical bytes."""
from pathlib import Path
import hashlib,io,json,os,subprocess,sys,time,unittest
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'manifests/game_section15_adoption.json'
sys.path.insert(0,str(ROOT))

def identity():
    data=json.loads(MANIFEST.read_text())
    inventory={};records=[]
    for part in data['record_parts']:
        raw=(ROOT/part['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=part['sha256']:raise ValueError('GAME_MANIFEST_PART_HASH')
        records.extend(json.loads(raw))
    data['records']=records
    for row in records:
        p=ROOT/row['canonical_path']
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=row['sha256']:raise ValueError('GAME_ADOPTION_HASH:'+row['canonical_path'])
        inventory[row['canonical_path']]=digest
    commit=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    return data,{'tested_commit':commit,'manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),'source_inventory_sha256':hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()}

def read_bound_result(output):
    data,binding=identity();result=json.loads((Path(output)/'RESULT.json').read_text())
    if any(result.get(k)!=v for k,v in binding.items()):raise ValueError('GAME_RESULT_SOURCE_BINDING')
    rows=result['results']
    if sorted(r['path'] for r in rows)!=data['test_paths']:raise ValueError('GAME_RESULT_TEST_COVERAGE')
    if result['tests_run']!=sum(r['tests'] for r in rows):raise ValueError('GAME_RESULT_TEST_COUNT')
    for r in rows:
        passed=r['tests']>0 and not any(r[k] for k in ('failures','errors','skipped'))
        if r['passed']!=passed:raise ValueError('GAME_RESULT_STATUS')
    return rows

def main():
    output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=True)
    os.environ['BIE_GAME_EVIDENCE']=str(output)
    data,binding=identity();started=time.monotonic();rows=[]
    report={**binding,'product_accepted':False,'results':rows}
    for rel in data['test_paths']:
        name='.'.join(Path(rel).with_suffix('').parts);log=io.StringIO()
        suite=unittest.defaultTestLoader.loadTestsFromName(name)
        r=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
        row={'path':rel,'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'passed':r.wasSuccessful() and r.testsRun>0 and not r.skipped}
        rows.append(row);(output/(name+'.log')).write_text(log.getvalue(),encoding='utf-8')
        print(json.dumps(row),flush=True)
        if not row['passed']:row['log']=log.getvalue();print(log.getvalue(),flush=True)
    report.update(tests_run=sum(r['tests'] for r in rows),passed=all(r['passed'] for r in rows),seconds=round(time.monotonic()-started,3))
    (output/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
