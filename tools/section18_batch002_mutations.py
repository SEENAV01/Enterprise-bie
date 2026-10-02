"""Seeded validator/integrity bypass controls using existing authored tests."""
from pathlib import Path
import sys,io,json,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator import view_contracts as vc,artifacts as artifacts
def main():
    t=load('tests/section18/test_batch002.py');native=vc.require;native_art=artifacts.require
    def bypass(code):return patch.object(vc,'require',lambda condition,c,status=409:None if c==code else native(condition,c,status))
    rows=[('curriculum_plan_integrity_bypass',t.Lesson001,'test_stored_plan_edit_rejected',bypass('curriculum_plan_tampered')),
          ('lesson_source_binding_bypass',t.Lesson002,'test_foreign_source_ids_rejected',bypass('view_source_reference_invalid')),
          ('game_fingerprint_bypass',t.Lesson005,'test_game_plan_stale_fingerprint_rejected',bypass('game_plan_fingerprint_invalid')),
          ('artifact_record_seal_bypass',t.Art002,'test_record_parent_tamper_detected_by_seal',
            patch.object(artifacts,'require',lambda cond,code,status=409:None if code in ('artifact_record_tampered','view_parent_binding_invalid') else native_art(cond,code,status)))]
    receipts=[]
    for name,cls,method,mutant in rows:
        stream=io.StringIO()
        with mutant:result=unittest.TextTestRunner(stream=stream).run(unittest.TestSuite([cls(method)]))
        receipts.append(dict(mutation=name,authored_test=cls.__name__+'.'+method,killed=bool(result.failures),harness_error=bool(result.errors),
                             transcript=stream.getvalue(),counted_as_new_test=False))
    result=dict(controls=receipts,passed=all(r['killed'] and not r['harness_error'] for r in receipts),new_distinct_tests=0)
    out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
