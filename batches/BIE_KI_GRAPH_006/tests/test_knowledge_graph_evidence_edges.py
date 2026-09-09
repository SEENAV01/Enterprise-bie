import unittest
from knowledge_intelligence.knowledge_graph_evidence_edges import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertTrue(bind([{"anchors":["p1"]}])[0]["grounded"])
  self.assertEqual(bind([{"anchors":["p1","p1"]}])[0]["anchors"],("p1",))
  self.assertEqual(bind([]),())
  with self.assertRaises(E):bind([{"anchors":[]}])
if __name__=='__main__':unittest.main()
