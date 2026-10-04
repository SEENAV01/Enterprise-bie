"""Six focused seeded controls. Replays are not new distinct tests."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator import quality as module
def main():
    tests=load('tests/section18/test_batch003b.py');original=module.require
    def bypass(code):return patch.object(module,'require',lambda cond,c,status=409:None if c==code else original(cond,c,status))
    controls=[('denominator_bypass',tests.Qa002,'test_projection_rechecks_denominator_even_if_checksum_recomputed',bypass('quality_denominator_invalid')),
        ('candidate_binding_bypass',tests.Qa002,'test_candidate_binding_mismatch_rejected',bypass('quality_candidate_mismatch')),
        ('product_promotion_bypass',tests.Qa002,'test_projection_rejects_unauthorized_product_promotion',bypass('quality_unauthorized_promotion')),
        ('pagination_bypass',tests.Qa002,'test_pagination_strict_not_unbounded',patch.object(module,'pagination',lambda *a:None)),
        ('frozen_policy_pin_bypass',tests.Qa004,'test_changed_policy_not_silently_activated',bypass('quality_release_pins_mismatch')),
        ('cross_run_binding_bypass',tests.Qa004,'test_cross_run_context_rejected',bypass('quality_run_binding_mismatch'))]
    rows=[]
    for name,cls,method,mutant in controls:
        transcript=io.StringIO()
        with mutant:r=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([cls(method)]))
        rows.append(dict(control=name,killed=bool(r.failures),harness_error=bool(r.errors),transcript=transcript.getvalue(),new_tests=0))
    receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in rows),controls=rows,new_distinct_tests=0,product_accepted=False)
    output=Path(sys.argv[1]);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(passed=receipt['passed'],controls=len(rows),new_distinct_tests=0)));return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
