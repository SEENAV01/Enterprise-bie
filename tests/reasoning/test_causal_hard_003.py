import unittest
from bie.reasoning.temporal_causal_guard import assess_temporal_causal_claim

class TestTemporalCausalGuard(unittest.TestCase):
    def test_before_alone_is_not_causation(self):
        r=assess_temporal_causal_claim("BEFORE")
        self.assertFalse(r.causal_claim_allowed)
        self.assertEqual(r.reason_code,"BEFORE_DOES_NOT_IMPLY_CAUSES")

    def test_supported_before_plus_mechanism_allows(self):
        r=assess_temporal_causal_claim("BEFORE",causal_evidence_ids=("e1",),mechanism_supported=True)
        self.assertTrue(r.causal_claim_allowed)

    def test_unknown_temporal_relation_blocks(self):
        self.assertFalse(assess_temporal_causal_claim("UNKNOWN",causal_evidence_ids=("e1",),mechanism_supported=True).causal_claim_allowed)

    def test_contradiction_blocks(self):
        r=assess_temporal_causal_claim("BEFORE",causal_evidence_ids=("e1",),mechanism_supported=True,contradicting_evidence_ids=("e2",))
        self.assertTrue(r.requires_review)
