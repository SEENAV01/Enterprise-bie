import unittest
from bie.knowledge_intelligence.concept_salience import *
class T(unittest.TestCase):
 def test_contract(self):
  self.assertEqual(score(1,1,1,1)["band"],"CORE")
  self.assertEqual(score(.6,.6,.6,.6)["band"],"SUPPORTING")
  self.assertEqual(score(.1,.1,.1,.1)["band"],"INCIDENTAL")
  with self.assertRaises(E):score(2,1,1,1)
