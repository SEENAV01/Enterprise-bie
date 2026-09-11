import unittest
from bie.reasoning.temporal_scope_reasoning import *
class T(unittest.TestCase):
 def test_inside(self): self.assertTrue(in_temporal_scope(5,TemporalScope(1,10)))
 def test_boundary_inclusive(self): self.assertTrue(in_temporal_scope(1,TemporalScope(1,10)))
 def test_boundary_exclusive(self): self.assertFalse(in_temporal_scope(1,TemporalScope(1,10,False)))
 def test_filter(self): self.assertEqual(filter_temporal_scope([0,2,5,9],TemporalScope(2,5)),(2,5))
 def test_invalid(self):
  with self.assertRaises(ValueError): in_temporal_scope(1,TemporalScope(5,2))
