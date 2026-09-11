import unittest
from bie.reasoning.temporal_causal_order_guard import *
class T(unittest.TestCase):
 def test_allowed_not_proven(self): self.assertEqual(validate_causal_temporal_order(2,3).status,"TEMPORALLY_ADMISSIBLE_NOT_CAUSALLY_PROVEN")
 def test_reject(self): self.assertFalse(validate_causal_temporal_order(5,3).allowed)
 def test_unknown_cause(self): self.assertEqual(validate_causal_temporal_order(None,3).status,"ABSTAIN_UNKNOWN_TEMPORAL_ORDER")
 def test_unknown_effect(self): self.assertFalse(validate_causal_temporal_order(2,None).allowed)
