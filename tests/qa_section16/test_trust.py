from dataclasses import replace
import unittest
from bie.qa.release_v2 import ContractError, DenyAllVerifier, HmacEvidenceVerifier
from bie.qa.release_v2.trust import TrustResult
from helpers import CaseTest, sign


class TrustTests(CaseTest):
    def test_authorized_signature_verified(self):
        result = self.verifier.verify(self.bundle.evidence[0])
        self.assertTrue(result.accepted)
        self.assertEqual(result.assurance, "test_only")

    def test_deny_all_never_authenticates(self):
        self.assertFalse(DenyAllVerifier().verify(self.bundle.evidence[0]).accepted)

    def test_default_key_is_test_only(self):
        self.assertEqual(self.key.assurance, "test_only")

    def test_wrong_signature_rejected(self):
        record = replace(self.bundle.evidence[0], signature="0" * 64)
        self.assertEqual(self.verifier.verify(record).diagnostic, "BAD_SIGNATURE")

    def test_modified_payload_rejected_even_when_signature_format_valid(self):
        record = replace(self.bundle.evidence[0], run_id="different")
        self.assertEqual(self.verifier.verify(record).diagnostic, "BAD_SIGNATURE")

    def test_report_descriptor_is_signed(self):
        ev = self.bundle.evidence[0]
        record = replace(ev, report=replace(ev.report, sha256="0" * 64))
        self.assertEqual(self.verifier.verify(record).diagnostic, "BAD_SIGNATURE")

    def test_unknown_key_rejected(self):
        record = replace(self.bundle.evidence[0], signer_key_id="unknown-key")
        self.assertEqual(self.verifier.verify(record).diagnostic, "UNTRUSTED_SIGNER")

    def test_revoked_key_rejected(self):
        verifier = HmacEvidenceVerifier((replace(self.key, enabled=False),))
        self.assertEqual(verifier.verify(self.bundle.evidence[0]).diagnostic, "REVOKED_SIGNER")

    def test_wrong_evaluator_rejected_even_when_signed(self):
        record = sign(replace(self.bundle.evidence[0], evaluator_id="unauthorized"), self.key)
        self.assertEqual(self.verifier.verify(record).diagnostic, "UNAUTHORIZED_EVALUATOR")

    def test_wrong_evaluator_version_rejected_even_when_signed(self):
        record = sign(replace(self.bundle.evidence[0], evaluator_version="2.0.0"), self.key)
        self.assertEqual(self.verifier.verify(record).diagnostic, "UNAUTHORIZED_EVALUATOR")

    def test_gate_authority_is_scoped(self):
        ev = self.bundle.evidence[0]
        limited = replace(self.key, authorized_gate_ids=("video_render",))
        self.assertNotEqual(ev.gate_id, "video_render")
        self.assertEqual(HmacEvidenceVerifier((limited,)).verify(ev).diagnostic, "UNAUTHORIZED_GATE")

    def test_kind_authority_is_scoped(self):
        limited = replace(self.key, allowed_kinds=("review",))
        self.assertEqual(HmacEvidenceVerifier((limited,)).verify(self.bundle.evidence[0]).diagnostic,
                         "UNAUTHORIZED_EVIDENCE_KIND")

    def test_duplicate_key_ids_rejected(self):
        with self.assertRaisesRegex(ContractError, "DUPLICATE_TRUST_KEY"):
            HmacEvidenceVerifier((self.key, self.key))

    def test_too_short_secret_rejected(self):
        with self.assertRaises(ContractError):
            replace(self.key, secret=b"short")

    def test_secret_not_exposed_in_repr(self):
        self.assertNotIn(self.key.secret.decode(), repr(self.key))
        self.assertNotIn(self.key.secret.decode(), repr(self.verifier))

    def test_inconsistent_trust_result_rejected(self):
        for args in ((True, "OK", "none"), (False, "BAD", "operator_managed"), (1, "OK", "test_only")):
            with self.subTest(args=args), self.assertRaises(ContractError):
                TrustResult(*args)

    def test_empty_signature_never_passes(self):
        ev = replace(self.bundle.evidence[0], signature="")
        self.assertFalse(self.verifier.verify(ev).accepted)


if __name__ == "__main__":
    unittest.main()
