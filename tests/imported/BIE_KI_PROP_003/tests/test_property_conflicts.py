import unittest
from bie.knowledge_intelligence.property_conflicts import *
class T(unittest.TestCase):
 def test_contract(self):
  a={"concept_id":"c","property":"x","scope":"s","value":1};b={**a,"value":2}
  self.assertEqual(len(detect([a,b])),1)
  self.assertEqual(detect([a,b])[0]["status"],"REVIEW")
  self.assertEqual(detect([a,a]),())
  self.assertEqual(detect([]),())
