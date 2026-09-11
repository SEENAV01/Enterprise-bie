import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.duration_reasoning import DurationClaim,duration
class Tests(unittest.TestCase):
 def setUp(self): self.refs=(EvidenceRef('s:1','primary',.9),)
 def c(self,a,b,c,d,axis='historical_year'): return DurationClaim('D',TimeSpan(a,b,axis),TimeSpan(c,d,axis),('s:1',))
 def test_exact(self):
  r=duration(self.c(1,1,5,5),self.refs);self.assertEqual((r.value['minimum'],r.value['maximum'],r.value['exact']),(4,4,True))
 def test_uncertain(self):
  r=duration(self.c(1,2,5,7),self.refs);self.assertEqual((r.value['minimum'],r.value['maximum']),(3,6))
 def test_overlap_ambiguous(self): self.assertEqual(duration(self.c(1,5,3,7),self.refs).status,'AMBIGUOUS')
 def test_reversed_conflict(self): self.assertEqual(duration(self.c(5,6,1,2),self.refs).status,'CONFLICT')
 def test_open(self): self.assertEqual(duration(DurationClaim('D',TimeSpan(None,2),TimeSpan(5,6),('s:1',)),self.refs).status,'AMBIGUOUS')
 def test_day_unit(self): self.assertEqual(duration(self.c(10,10,12,12,'gregorian_day'),self.refs).value['unit'],'day')
 def test_axis_refused(self):
  with self.assertRaises(ValueError): duration(DurationClaim('D',TimeSpan(1,1),TimeSpan(2,2,'gregorian_day'),('s:1',)),self.refs)
