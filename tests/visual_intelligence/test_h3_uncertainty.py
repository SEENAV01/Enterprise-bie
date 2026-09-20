import unittest
from bie.visual_intelligence.uncertainty_propagation import *
class T(unittest.TestCase):
 def e(self,c=.9,g=None,b=None): return UncertaintyEvidence('e'+str(c)+str(g),c,'source',b,g,'src')
 def test_pass(self): self.assertEqual(propagate_uncertainty(claim_id='c',evidence=[self.e()],stage_confidences={'rep':.9}).status,'PASS')
 def test_review(self): self.assertEqual(propagate_uncertainty(claim_id='c',evidence=[self.e(.6)],stage_confidences={}).status,'REVIEW')
 def test_abstain(self): self.assertTrue(propagate_uncertainty(claim_id='c',evidence=[self.e(.3)],stage_confidences={}).abstain)
 def test_conflict(self):
  x=[UncertaintyEvidence('a',.9,'s',None,'g'),UncertaintyEvidence('b',.8,'s',None,'g')];self.assertIn('conflicting_evidence',propagate_uncertainty(claim_id='c',evidence=x,stage_confidences={}).reasons)
 def test_bounds(self): self.assertEqual(propagate_uncertainty(claim_id='c',evidence=[self.e(.9,b=(1,2))],stage_confidences={}).bounds,(1.0,2.0))
 def test_disclosure(self):
  s=propagate_uncertainty(claim_id='c',evidence=[self.e(.7)],stage_confidences={})
  with self.assertRaises(UncertaintyError): enforce_visual_certainty(s,{'asserted_certain':True,'uncertainty_visible':False})
 def test_not_accepted(self): self.assertFalse(propagate_uncertainty(claim_id='c',evidence=[self.e()],stage_confidences={}).accepted)
