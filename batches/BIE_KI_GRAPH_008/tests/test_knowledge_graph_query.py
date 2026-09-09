import unittest
from knowledge_intelligence.knowledge_graph_query import *
class T(unittest.TestCase):
 def test_contract(self):
  g={"nodes":{"a":{"label":"Electric Field"},"b":{"label":"Force"}},"edges":[{"source":"a","target":"b","type":"X","confidence":.9}]}
  self.assertEqual(query(g,label="field")["node_ids"],("a",))
  self.assertEqual(len(query(g,relation_type="X")["edges"]),1)
  self.assertEqual(len(query(g,min_confidence=.95)["edges"]),0)
  self.assertEqual(query(g,label="none")["node_ids"],())
if __name__=='__main__':unittest.main()
