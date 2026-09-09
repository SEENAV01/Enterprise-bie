import unittest
from app.bie.reasoning.confidence_calibration import *
class T(unittest.TestCase):
 def test_cal(self):self.assertEqual(calibrate(.8,[(.7,.9,.72)]),.72)
 def test_fallback(self):self.assertEqual(calibrate(.4,[]),.4)
 def test_specific(self):self.assertEqual(calibrate(.8,[(0,1,.5),(.7,.9,.75)]),.75)
 def test_bad(self):
  with self.assertRaises(ValueError):calibrate(2,[])
