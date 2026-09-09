import unittest
from crossmodal_conflict import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(detect([{"semantic_key":"k","value":1}])["passed"])
  self.assertFalse(detect([{"semantic_key":"k","value":1},{"semantic_key":"k","value":2}])["passed"])
  self.assertEqual(detect([{"semantic_key":"k","value":1},{"semantic_key":"k","value":2}])["status"],"REVIEW")
  with self.assertRaises(E):detect([])
