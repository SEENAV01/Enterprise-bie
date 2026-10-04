"""Seeded bypass checks; replays/mutations are never distinct test counts."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator import assurance as module
tests=load('tests/section18/test_batch003c.py');original=module.require
def bypass(code):return patch.object(module,'require',lambda cond,c,status=409:None if c==code else original(cond,c,status))
controls=[('gate_blocker_inventory',tests.Qa001,'test_blocking_inventory_tamper_rejected',bypass('gate_blockers_invalid')),
    ('candidate_content_binding',tests.Qa001,'test_changed_candidate_content_rejected_before_evaluation',bypass('assurance_candidate_binding')),
    ('run_identity_binding',tests.Qa001,'test_wrong_run_candidate_rejected',bypass('assurance_run_binding')),
    ('repair_receipt_hash',tests.Qa003Projection,'test_unit_receipt_tamper_rejected',bypass('repair_receipt_integrity')),
    ('repair_journal_binding',tests.Qa003Projection,'test_unit_journal_binding_change_rejected',bypass('repair_context_binding')),
    ('repair_staged_approval',tests.Qa003Projection,'test_unit_staged_requires_authenticated_inventory',bypass('repair_staged_without_checks'))]
rows=[]
for name,cls,method,mutant in controls:
    transcript=io.StringIO()
    baseline=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([cls(method)]))
    if not baseline.wasSuccessful():raise SystemExit('MUTATION_BASELINE_NOT_PASS:'+name)
    with mutant:r=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([cls(method)]))
    rows.append(dict(control=name,killed=bool(r.failures),harness_error=bool(r.errors),transcript=transcript.getvalue(),new_tests=0))
receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in rows),controls=rows,new_distinct_tests=0,product_accepted=False)
path=Path(sys.argv[1]);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(passed=receipt['passed'],controls=len(rows),new_distinct_tests=0)))
raise SystemExit(0 if receipt['passed'] else 1)
