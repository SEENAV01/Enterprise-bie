"""Six meaningful seeded bypass controls; never count reruns as new tests."""
from pathlib import Path
import io,json,sys,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from run_section18_tests import load
from apps.operator import previews as module
from apps.operator.contracts import Credentials
def main():
    tests=load('tests/section18/test_batch003.py');original=module.require
    def bypass(code):return patch.object(module,'require',lambda cond,c,status=409:None if c==code else original(cond,c,status))
    rows=[('preview_source_identity_bypass',tests.Art005,'test_source_identity_mismatch_rejected',bypass('preview_source_mismatch')),
        ('range_policy_bypass',tests.Art005,'test_unsatisfiable_range_416_safe_length',patch.object(module,'byte_range',lambda v,size,*args:(0,size-1,200))),
        ('injected_decoder_native_claim_bypass',tests.Art005,'test_injected_decoder_cannot_claim_native',bypass('render_execution_kind_invalid')),
        ('native_entrypoint_binding_bypass',tests.Art006,'test_resealed_noncanonical_game_entry_rejected',bypass('game_entry_not_canonical')),
        ('package_self_manifest_bypass',tests.Art006,'test_manifest_self_hash_tamper_rejected',patch.object(module,'verify_package',lambda *a:None)),
        ('specific_credential_revocation_bypass',tests.Art006,'test_distinct_same_principal_grant_cannot_preserve_revoked_token',
            patch.object(Credentials,'check_binding',lambda self,binding,p,permission:self.check(p,permission)))]
    results=[]
    for name,cls,method,mutant in rows:
        transcript=io.StringIO()
        with mutant:r=unittest.TextTestRunner(stream=transcript).run(unittest.TestSuite([cls(method)]))
        results.append(dict(control=name,authored_method=cls.__name__+'.'+method,killed=bool(r.failures),harness_error=bool(r.errors),
                            transcript=transcript.getvalue(),counted_as_new_test=False))
    receipt=dict(passed=all(r['killed'] and not r['harness_error'] for r in results),controls=results,new_distinct_tests=0,product_accepted=False)
    out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='controls'}));return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
