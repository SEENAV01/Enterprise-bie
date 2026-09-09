import unittest
from bie.knowledge_intelligence.equation_semantics import *
class T(unittest.TestCase):
 def test_contract(self):
  r=semantics("e",[{"symbol":"F","meaning":"force"}],["k"],["p"]);self.assertEqual(r["variables"][0]["meaning"],"force")
  self.assertEqual(r["condition_ids"],("k",))
  with self.assertRaises(E):semantics("",[{"symbol":"x","meaning":"x"}],[],["p"])
  with self.assertRaises(E):semantics("e",[{"symbol":"","meaning":"x"}],[],["p"])
