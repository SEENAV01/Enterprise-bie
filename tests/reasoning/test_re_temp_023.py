import unittest
from bie.reasoning.temporal_revision_reasoning import *
class T(unittest.TestCase):
 def test_empty(self): self.assertIsNone(latest_temporal_assertion([]))
 def test_latest(self): self.assertEqual(latest_temporal_assertion([TemporalAssertion("a","x",1),TemporalAssertion("b","y",2,"a")]).assertion_id,"b")
 def test_deterministic(self): self.assertEqual(latest_temporal_assertion([TemporalAssertion("b","x",2),TemporalAssertion("a","y",2)]).assertion_id,"a")
 def test_missing_parent(self):
  with self.assertRaises(ValueError): latest_temporal_assertion([TemporalAssertion("b","x",2,"a")])
