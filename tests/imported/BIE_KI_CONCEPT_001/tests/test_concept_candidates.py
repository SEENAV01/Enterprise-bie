import unittest
from bie.knowledge_intelligence.concept_candidates import *
class T(unittest.TestCase):
 def test_contract(self):
  b=[{"anchor_id":"a","concept_candidates":["Force"]},{"anchor_id":"b","concept_candidates":["force","Mass"]}]
  r=extract(b);self.assertEqual(len(r),2)
  self.assertEqual(r[0]["evidence"],("a","b"))
  self.assertEqual(extract([]),())
  self.assertEqual(extract([{"anchor_id":"a","concept_candidates":[" "]}]),())
if __name__=='__main__':unittest.main()
