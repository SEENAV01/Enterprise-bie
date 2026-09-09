import unittest
from knowledge_intelligence.knowledge_graph_validate import *
class T(unittest.TestCase):
 def test_contract(self):
  g={"nodes":{"a":{},"b":{}},"edges":[{"source":"a","target":"b","type":"X"}]};self.assertTrue(validate(g)["passed"])
  self.assertFalse(validate({"nodes":{"a":{}},"edges":[{"source":"a","target":"x","type":"X"}]})["passed"])
  self.assertFalse(validate({"nodes":{"a":{}},"edges":[{"source":"a","target":"a","type":"X"}]})["passed"])
  self.assertFalse(validate({"nodes":{"a":{},"b":{}},"edges":[{"source":"a","target":"b"}]})["passed"])
if __name__=='__main__':unittest.main()
