import unittest
from bie.knowledge_intelligence.entity_resolution import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(resolve("m",[{"entity_id":"e","confidence":.9}])["entity_id"],"e")
  self.assertEqual(resolve("m",[{"entity_id":"a","confidence":.8},{"entity_id":"b","confidence":.8}])["status"],"REVIEW")
  with self.assertRaises(E):resolve("m",[])
  with self.assertRaises(E):resolve("m",[{"entity_id":"e","confidence":2}])
