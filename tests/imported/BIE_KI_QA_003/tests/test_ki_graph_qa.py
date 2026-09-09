import unittest
from knowledge_intelligence.ki_graph_qa import *
class T(unittest.TestCase):
 def test_contract(self):
  g={"nodes":{"a":{},"b":{}},"edges":[{"source":"a","target":"b","anchors":["p"]}]};self.assertTrue(evaluate(g)["passed"])
  self.assertEqual(evaluate(g)["orphans"],())
  self.assertFalse(evaluate({"nodes":{"a":{}},"edges":[{"source":"a","target":"x","anchors":["p"]}]})["passed"])
  self.assertFalse(evaluate({"nodes":{"a":{},"b":{}},"edges":[{"source":"a","target":"b","anchors":[]}]})["passed"])
if __name__=='__main__':unittest.main()
