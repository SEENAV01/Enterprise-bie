import unittest
from bie.prerequisite_intelligence.strength import *
class T(unittest.TestCase):
 def test_strong(self):
  r=score_prerequisite_strength(StrengthSignals(1,1,1,1,0)); self.assertEqual(r.score,1); self.assertEqual(r.band,"strong")
 def test_weak(self): self.assertEqual(score_prerequisite_strength(StrengthSignals()).band,"weak")
 def test_contradiction(self):
  a=score_prerequisite_strength(StrengthSignals(explicit=1))
  b=score_prerequisite_strength(StrengthSignals(explicit=1,contradiction=1))
  self.assertLess(b.score,a.score)
 def test_invalid(self):
  with self.assertRaises(ValueError): score_prerequisite_strength(StrengthSignals(explicit=2))
if __name__=="__main__": unittest.main()
