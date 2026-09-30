#!/usr/bin/env python3
"""Controlled local source mutation probes. Use only a disposable validation copy."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
CASES=[
 ('alias','contracts.py',"require(effect not in effects.values(), 'CAMPAIGN_CONTENT_ALIAS')","require(True, 'CAMPAIGN_CONTENT_ALIAS')",'test_native_campaign.Contracts.test_renamed_identical_candidate_rejected'),
 ('replay','runtime.py',"if claim['replayed']:","if False and claim['replayed']:",'test_native_campaign.Persistence.test_replay_does_not_execute_again'),
 ('result_hash','runtime.py',"require(hashlib.sha256(raw).hexdigest() == result_sha, 'CAMPAIGN_RESULT_HASH')","require(True, 'CAMPAIGN_RESULT_HASH')",'test_native_campaign.Persistence.test_result_bytes_tampering_rejected'),
 ('lease_budget','contracts.py',"require(lease.lease_seconds >= 3 * limits.deadline_s + 30, 'CAMPAIGN_LEASE_BUDGET')","require(True, 'CAMPAIGN_LEASE_BUDGET')",'test_native_campaign.Contracts.test_too_short_lease_rejected'),
 ('promotion','runtime.py',"require(measured.get('release_authorized') is False and measured.get('product_accepted') is False\n                    and measured.get('native_qa_report', {}).get('release_status') == 'BLOCKED',\n                    'CAMPAIGN_UPSTREAM_PROMOTION')","require(True, 'CAMPAIGN_UPSTREAM_PROMOTION')",'test_native_campaign.Persistence.test_injected_positive_upstream_cannot_authorize')]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();out=a.output_dir.absolute();out.mkdir(parents=True,exist_ok=False)
 env=dict(os.environ,PYTHONPATH=os.pathsep.join([str(ROOT),str(ROOT/'tests/section17')]),PYTHONDONTWRITEBYTECODE='1')
 results=[]
 for label,file,old,new,test in CASES:
  folder=out/label;folder.mkdir();path=ROOT/'bie/evaluation/benchmarks/native_campaign'/file;before=path.read_bytes();text=before.decode();assert text.count(old)==1
  (folder/'before.py').write_bytes(before);cmd=[sys.executable,'-B','-m','unittest','-v',test]
  def run(name):
   r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=40)
   (folder/(name+'.stdout.txt')).write_text(r.stdout);(folder/(name+'.stderr.txt')).write_text(r.stderr)
   return r
  baseline=run('control_before');assert baseline.returncode==0
  mutated=text.replace(old,new,1).encode();(folder/'mutated.py').write_bytes(mutated)
  try:
   path.write_bytes(mutated);bad=run('mutant')
  finally:path.write_bytes(before)
  restored=run('control_restored');assert path.read_bytes()==before
  detected=bad.returncode!=0 and ('FAIL' in bad.stderr or 'ERROR' in bad.stderr) and 'Ran 1 test' in bad.stderr
  assert detected and restored.returncode==0,(label,bad.stderr,restored.stderr)
  results.append(dict(control=label,test_id=test,command=cmd,detected=detected,before_exit=baseline.returncode,mutant_exit=bad.returncode,restored_exit=restored.returncode,before_sha256=hashlib.sha256(before).hexdigest(),mutated_sha256=hashlib.sha256(mutated).hexdigest(),restored_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 (out/'RESULT.json').write_text(json.dumps({'mutation_controls':results,'detected':len(results),'all_original_bytes_restored':True,'counted_as_additional_distinct_tests':False},indent=2)+'\n')
 print(json.dumps({'detected':len(results),'restored':True}))
if __name__=='__main__':main()
