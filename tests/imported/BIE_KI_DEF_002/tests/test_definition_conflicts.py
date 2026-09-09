import unittest
from knowledge_intelligence.definition_conflicts import *
class T(unittest.TestCase):
 def test_contract(self):
  d=[{"concept_id":"c","anchor_id":"a","scope":"s","polarity":1},{"concept_id":"c","anchor_id":"b","scope":"x","polarity":1}]
  self.assertEqual(len(detect(d)),1)
  self.assertEqual(detect(d)[0]["status"],"REVIEW")
  self.assertEqual(detect([d[0]]),())
  self.assertEqual(detect([{**d[0],"concept_id":"x"},d[1]]),())
if __name__=='__main__':unittest.main()
