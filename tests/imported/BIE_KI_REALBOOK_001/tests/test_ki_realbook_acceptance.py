import unittest
from bie.knowledge_intelligence.ki_realbook_acceptance import *
class T(unittest.TestCase):
 def test_contract(self):
  cases=[{"case_id":d,"domain":d,"concept_coverage":.95,"unsupported_claims":0,"graph_valid":True} for d in DOMAINS];r=evaluate(cases)
  self.assertTrue(r["five_domain_ready"])
  self.assertTrue(r["accepted"])
  self.assertFalse(evaluate(cases[:-1])["accepted"])
  with self.assertRaises(E):evaluate([{"domain":"BAD"}])
