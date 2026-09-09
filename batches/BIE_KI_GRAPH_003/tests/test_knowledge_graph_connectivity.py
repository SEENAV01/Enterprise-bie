import unittest
from knowledge_intelligence.knowledge_graph_connectivity import *
class T(unittest.TestCase):
 def test_contract(self):
  g={"nodes":{"a":{},"b":{},"c":{}},"edges":[{"source":"a","target":"b"}]};r=components(g)
  self.assertEqual(len(r),2)
  self.assertTrue(any(x==frozenset({"a","b"}) for x in r))
  self.assertEqual(len(components({"nodes":{},"edges":[]})),0)
  self.assertEqual(len(components({"nodes":{"a":{}},"edges":[]})),1)
if __name__=='__main__':unittest.main()
