import unittest
from app.bie.math_intelligence.canonical_math import *
class T(unittest.TestCase):
 def test_mul(self): self.assertEqual(canonicalize("a × b"),"a*b")
 def test_minus(self): self.assertEqual(canonicalize("x − 1"),"x-1")
 def test_latex_wrapper(self): self.assertEqual(canonicalize(r"\\left(x\\right)"),"(x)")
 def test_equiv(self): self.assertTrue(canonical_equivalent("a·b","a * b"))
if __name__=="__main__":unittest.main()
