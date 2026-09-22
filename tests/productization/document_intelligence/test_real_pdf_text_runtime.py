from __future__ import annotations

from io import BytesIO
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pypdf import PdfWriter

from bie.document_intelligence.layout_segmentation import Region, normalize
from bie.document_intelligence.page_mapping import validate as validate_page_map
from bie.document_intelligence.pdfplumber_text_adapter import (
    NativeTextDocument,
    NativeTextLine,
    NativeTextPage,
    PdfPlumberTextAdapter,
    PdfPlumberTextAdapterError,
)
from bie.document_intelligence.reading_order import validate_order
from bie.document_intelligence.real_pdf_runtime import inspect_real_pdf
from bie.document_intelligence.real_pdf_text_runtime import (
    READING_ORDER_POLICY,
    RealPdfTextRuntimeError,
    inspect_real_pdf_text,
)
from bie.document_intelligence.source_anchors import validate as validate_source_anchor
from bie.document_intelligence.source_hash import source_sha256
from bie.document_intelligence.text_blocks import TextBlock
from structural_pdf_fixtures import positioned_text_pdf, structural_pdf


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "inspect_real_pdf_text.py"


class StaticTextAdapter:
    def __init__(self, document: NativeTextDocument):
        self.document = document

    def extract(self, data: bytes) -> NativeTextDocument:
        return self.document


def native_line(
    text: str,
    *,
    x0: float,
    top: float,
    x1: float,
    bottom: float,
) -> NativeTextLine:
    return NativeTextLine(
        page=1,
        text=text,
        x0=x0,
        top=top,
        x1=x1,
        bottom=bottom,
        box=(x0 / 100, top / 100, x1 / 100, bottom / 100),
    )


class PdfPlumberTextAdapterTests(unittest.TestCase):
    def test_genuine_native_text_lines_include_normalized_geometry(self):
        data = positioned_text_pdf(
            [[(72, 720, "First structural line"), (144, 680, "Second line")], []]
        )

        document = PdfPlumberTextAdapter().extract(data)

        self.assertEqual(document.page_count, 2)
        self.assertEqual(len(document.pages[0].lines), 2)
        self.assertEqual(document.pages[1].lines, ())
        for line in document.pages[0].lines:
            self.assertEqual(line.page, 1)
            self.assertTrue(line.text.strip())
            x0, y0, x1, y1 = line.box
            self.assertTrue(0 <= x0 < x1 <= 1)
            self.assertTrue(0 <= y0 < y1 <= 1)

    def test_invalid_inputs_fail_closed(self):
        adapter = PdfPlumberTextAdapter()
        with self.assertRaises(PdfPlumberTextAdapterError):
            adapter.extract("not bytes")  # type: ignore[arg-type]
        with self.assertRaises(PdfPlumberTextAdapterError):
            adapter.extract(b"%PDF-1.7\nmalformed")


class RealPdfTextRuntimeTests(unittest.TestCase):
    def test_native_text_reuses_all_canonical_contract_types(self):
        data = positioned_text_pdf(
            [[(72, 720, "Top line"), (72, 680, "Lower line")], [(72, 720, "Page two")]]
        )

        result = inspect_real_pdf_text(data)

        self.assertEqual(result.source_hash, source_sha256(data))
        self.assertEqual(result.page_count, 2)
        self.assertEqual(result.total_blocks, 3)
        self.assertEqual(result.reading_order_policy, READING_ORDER_POLICY)
        for page in result.pages:
            region_ids = tuple(
                item.region.region_id for item in page.source_linked_blocks
            )
            self.assertEqual(
                page.ordered_region_ids,
                validate_order(region_ids, page.ordered_region_ids),
            )
            self.assertEqual(
                page.reading_order_edges,
                tuple(zip(region_ids, region_ids[1:])),
            )
            normalize([item.region for item in page.source_linked_blocks])
            validate_page_map(
                [item.page_map_anchor for item in page.source_linked_blocks],
                result.page_count,
            )
            for item in page.source_linked_blocks:
                self.assertIsInstance(item.region, Region)
                self.assertIsInstance(item.block, TextBlock)
                self.assertEqual(item.block.region_ids, (item.region.region_id,))
                self.assertEqual(item.block.page, page.page)
                self.assertEqual(item.source_anchor.page, item.block.page)
                self.assertEqual(item.source_anchor.region_id, item.region.region_id)
                self.assertEqual(item.source_anchor.source_hash, result.source_hash)
                self.assertEqual(item.source_anchor.box, item.region.box)
                self.assertTrue(validate_source_anchor(item.source_anchor))
                self.assertEqual(item.page_map_anchor.box, item.region.box)
                self.assertEqual(
                    item.page_map_anchor.physical_page,
                    item.block.page,
                )
                self.assertEqual(
                    item.page_map_anchor.logical_id,
                    item.block.block_id,
                )

    def test_ids_and_repeated_runtime_are_deterministic(self):
        data = positioned_text_pdf(
            [[(72, 720, "One"), (72, 680, "Two")], [(72, 720, "Three")]]
        )
        first = inspect_real_pdf_text(data)
        second = inspect_real_pdf_text(data)

        self.assertEqual(first, second)
        self.assertEqual(first.to_safe_dict(), second.to_safe_dict())
        self.assertEqual(
            first.pages[0].ordered_region_ids,
            ("p0001-r0001", "p0001-r0002"),
        )
        self.assertEqual(
            tuple(item.block.block_id for item in first.pages[0].source_linked_blocks),
            ("p0001-b0001", "p0001-b0002"),
        )

    def test_top_then_left_policy_is_stable(self):
        data = structural_pdf(page_count=1)
        document = NativeTextDocument(
            page_count=1,
            pages=(
                NativeTextPage(
                    page=1,
                    width=100,
                    height=100,
                    lines=(
                        native_line("Right", x0=0.6, top=0.1, x1=0.9, bottom=0.2),
                        native_line("Lower", x0=0.1, top=0.5, x1=0.4, bottom=0.6),
                        native_line("Left", x0=0.1, top=0.1, x1=0.4, bottom=0.2),
                    ),
                ),
            ),
        )

        result = inspect_real_pdf_text(data, text_adapter=StaticTextAdapter(document))
        texts = tuple(
            item.block.text for item in result.pages[0].source_linked_blocks
        )

        self.assertEqual(texts, ("Left", "Right", "Lower"))
        self.assertEqual(
            result.pages[0].reading_order_edges,
            (("p0001-r0001", "p0001-r0002"), ("p0001-r0002", "p0001-r0003")),
        )

    def test_blank_page_has_no_fabricated_blocks(self):
        result = inspect_real_pdf_text(structural_pdf(page_count=1))
        self.assertEqual(result.total_blocks, 0)
        self.assertEqual(result.pages[0].ordered_region_ids, ())
        self.assertEqual(result.pages[0].reading_order_edges, ())
        self.assertEqual(result.pages[0].source_linked_blocks, ())

    def test_malformed_pdf_fails_closed(self):
        with self.assertRaises(RealPdfTextRuntimeError):
            inspect_real_pdf_text(b"%PDF-1.7\nmalformed")

    def test_encrypted_pdf_fails_closed(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("structural-password")
        output = BytesIO()
        writer.write(output)

        with self.assertRaises(RealPdfTextRuntimeError):
            inspect_real_pdf_text(output.getvalue())

    def test_parser_page_count_mismatch_fails_closed(self):
        data = structural_pdf(page_count=1)
        mismatched = NativeTextDocument(
            page_count=2,
            pages=(
                NativeTextPage(page=1, width=612, height=792, lines=()),
                NativeTextPage(page=2, width=612, height=792, lines=()),
            ),
        )

        with self.assertRaisesRegex(RealPdfTextRuntimeError, "page-count mismatch"):
            inspect_real_pdf_text(data, text_adapter=StaticTextAdapter(mismatched))

    def test_safe_serialization_hashes_text_without_emitting_it(self):
        marker = "BOOK_TEXT_MUST_NOT_BE_SERIALIZED"
        result = inspect_real_pdf_text(
            positioned_text_pdf([[(72, 720, marker)]])
        )

        safe = result.to_safe_dict()
        serialized = json.dumps(safe, sort_keys=True)
        descriptor = safe["pages"][0]["blocks"][0]

        self.assertNotIn(marker, serialized)
        self.assertEqual(descriptor["char_count"], len(marker))
        self.assertEqual(
            descriptor["text_sha256"],
            hashlib.sha256(marker.encode("utf-8")).hexdigest(),
        )

    def test_canonical_base_real_pdf_runtime_remains_functional(self):
        data = positioned_text_pdf([[(72, 720, "Base runtime")]])
        result = inspect_real_pdf(data)
        self.assertEqual(result.source_hash, source_sha256(data))
        self.assertEqual(result.page_count, 1)


class RealPdfTextCliTests(unittest.TestCase):
    def run_cli(self, data: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "structural.pdf"
            path.write_bytes(data)
            return subprocess.run(
                [sys.executable, str(CLI), str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_safe_cli_has_required_fields_and_no_text(self):
        marker = "CLI_TEXT_MUST_NOT_APPEAR"
        completed = self.run_cli(positioned_text_pdf([[(72, 720, marker)]]))

        self.assertEqual(completed.returncode, 0, completed.stderr)
        parsed = json.loads(completed.stdout)
        self.assertNotIn(marker, completed.stdout)
        self.assertEqual(parsed["reading_order_policy"], READING_ORDER_POLICY)
        self.assertEqual(parsed["total_blocks"], 1)
        block = parsed["pages"][0]["blocks"][0]
        self.assertEqual(block["char_count"], len(marker))
        self.assertEqual(
            block["text_sha256"],
            hashlib.sha256(marker.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(completed.stderr, "")

    def test_safe_cli_output_is_deterministic(self):
        data = positioned_text_pdf([[(72, 720, "Repeatable CLI")]])
        first = self.run_cli(data)
        second = self.run_cli(data)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout.encode(), second.stdout.encode())

    def test_safe_cli_invalid_pdf_has_no_success_json(self):
        completed = self.run_cli(b"not a PDF")
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("PDF text inspection failed", completed.stderr)


if __name__ == "__main__":
    unittest.main()
