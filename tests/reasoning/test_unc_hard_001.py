import unittest, json
from bie.reasoning.structured_uncertainty import UncertaintyComponent, assess_uncertainty

class TestStructuredUncertainty(unittest.TestCase):
    def test_conflict_forces_review(self):
        r=assess_uncertainty([UncertaintyComponent("u","CONFLICT","sources disagree",("e1","e2"),weight=.9)])
        self.assertTrue(r.requires_review)

    def test_conservative_ceiling(self):
        r=assess_uncertainty([
          UncertaintyComponent("a","SOURCE","weak source",weight=.6),
          UncertaintyComponent("b","MODEL","model uncertainty",weight=.8)])
        self.assertEqual(r.conservative_confidence_ceiling,.6)

    def test_bounds_validated(self):
        with self.assertRaises(ValueError):
            assess_uncertainty([UncertaintyComponent("u","MEASUREMENT","x",lower=2,upper=1)])

    def test_canonical_serialization_deterministic(self):
        a=assess_uncertainty([UncertaintyComponent("b","MODEL","b"),UncertaintyComponent("a","SOURCE","a")])
        b=assess_uncertainty([UncertaintyComponent("a","SOURCE","a"),UncertaintyComponent("b","MODEL","b")])
        self.assertEqual(a.canonical_json(),b.canonical_json())
