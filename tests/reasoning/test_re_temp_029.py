import unittest
from bie.reasoning.temporal_consistency_audit import *
class T(unittest.TestCase):
 def test_ok(self): self.assertTrue(audit_before_relations([("a","b"),("b","c")]).consistent)
 def test_cycle(self): self.assertIn("directed_cycle",audit_before_relations([("a","b"),("b","a")]).issues)
 def test_self(self): self.assertIn("self_loop:a",audit_before_relations([("a","a")]).issues)
 def test_empty(self): self.assertTrue(audit_before_relations([]).consistent)
