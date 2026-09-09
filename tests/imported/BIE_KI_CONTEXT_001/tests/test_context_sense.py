import unittest
from bie.knowledge_intelligence.context_sense import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(sense("field","physical field","ch1",["p"],.9)["scope"],"ch1")
  self.assertEqual(sense("cell","biology","s",["p","p"],1)["anchors"],("p",))
  with self.assertRaises(E):sense("","x","s",["p"],1)
  with self.assertRaises(E):sense("x","y","s",[],1)
