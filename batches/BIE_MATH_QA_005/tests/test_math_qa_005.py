import unittest
from app.bie.math_intelligence.symbolic_qa import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(assess_symbolic({"x","y"},{"x"},True).passed)
 def test_undefined(self): self.assertIn("undefined_symbols:z",assess_symbolic({"x"},{"x","z"},True).failures)
 def test_equiv(self): self.assertIn("symbolic_non_equivalence",assess_symbolic({"x"},{"x"},False).failures)
 def test_scope(self): self.assertIn("symbol_scope_conflict",assess_symbolic({"x"},{"x"},True,(("s","x"),)).failures)
if __name__=="__main__":unittest.main()
