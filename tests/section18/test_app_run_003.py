from __future__ import annotations

from batch001_support import OperatorCase

from bie.product_app_v1.source_validation import (
    MAX_SOURCE_BYTES,
    render_source_validation,
    validate_pdf_source,
)


class AppRun003Tests(OperatorCase):
    def test_valid_pdf_gets_basic_validated_state(self):
        v = validate_pdf_source(self.pdf)
        self.assertTrue(v.accepted)
        self.assertEqual(v.status, "BASIC_VALIDATED")
        self.assertEqual(v.diagnostics, ())

    def test_validation_distinguishes_deep_runtime_validation(self):
        v = validate_pdf_source(b"%PDF-1.7\nmalformed")
        self.assertTrue(v.accepted)
        self.assertEqual(v.to_safe_dict()["deep_document_validation"], "DEFERRED_TO_CANONICAL_DOCUMENT_INTELLIGENCE")

    def test_empty_source_is_rejected(self):
        v = validate_pdf_source(b"")
        self.assertFalse(v.accepted)
        self.assertIn("EMPTY_SOURCE", v.diagnostics)

    def test_wrong_media_type_is_rejected(self):
        v = validate_pdf_source(self.pdf, media_type="application/octet-stream")
        self.assertFalse(v.accepted)
        self.assertIn("UNSUPPORTED_MEDIA_TYPE", v.diagnostics)

    def test_pdf_header_must_be_in_first_1024_bytes(self):
        good = validate_pdf_source(b"x" * 100 + b"%PDF-1.7\n")
        bad = validate_pdf_source(b"x" * 1025 + b"%PDF-1.7\n")
        self.assertTrue(good.accepted)
        self.assertFalse(bad.accepted)
        self.assertIn("PDF_SIGNATURE_NOT_FOUND", bad.diagnostics)

    def test_oversize_is_rejected_without_hash_claim_change(self):
        v = validate_pdf_source(b"%PDF-" + b"x" * 20, max_bytes=8)
        self.assertFalse(v.accepted)
        self.assertIn("SOURCE_TOO_LARGE", v.diagnostics)

    def test_html_is_accessible_and_truthful(self):
        html = render_source_validation(validate_pdf_source(self.pdf), display_name="Book.pdf")
        self.assertIn("aria-labelledby='source-validation-title'", html)
        self.assertIn("Basic transport validation only", html)
        self.assertIn("Deep document validation", html)

    def test_html_escapes_untrusted_filename(self):
        html = render_source_validation(validate_pdf_source(self.pdf), display_name="<script>alert(1)</script>.pdf")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    import unittest
    unittest.main()
