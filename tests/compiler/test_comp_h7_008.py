import unittest
from copy import deepcopy
from bie.compiler.section_closure import *
def rows():return [{'capability':c,'status':'VERIFIED_ACTUAL' if c in {'actual_render','pinned_compile'} else 'IMPLEMENTED_TESTED','evidence':['test:synthetic-register-only'],'remaining':[]} for c in REQUIRED]
class ClosureRegisterTests(unittest.TestCase):
    def test_full_register_not_product_acceptance(self):r=evaluate_section_closure(rows());self.assertTrue(r['section_exit_permitted']);self.assertFalse(r['product_accepted']);self.assertFalse(r['actual_render_authorization'])
    def test_environment_blocks_exit(self):r=rows();r[-1].update(status='BLOCKED_ENVIRONMENT',remaining=['real dependencies unavailable']);x=evaluate_section_closure(r);self.assertTrue(x['implementation_complete']);self.assertFalse(x['section_exit_permitted'])
    def test_implementation_gap_blocks_exit(self):r=rows();r[0].update(status='OPEN_IMPLEMENTATION',remaining=['required path missing']);self.assertFalse(evaluate_section_closure(r)['implementation_complete'])
    def test_missing_capability(self):self.assertRaises(ValueError,evaluate_section_closure,rows()[:-1])
    def test_duplicate_capability(self):r=rows();r[-1]=deepcopy(r[0]);self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_unknown_capability(self):r=rows();r[0]['capability']='magic';self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_required_cannot_be_scoped_out(self):r=rows();r[0]['status']='OUT_OF_SCOPE';self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_missing_evidence(self):r=rows();r[0]['evidence']=[];self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_complete_with_remaining_reject(self):r=rows();r[0]['remaining']=['not really complete'];self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_actual_test_count_cannot_replace_run(self):r=rows();r[-1]['status']='IMPLEMENTED_TESTED';self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_open_without_reason_reject(self):r=rows();r[0]['status']='OPEN_IMPLEMENTATION';self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_unknown_fields_reject(self):r=rows();r[0]['accepted']=True;self.assertRaises(ValueError,evaluate_section_closure,r)
    def test_digest_changes(self):r=rows();a=evaluate_section_closure(r);r[0]['evidence'].append('different');self.assertNotEqual(a['register_sha256'],evaluate_section_closure(r)['register_sha256'])
