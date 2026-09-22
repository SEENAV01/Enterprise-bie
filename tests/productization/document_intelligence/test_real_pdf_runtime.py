from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from bie.document_intelligence.pypdf_adapter import PyPdfAdapter, PyPdfAdapterError
from bie.document_intelligence.real_pdf_runtime import (
    RealPdfRuntimeError,
    inspect_real_pdf,
)
from bie.document_intelligence.source_hash import source_sha256
from structural_pdf_fixtures import structural_pdf


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "inspect_real_pdf.py"


class PyPdfAdapterTests(unittest.TestCase):
    def test_genuine_multi_page_pdf_reaches_ingest_shape(self):
        data = structural_pdf(
            page_count=2,
            text_pages={0},
            metadata={"/Title": "Deterministic Fixture", "/Author": "BIE"},
        )

        result = PyPdfAdapter().inspect(data)

        self.assertEqual(result["page_count"], 2)
        self.assertEqual(result["text_pages"], 1)
        self.assertFalse(result["encrypted"])
        self.assertEqual(result["metadata"]["/Title"], "Deterministic Fixture")
        self.assertEqual(result["metadata"]["/Author"], "BIE")
        json.dumps(result["metadata"], sort_keys=True)

    def test_encrypted_pdf_fails_closed(self):
        from io import BytesIO

        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("fixture-password")
        output = BytesIO()
        writer.write(output)

        with self.assertRaises(PyPdfAdapterError):
            PyPdfAdapter().inspect(output.getvalue())


class RealPdfRuntimeTests(unittest.TestCase):
    def test_contract_hash_length_pages_and_metadata(self):
        data = structural_pdf(
            page_count=3,
            text_pages={0, 2},
            metadata={"/Title": "Runtime Fixture"},
        )

        result = inspect_real_pdf(data)

        self.assertEqual(result.source_hash, source_sha256(data))
        self.assertEqual(result.byte_length, len(data))
        self.assertEqual(result.page_count, 3)
        self.assertEqual(result.text_pages, 2)
        self.assertEqual(result.metadata["/Title"], "Runtime Fixture")

    def test_blank_pages_have_zero_text_pages(self):
        result = inspect_real_pdf(structural_pdf(page_count=2))
        self.assertEqual(result.text_pages, 0)

    def test_repeated_inspection_is_deterministic(self):
        data = structural_pdf(
            page_count=1,
            text_pages={0},
            metadata={"/Subject": "Repeatable"},
        )
        first = inspect_real_pdf(data)
        second = inspect_real_pdf(data)
        self.assertEqual(first, second)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_non_pdf_empty_and_malformed_input_fail_closed(self):
        for data in (b"", b"not a PDF", b"%PDF-1.7\nmalformed"):
            with self.subTest(data=data):
                with self.assertRaises(RealPdfRuntimeError):
                    inspect_real_pdf(data)


class RealPdfCliTests(unittest.TestCase):
    def test_cli_emits_json_without_full_document_text(self):
        marker = "SENSITIVE_FULL_CONTENT_SHOULD_NOT_APPEAR"
        data = structural_pdf(
            page_count=1,
            text_pages={0},
            metadata={"/Title": "CLI Fixture"},
            text=marker,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.pdf"
            path.write_bytes(data)
            completed = subprocess.run(
                [sys.executable, str(CLI), str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        parsed = json.loads(completed.stdout)
        self.assertEqual(parsed["page_count"], 1)
        self.assertEqual(parsed["text_pages"], 1)
        self.assertEqual(parsed["source_hash"], source_sha256(data))
        self.assertNotIn(marker, completed.stdout)
        self.assertEqual(completed.stderr, "")

    def test_cli_invalid_pdf_exits_nonzero_without_success_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.pdf"
            path.write_bytes(b"not a PDF")
            completed = subprocess.run(
                [sys.executable, str(CLI), str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("PDF inspection failed", completed.stderr)


if __name__ == "__main__":
    unittest.main()
