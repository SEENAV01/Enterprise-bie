#!/usr/bin/env python3
"""Selected fault sensitivity: mutate only a disposable copy, then restore/retest.

These ten chosen faults do not constitute exhaustive mutation or security coverage.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args()
    out=Path(a.output_dir).absolute();out.mkdir(parents=True,exist_ok=False)
    clone=out/'disposable_runtime'
    for folder in ('bie','tests','tools','metadata','evidence/section17/h1/preimages'):
        src=ROOT/folder
        if src.exists():shutil.copytree(src,clone/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    prefix='bie/evaluation/benchmarks/'
    faults=[
      (1,prefix+'models.py','baseline',None),
      (2,prefix+'storage.py',"if hasattr(sqlite3, 'LEGACY_TRANSACTION_CONTROL'):","if True:"),
      (3,prefix+'release/deterministic.py','baseline',None),
      (4,prefix+'release/model.py','baseline',None),
      (5,prefix+'release/supervised.py','proc.join(max(0, self.timeout_seconds - (time.monotonic()-started)))','proc.join(0)'),
      (6,prefix+'release/bundle.py',"if digest(bundle) != manifest['artifact_sha256']:",'if False:'),
      (7,prefix+'release/admission.py',"if fingerprint in used_secrets and used_secrets[fingerprint] != assessor:",'if False:'),
      (8,prefix+'release/coverage.py',"if groups < minimum: reasons.append('DOMAIN_METRIC_COVERAGE_INCOMPLETE')","if False: reasons.append('DOMAIN_METRIC_COVERAGE_INCOMPLETE')"),
      (9,prefix+'release/ledger.py','baseline',None),
      (10,'tools/verify_section17_package.py','baseline',None)]
    results=[]
    for n,rel,before,after in faults:
        path=clone/rel;good=path.read_bytes();bucket=out/f'H1_{n:03}';bucket.mkdir()
        if before=='baseline':bad=(ROOT/'evidence/section17/h1/preimages'/rel).read_bytes()
        else:
            text=good.decode();assert text.count(before)==1,(rel,before)
            bad=text.replace(before,after).encode()
        assert bad!=good
        path.write_bytes(bad);(bucket/'INJECTED_FILE.txt').write_bytes(bad)
        command=[sys.executable,'-B',str(clone/'tools/run_section17_h1_tests.py'),'--pattern',f'test_h1_{n:03}.py']
        try:
            proc=subprocess.run(command+['--output-dir',str(bucket/'injected')],cwd=clone,capture_output=True,text=True,timeout=30)
            (bucket/'injected_console.txt').write_text(proc.stdout+proc.stderr)
            red=json.loads((bucket/'injected/TEST_RESULT.json').read_text())
        finally:path.write_bytes(good)
        proc2=subprocess.run(command+['--output-dir',str(bucket/'restored')],cwd=clone,capture_output=True,text=True,timeout=30)
        (bucket/'restored_console.txt').write_text(proc2.stdout+proc2.stderr)
        green=json.loads((bucket/'restored/TEST_RESULT.json').read_text())
        r={'task_id':f'BIE-EVAL-H1-{n:03}','path':rel,'original_sha256':hashlib.sha256(good).hexdigest(),
           'injected_sha256':hashlib.sha256(bad).hexdigest(),'injection':before,'replacement':after,
           'detected':proc.returncode!=0 and not red['all_passed'],'injected_failures':red['failed'],'injected_errors':red['errors'],
           'restored_passed':proc2.returncode==0 and green['all_passed'],'selected_tests':green['tests_run'],
           'original_source_unchanged':digest(ROOT/rel)==hashlib.sha256(good).hexdigest()}
        results.append(r);dump(bucket/'CONTROL_RESULT.json',r);print(json.dumps(r),flush=True)
    shutil.rmtree(clone)
    summary={'scope':'TEN_SELECTED_FAULT_CONTROLS_NOT_EXHAUSTIVE_MUTATION_AUDIT','controls':results,
        'all_detected':all(r['detected'] for r in results),'all_restored_passed':all(r['restored_passed'] for r in results),
        'no_original_source_mutation':all(r['original_source_unchanged'] for r in results),
        'repeated_tests_are_not_additional_unique_tests':True}
    dump(out/'FAULT_CONTROL_RESULT.json',summary)
    return 0 if all(summary[k] for k in ['all_detected','all_restored_passed','no_original_source_mutation']) else 1
if __name__=='__main__':raise SystemExit(main())
