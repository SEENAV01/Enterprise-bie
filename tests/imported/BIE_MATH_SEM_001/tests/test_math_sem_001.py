import unittest
from bie.math_intelligence.equation_semantics import *
class T(unittest.TestCase):
 def test_fma(self):
  s=infer_semantics(["F"],["m","a"]);self.assertEqual((s.dependent,s.independent),(("F",),("a","m")))
 def test_constant(self): self.assertEqual(infer_semantics(["E"],["m","c"],{"c"}).constants,("c",))
 def test_ineq(self): self.assertEqual(infer_semantics(["x"],["a"],relation="<").relation_type,"inequality")
 def test_bad(self):
  with self.assertRaises(ValueError):infer_semantics([],["x"])
if __name__=="__main__":unittest.main()
