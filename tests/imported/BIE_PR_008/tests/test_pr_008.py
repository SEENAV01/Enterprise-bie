import unittest
from bie.prerequisite_intelligence.cycle_resolution import *
class T(unittest.TestCase):
 def test_cycle_removed(self):
  e=[WeightedEdge("a","b",.9),WeightedEdge("b","c",.8),WeightedEdge("c","a",.2)]
  kept,removed=resolve_cycles({"a","b","c"},e)
  self.assertEqual(removed[0].confidence,.2); self.assertEqual(find_cycle({"a","b","c"},kept),[])
 def test_acyclic(self):
  e=[WeightedEdge("a","b",1)]; self.assertEqual(resolve_cycles({"a","b"},e)[1],[])
 def test_two_cycle(self):
  e=[WeightedEdge("a","b",.4),WeightedEdge("b","a",.7)]
  self.assertEqual(resolve_cycles({"a","b"},e)[1][0].confidence,.4)
 def test_deterministic_tie(self):
  e=[WeightedEdge("a","b",.5),WeightedEdge("b","a",.5)]
  _,r=resolve_cycles({"a","b"},e); self.assertEqual((r[0].source,r[0].target),("a","b"))
if __name__=="__main__": unittest.main()
