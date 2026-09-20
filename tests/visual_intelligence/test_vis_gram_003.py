import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.field_grammar import plan_field, FIELD_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def test_identity(self): self.assertEqual(FIELD_GRAMMAR.grammar_id,'bie.vis.grammar.field')
    def test_scalar(self):
        p=plan_field([{'id':'a','coordinates':[0,1],'value':5,'source_ids':['s']}],field_type='scalar',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'sample_point')
    def test_vector(self):
        p=plan_field([{'id':'a','coordinates':[0,1],'vector':[1,2],'source_ids':['s']}],field_type='vector',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'field_arrow')
    def test_bad_type(self):
        with self.assertRaises(GrammarValidationError): plan_field([],field_type='tensor',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r'])
    def test_dim_mismatch(self):
        with self.assertRaises(GrammarValidationError): plan_field([{'id':'a','coordinates':[0,1],'vector':[1]}],field_type='vector',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty_rejected(self):
        with self.assertRaises(GrammarValidationError): plan_field([],field_type='scalar',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r'])
    def test_derived_warning(self):
        p=plan_field([{'id':'a','coordinates':[0,1],'value':5,'source_ids':['s']}],field_type='scalar',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r'],derived_lines=True); self.assertTrue(p.warnings)
    def test_no_invented_derived(self):
        p=plan_field([{'id':'a','coordinates':[0,1],'value':5,'source_ids':['s']}],field_type='scalar',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(len(p.elements),2)
    def test_deterministic(self):
        kw=dict(samples=[{'id':'a','coordinates':[0,1],'value':5,'source_ids':['s']}],field_type='scalar',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_field(**kw).fingerprint,plan_field(**kw).fingerprint)
    def test_review(self):
        p=plan_field([{'id':'a','coordinates':[0,1],'value':5,'source_ids':['s']}],field_type='scalar',frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); self.assertTrue(p.review_required)
if __name__=='__main__': unittest.main()
