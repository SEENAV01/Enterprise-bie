import unittest
from app.bie.math_intelligence.equation_ast import *
class T(unittest.TestCase):
 def test_eq(self): self.assertEqual(parse_equation("F = ma").right,"ma")
 def test_ineq(self): self.assertEqual(parse_equation("x ≤ 3").relation,"≤")
 def test_approx(self): self.assertEqual(parse_equation("pi≈3.14").relation,"≈")
 def test_bad(self):
  with self.assertRaises(ValueError): parse_equation("x+1")
if __name__=="__main__":unittest.main()
