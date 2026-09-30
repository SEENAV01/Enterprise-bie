#!/usr/bin/env python3
"""Temporary, local, reversible fault injection into only the new bridge source.

Run in an isolated disposable copy; do not invoke during another process's tests.
Never mutates QA dependency files, GitHub, or any production data.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
DEPENDENCY=ROOT.parent/'dependency_snapshot'
FAULTS=[
('candidate_pin','if candidate.content_digest != digest_string(expected_candidate_digest):','if False:',
 'test_native_qa_001.NativeQA001.test_product_candidate_pin_rejected'),
('artifact_hash','if total != ref.size or h.hexdigest() != ref.sha256:','if total != ref.size:',
 'test_native_qa_001.NativeQA001.test_changed_source_bytes_rejected'),
('partial_coverage',"'FAIL' if 'FAIL' in outcomes else 'NOT_RUN')","'FAIL' if 'FAIL' in outcomes else 'PASS')",
 'test_native_qa_001.NativeQA001.test_native_evidence_stays_unsigned_and_not_run'),
('wire_serialization',"'native_qa_report': json.loads(qa.to_bytes()),","'native_qa_report': qa.to_dict(),",
 'test_native_qa_cli_001.NativeQACLI001.test_native_report_export_uses_native_wire_serialization'),
('negative_propagation',"'FAIL' if 'FAIL' in outcomes else 'NOT_RUN')","'NOT_RUN' if 'FAIL' in outcomes else 'NOT_RUN')",
 'test_native_qa_001.NativeQA001.test_real_frame_mismatch_propagates_failure')]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);args=p.parse_args()
 out=Path(args.output_dir).absolute();out.mkdir(parents=True,exist_ok=False)
 target=ROOT/'bie/evaluation/benchmarks/native_qa/bridge.py';original=target.read_bytes();text=original.decode()
 env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join([str(ROOT),str(DEPENDENCY),str(ROOT/'tests/section17')]);env['PYTHONDONTWRITEBYTECODE']='1'
 # Prevent stale bytecode reuse for the intentionally modified file.
 import shutil
 shutil.rmtree(target.parent/'__pycache__',ignore_errors=True)
 rows=[]
 def run(name,test):
  result=subprocess.run([sys.executable,'-B','-m','unittest',test],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
  (out/(name+'.txt')).write_text(result.stdout+result.stderr)
  return result.returncode
 try:
  for name,old,new,test in FAULTS:
   if text.count(old)!=1:raise RuntimeError('Unambiguous mutation target required: '+name)
   before=run(name+'_before',test)
   mutant=text.replace(old,new).encode();target.write_bytes(mutant)
   (out/(name+'.mutant.py')).write_bytes(mutant)
   fault=run(name+'_mutant',test)
   target.write_bytes(original)
   after=run(name+'_restored',test)
   rows.append({'fault':name,'test_id':test,'before_returncode':before,'mutant_returncode':fault,
                'restored_returncode':after,'detected':before==0 and fault!=0 and after==0,
                'mutant_sha256':hashlib.sha256(mutant).hexdigest()})
   if not rows[-1]['detected']:raise AssertionError(name)
 finally:
  target.write_bytes(original)
  receipt={'faults':rows,'faults_tested':len(rows),'faults_detected':sum(r['detected'] for r in rows),
           'original_sha256':hashlib.sha256(original).hexdigest(),
           'restored_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
           'all_originals_restored':target.read_bytes()==original,
           'counting_note':'Repeated/mutated controls do not increase distinct test counts.'}
  (out/'FAULT_CONTROLS.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
