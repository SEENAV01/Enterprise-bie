#!/usr/bin/env python3
"""Ten scoped fault injections in an isolated COPY; restores every edited byte.

This tests selected detection boundaries, not exhaustive mutation coverage.
Never run fault mutations in the active collector or canonical repository.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAULTS=[
 ('001','custody.py','if total!=before.st_size or h.hexdigest()!=expected_sha256:', 'if total!=before.st_size:', 'test_h2_001.H2001.test_wrong_hash_rejected'),
 ('002','process.py','if rc!=0 or ne:', 'if rc!=0:', 'test_h2_002.H2002.test_stderr_not_silently_accepted'),
 ('003','probe.py','if len(vs)!=1:', 'if len(vs)<1:', 'test_h2_003.H2003.test_duplicate_video'),
 ('004','video.py','self.dark_frames+=int(dark);', 'self.dark_frames+=0;', 'test_h2_004.H2004.test_black_frame_detection'),
 ('005','audio.py','clips=sum(abs(x)>=0.999 for x in vals);', 'clips=0;', 'test_h2_005.H2005.test_clipping_positive_and_negative'),
 ('006','timeline.py','if pts<=self.last:', 'if pts<self.last:', 'test_h2_006.H2006.test_duplicate_pts'),
 ('007','captions.py','or start<end-1e-7:', 'or False:', 'test_h2_007.H2007.test_overlap_rejected'),
 ('008','service.py',"if v['decoded_frames']!=policy['expected_frames']:", 'if False:', 'test_h2_008.H2008.test_wrong_frame_reference_fails'),
 ('009','native.py',"if n['accepted'] is not False:", 'if False:', 'test_h2_009.H2009.test_self_claimed_acceptance_rejected'),
 ('010','ledger.py',"if digest(r)!=row[5] or (r['run_id'],r['candidate_sha256'],r['reference_sha256'],r['evaluator_code_sha256'])!=(run_id,row[0],row[1],row[2]):", 'if False:', 'test_h2_010.H2010.test_row_pin_tamper')]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True);args=parser.parse_args()
 out=Path(args.output_dir).resolve();out.mkdir(parents=True,exist_ok=False);results=[]
 with tempfile.TemporaryDirectory(prefix='bie-h2-mutants-') as td:
  work=Path(td)
  for folder in ('bie','tests','provenance'):
   shutil.copytree(ROOT/folder,work/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  env=dict(os.environ,PYTHONPATH=str(work)+os.pathsep+str(work/'tests/section17'),PYTHONDONTWRITEBYTECODE='1')
  def run(test):return subprocess.run([sys.executable,'-B','-m','unittest','-v',test],cwd=work,env=env,capture_output=True,text=True,timeout=20)
  for task,name,old,new,test in FAULTS:
   file=work/'bie/evaluation/benchmarks/av'/name;before=file.read_bytes();assert file.read_text().count(old)==1,(name,old)
   bad=before.decode().replace(old,new).encode();d=out/task;d.mkdir();(d/'before.py.txt').write_bytes(before);(d/'mutated.py.txt').write_bytes(bad)
   try:
    file.write_bytes(bad);red=run(test);(d/'FAULT_RUN.txt').write_text(red.stdout+red.stderr)
   finally:file.write_bytes(before)
   green=run(test);(d/'RESTORED_RUN.txt').write_text(green.stdout+green.stderr)
   detected=red.returncode!=0 and 'Ran 1 test' in red.stderr and 'FAILED (' in red.stderr and '_FailedTest' not in red.stderr
   restored=green.returncode==0 and 'Ran 1 test' in green.stderr and file.read_bytes()==before
   results.append({'task_id':'BIE-EVAL-H2-'+task,'path':str(file.relative_to(work)),'test_id':test,'before_sha256':sha(before),'mutation_sha256':sha(bad),'restored_sha256':sha(file.read_bytes()),'detected':detected,'restored_pass':restored,'fault_returncode':red.returncode,'restored_returncode':green.returncode})
 summary={'faults':len(results),'detected':sum(x['detected'] for x in results),'restored_passes':sum(x['restored_pass'] for x in results),'all_verified':all(x['detected'] and x['restored_pass'] for x in results),'records':results,'scope':'10 targeted injected faults; not exhaustive mutation coverage','live_source_changed':False}
 (out/'MUTATION_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k] for k in ('faults','detected','restored_passes','all_verified')}))
 return 0 if summary['all_verified'] else 1
if __name__=='__main__':raise SystemExit(main())
