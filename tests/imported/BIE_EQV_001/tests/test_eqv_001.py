import unittest
from app.bie.math_intelligence.symbolic_equivalence import *
class T(unittest.TestCase):
 def test_expand(self): self.assertTrue(equivalent("(x+1)*(x+1)","x^2+2*x+1").equivalent)
 def test_false(self): self.assertFalse(equivalent("x+1","x+2").equivalent)
 def test_two_vars(self): self.assertTrue(equivalent("x+y","y+x",("x","y")).equivalent)
 def test_unsafe(self):
  with self.assertRaises(ValueError):equivalent("__import__('os')","x")
if __name__=="__main__":unittest.main()
