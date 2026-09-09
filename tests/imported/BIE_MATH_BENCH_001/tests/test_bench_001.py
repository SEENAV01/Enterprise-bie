import unittest
from bie.math_intelligence.math_benchmark import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(evaluate([Metric("formula",.95,.9)],{"physics"},{"physics"}).passed)
 def test_floor(self): self.assertIn("formula",evaluate([Metric("formula",.8,.9)],set(),set()).failures)
 def test_domain(self): self.assertIn("missing_domain:math",evaluate([Metric("x",1,1)],{"math"},set()).failures)
 def test_empty(self):
  with self.assertRaises(ValueError):evaluate([],set(),set())
if __name__=="__main__":unittest.main()
