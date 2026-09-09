import unittest
from app.bie.math_intelligence.realbook_benchmark import *
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(evaluate_case("p1","physics",1,1,1,1).passed)
 def test_failures(self): self.assertIn("derivation",evaluate_case("m1","mathematics",1,1,0,1).failures)
 def test_summary(self):
  r=[evaluate_case("p","physics",1,1,1,1),evaluate_case("m","mathematics",1,1,1,1),evaluate_case("c","chemistry",1,1,1,1)]
  self.assertEqual(summarize(r)["missing_domains"],())
 def test_empty(self): self.assertEqual(summarize([])["pass_rate"],0.0)
if __name__=="__main__":unittest.main()
