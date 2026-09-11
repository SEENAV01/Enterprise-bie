import unittest
from bie.reasoning.reasoning_provenance_envelope import make_reasoning_envelope

class TestReasoningProvenanceEnvelope(unittest.TestCase):
    def test_deterministic_evidence_order(self):
        a=make_reasoning_envelope(artifact_id="a",reasoning_family="temporal",status="RESOLVED",evidence_ids=["e2","e1"])
        b=make_reasoning_envelope(artifact_id="a",reasoning_family="temporal",status="RESOLVED",evidence_ids=["e1","e2"])
        self.assertEqual(a.fingerprint(),b.fingerprint())
    def test_nonresolved_requires_review(self):
        with self.assertRaises(ValueError):
            make_reasoning_envelope(artifact_id="a",reasoning_family="causal",status="AMBIGUOUS",evidence_ids=["e"],requires_review=False)
    def test_lineage_preserved(self):
        e=make_reasoning_envelope(artifact_id="x",reasoning_family="graph",status="RESOLVED",evidence_ids=["e"],parent_artifact_ids=["p"])
        self.assertEqual(e.parent_artifact_ids,("p",))
