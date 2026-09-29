"""Synthetic contract fixtures only. They are not textbook/media/game evidence."""
from dataclasses import replace
import hashlib
import hmac
from pathlib import Path
import tempfile
import unittest

from bie.qa.release_v2 import (ArtifactRef, EvidenceBundle, GateEvidence, ReleaseCandidate,
                              TrustedKey, HmacEvidenceVerifier, ReleaseEvaluator, enterprise_policy)
from bie.qa.release_v2.contracts import VERSION, canonical_bytes

NOW = 1790413200
REVISION = "375d99af0edd0086206817dae932156ddf61c569"
TEST_SECRET = b"BIE-SECTION16-TEST-ONLY-NOT-A-PRODUCTION-SECRET-001"


def write_ref(root: Path, artifact_id: str, path: str, content: bytes, role: str) -> ArtifactRef:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return ArtifactRef(artifact_id, path, hashlib.sha256(content).hexdigest(), len(content), role)


def sign(evidence: GateEvidence, key: TrustedKey) -> GateEvidence:
    return replace(evidence, signature=hmac.new(key.secret, evidence.signing_bytes(), hashlib.sha256).hexdigest())


def make_case(root: Path, policy=None, assurance="test_only"):
    policy = enterprise_policy() if policy is None else policy
    refs = (
        write_ref(root, "source-1", "subjects/source.txt", b"SYNTHETIC source fixture; not a real textbook.", "source"),
        write_ref(root, "video-1", "subjects/video.fixture", b"SYNTHETIC video bytes; not an encoded video.", "video"),
        write_ref(root, "game-1", "subjects/game.fixture", b"SYNTHETIC game bytes; not a playable game.", "game"),
    )
    candidate = ReleaseCandidate(VERSION, "candidate-1", "run-1", REVISION, refs)
    key = TrustedKey("test-key-1", TEST_SECRET, "contract-test-runner", "1.0.0",
                     tuple(g.gate_id for g in policy.gates), ("execution", "review"), assurance)
    evidence = []
    for gate in policy.gates:
        body = canonical_bytes({"synthetic_contract_fixture": True, "gate_id": gate.gate_id,
                                "claims_real_runtime": False, "candidate_digest": candidate.content_digest})
        report = write_ref(root, f"report-{gate.gate_id}", f"reports/{gate.gate_id}.json", body, "report")
        record = GateEvidence(VERSION, f"evidence-{gate.gate_id}", gate.gate_id,
                              candidate.content_digest, policy.content_digest, candidate.run_id,
                              candidate.revision, "PASS", key.evaluator_id, key.evaluator_version,
                              "execution", tuple(a.artifact_id for a in refs if a.role in gate.required_roles),
                              report, NOW - 30, NOW + 3600, (), key.key_id)
        evidence.append(sign(record, key))
    return EvidenceBundle(VERSION, candidate, tuple(evidence)), key, HmacEvidenceVerifier((key,)), policy


class CaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle, self.key, self.verifier, self.policy = make_case(self.root)

    def evaluate(self, bundle=None, verifier=None, policy=None, as_of=NOW):
        return ReleaseEvaluator(policy or self.policy, verifier or self.verifier).evaluate(
            self.bundle if bundle is None else bundle, self.root, as_of=as_of)

    def replace_evidence(self, gate_id="video_render", resign=True, **changes):
        records = []
        for record in self.bundle.evidence:
            if record.gate_id == gate_id:
                record = replace(record, **changes)
                if resign:
                    record = sign(record, self.key)
            records.append(record)
        return replace(self.bundle, evidence=tuple(records))

    def assertBlocked(self, report):
        self.assertEqual(report.release_status, "BLOCKED")
        self.assertFalse(report.release_authorized)
        self.assertFalse(report.product_accepted)
        self.assertFalse(report.ready_for_review)

    def codes(self, report):
        return {code for gate in report.gate_results for ev in gate.evidence for code in ev.diagnostics} | set(report.global_diagnostics)
