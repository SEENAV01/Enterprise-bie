from dataclasses import replace
import unittest
from bie.qa.release_v2 import (ContractError, DenyAllVerifier, EvidenceBundle, HmacEvidenceVerifier,
                              ReleaseEvaluator)
from helpers import CaseTest, NOW, make_case, sign, write_ref


class EvaluatorTests(CaseTest):
    def test_complete_test_evidence_is_contract_only_not_release(self):
        report = self.evaluate()
        self.assertEqual(report.release_status, "CONTRACT_ONLY")
        self.assertTrue(all(g.status == "PASS" for g in report.gate_results))
        self.assertFalse(report.release_authorized)
        self.assertFalse(report.product_accepted)
        self.assertFalse(report.ready_for_review)
        self.assertIn("NON_PRODUCTION_TRUST", report.global_diagnostics)

    def test_operator_authority_only_reaches_review_not_success(self):
        # Controlled synthetic unit test of the trust branch, NOT production proof.
        verifier = HmacEvidenceVerifier((replace(self.key, assurance="operator_managed"),))
        report = self.evaluate(verifier=verifier)
        self.assertEqual(report.release_status, "READY_FOR_REVIEW")
        self.assertTrue(report.ready_for_review)
        self.assertFalse(report.release_authorized)
        self.assertFalse(report.product_accepted)

    def test_no_trust_provider_blocks(self):
        result = ReleaseEvaluator(self.policy).evaluate(self.bundle, self.root, as_of=NOW)
        self.assertBlocked(result)
        self.assertIn("NO_AUTHORIZED_EVIDENCE_VERIFIER", self.codes(result))

    def test_empty_evidence_cannot_pass_vacuously(self):
        report = self.evaluate(replace(self.bundle, evidence=()))
        self.assertBlocked(report)
        self.assertEqual(len(report.blocking_gates), len(self.policy.gates))
        self.assertTrue(all(g.status == "PENDING" for g in report.gate_results))

    def test_missing_game_evidence_does_not_require_stopping_qa_development(self):
        # The QA evaluator runs normally while the GAME lane is incomplete.
        bundle = replace(self.bundle, evidence=tuple(e for e in self.bundle.evidence if not e.gate_id.startswith("game_")))
        report = self.evaluate(bundle)
        self.assertBlocked(report)
        self.assertIn("game_runtime", report.blocking_gates)
        self.assertEqual(next(g for g in report.gate_results if g.gate_id == "video_render").status, "PASS")

    def test_unexpected_gate_is_not_silently_ignored(self):
        ev = replace(self.bundle.evidence[0], evidence_id="extra", gate_id="invented_gate")
        report = self.evaluate(replace(self.bundle, evidence=self.bundle.evidence + (ev,)))
        self.assertBlocked(report)
        self.assertIn("UNKNOWN_EVIDENCE_GATE", report.global_diagnostics)

    def test_candidate_binding_mismatch(self):
        result = self.evaluate(self.replace_evidence(candidate_digest="0" * 64))
        self.assertBlocked(result)
        self.assertIn("CANDIDATE_BINDING_MISMATCH", self.codes(result))

    def test_run_binding_mismatch(self):
        result = self.evaluate(self.replace_evidence(run_id="wrong-run"))
        self.assertBlocked(result)
        self.assertIn("RUN_BINDING_MISMATCH", self.codes(result))

    def test_revision_binding_mismatch(self):
        result = self.evaluate(self.replace_evidence(revision="0" * 40))
        self.assertBlocked(result)
        self.assertIn("REVISION_BINDING_MISMATCH", self.codes(result))

    def test_policy_binding_mismatch(self):
        result = self.evaluate(self.replace_evidence(policy_digest="0" * 64))
        self.assertBlocked(result)
        self.assertIn("POLICY_BINDING_MISMATCH", self.codes(result))

    def test_report_file_tampering_blocks(self):
        ev = next(e for e in self.bundle.evidence if e.gate_id == "video_render")
        (self.root / ev.report.path).write_bytes(b"X" * ev.report.size)
        result = self.evaluate()
        self.assertBlocked(result)
        self.assertIn("ARTIFACT_HASH_MISMATCH", self.codes(result))

    def test_candidate_file_tampering_blocks(self):
        ref = self.bundle.candidate.artifacts[1]
        (self.root / ref.path).write_bytes(b"X" * ref.size)
        result = self.evaluate()
        self.assertBlocked(result)
        self.assertIn("CANDIDATE_ARTIFACT_INVALID", result.global_diagnostics)

    def test_missing_report_blocks(self):
        ev = self.bundle.evidence[0]
        (self.root / ev.report.path).unlink()
        self.assertBlocked(self.evaluate())

    def test_expired_evidence_blocks_at_exact_boundary(self):
        result = self.evaluate(self.replace_evidence(expires_at=NOW))
        self.assertBlocked(result)
        self.assertIn("EXPIRED_EVIDENCE", self.codes(result))

    def test_future_evidence_blocks(self):
        result = self.evaluate(self.replace_evidence(created_at=NOW + 1))
        self.assertBlocked(result)
        self.assertIn("FUTURE_EVIDENCE", self.codes(result))

    def test_expiry_lifetime_cannot_exceed_policy(self):
        result = self.evaluate(self.replace_evidence(expires_at=NOW + 700000))
        self.assertBlocked(result)
        self.assertIn("EVIDENCE_LIFETIME_EXCEEDED", self.codes(result))

    def test_boolean_clock_rejected(self):
        with self.assertRaises(ContractError):
            self.evaluate(as_of=True)

    def test_unknown_inspected_artifact_blocks(self):
        result = self.evaluate(self.replace_evidence(inspected_artifact_ids=("video-1", "unknown")))
        self.assertBlocked(result)
        self.assertIn("UNKNOWN_INSPECTED_ARTIFACT", self.codes(result))

    def test_wrong_output_coverage_blocks(self):
        result = self.evaluate(self.replace_evidence(inspected_artifact_ids=("source-1",)))
        self.assertBlocked(result)
        self.assertIn("INCOMPLETE_ARTIFACT_COVERAGE", self.codes(result))

    def test_multiple_subjects_require_complete_coverage(self):
        extra = write_ref(self.root, "video-2", "subjects/video2.fixture", b"SYNTHETIC second video", "video")
        candidate = replace(self.bundle.candidate, artifacts=self.bundle.candidate.artifacts + (extra,))
        evs = tuple(sign(replace(ev, candidate_digest=candidate.content_digest), self.key) for ev in self.bundle.evidence)
        result = self.evaluate(replace(self.bundle, candidate=candidate, evidence=evs))
        self.assertBlocked(result)
        self.assertIn("INCOMPLETE_ARTIFACT_COVERAGE", self.codes(result))

    def test_skipped_required_evidence_blocks(self):
        result = self.evaluate(self.replace_evidence(status="SKIPPED", diagnostics=("PROVIDER_UNAVAILABLE",)))
        self.assertBlocked(result)
        self.assertIn("EVIDENCE_SKIPPED", self.codes(result))

    def test_not_run_required_evidence_blocks(self):
        result = self.evaluate(self.replace_evidence(status="NOT_RUN", diagnostics=("SECTION15_PENDING",)))
        self.assertBlocked(result)
        self.assertIn("EVIDENCE_NOT_RUN", self.codes(result))

    def test_failed_evidence_is_not_outvoted_by_pass(self):
        failed = next(e for e in self.bundle.evidence if e.gate_id == "video_render")
        failed = sign(replace(failed, evidence_id="failure-record", status="FAIL", diagnostics=("BLANK_FRAME",)), self.key)
        result = self.evaluate(replace(self.bundle, evidence=self.bundle.evidence + (failed,)))
        self.assertBlocked(result)
        gate = next(g for g in result.gate_results if g.gate_id == "video_render")
        self.assertEqual(gate.status, "FAIL")

    def test_error_evidence_blocks(self):
        self.assertBlocked(self.evaluate(self.replace_evidence(status="ERROR", diagnostics=("WORKER_CRASH",))))

    def test_runtime_requires_execution_not_review(self):
        result = self.evaluate(self.replace_evidence(kind="review"))
        self.assertBlocked(result)
        self.assertIn("UNSUPPORTED_PROOF_KIND", self.codes(result))

    def test_fixture_declaration_and_historical_not_runtime_proof(self):
        for kind in ("fixture", "declaration", "historical"):
            with self.subTest(kind=kind):
                result = self.evaluate(self.replace_evidence(kind=kind))
                self.assertBlocked(result)
                self.assertIn("UNSUPPORTED_PROOF_KIND", self.codes(result))

    def test_bad_signature_blocks_even_when_files_match(self):
        result = self.evaluate(self.replace_evidence(resign=False, signature="0" * 64))
        self.assertBlocked(result)
        self.assertIn("BAD_SIGNATURE", self.codes(result))

    def test_verifier_exception_fails_closed(self):
        class Broken:
            def verify(self, ev):
                raise RuntimeError("do not expose this secret")
        result = self.evaluate(verifier=Broken())
        self.assertBlocked(result)
        self.assertIn("TRUST_VERIFIER_ERROR", self.codes(result))
        self.assertNotIn("do not expose", result.to_bytes().decode())

    def test_malformed_verifier_return_fails_closed(self):
        class Broken:
            def verify(self, ev):
                return True
        result = self.evaluate(verifier=Broken())
        self.assertBlocked(result)
        self.assertIn("TRUST_VERIFIER_ERROR", self.codes(result))

    def test_duplicate_evaluator_cannot_satisfy_stronger_floor(self):
        stronger = replace(self.policy, gates=tuple(replace(g, min_distinct_evaluators=2) if g.gate_id == "video_render" else g
                                                   for g in self.policy.gates))
        bundle, key, verifier, _ = make_case(self.root, stronger)
        original = next(e for e in bundle.evidence if e.gate_id == "video_render")
        duplicate = sign(replace(original, evidence_id="other-id"), key)
        bundle = replace(bundle, evidence=bundle.evidence + (duplicate,))
        result = self.evaluate(bundle, verifier=verifier, policy=stronger)
        self.assertBlocked(result)
        gate = next(g for g in result.gate_results if g.gate_id == "video_render")
        self.assertIn("INSUFFICIENT_DISTINCT_EVALUATORS", gate.diagnostics)
        self.assertIn("INSUFFICIENT_DISTINCT_REPORTS", gate.diagnostics)

    def test_evaluation_has_no_file_side_effects(self):
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.evaluate()
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_report_does_not_offer_success_or_certification(self):
        result = self.evaluate()
        self.assertNotEqual(result.release_status, "SUCCESS")
        self.assertFalse(result.release_authorized)
        self.assertIn("NOT_IMPLEMENTED", result.certification_boundary)


if __name__ == "__main__":
    unittest.main()
