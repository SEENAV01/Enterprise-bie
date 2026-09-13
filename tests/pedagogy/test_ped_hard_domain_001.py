import unittest
from bie.pedagogy.domain_pedagogy_policy import *
class T(unittest.TestCase):
 def test_source_policy(self):
  r=default_policy_registry().match(content_types=["SOURCE_CRITICISM"],objective_level="EVALUATE",available_evidence_kinds=["primary_source"])
  self.assertEqual(r[0].policy_id,"source_criticism")
 def test_programming_policy(self):
  r=default_policy_registry().match(content_types=["PROGRAMMING","PROCEDURAL"],objective_level="CREATE",available_evidence_kinds=["code_example"])
  self.assertEqual(r[0].policy_id,"programming")
 def test_required_evidence(self):
  self.assertEqual(default_policy_registry().match(content_types=["SOURCE_CRITICISM"],objective_level="EVALUATE",available_evidence_kinds=[]),())
