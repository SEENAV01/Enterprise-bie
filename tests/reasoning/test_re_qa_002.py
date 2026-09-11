import unittest
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.unsupported_reasoning_detection import ReasoningClaim, detect_unsupported_reasoning

def dec():
    return ReasoningDecision("d","causal_explanation","s","q","x","r",.8,[EvidenceRef("e1","primary",.8)])

class TestUnsupportedReasoning(unittest.TestCase):
    def test_grounded_chain_passes(self):
        claims=[ReasoningClaim("c1","source fact",("e1",)),ReasoningClaim("c2","derived",(),("c1",))]
        self.assertTrue(detect_unsupported_reasoning(dec(),claims).passed)

    def test_bare_claim_is_unsupported(self):
        r=detect_unsupported_reasoning(dec(),[ReasoningClaim("c1","bare")])
        self.assertEqual(r.unsupported_claim_ids,("c1",)); self.assertTrue(r.requires_review)

    def test_unknown_evidence_is_detected(self):
        r=detect_unsupported_reasoning(dec(),[ReasoningClaim("c1","x",("missing",))])
        self.assertEqual(r.unresolved_evidence_ids,("missing",))

    def test_cycle_is_detected(self):
        r=detect_unsupported_reasoning(dec(),[
            ReasoningClaim("a","a",(),("b",)),ReasoningClaim("b","b",(),("a",))])
        self.assertEqual(set(r.cyclic_claim_ids),{"a","b"})
