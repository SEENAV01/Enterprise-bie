
import unittest
from bie.infrastructure.impact_propagation import *
class T(unittest.TestCase):
 def setUp(self):
  self.t={"A":{"dependencies":[],"status":"ACCEPTED"},"B":{"dependencies":["A"],"status":"ACCEPTED"},"C":{"dependencies":["B"],"status":"PLANNED"},"D":{"dependencies":["A"],"status":"IMPLEMENTED"}}
 def test_reverse(self): self.assertEqual(reverse_graph(self.t)["A"],["B","D"])
 def test_impact_count(self): self.assertEqual(len(impact(self.t,"A")),3)
 def test_distance(self): self.assertEqual({x["task_id"]:x["distance"] for x in impact(self.t,"A")}["C"],2)
 def test_candidates(self): self.assertEqual(invalidation_candidates(self.t,"A"),["B","D"])
 def test_planned_not_candidate(self): self.assertNotIn("C",invalidation_candidates(self.t,"A"))
 def test_unknown(self):
  with self.assertRaises(ImpactError): impact(self.t,"X")
 def test_leaf(self): self.assertEqual(impact(self.t,"C"),[])
if __name__=="__main__": unittest.main()
