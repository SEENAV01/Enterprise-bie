import unittest
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.rationale_evidence_consistency import evaluate_rationale_evidence_consistency

def d(**kw):
    base=dict(decision_id="d1", decision_type="teaching_order", subject_id="s",
              question="q", selected_option="x", rationale_summary="Because source supports x.",
              confidence=.8, evidence_refs=[EvidenceRef("e1","primary",.8)])
    base.update(kw); return ReasoningDecision(**base)

class TestRationaleEvidenceConsistency(unittest.TestCase):
    def test_consistent_decision_passes(self):
        r=evaluate_rationale_evidence_consistency(d(), rationale_evidence_ids=["e1"])
        self.assertTrue(r.passed); self.assertFalse(r.findings)

    def test_unknown_citation_fails(self):
        r=evaluate_rationale_evidence_consistency(d(), rationale_evidence_ids=["e2"])
        self.assertFalse(r.passed)
        self.assertIn("UNKNOWN_RATIONALE_EVIDENCE",[x.code for x in r.findings])

    def test_contradiction_requires_review(self):
        dec=d(confidence=.6, requires_review=True, evidence_refs=[
            EvidenceRef("e1","primary",.8),EvidenceRef("e2","contradicting",.6)])
        r=evaluate_rationale_evidence_consistency(dec)
        self.assertTrue(r.requires_review)
        self.assertEqual(r.contradicting_evidence_ids,("e2",))
