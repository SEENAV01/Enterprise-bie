import unittest
from app.bie.math_intelligence.function_intelligence import *
class T(unittest.TestCase):
 def test_explicit(self): self.assertEqual(function_spec("f",["x"],"x^2").variables,("x",))
 def test_parametric(self): self.assertEqual(function_spec("r",["t"],"(cos(t),sin(t))","parametric").representation,"parametric")
 def test_duplicate(self):
  with self.assertRaises(ValueError):function_spec("f",["x","x"],"x")
 def test_bad_repr(self):
  with self.assertRaises(ValueError):function_spec("f",["x"],"x","unknown")
if __name__=="__main__":unittest.main()
