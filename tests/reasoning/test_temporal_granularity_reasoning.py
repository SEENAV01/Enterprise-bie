import unittest
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.temporal_granularity_reasoning import GranularTime, compare_granular_times
class Tests(unittest.TestCase):
 def setUp(self):self.refs=(EvidenceRef("a","primary",.9),EvidenceRef("b","primary",.8))
 def test_mixed_precision_before(self):
  r=compare_granular_times(GranularTime("x",TimeSpan(1,1),"year",("a",)),GranularTime("y",TimeSpan(3,4),"period",("b",)),self.refs);self.assertEqual(r.status,"RESOLVED");self.assertEqual(r.value["relation"],"before");self.assertEqual(r.value["precision_relation"],"mixed")
 def test_overlap_remains_ambiguous(self):
  r=compare_granular_times(GranularTime("x",TimeSpan(1,3),"year",("a",)),GranularTime("y",TimeSpan(2,4),"year",("b",)),self.refs);self.assertEqual(r.status,"AMBIGUOUS")
 def test_axis_mismatch_rejected(self):
  with self.assertRaises(ValueError):compare_granular_times(GranularTime("x",TimeSpan(1,1),"year",("a",)),GranularTime("y",TimeSpan(1,1,"gregorian_day"),"day",("b",)),self.refs)
 def test_bad_granularity_rejected(self):
  with self.assertRaises(ValueError):compare_granular_times(GranularTime("x",TimeSpan(1,1),"hour",("a",)),GranularTime("y",TimeSpan(2,2),"year",("b",)),self.refs)
 def test_same_identifier_rejected(self):
  with self.assertRaises(ValueError):compare_granular_times(GranularTime("x",TimeSpan(1,1),"year",("a",)),GranularTime("x",TimeSpan(2,2),"year",("b",)),self.refs)
