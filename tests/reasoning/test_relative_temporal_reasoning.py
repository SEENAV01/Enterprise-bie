import unittest
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.relative_temporal_reasoning import RelativeOffset, resolve_relative_time
class Tests(unittest.TestCase):
 def setUp(self): self.refs=(EvidenceRef("e1","primary",0.9),EvidenceRef("e2","supporting",0.8))
 def test_exact_relative_offset(self):
  r=resolve_relative_time("a",TimeSpan(100,100),RelativeOffset("r","a","b",5,5,("e1",)),self.refs);self.assertEqual(r.status,"RESOLVED");self.assertEqual(r.value["target_span"]["earliest"],105)
 def test_uncertainty_propagates(self):
  r=resolve_relative_time("a",TimeSpan(100,102),RelativeOffset("r","a","b",3,5,("e1",)),self.refs);self.assertEqual(r.status,"AMBIGUOUS");self.assertEqual((r.value["target_span"]["earliest"],r.value["target_span"]["latest"]),(103,107))
 def test_open_anchor_propagates_open_bound(self):
  r=resolve_relative_time("a",TimeSpan(None,10),RelativeOffset("r","a","b",1,1,("e1",)),self.refs);self.assertIsNone(r.value["target_span"]["earliest"])
 def test_reversed_offset_rejected(self):
  with self.assertRaises(ValueError):resolve_relative_time("a",TimeSpan(1,1),RelativeOffset("r","a","b",2,1,("e1",)),self.refs)
 def test_unresolved_evidence_rejected(self):
  with self.assertRaises(ValueError):resolve_relative_time("a",TimeSpan(1,1),RelativeOffset("r","a","b",1,1,("missing",)),self.refs)
