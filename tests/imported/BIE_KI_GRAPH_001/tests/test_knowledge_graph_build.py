import unittest
from bie.knowledge_intelligence.knowledge_graph_build import *
class T(unittest.TestCase):
 def test_contract(self):
  c=[{"concept_id":"a"},{"concept_id":"b"}];r=[{"source":"a","target":"b","type":"IS_A"}]
  self.assertEqual(len(build(c,r)["nodes"]),2)
  self.assertEqual(len(build(c,r)["edges"]),1)
  with self.assertRaises(E):build([{"concept_id":"a"},{"concept_id":"a"}],[])
  with self.assertRaises(E):build(c,[{"source":"a","target":"x"}])
if __name__=='__main__':unittest.main()
