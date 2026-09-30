#!/usr/bin/env python3
"""Inject one fault per H4 task in an isolated source copy; require restored PASS."""
from pathlib import Path
import argparse,sys,shutil,tempfile,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
FAULTS=[
 ('001','bie/evaluation/benchmarks/browser/contracts.py',"chk['id'] in ('runtime-health','fresh-context-replay') or ",''),
 ('002','bie/evaluation/benchmarks/browser/bundle.py','records.append(capture(fd,row,maximum=limits.max_file_bytes,destination=out))',"out.write((Path(root)/row['path']).read_bytes());records.append(row)"),
 ('003','bie/evaluation/benchmarks/browser/service.py',"if binary_hash(context.chromium_executable)!=context.chromium_sha256:raise BenchmarkError('BROWSER_TOOL_PIN_MISMATCH')","if False:raise BenchmarkError('BROWSER_TOOL_PIN_MISMATCH')"),
 ('004','bie/evaluation/benchmarks/browser/actions.py',"elif op=='press':page.keyboard.press(step['value'])","elif op=='press':pass"),
 ('005','bie/evaluation/benchmarks/browser/observe.py',"result['observer_world']='ISOLATED_CDP'","result['observer_world']='ISOLATED_CDP';result['contrast_at_least']=None"),
 ('006','bie/evaluation/benchmarks/browser/scoring.py','type(actual) is type(exp) and actual==exp','type(actual) is type(exp)'),
 ('007','bie/evaluation/benchmarks/browser/replay.py',"'matches':a==b","'matches':True"),
 ('008','bie/evaluation/benchmarks/metrics/__init__.py',"reference.get('schema_version') == 'browser-reference-1'","reference.get('schema_version') == 'browser-reference-broken'"),
 ('009','bie/evaluation/benchmarks/browser/ledger.py',"if self.db.execute('SELECT 1 FROM browser_runs WHERE run_id=? OR (campaign=? AND content_sha=?)',","if False and self.db.execute('SELECT 1 FROM browser_runs WHERE run_id=? OR (campaign=? AND content_sha=?)',"),
 ('010','bie/evaluation/benchmarks/browser/integrity.py',"if hashlib.file_digest(f,'sha256').hexdigest()!=expected_sha256:","if False:")]

def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=False);rows=[]
 with tempfile.TemporaryDirectory(prefix='bie-h4-mutations-') as tmp:
  src=Path(tmp)/'source';src.mkdir()
  for folder in ('bie','tests','tools','examples'):shutil.copytree(ROOT/folder,src/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  for task,name,old,new in FAULTS:
   case=out/task;case.mkdir();p=src/name;raw=p.read_bytes();text=raw.decode();assert old in text,(task,name)
   (case/'preimage.py').write_bytes(raw);p.write_text(text.replace(old,new,1));(case/'mutant.py').write_bytes(p.read_bytes())
   cmd=[sys.executable,str(src/'tools/run_section17_h4_tests.py'),'--pattern',f'test_h4_{task}.py','--output-dir',str(case/'mutated')]
   env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'}
   try:
    mutated=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env=env)
    (case/'mutated_process.txt').write_text(mutated.stdout+mutated.stderr)
   finally:p.write_bytes(raw)
   cmd[-1]=str(case/'restored');restored=subprocess.run(cmd,capture_output=True,text=True,timeout=120,env=env)
   (case/'restored_process.txt').write_text(restored.stdout+restored.stderr)
   m=json.loads((case/'mutated/TEST_RESULT.json').read_text());r=json.loads((case/'restored/TEST_RESULT.json').read_text())
   rows.append({'task_id':'BIE-EVAL-H4-'+task,'fault_detected':mutated.returncode!=0 and (m['failed']+m['errors'])>0,
               'restored_pass':restored.returncode==0 and r['all_passed'],'restored_exact':p.read_bytes()==raw,
               'original_sha256':hashlib.sha256(raw).hexdigest(),'mutant_failed_methods':m['failed'],'mutant_error_methods':m['errors']})
 result={'controls':rows,'detected':sum(x['fault_detected'] for x in rows),'restored_pass':sum(x['restored_pass'] for x in rows),
         'all_expected':all(x['fault_detected'] and x['restored_pass'] and x['restored_exact'] for x in rows)}
 (out/'FAULT_CONTROLS.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return 0 if result['all_expected'] else 1
if __name__=='__main__':raise SystemExit(main())
