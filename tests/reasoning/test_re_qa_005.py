import unittest
from dataclasses import replace
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.decision_reproducibility import decision_fingerprint,compare_decisions

def d():
    return ReasoningDecision("d","teaching_order","s","q","x","r",.8,[EvidenceRef("e","primary",.8)])

class TestDecisionReproducibility(unittest.TestCase):
    def test_same_decision_same_fingerprint(self):
        a=d(); b=d()
        self.assertEqual(decision_fingerprint(a),decision_fingerprint(b))
        self.assertTrue(compare_decisions(a,b).passed)

    def test_changed_semantics_are_reported(self):
        a=d(); b=replace(a,selected_option="y")
        r=compare_decisions(a,b)
        self.assertFalse(r.passed); self.assertIn("selected_option",r.changed_fields)

    def test_evidence_order_is_part_of_contract(self):
        a=ReasoningDecision("d","teaching_order","s","q","x","r",.7,
          [EvidenceRef("a","primary",.8),EvidenceRef("b","supporting",.7)],requires_review=True)
        b=ReasoningDecision("d","teaching_order","s","q","x","r",.7,
          [EvidenceRef("b","supporting",.7),EvidenceRef("a","primary",.8)],requires_review=True)
        self.assertFalse(compare_decisions(a,b).passed)
