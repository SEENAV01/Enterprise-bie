import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.periodization_reasoning import Period
from bie.reasoning.temporal_scheme_alignment import PeriodAlignment, align_period_schemes
class Tests(unittest.TestCase):
 def setUp(self):self.refs=(EvidenceRef("p1","primary",.9),EvidenceRef("p2","primary",.9),EvidenceRef("a","supporting",.8))
 def periods(self):return [Period("x","X",0,10,("p1",),scheme_id="s1"),Period("y","Y",5,15,("p2",),scheme_id="s2")]
 def test_alignment_overlap(self):
  r=align_period_schemes(self.periods(),[PeriodAlignment("x","y",("a",))],self.refs);self.assertEqual(r.status,"RESOLVED");self.assertEqual(r.value["alignments"][0]["boundary_overlap_ticks"],5)
 def test_no_alignment_is_ambiguous(self):self.assertEqual(align_period_schemes(self.periods(),[],self.refs).status,"AMBIGUOUS")
 def test_same_scheme_rejected(self):
  ps=[Period("x","X",0,10,("p1",),scheme_id="s"),Period("y","Y",5,15,("p2",),scheme_id="s")]
  with self.assertRaises(ValueError):align_period_schemes(ps,[PeriodAlignment("x","y",("a",))],self.refs)
 def test_unknown_period_rejected(self):
  with self.assertRaises(ValueError):align_period_schemes(self.periods(),[PeriodAlignment("x","z",("a",))],self.refs)
 def test_duplicate_alignment_rejected(self):
  with self.assertRaises(ValueError):align_period_schemes(self.periods(),[PeriodAlignment("x","y",("a",)),PeriodAlignment("y","x",("a",))],self.refs)
