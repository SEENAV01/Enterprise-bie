import unittest
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef
from bie.reasoning.contradiction_resolution_qa import ContradictionResolution,evaluate_contradiction_resolution

def d(review=True):
    return ReasoningDecision("d","contradiction_resolution","s","q","x","r",.6,
      [EvidenceRef("e1","primary",.8),EvidenceRef("e2","contradicting",.6)],requires_review=review)

class TestContradictionQA(unittest.TestCase):
    def test_resolved_contradiction_passes(self):
        r=evaluate_contradiction_resolution(d(),[
          ContradictionResolution("c",("e1","e2"),"RESOLVED","primary source controls","d")])
        self.assertTrue(r.passed)

    def test_preserved_ambiguity_remains_reviewable(self):
        r=evaluate_contradiction_resolution(d(),[
          ContradictionResolution("c",("e1","e2"),"PRESERVED_AMBIGUITY","both plausible")])
        self.assertFalse(r.passed); self.assertTrue(r.requires_review)

    def test_uncovered_contradicting_evidence_is_detected(self):
        r=evaluate_contradiction_resolution(d(),[])
        self.assertIn("uncovered:e2",r.unresolved_contradiction_ids)
