import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep006_graph import *
def I(**kw):
 d=dict(intent_id='i',domain='mathematics',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=());d.update(kw);return SemanticIntent(**d)
class T(unittest.TestCase):
 def test_none(self):self.assertEqual(choose(I()).status,'UNSUPPORTED')
 def test_quant(self):self.assertEqual(choose(I(quantitative=True),axis_semantics=True).selected,'graph')
 def test_data(self):self.assertEqual(choose(I(),4,axis_semantics=True).selected,'graph')
 def test_fun(self):self.assertEqual(choose(I(),function_defined=True,axis_semantics=True).selected,'graph')
 def test_axis(self):self.assertEqual(choose(I(quantitative=True)).status,'BLOCKED')
 def test_exact(self):self.assertEqual(choose(I(),3,axis_semantics=True,sampled_data=True,exact_curve_claim=True).status,'BLOCKED')
 def test_units_review(self):self.assertEqual(choose(I(quantitative=True,payload={'units_required':True}),axis_semantics=True).status,'REVIEW')
 def test_units_pass(self):self.assertEqual(choose(I(quantitative=True,payload={'units_required':True}),axis_semantics=True,units_known=True).status,'PASS')
 def test_domain(self):self.assertTrue(choose(I(),function_defined=True,axis_semantics=True,domain_restriction=True).payload['domain_restriction'])
 def test_bad(self):
  with self.assertRaises(RepresentationError):choose(I(),-1)
 def test_det(self):self.assertEqual(choose(I(),function_defined=True,axis_semantics=True).fingerprint,choose(I(),function_defined=True,axis_semantics=True).fingerprint)
 def test_accept(self):self.assertFalse(choose(I(),function_defined=True,axis_semantics=True).accepted)
