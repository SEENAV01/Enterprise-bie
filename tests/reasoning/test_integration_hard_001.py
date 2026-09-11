import unittest
from bie.reasoning.reasoning_integration_gate import ReasoningStageEvidence,reasoning_integration_gate

class TestReasoningIntegrationGate(unittest.TestCase):
    def complete(self):
        return [
          ReasoningStageEvidence("evidence","e1"),
          ReasoningStageEvidence("decision","d1",("e1",),("e1",)),
          ReasoningStageEvidence("graph","g1",("e1",),("d1",)),
          ReasoningStageEvidence("uncertainty","u1",("e1",),("d1",)),
          ReasoningStageEvidence("qa","q1",("e1",),("d1","g1","u1"))
        ]

    def test_complete_lineage_passes(self):
        r=reasoning_integration_gate(self.complete())
        self.assertTrue(r.passed)

    def test_missing_stage_blocks(self):
        r=reasoning_integration_gate(self.complete()[:-1])
        self.assertIn("qa",r.missing_required_stages)

    def test_dangling_parent_blocks(self):
        x=self.complete()
        x[-1]=ReasoningStageEvidence("qa","q1",("e1",),("missing",))
        r=reasoning_integration_gate(x)
        self.assertIn("missing",r.dangling_parent_ids)

    def test_review_blocks_release(self):
        x=self.complete()
        x[1]=ReasoningStageEvidence("decision","d1",("e1",),("e1",),True)
        self.assertFalse(reasoning_integration_gate(x).passed)

    def test_fingerprint_deterministic(self):
        a=reasoning_integration_gate(self.complete()).fingerprint
        b=reasoning_integration_gate(reversed(self.complete())).fingerprint
        self.assertEqual(a,b)
