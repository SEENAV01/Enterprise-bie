import unittest
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.confidence_qa import evaluate_confidence

def d(conf=.8,strength=.8,review=False,unc=None,role="primary"):
    return ReasoningDecision("d","example_selection","s","q","x","r",conf,
        [EvidenceRef("e",role,strength)],uncertainty=unc or [],requires_review=review)

class TestConfidenceQA(unittest.TestCase):
    def test_calibrated_bound_passes(self):
        self.assertTrue(evaluate_confidence(d()).passed)

    def test_overconfidence_fails(self):
        r=evaluate_confidence(d(conf=.9,strength=.7,review=True))
        self.assertIn("OVERCONFIDENT_VS_EVIDENCE",[f.code for f in r.findings])

    def test_uncertainty_requires_review(self):
        # Decision contract itself allows this combination at >=.75; QA catches it.
        r=evaluate_confidence(d(conf=.8,strength=.8,review=False,unc=["ambiguous wording"]))
        self.assertFalse(r.passed)
        self.assertIn("UNCERTAINTY_WITHOUT_REVIEW",[f.code for f in r.findings])
