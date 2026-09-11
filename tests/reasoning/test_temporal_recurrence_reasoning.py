import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.temporal_recurrence_reasoning import RecurrenceRule, expand_recurrence
class Tests(unittest.TestCase):
 def setUp(self):self.refs=(EvidenceRef("e","primary",0.9),)
 def test_window_expansion(self):
  r=expand_recurrence(RecurrenceRule("r","s",2,3,("e",)),5,12,"historical_year",self.refs);self.assertEqual([x["tick"] for x in r.value["occurrences"]],[5,8,11])
 def test_last_tick_bounds_series(self):
  r=expand_recurrence(RecurrenceRule("r","s",1,2,("e",),last_tick=5),1,20,"historical_year",self.refs);self.assertEqual([x["tick"] for x in r.value["occurrences"]],[1,3,5])
 def test_max_occurrence_bounds_series(self):
  r=expand_recurrence(RecurrenceRule("r","s",1,2,("e",),max_occurrences=2),1,20,"historical_year",self.refs);self.assertEqual(len(r.value["occurrences"]),2)
 def test_invalid_cadence_rejected(self):
  with self.assertRaises(ValueError):expand_recurrence(RecurrenceRule("r","s",1,0,("e",)),1,2,"historical_year",self.refs)
 def test_unknown_axis_rejected(self):
  with self.assertRaises(ValueError):expand_recurrence(RecurrenceRule("r","s",1,1,("e",)),1,2,"clock",self.refs)
