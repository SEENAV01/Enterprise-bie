import unittest
from app.bie.prerequisite_intelligence.realbook_benchmark import *
class T(unittest.TestCase):
 def test_perfect(self):
  r=evaluate([BookCase("physics",{("a","b")},{("a","b")})]);self.assertEqual(r.f1,1)
 def test_miss(self): self.assertLess(evaluate([BookCase("physics",{("a","b")},set())]).recall,1)
 def test_gate_domains(self): self.assertFalse(acceptance_ready(evaluate([BookCase("physics",set(),set())])))
 def test_five_domains(self):
  cs=[BookCase(d,{("a","b")},{("a","b")}) for d in ["physics","math","biology","history","geography"]]
  self.assertTrue(acceptance_ready(evaluate(cs)))
if __name__=="__main__": unittest.main()
