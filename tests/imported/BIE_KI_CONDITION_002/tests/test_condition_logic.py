import unittest
from knowledge_intelligence.condition_logic import *
class T(unittest.TestCase):
 def test_contract(self):
  g=group("ALL",["a","b"]);self.assertTrue(satisfied(g,{"a":1,"b":1}))
  self.assertFalse(satisfied(g,{"a":1,"b":0}))
  self.assertTrue(satisfied(group("NOT",["a"]),{"a":0}))
  with self.assertRaises(E):group("NOT",["a","b"])
