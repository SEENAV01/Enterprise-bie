import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.physics_vector_grammar import plan_physics_vectors, PHYSICS_VECTOR_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError

class T(unittest.TestCase):
    def base(self, **kw):
        args=dict(vectors=[{'id':'F','quantity':'force','direction':[1,0],'magnitude':10,'unit':'N','source_ids':['s']}],frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); args.update(kw); return plan_physics_vectors(**args)
    def test_grammar_identity(self): self.assertEqual(PHYSICS_VECTOR_GRAMMAR.grammar_id,'bie.vis.grammar.physics_vector')
    def test_valid_plan(self): self.assertEqual(self.base().elements[1]['payload']['magnitude'],10.0)
    def test_review_required(self): self.assertTrue(self.base().review_required); self.assertFalse(self.base().accepted)
    def test_no_scale_warning(self): self.assertTrue(self.base().warnings)
    def test_scale_removes_warning(self): self.assertFalse(self.base(scale=2).warnings)
    def test_components(self): self.assertEqual(self.base(vectors=[{'id':'v','components':[3,4],'source_ids':['s']}]).elements[1]['payload']['components'],[3.0,4.0])
    def test_zero_direction_rejected(self):
        with self.assertRaises(GrammarValidationError): self.base(vectors=[{'id':'v','direction':[0,0],'source_ids':['s']}])
    def test_negative_magnitude_rejected(self):
        with self.assertRaises(GrammarValidationError): self.base(vectors=[{'id':'v','direction':[1,0],'magnitude':-1,'source_ids':['s']}])
    def test_duplicate_vector_rejected(self):
        with self.assertRaises(GrammarValidationError): self.base(vectors=[{'id':'v','direction':[1,0],'source_ids':['s']},{'id':'v','direction':[0,1],'source_ids':['s']}])
    def test_missing_direction_rejected(self):
        with self.assertRaises(GrammarValidationError): self.base(vectors=[{'id':'v','source_ids':['s']}])
    def test_deterministic(self): self.assertEqual(self.base().fingerprint,self.base().fingerprint)
    def test_frame_relation(self): self.assertEqual(self.base().relations[0]['kind'],'expressed_in')

if __name__=='__main__': unittest.main()
