import unittest
from bie.knowledge_intelligence.salience_ranking import *
class T(unittest.TestCase):
 def test_contract(self):
  r=rank([{"concept_id":"b","salience":.5},{"concept_id":"a","salience":.9}]);self.assertEqual(r[0]["concept_id"],"a")
  self.assertEqual(len(r),2)
  self.assertEqual(rank([]),())
  with self.assertRaises(E):rank([{"concept_id":"x","salience":2}])
