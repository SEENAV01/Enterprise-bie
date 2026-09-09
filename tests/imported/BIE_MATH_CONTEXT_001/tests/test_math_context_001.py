import unittest
from bie.math_intelligence.context_grounding import *
class T(unittest.TestCase):
 def test_link(self): self.assertEqual(ground_equation("e1","force","p2","explicit formula",.9).concept_id,"force")
 def test_best(self):
  a=ground_equation("e","c","p1","x",.5);b=ground_equation("e","c","p2","x",.9);self.assertEqual(best_grounding([a,b]),b)
 def test_empty(self): self.assertIsNone(best_grounding([]))
 def test_conf(self):
  with self.assertRaises(ValueError):ground_equation("e","c","p","x",1.2)
if __name__=="__main__":unittest.main()
