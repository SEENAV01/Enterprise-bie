import unittest
from bie.knowledge_intelligence.knowledge_graph_traversal import *
class T(unittest.TestCase):
 def test_contract(self):
  g={"nodes":{"a":{},"b":{},"c":{}},"edges":[{"source":"a","target":"b","type":"X"},{"source":"b","target":"c","type":"X"}]}
  self.assertEqual(traverse(g,"a",2),("a","b","c"))
  self.assertEqual(traverse(g,"a",1),("a","b"))
  self.assertEqual(traverse(g,"a",2,["Y"]),("a",))
  with self.assertRaises(E):traverse(g,"x",1)
if __name__=='__main__':unittest.main()
