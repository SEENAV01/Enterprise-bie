import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep005_timeline import *
def I(**kw):
 d=dict(intent_id='i',domain='history',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=());d.update(kw);return SemanticIntent(**d)
class T(unittest.TestCase):
 def test_none(self):self.assertEqual(choose(I(),0).status,'UNSUPPORTED')
 def test_temporal(self):self.assertEqual(choose(I(temporal=True),3).selected,'timeline')
 def test_events(self):self.assertEqual(choose(I(),3).selected,'timeline')
 def test_one(self):self.assertEqual(choose(I(temporal=True),1).status,'REVIEW')
 def test_order(self):self.assertEqual(choose(I(temporal=True),3,False).status,'REVIEW')
 def test_uncertain(self):self.assertTrue(choose(I(temporal=True),3,uncertain_dates=True).payload['preserve_uncertainty'])
 def test_intervals(self):self.assertTrue(choose(I(temporal=True),3,has_intervals=True).payload['intervals'])
 def test_simult(self):self.assertTrue(choose(I(temporal=True),3,simultaneous_events=True).payload['simultaneous_events'])
 def test_bad(self):
  with self.assertRaises(RepresentationError):choose(I(),-1)
 def test_accept(self):self.assertFalse(choose(I(temporal=True),3).accepted)
