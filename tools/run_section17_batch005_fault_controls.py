#!/usr/bin/env python3
"""Inject one actual implementation fault per task in private copies; restore/retest.

These are defect-detection controls, not new unique test methods or a claim of
comprehensive mutation coverage. No delivered source is modified by this tool.
"""
import argparse,hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MUTATIONS=[
 ('BIE-EVAL-METRIC-017','metrics/regression.py','if actual < baseline-drop:','if False:','test_metric_017.py'),
 ('BIE-EVAL-RATER-001','release/deterministic.py','if service_code_sha256()!=digest_string(expected_code_sha256):','if False:','test_rater_001.py'),
 ('BIE-EVAL-RATER-002','release/model.py',"value,reasons=grade(rubric,body['units'])","value,reasons=(1,[])",'test_rater_002.py'),
 ('BIE-EVAL-RATER-003','release/auth.py',"if not hmac.compare_digest(expected,token['signature']):","if False:",'test_rater_003.py'),
 ('BIE-EVAL-RATER-004','release/agreement.py','kappa=None if chance==1 else str((observed-chance)/(1-chance))',"kappa=None if chance==1 else '1'",'test_rater_004.py'),
 ('BIE-EVAL-RATER-005','release/aggregation.py',"'score_exact':str(min(values))","'score_exact':str(max(values))",'test_rater_005.py'),
 ('BIE-EVAL-REL-001','release/thresholds.py','if value<floor:','if False:','test_rel_001.py'),
 ('BIE-EVAL-REL-002','release/floors.py','elif values[key]<minimums[key]:','elif False:','test_rel_002.py'),
 ('BIE-EVAL-REL-003','release/domains.py',"groups={cases[k]['leakage_group'] for k in good}",'groups=set(good)','test_rel_003.py'),
 ('BIE-EVAL-REL-004','release/gate.py','for missing in sorted(required-seen):','for missing in sorted([]):','test_rel_004.py')]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True);a=parser.parse_args()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False);results=[]
    with tempfile.TemporaryDirectory(prefix='bie-s17-faults-') as tmp:
        work=Path(tmp)
        for folder in ['bie','tests','tools','metadata']:
            shutil.copytree(ROOT/folder,work/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for task,file,old,new,pattern in MUTATIONS:
            target=work/'bie/evaluation/benchmarks'/file;original=target.read_bytes();text=original.decode()
            if text.count(old)!=1:raise RuntimeError(f'Ambiguous mutation for {task}')
            target.write_text(text.replace(old,new,1))
            cmd=[sys.executable,'-B','-m','unittest','discover','-s','tests/section17','-p',pattern]
            mutated=subprocess.run(cmd,cwd=work,capture_output=True,text=True,timeout=30)
            (out/f'{task}_INJECTED.txt').write_text(mutated.stdout+mutated.stderr)
            mutated_sha=hashlib.sha256(target.read_bytes()).hexdigest();target.write_bytes(original)
            restored=subprocess.run(cmd,cwd=work,capture_output=True,text=True,timeout=30)
            (out/f'{task}_RESTORED.txt').write_text(restored.stdout+restored.stderr)
            detected=mutated.returncode!=0 and ('FAIL:' in mutated.stderr or 'ERROR:' in mutated.stderr) and 'SyntaxError' not in mutated.stderr
            results.append({'task_id':task,'file':file,'original_sha256':hashlib.sha256(original).hexdigest(),
                'mutated_sha256':mutated_sha,'mutation_before':old,'mutation_after':new,
                'injected_exit_code':mutated.returncode,'restored_exit_code':restored.returncode,
                'detected':detected,'restored_passed':restored.returncode==0})
    report={'controls':results,'detected':sum(r['detected'] for r in results),'restored_passed':sum(r['restored_passed'] for r in results),
            'control_count':len(results),'delivered_source_modified':False,'counted_as_unique_tests':False}
    (out/'FAULT_CONTROL_RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='controls'},indent=2))
    return 0 if report['detected']==report['control_count']==report['restored_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
