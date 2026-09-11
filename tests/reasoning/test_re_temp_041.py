import unittest
from bie.reasoning.temporal_evidence_conflict_matrix import *
class T(unittest.TestCase):
 def test_opposite(self): self.assertTrue(temporal_claim_conflicts(TemporalClaim("1","a","before","b"),TemporalClaim("2","a","after","b")))
 def test_reverse(self): self.assertTrue(temporal_claim_conflicts(TemporalClaim("1","a","before","b"),TemporalClaim("2","b","before","a")))
 def test_no_conflict(self): self.assertFalse(temporal_claim_conflicts(TemporalClaim("1","a","before","b"),TemporalClaim("2","a","before","b")))
 def test_pairs(self): self.assertEqual(conflict_pairs([TemporalClaim("b","a","after","b"),TemporalClaim("a","a","before","b")]),(("a","b"),))
