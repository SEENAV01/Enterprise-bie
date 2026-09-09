import unittest
from bie.knowledge_intelligence.concept_dedup import *
class T(unittest.TestCase):
 def test_contract(self):
  x=[{"concept_id":"a","label":"Electric Field","evidence":("p1",)},{"concept_id":"b","label":"electric-field","evidence":("p2",)}]
  r=dedupe(x);self.assertEqual(len(r["concepts"]),1)
  self.assertEqual(r["redirects"]["b"],"a")
  self.assertEqual(r["concepts"][0]["evidence"],("p1","p2"))
  with self.assertRaises(E):dedupe([{"concept_id":"","label":"x"}])
if __name__=='__main__':unittest.main()
