import unittest
from bie.reasoning.temporal_multi_scale_reasoning import *
class T(unittest.TestCase):
 def test_convert(self): self.assertEqual(to_seconds(ScaledTime(2,"minute")),120)
 def test_equal(self): self.assertEqual(compare_scaled_times(ScaledTime(1,"hour"),ScaledTime(60,"minute")),"EQUIVALENT")
 def test_short(self): self.assertEqual(compare_scaled_times(ScaledTime(1,"minute"),ScaledTime(2,"minute")),"SHORTER")
 def test_unknown(self):
  with self.assertRaises(ValueError): to_seconds(ScaledTime(1,"century"))
