import unittest
from bie.math_intelligence.graph_features import *
class T(unittest.TestCase):
 def test_root(self): self.assertEqual(analyze_samples([(-1,-1),(0,0),(1,1)]).roots,(0,))
 def test_inc(self): self.assertEqual(analyze_samples([(0,0),(1,2)]).monotonic,"increasing")
 def test_ext(self): self.assertEqual(analyze_samples([(-1,0),(0,1),(1,0)]).extrema,((0,1),))
 def test_empty(self):
  with self.assertRaises(ValueError):analyze_samples([])
if __name__=="__main__":unittest.main()
