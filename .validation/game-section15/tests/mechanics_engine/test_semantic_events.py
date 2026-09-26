import unittest
from bie.game_engine.mechanics_engine import parameter
from bie.game_engine.mechanics_engine.common import sample_context
from bie.game_engine.mechanics_engine.semantic_events import from_receipt
class SemanticEventTests(unittest.TestCase):
 def test_event_is_causally_bound_to_receipt(self):
  d=parameter.define(sample_context());_,_,r=parameter.execute(sample_context(),{'value':1},1,(0,10));e=from_receipt(d,r);self.assertTrue(e.causal);self.assertFalse(e.decorative_only);self.assertEqual(e.receipt_id,r.receipt_id);self.assertEqual(e.motion_ids,r.semantic_motion_ids)
 def test_mismatched_mechanic_rejected(self):
  from bie.game_engine.mechanics_engine import retrieval
  d=retrieval.define(sample_context());_,_,r=parameter.execute(sample_context(),{'value':1},1,(0,10))
  with self.assertRaises(Exception):from_receipt(d,r)
