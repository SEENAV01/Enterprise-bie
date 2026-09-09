import unittest
from app.bie.math_intelligence.derivation_validation import *
class T(unittest.TestCase):
 def test_ok(self): self.assertTrue(validate_step(StepEvidence(1,1,1)).valid)
 def test_equiv(self): self.assertIn("not_equivalent",validate_step(StepEvidence(0,1,1)).failures)
 def test_rule(self): self.assertIn("unknown_rule",validate_step(StepEvidence(1,0,1)).failures)
 def test_just(self): self.assertIn("missing_justification",validate_step(StepEvidence(1,1,0)).failures)
if __name__=="__main__":unittest.main()
