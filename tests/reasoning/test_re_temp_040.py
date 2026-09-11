import unittest
from bie.reasoning.temporal_precision_compatibility import *
class T(unittest.TestCase):
 def test_same(self): self.assertTrue(exact_comparison_allowed(PreciseTime(1,"day"),PreciseTime(2,"day")))
 def test_mixed_not_exact(self): self.assertFalse(exact_comparison_allowed(PreciseTime(1,"year"),PreciseTime(2,"day")))
 def test_common(self): self.assertEqual(compatible_precision(PreciseTime(1,"month"),PreciseTime(2,"day")),"month")
 def test_unknown(self):
  with self.assertRaises(ValueError): compatible_precision(PreciseTime(1,"era"),PreciseTime(2,"day"))
