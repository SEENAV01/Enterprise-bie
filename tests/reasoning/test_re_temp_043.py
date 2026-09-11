import unittest
from bie.reasoning.temporal_reproducibility_fingerprint import *
class T(unittest.TestCase):
 def test_deterministic(self): self.assertEqual(temporal_fingerprint({"b":2,"a":1}),temporal_fingerprint({"a":1,"b":2}))
 def test_change(self): self.assertNotEqual(temporal_fingerprint({"a":1}),temporal_fingerprint({"a":2}))
 def test_set(self): self.assertEqual(temporal_fingerprint({"x":{"b","a"}}),temporal_fingerprint({"x":{"a","b"}}))
 def test_bad(self):
  with self.assertRaises(TypeError): temporal_fingerprint({"x":object()})
