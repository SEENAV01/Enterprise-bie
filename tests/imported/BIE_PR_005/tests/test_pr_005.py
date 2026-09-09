import unittest
from app.bie.prerequisite_intelligence.confidence import *
class T(unittest.TestCase):
 def test_accept(self): self.assertEqual(calibrate_confidence(.8).band,"accepted")
 def test_corroboration(self): self.assertGreater(calibrate_confidence(.6,4).calibrated,.6)
 def test_contradiction(self): self.assertEqual(calibrate_confidence(.8,1,.6).band,"review")
 def test_reject(self): self.assertEqual(calibrate_confidence(.2).band,"rejected")
 def test_invalid(self):
  with self.assertRaises(ValueError): calibrate_confidence(2)
if __name__=="__main__": unittest.main()
