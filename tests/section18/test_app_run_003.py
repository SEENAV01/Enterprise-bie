from __future__ import annotations

from bie.app_product.source_validation import render_source_validation_html, validate_source
from .support import AppProductCase


class SourceValidationUiTests(AppProductCase):
    def test_ui_has_accessible_section_label(self):
        html = render_source_validation_html(validate_source(self.pdf, "Book.pdf", "application/pdf"))
        self.assertIn('aria-label="Source validation"', html)

    def test_ui_shows_truthful_pending_native_validation(self):
        html = render_source_validation_html(validate_source(self.pdf, "Book.pdf", "application/pdf"))
        self.assertIn(">PENDING<", html)
        self.assertNotIn(">SUCCEEDED<", html)

    def test_ui_shows_hash_and_byte_count(self):
        view = validate_source(self.pdf, "Book.pdf", "application/pdf")
        html = render_source_validation_html(view)
        self.assertIn(view.source_sha256, html)
        self.assertIn(str(len(self.pdf)), html)

    def test_ui_escapes_display_name(self):
        view = validate_source(self.pdf, "<script>.pdf", "application/pdf")
        html = render_source_validation_html(view)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_ui_lists_rejection_issues(self):
        view = validate_source(b"garbage", "Book.pdf", "application/pdf")
        html = render_source_validation_html(view)
        self.assertIn("PDF_HEADER_NOT_FOUND", html)
        self.assertIn('data-status="REJECTED"', html)

    def test_ui_lists_warnings(self):
        view = validate_source(self.pdf, "Book.bin", "application/pdf")
        self.assertIn("DISPLAY_NAME_NOT_PDF_SUFFIX", render_source_validation_html(view))

    def test_ui_does_not_embed_pdf_bytes(self):
        marker = b"SECRET_PDF_PAYLOAD_MARKER"
        payload = b"%PDF-1.7\n" + marker
        html = render_source_validation_html(validate_source(payload, "Book.pdf", "application/pdf"))
        self.assertNotIn(marker.decode(), html)

    def test_ui_ready_state_has_no_issues(self):
        view = validate_source(self.pdf, "Book.pdf", "application/pdf")
        self.assertEqual(view.issues, ())
        self.assertIn("<li>None</li>", render_source_validation_html(view))


if __name__ == "__main__":
    import unittest
    unittest.main()
