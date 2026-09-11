import unittest
from bie.reasoning.temporal_relative_anchor_resolution import *
class T(unittest.TestCase):
 def test_after(self): self.assertEqual(resolve_relative_time(RelativeTime(2,"day"),AnchoredTime(10,"day")).value,12)
 def test_cross_unit(self): self.assertEqual(resolve_relative_time(RelativeTime(60,"minute"),AnchoredTime(2,"hour")).value,3)
 def test_before(self): self.assertEqual(resolve_relative_time(RelativeTime(-1,"day"),AnchoredTime(10,"day")).value,9)
 def test_missing_anchor(self):
  with self.assertRaises(ValueError): resolve_relative_time(RelativeTime(1,"day"),None)
 def test_bad_unit(self):
  with self.assertRaises(ValueError): resolve_relative_time(RelativeTime(1,"fortnight"),AnchoredTime(1,"day"))
