import unittest
from bie.pedagogy.derivation_mode import plan_derivation

class TestDerivationMode(unittest.TestCase):
    def test_grounded_multistep(self):
        r=plan_derivation([("a=b","given",("e1",)),("b=c","substitution",("e2",))])
        self.assertEqual(len(r.steps),2)

    def test_assumptions_require_review(self):
        r=plan_derivation([("a=b","given",("e1",)),("b=c","rule",("e2",))],assumptions=("ideal system",))
        self.assertTrue(r.requires_review)
