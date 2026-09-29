from dataclasses import FrozenInstanceError, replace
import unittest
from bie.qa.release_v2 import ArtifactRef, ContractError, EvidenceBundle, GateEvidence, ReleaseCandidate
from bie.qa.release_v2.contracts import MAX_ARTIFACTS, MAX_EVIDENCE, MAX_FILE_BYTES, VERSION, canonical_bytes
from helpers import CaseTest


class ContractTests(CaseTest):
    def test_candidate_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.bundle.candidate.run_id = "different"

    def test_nested_ref_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.bundle.candidate.artifacts[0].size = 1

    def test_frozen_collections_reject_mutable_list(self):
        with self.assertRaises(ContractError):
            replace(self.bundle.candidate, artifacts=list(self.bundle.candidate.artifacts))
        with self.assertRaises(ContractError):
            replace(self.bundle, evidence=list(self.bundle.evidence))

    def test_no_empty_or_partial_product_scope(self):
        for removed in ("source", "video", "game"):
            with self.subTest(removed=removed), self.assertRaises(ContractError):
                replace(self.bundle.candidate, artifacts=tuple(a for a in self.bundle.candidate.artifacts if a.role != removed))

    def test_multiple_artifacts_do_not_mask_missing_role(self):
        refs = tuple(replace(a, role="source") for a in self.bundle.candidate.artifacts)
        with self.assertRaisesRegex(ContractError, "INCOMPLETE_PRODUCT_SCOPE"):
            replace(self.bundle.candidate, artifacts=refs)

    def test_duplicate_artifact_identity_rejected(self):
        refs = self.bundle.candidate.artifacts + (self.bundle.candidate.artifacts[0],)
        with self.assertRaisesRegex(ContractError, "DUPLICATE_ARTIFACT_ID"):
            replace(self.bundle.candidate, artifacts=refs)

    def test_duplicate_artifact_path_rejected(self):
        first = self.bundle.candidate.artifacts[0]
        refs = self.bundle.candidate.artifacts + (replace(first, artifact_id="other"),)
        with self.assertRaisesRegex(ContractError, "DUPLICATE_ARTIFACT_PATH"):
            replace(self.bundle.candidate, artifacts=refs)

    def test_boolean_is_not_a_size_or_timestamp(self):
        with self.assertRaises(ContractError):
            replace(self.bundle.candidate.artifacts[0], size=True)
        with self.assertRaises(ContractError):
            replace(self.bundle.evidence[0], created_at=False)

    def test_zero_and_oversized_artifacts_rejected(self):
        for size in (0, -1, MAX_FILE_BYTES + 1):
            with self.subTest(size=size), self.assertRaises(ContractError):
                replace(self.bundle.candidate.artifacts[0], size=size)

    def test_unsupported_schema_versions_rejected(self):
        for value in ("1.0.0", "2.1.0", "3.0.0", 2, True, None):
            with self.subTest(value=value), self.assertRaises(ContractError):
                replace(self.bundle, schema_version=value)

    def test_invalid_revision_rejected(self):
        for value in ("main", "a" * 39, "G" * 40, "A" * 40, 123):
            with self.subTest(value=value), self.assertRaises(ContractError):
                replace(self.bundle.candidate, revision=value)

    def test_invalid_digest_rejected(self):
        for value in ("f" * 63, "A" * 64, "z" * 64, "", None):
            with self.subTest(value=value), self.assertRaises(ContractError):
                replace(self.bundle.candidate.artifacts[0], sha256=value)

    def test_expiry_must_exceed_creation(self):
        ev = self.bundle.evidence[0]
        with self.assertRaises(ContractError):
            replace(ev, expires_at=ev.created_at)

    def test_failure_requires_machine_readable_diagnostic(self):
        for status in ("FAIL", "ERROR", "SKIPPED", "NOT_RUN"):
            with self.subTest(status=status), self.assertRaises(ContractError):
                replace(self.bundle.evidence[0], status=status)

    def test_unknown_status_or_kind_rejected(self):
        for kwargs in ({"status": "SUCCESS"}, {"status": True}, {"kind": "human_said_ok"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ContractError):
                replace(self.bundle.evidence[0], **kwargs)

    def test_report_must_have_report_role(self):
        ev = self.bundle.evidence[0]
        with self.assertRaisesRegex(ContractError, "INVALID_REPORT"):
            replace(ev, report=replace(ev.report, role="video"))

    def test_inspected_artifacts_must_be_nonempty_unique(self):
        for values in ((), ("video-1", "video-1"), ["video-1"]):
            with self.subTest(values=values), self.assertRaises(ContractError):
                replace(self.bundle.evidence[0], inspected_artifact_ids=values)

    def test_duplicate_evidence_id_rejected(self):
        with self.assertRaisesRegex(ContractError, "DUPLICATE_EVIDENCE_ID"):
            replace(self.bundle, evidence=self.bundle.evidence + (self.bundle.evidence[0],))

    def test_ambiguous_report_id_rejected(self):
        a, b = self.bundle.evidence[:2]
        b = replace(b, report=replace(b.report, artifact_id=a.report.artifact_id))
        with self.assertRaisesRegex(ContractError, "AMBIGUOUS_ARTIFACT_BINDING"):
            replace(self.bundle, evidence=(a, b))

    def test_ambiguous_report_path_rejected(self):
        a, b = self.bundle.evidence[:2]
        b = replace(b, report=replace(b.report, path=a.report.path))
        with self.assertRaisesRegex(ContractError, "AMBIGUOUS_ARTIFACT_BINDING"):
            replace(self.bundle, evidence=(a, b))

    def test_evidence_collection_limit(self):
        with self.assertRaisesRegex(ContractError, "INVALID_EVIDENCE_COLLECTION"):
            replace(self.bundle, evidence=(self.bundle.evidence[0],) * (MAX_EVIDENCE + 1))

    def test_artifact_collection_limit(self):
        with self.assertRaisesRegex(ContractError, "INVALID_ARTIFACT_COLLECTION"):
            replace(self.bundle.candidate, artifacts=(self.bundle.candidate.artifacts[0],) * (MAX_ARTIFACTS + 1))

    def test_non_string_identifiers_rejected(self):
        for value in (None, True, [], 1, " bad", "\u202erun"):
            with self.subTest(value=value), self.assertRaises(ContractError):
                replace(self.bundle.candidate, run_id=value)

    def test_digest_changes_with_candidate_content(self):
        changed = replace(self.bundle.candidate, run_id="another-run")
        self.assertNotEqual(changed.content_digest, self.bundle.candidate.content_digest)

    def test_canonical_encoding_rejects_float_nan_and_objects(self):
        for value in (0.5, float("nan"), float("inf"), object(), {1: "bad"}):
            with self.subTest(kind=type(value)), self.assertRaises(ContractError):
                canonical_bytes(value)

    def test_rejects_surrogate_unicode(self):
        with self.assertRaises(ContractError):
            canonical_bytes({"text": "\ud800"})


if __name__ == "__main__":
    unittest.main()
