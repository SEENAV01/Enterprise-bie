import unittest
from bie.knowledge_intelligence.knowledge_graph_edge_confidence import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(assess([{"confidence":.9}])[0]["confidence_status"],"ACCEPT")
  self.assertEqual(assess([{"confidence":.7}])[0]["confidence_status"],"REVIEW")
  self.assertEqual(assess([{"confidence":.2}])[0]["confidence_status"],"REJECT")
  with self.assertRaises(E):assess([{"confidence":2}])
if __name__=='__main__':unittest.main()
