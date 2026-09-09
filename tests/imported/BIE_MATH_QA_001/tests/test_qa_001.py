import unittest
from app.bie.math_intelligence.formula_qa import *
class T(unittest.TestCase):
 def test_ok(self): self.assertTrue(check_formula("F=ma").passed)
 def test_empty(self): self.assertFalse(check_formula("").passed)
 def test_balance(self): self.assertIn("unbalanced_structure",check_formula("x=y",False).failures)
 def test_unknown(self): self.assertIn("unknown_symbols:z",check_formula("x=z",True,{"x"},{"x","z"}).failures)
if __name__=="__main__":unittest.main()
