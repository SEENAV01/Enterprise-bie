import unittest
from bie.reasoning.grounded_counterfactual import CounterfactualIntervention,evaluate_counterfactual

class TestGroundedCounterfactual(unittest.TestCase):
    def test_no_causal_path_abstains(self):
        i=CounterfactualIntervention("x","1","0",evidence_ids=("e1",))
        r=evaluate_counterfactual(i,causal_path_supported=False,causal_confidence=.9,predicted_effect="y decreases")
        self.assertEqual(r.status,"ABSTAINED")

    def test_low_confidence_is_ambiguous(self):
        i=CounterfactualIntervention("x","1","0",evidence_ids=("e1",))
        r=evaluate_counterfactual(i,causal_path_supported=True,causal_confidence=.5,predicted_effect="y decreases")
        self.assertEqual(r.status,"AMBIGUOUS")
        self.assertTrue(r.requires_review)

    def test_supported_counterfactual_resolves(self):
        i=CounterfactualIntervention("x","1","0",evidence_ids=("e1",))
        r=evaluate_counterfactual(i,causal_path_supported=True,causal_confidence=.9,predicted_effect="y decreases")
        self.assertEqual(r.status,"RESOLVED")

    def test_noop_intervention_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_counterfactual(CounterfactualIntervention("x","1","1"),causal_path_supported=True,causal_confidence=.9,predicted_effect="z")
