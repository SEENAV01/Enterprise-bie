import unittest
from app.bie.misconception_intelligence.severity import *
class T(unittest.TestCase):
 def test_critical(self): self.assertEqual(score_severity(1,1,1,1).band,"critical")
 def test_low(self): self.assertEqual(score_severity(0,0,0).band,"low")
 def test_impact(self): self.assertGreater(score_severity(0,1,0).score,score_severity(1,0,0).score)
 def test_invalid(self):
  with self.assertRaises(ValueError): score_severity(-1,0,0)
if __name__=="__main__": unittest.main()
