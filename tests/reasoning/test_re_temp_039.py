import unittest
from bie.reasoning.temporal_iterator_safety import *
class T(unittest.TestCase):
 def test_generators_preserved(self):
  m=materialize_temporal_inputs((x for x in range(3)),(x for x in range(2)),(x for x in range(4)))
  self.assertEqual(temporal_input_counts(m),{"events":3,"constraints":2,"evidence":4})
 def test_reusable(self):
  m=materialize_temporal_inputs((x for x in [1,2]))
  self.assertEqual(tuple(m.events),(1,2)); self.assertEqual(tuple(m.events),(1,2))
 def test_empty(self): self.assertEqual(temporal_input_counts(materialize_temporal_inputs()),{"events":0,"constraints":0,"evidence":0})
 def test_tuple_identity_semantics(self): self.assertEqual(materialize_temporal_inputs([1]).events,(1,))
