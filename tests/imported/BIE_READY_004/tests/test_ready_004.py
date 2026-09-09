import unittest
from app.bie.readiness_intelligence.readiness_evidence import *
class T(unittest.TestCase):
 def test_ready(self): self.assertTrue(decide_readiness([ReadinessEvidence("quiz",.9,1)]).ready)
 def test_weighted(self):
  r=decide_readiness([ReadinessEvidence("a",1,1),ReadinessEvidence("b",0,.5)],.5); self.assertAlmostEqual(r.weighted_score,.666667,6)
 def test_insufficient(self): self.assertEqual(decide_readiness([],min_evidence=1).reason,"insufficient_evidence")
 def test_invalid(self):
  with self.assertRaises(ValueError): decide_readiness([ReadinessEvidence("x",2,1)])
if __name__=="__main__": unittest.main()
