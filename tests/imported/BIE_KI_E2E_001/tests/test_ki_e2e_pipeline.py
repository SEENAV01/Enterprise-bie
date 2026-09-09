import unittest
from ki_e2e_pipeline import *
class T(unittest.TestCase):
 def test_contract(self):
  d={"concepts":[{"concept_id":"a"},{"concept_id":"b"}],"relations":[{"source":"a","target":"b"}],"claims":[{"claim_id":"c","anchor_ids":["p"]}],"definitions":[],"examples":[],"terms":[],"entities":[],"conditions":[]};r=run(d)
  self.assertTrue(r["passed"])
  self.assertEqual(r["concept_count"],2)
  self.assertEqual(r["stages"],REQUIRED)
  with self.assertRaises(E):run({})
