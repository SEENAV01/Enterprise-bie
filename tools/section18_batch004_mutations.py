"""Passing baseline then assertion-killed seeded faults, never extra tests."""
from pathlib import Path
from copy import deepcopy
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator.governance import Governance
tests=load('tests/section18/test_batch004.py');original_activate=Governance.activate;original_audit=Governance.audit
def stale(self,p,kind,id,revision,sha,previous,key):
    with self.s.catalog.tx(read_only=True) as db:a=self._active(db,p,kind)
    return original_activate(self,p,kind,id,revision,sha,a['activation_sha256'] if a else None,key)
def unsafe_binding(self,db,p,id,revision,sha):return self._version(db,p,'policy',id,revision)
def details(self,*args,**kwargs):
    result=original_audit(self,*args,**kwargs);result['raw_details']='PRIVATE C:/user/path';return result
controls=[
 ('activation_cas','Admin005','test_activate_explicit_pins_and_compare_and_set',patch.object(Governance,'activate',stale)),
 ('active_policy_pin','Admin005','test_policy_binding_wrong_hash_and_locale_fail_closed',patch.object(Governance,'binding',unsafe_binding)),
 ('independent_rater_roster','Admin006','test_duplicate_independence_group_is_rejected',patch('apps.operator.governance.validate_benchmark',side_effect=deepcopy)),
 ('native_evaluator_execution','Admin006','test_canonical_ledger_execute_actually_invoked',patch.object(Governance,'execute_benchmark',return_value={'report':{'outcome':'DIAGNOSTIC_PASS'}})),
 ('audit_tenant_isolation','Admin007','test_explicit_tenant_same_id_isolated',patch.object(Governance,'_tenant',return_value='tenant-a')),
 ('audit_secret_redaction','Admin007','test_unknown_details_never_echo_secret_or_path',patch.object(Governance,'audit',details)),
]
rows=[]
for name,cls,method,mutation in controls:
    log=io.StringIO();case=getattr(tests,cls)
    baseline=unittest.TextTestRunner(stream=log).run(unittest.TestSuite([case(method)]))
    assert baseline.wasSuccessful(),'BASELINE_FAILED:'+name
    with mutation:r=unittest.TextTestRunner(stream=log).run(unittest.TestSuite([case(method)]))
    rows.append(dict(control=name,baseline_passed=True,killed=bool(r.failures),harness_error=bool(r.errors),transcript=log.getvalue()))
receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in rows),controls=rows,new_distinct_tests=0,product_accepted=False)
p=Path(sys.argv[1]);assert not p.exists(),'RECEIPT_ALREADY_EXISTS';p.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(passed=receipt['passed'],controls=len(rows),new_distinct_tests=0)))
raise SystemExit(not receipt['passed'])
