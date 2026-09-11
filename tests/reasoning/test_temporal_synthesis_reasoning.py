import unittest
from bie.reasoning.chronology_reasoning import Event, TimeSpan
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.event_order_reasoning import Before
from bie.reasoning.periodization_reasoning import Period
from bie.reasoning.temporal_synthesis_reasoning import synthesize_timeline
class Tests(unittest.TestCase):
 def setUp(self):self.refs=(EvidenceRef("a","primary",.9),EvidenceRef("b","primary",.9),EvidenceRef("p","supporting",.8),EvidenceRef("c","constraint",.8))
 def events(self):return [Event("e1","one",TimeSpan(1,1),("a",)),Event("e2","two",TimeSpan(2,2),("b",))]
 def periods(self):return [Period("p1","P",0,3,("p",))]
 def test_resolved_synthesis(self):
  r=synthesize_timeline(self.events(),[],self.periods(),self.refs);self.assertEqual(r.status,"RESOLVED");self.assertEqual(r.value["proven_sequence"],["e1","e2"]);self.assertEqual(len(r.value["timeline_rows"]),2)
 def test_periods_are_attached(self):
  r=synthesize_timeline(self.events(),[],self.periods(),self.refs);self.assertEqual(r.value["timeline_rows"][0]["definite_period_ids"],["p1"])
 def test_cycle_propagates_conflict(self):
  es=[Event("e1","one",TimeSpan(1,3),("a",)),Event("e2","two",TimeSpan(1,3),("b",))];cs=[Before("e1","e2",("c",)),Before("e2","e1",("c",))]
  r=synthesize_timeline(es,cs,self.periods(),self.refs);self.assertEqual(r.status,"CONFLICT");self.assertEqual(r.value["proven_sequence"],[])
 def test_ambiguous_dates_preserved(self):
  es=[Event("e1","one",TimeSpan(1,3),("a",)),Event("e2","two",TimeSpan(2,4),("b",))];r=synthesize_timeline(es,[],self.periods(),self.refs);self.assertEqual(r.status,"AMBIGUOUS")
 def test_deterministic_output(self):
  r1=synthesize_timeline(self.events(),[],self.periods(),self.refs);r2=synthesize_timeline(list(reversed(self.events())),[],self.periods(),self.refs);self.assertEqual(r1.value_json,r2.value_json)
