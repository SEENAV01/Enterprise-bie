"""Qualified single-flight fault controls; synthetic unit evidence, no new tests."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator.admission import CreationAdmission
from apps.operator.service import Service
tests=load('tests/section18/test_batch003e.py');original=CreationAdmission.run

def cached(self,key,operation):
    if hasattr(self,'_bad_cached'):return self._bad_cached,True
    result=original(self,key,operation);self._bad_cached=result[0];return result

def no_response_check(self,p,permission):
    # Seeded revocation bypass. Tests must reject it, not classify harness errors.
    return None

controls=[('no_historical_result_cache','test_no_historical_cache_after_completion',patch.object(CreationAdmission,'run',cached)),
 ('no_duplicate_overlapping_execution','test_one_owner_committed_result_for_overlapping_requests',
     patch.object(CreationAdmission,'run',lambda self,key,operation:(operation(),False))),
 ('no_revoked_result_disclosure','test_revocation_while_waiting_prevents_result_disclosure',patch.object(Service,'authorize',no_response_check))]
rows=[]
for name,method,mutation in controls:
    transcript=io.StringIO();baseline=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([tests.AdmissionHardening(method)]))
    assert baseline.wasSuccessful(),'BASELINE_NOT_PASS:'+name
    with mutation:r=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([tests.AdmissionHardening(method)]))
    rows.append(dict(control=name,baseline_passed=True,killed=bool(r.failures),harness_error=bool(r.errors),
        transcript=transcript.getvalue(),new_distinct_tests=0))
receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in rows),controls=rows,new_distinct_tests=0,product_accepted=False)
p=Path(sys.argv[1]);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(passed=receipt['passed'],controls=len(rows),new_distinct_tests=0)))
raise SystemExit(not receipt['passed'])
