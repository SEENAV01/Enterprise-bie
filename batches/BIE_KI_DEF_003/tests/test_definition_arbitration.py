import unittest
from knowledge_intelligence.definition_arbitration import *
class T(unittest.TestCase):
 def test_contract(self):
  d=[{"anchor_id":"a","confidence":.9,"source_priority":1},{"anchor_id":"b","confidence":.7,"source_priority":2}]
  self.assertEqual(arbitrate(d)["selected"]["anchor_id"],"a")
  self.assertEqual(arbitrate([d[0],dict(d[0],anchor_id="x")])["status"],"REVIEW")
  with self.assertRaises(E):arbitrate([])
  with self.assertRaises(E):arbitrate([{"anchor_id":"","confidence":1}])
if __name__=='__main__':unittest.main()
