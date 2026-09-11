import unittest
from bie.reasoning.temporal_abstention_policy import *
class T(unittest.TestCase):
 def test_assert(self): self.assertTrue(temporal_decision(TemporalDecisionContext(.9,2)).may_assert)
 def test_contradiction(self): self.assertEqual(temporal_decision(TemporalDecisionContext(.9,2,1)).status,"ABSTAIN_CONTRADICTION")
 def test_evidence(self): self.assertEqual(temporal_decision(TemporalDecisionContext(.9,0)).status,"ABSTAIN_INSUFFICIENT_EVIDENCE")
 def test_confidence(self): self.assertEqual(temporal_decision(TemporalDecisionContext(.2,2)).status,"ABSTAIN_LOW_CONFIDENCE")
 def test_invalid_confidence(self):
  with self.assertRaises(ValueError): temporal_decision(TemporalDecisionContext(1.2,1))
 def test_invalid_count(self):
  with self.assertRaises(ValueError): temporal_decision(TemporalDecisionContext(.8,-1))
