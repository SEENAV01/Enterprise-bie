import unittest
from app.bie.prerequisite_intelligence.calibration import *
class T(unittest.TestCase):
 def test_perfect(self): self.assertEqual(calibration_report([0,1],[0,1],2).ece,0)
 def test_nonzero(self): self.assertGreater(calibration_report([.9],[0]).ece,0)
 def test_empty(self): self.assertEqual(calibration_report([],[]).ece,0)
 def test_invalid(self):
  with self.assertRaises(ValueError): calibration_report([.5],[2])
if __name__=="__main__": unittest.main()
