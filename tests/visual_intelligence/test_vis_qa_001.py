import unittest
from bie.visual_intelligence.semantic_alignment_qa import *
class T(unittest.TestCase):
 def spec(self): return SemanticSpec(("force","acceleration"),("causes",),("e",),("r",),("false",))
 def test_pass(self): self.assertTrue(evaluate_semantic_alignment(self.spec(),["force","acceleration"],["causes"],[],["e"]).passed)
 def test_missing(self): self.assertIn("missing_required_concepts",evaluate_semantic_alignment(self.spec(),["force"],["causes"],[],["e"]).blockers)
 def test_relation(self): self.assertIn("missing_required_relations",evaluate_semantic_alignment(self.spec(),["force","acceleration"],[],[],["e"]).blockers)
 def test_claim(self): self.assertIn("unsupported_claims",evaluate_semantic_alignment(self.spec(),["force","acceleration"],["causes"],["false"],["e"]).blockers)
 def test_source(self): self.assertIn("no_source_overlap",evaluate_semantic_alignment(self.spec(),["force","acceleration"],["causes"],[],["x"]).blockers)
 def test_extra(self): self.assertIn("extra_concepts_present",evaluate_semantic_alignment(self.spec(),["force","acceleration","mass"],["causes"],[],["e"]).warnings)
 def test_not_accepted(self): self.assertFalse(evaluate_semantic_alignment(self.spec(),["force","acceleration"],["causes"],[],["e"]).accepted)
