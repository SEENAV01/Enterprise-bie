import unittest
from bie.knowledge_intelligence.exceptions import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(make("r","except superconductors",["p"])["severity"],"NORMAL")
  self.assertEqual(make("r","x",["p"],"CRITICAL")["severity"],"CRITICAL")
  with self.assertRaises(E):make("r","",["p"])
  with self.assertRaises(E):make("r","x",["p"],"BAD")
