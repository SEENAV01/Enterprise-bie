import unittest
from bie.math_intelligence.advanced_notation import *
class T(unittest.TestCase):
 def test_integral(self): self.assertEqual(detect_notation("∫ f(x) dx")[0].kind,"integral")
 def test_sum(self): self.assertTrue(any(x.kind=="summation" for x in detect_notation(r"\\sum x_i")))
 def test_set(self): self.assertTrue(any(x.kind=="set" for x in detect_notation("x ∈ A")))
 def test_multi(self): self.assertGreaterEqual(len(detect_notation(r"\\lim_{x→∞} f(x)")),2)
if __name__=="__main__":unittest.main()
