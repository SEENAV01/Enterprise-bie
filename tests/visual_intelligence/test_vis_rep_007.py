import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep007_equation import *
def I(**kw):
 d=dict(intent_id='i',domain='physics',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=());d.update(kw);return SemanticIntent(**d)
class T(unittest.TestCase):
 def test_none(self):self.assertEqual(choose(I(),'x=1').status,'UNSUPPORTED')
 def test_eq(self):self.assertEqual(choose(I(equation_present=True),'F=ma').selected,'equation')
 def test_steps(self):self.assertEqual(choose(I(),'x=1',2).payload['states'],3)
 def test_morph_review(self):self.assertEqual(choose(I(equation_present=True),'x=1',morph_requested=True).status,'REVIEW')
 def test_morph(self):self.assertTrue(choose(I(equation_present=True),'x=1',morph_requested=True,semantic_token_map={'x':'x'}).payload['morph_allowed'])
 def test_sync(self):self.assertTrue(choose(I(equation_present=True),'x=1',narration_sync_available=True).payload['narration_sync_available'])
 def test_badexp(self):
  with self.assertRaises(RepresentationError):choose(I(equation_present=True),'')
 def test_badsteps(self):
  with self.assertRaises(RepresentationError):choose(I(equation_present=True),'x',-1)
 def test_ground(self):self.assertEqual(choose(I(equation_present=True),'x').evidence_refs,('e',))
 def test_accept(self):self.assertFalse(choose(I(equation_present=True),'x').accepted)
