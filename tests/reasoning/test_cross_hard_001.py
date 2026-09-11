import unittest
from bie.reasoning.cross_family_arbitration import FamilyConstraint,arbitrate_constraints

class TestCrossFamilyArbitration(unittest.TestCase):
    def test_disagreement_preserved_as_conflict(self):
        r=arbitrate_constraints([
          FamilyConstraint("temporal","p","SUPPORTS","RESOLVED",("e1",),.9),
          FamilyConstraint("causal","p","OPPOSES","RESOLVED",("e2",),.8)])
        self.assertEqual(r.status,"CONFLICT"); self.assertTrue(r.requires_review)
    def test_agreement_resolves_conservatively(self):
        r=arbitrate_constraints([
          FamilyConstraint("spatial","p","SUPPORTS","RESOLVED",("e1",),.9),
          FamilyConstraint("evidence","p","SUPPORTS","RESOLVED",("e2",),.7)])
        self.assertEqual(r.status,"RESOLVED"); self.assertEqual(r.confidence,.7)
    def test_multiple_propositions_rejected(self):
        with self.assertRaises(ValueError):
            arbitrate_constraints([
              FamilyConstraint("a","p","SUPPORTS","RESOLVED",("e",),.9),
              FamilyConstraint("b","q","SUPPORTS","RESOLVED",("e",),.9)])
