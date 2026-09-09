import unittest
from bie.math_intelligence.symbols import *
class T(unittest.TestCase):
 def test_pi(self): self.assertEqual(classify_symbol("π").category,"constant")
 def test_theta(self): self.assertEqual(classify_symbol("θ").canonical,"theta")
 def test_id(self): self.assertEqual(classify_symbol("x").category,"identifier")
 def test_empty(self):
  with self.assertRaises(ValueError):classify_symbol("")
if __name__=="__main__":unittest.main()
