import unittest
from bie.reasoning.temporal_uncertainty_chain import *

class T(unittest.TestCase):
    def test_single(self):
        self.assertEqual(apply_offset(UncertainTime(1,2),OffsetBound(3,4)),UncertainTime(4,6))
    def test_chain(self):
        self.assertEqual(propagate_offset_chain(UncertainTime(0,1),[OffsetBound(1,2),OffsetBound(2,3)]),UncertainTime(3,6))
    def test_axis(self):
        self.assertEqual(apply_offset(UncertainTime(1,1,"year"),OffsetBound(1,1)).axis,"year")
    def test_bad_time(self):
        with self.assertRaises(ValueError):
            apply_offset(UncertainTime(2,1),OffsetBound(1,1))
    def test_bad_offset(self):
        with self.assertRaises(ValueError):
            apply_offset(UncertainTime(1,2),OffsetBound(2,1))
