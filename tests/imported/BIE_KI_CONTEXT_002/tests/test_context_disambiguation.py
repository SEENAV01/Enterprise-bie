import unittest
from bie.knowledge_intelligence.context_disambiguation import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(choose("cell",[{"sense_id":"bio","confidence":.9}])["sense_id"],"bio")
  self.assertEqual(choose("x",[{"sense_id":"a","confidence":.8},{"sense_id":"b","confidence":.8}])["status"],"REVIEW")
  with self.assertRaises(E):choose("",[])
  with self.assertRaises(E):choose("x",[{"sense_id":"a","confidence":2}])
