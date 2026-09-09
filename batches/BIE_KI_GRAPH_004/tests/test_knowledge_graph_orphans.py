import unittest
from knowledge_intelligence.knowledge_graph_orphans import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(find({"nodes":{"a":{},"b":{}},"edges":[]}),("a","b"))
  self.assertEqual(find({"nodes":{"a":{},"b":{}},"edges":[{"source":"a","target":"b"}]}),())
  self.assertEqual(find({"nodes":{},"edges":[]}),())
  self.assertEqual(find({"nodes":{"a":{}},"edges":[{"source":"x","target":"y"}]}),("a",))
if __name__=='__main__':unittest.main()
