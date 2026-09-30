from __future__ import annotations

import hashlib

from bie.app_product.contracts import AppProductError
from bie.app_product.source_validation import validate_source
from .support import AppProductCase


class SourceImportTests(AppProductCase):
    def test_valid_pdf_ready_to_submit(self):
        result = validate_source(self.pdf, "Book.pdf", "application/pdf")
        self.assertEqual(result.status, "READY_TO_SUBMIT")
        self.assertEqual(result.native_validation, "PENDING")

    def test_content_type_parameters_allowed(self):
        result = validate_source(self.pdf, "Book.pdf", "application/pdf; charset=binary")
        self.assertEqual(result.media_type, "application/pdf")
        self.assertFalse(result.issues)

    def test_empty_source_rejected(self):
        result = validate_source(b"", "Book.pdf", "application/pdf")
        self.assertIn("EMPTY_SOURCE", result.issues)
        self.assertEqual(result.native_validation, "NOT_RUN")

    def test_wrong_media_type_rejected(self):
        result = validate_source(self.pdf, "Book.pdf", "application/octet-stream")
        self.assertIn("UNSUPPORTED_MEDIA_TYPE", result.issues)

    def test_non_pdf_bytes_rejected(self):
        result = validate_source(b"not a pdf", "Book.pdf", "application/pdf")
        self.assertIn("PDF_HEADER_NOT_FOUND", result.issues)

    def test_header_within_first_kib_is_detected(self):
        result = validate_source(b"x" * 40 + b"%PDF-1.7\nbody", "Book.pdf", "application/pdf")
        self.assertEqual(result.status, "READY_TO_SUBMIT")

    def test_bounded_limit_is_enforced_without_large_fixture(self):
        result = validate_source(b"%PDF-1.7\n1234", "Book.pdf", "application/pdf", max_bytes=8)
        self.assertIn("SOURCE_TOO_LARGE", result.issues)

    def test_source_hash_is_exact(self):
        result = validate_source(self.pdf, "Book.pdf", "application/pdf")
        self.assertEqual(result.source_sha256, hashlib.sha256(self.pdf).hexdigest())

    def test_display_path_is_rejected(self):
        with self.assertRaises(AppProductError):
            validate_source(self.pdf, "../Book.pdf", "application/pdf")

    def test_non_pdf_suffix_is_warning_not_fake_rejection(self):
        result = validate_source(self.pdf, "Book.bin", "application/pdf")
        self.assertEqual(result.status, "READY_TO_SUBMIT")
        self.assertIn("DISPLAY_NAME_NOT_PDF_SUFFIX", result.warnings)


if __name__ == "__main__":
    import unittest
    unittest.main()
