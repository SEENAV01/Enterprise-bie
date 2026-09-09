import unittest
from bie.knowledge_intelligence.graph_diff import *
class T(unittest.TestCase):
 def test_contract(self):
  a={"nodes":{"a":{"x":1}},"edges":[]};b={"nodes":{"a":{"x":2},"b":{}},"edges":[{"source":"a","target":"b","type":"X"}]};r=diff(a,b)
  self.assertEqual(r["nodes_added"],("b",))
  self.assertEqual(r["nodes_changed"],("a",))
  self.assertEqual(len(r["edges_added"]),1)
  self.assertEqual(diff(a,a)["nodes_added"],())
if __name__=='__main__':unittest.main()
