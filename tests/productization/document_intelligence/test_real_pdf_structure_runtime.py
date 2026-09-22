from __future__ import annotations

from dataclasses import replace
from io import BytesIO
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pypdf import PdfWriter

from bie.document_intelligence import (
    block_provenance,
    heading_detection,
    multicolumn_layout,
)
from bie.document_intelligence.pdfplumber_structure_adapter import (
    NativeStructureDocument,
    PdfPlumberStructureAdapter,
    PdfPlumberStructureAdapterError,
)
from bie.document_intelligence.reading_order import validate_order
from bie.document_intelligence.real_pdf_structure_runtime import (
    HEADING_FEATURE_POLICY,
    PROVENANCE_METHOD,
    STRUCTURE_ORDER_POLICY,
    RealPdfStructureRuntimeError,
    inspect_real_pdf_structure,
)
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text
from structural_pdf_fixtures import styled_text_pdf


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "inspect_real_pdf_structure.py"


def single_column_pdf() -> bytes:
    return styled_text_pdf(
        [[
            (72, 740, "1. Structured Heading", 22, True),
            (72, 690, "Ordinary body text for deterministic structure testing.", 12, False),
            (72, 670, "A second ordinary body line.", 12, False),
        ]]
    )


def two_column_pdf() -> bytes:
    return styled_text_pdf(
        [[
            (54, 730, "Left first", 12, False),
            (54, 700, "Left second", 12, False),
            (340, 720, "Right first", 12, False),
            (340, 690, "Right second", 12, False),
        ]]
    )


class StaticStructureAdapter:
    def __init__(self, document: NativeStructureDocument):
        self.document = document

    def extract(self, data: bytes) -> NativeStructureDocument:
        return self.document


class PdfPlumberStructureAdapterTests(unittest.TestCase):
    def test_extracts_geometry_and_style_observations(self):
        document = PdfPlumberStructureAdapter().extract(single_column_pdf())

        self.assertEqual(document.page_count, 1)
        self.assertEqual(len(document.pages[0].lines), 3)
        heading = document.pages[0].lines[0]
        self.assertEqual(heading.page, 1)
        self.assertEqual(heading.text, "1. Structured Heading")
        self.assertGreater(heading.representative_font_size, 12)
        self.assertEqual(heading.bold_fraction, 1.0)
        self.assertTrue(heading.font_sizes)
        self.assertTrue(all(heading.font_names))
        self.assertEqual(heading.char_count, len(heading.text))
        x0, y0, x1, y1 = heading.box
        self.assertTrue(0 <= x0 < x1 <= 1)
        self.assertTrue(0 <= y0 < y1 <= 1)

    def test_invalid_and_encrypted_pdf_fail_closed(self):
        adapter = PdfPlumberStructureAdapter()
        with self.assertRaises(PdfPlumberStructureAdapterError):
            adapter.extract("not bytes")  # type: ignore[arg-type]
        with self.assertRaises(PdfPlumberStructureAdapterError):
            adapter.extract(b"%PDF-1.7\nmalformed")

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("structure-password")
        output = BytesIO()
        writer.write(output)
        with self.assertRaises(PdfPlumberStructureAdapterError):
            adapter.extract(output.getvalue())


class RealPdfStructureRuntimeTests(unittest.TestCase):
    def test_strict_alignment_and_all_heading_features(self):
        result = inspect_real_pdf_structure(single_column_pdf())

        self.assertEqual(result.heading_feature_policy, HEADING_FEATURE_POLICY)
        self.assertEqual(result.structure_order_policy, STRUCTURE_ORDER_POLICY)
        self.assertEqual(result.total_blocks, 3)
        for signal in result.pages[0].blocks:
            self.assertEqual(
                signal.source_linked_block.block.text.strip(),
                signal.source_linked_block.block.text,
            )
            self.assertEqual(
                signal.source_linked_block.region.box,
                signal.source_linked_block.source_anchor.box,
            )
            for value in signal.heading_features.to_dict().values():
                self.assertTrue(0.0 <= value <= 1.0)

    def test_alignment_mismatch_fails_closed(self):
        data = single_column_pdf()
        document = PdfPlumberStructureAdapter().extract(data)
        first_page = document.pages[0]
        bad_line = replace(first_page.lines[0], text="different text")
        bad_document = replace(
            document,
            pages=(replace(first_page, lines=(bad_line, *first_page.lines[1:])),),
        )

        with self.assertRaisesRegex(RealPdfStructureRuntimeError, "content mismatch"):
            inspect_real_pdf_structure(
                data,
                structure_adapter=StaticStructureAdapter(bad_document),
            )

    def test_larger_bold_heading_scores_above_body(self):
        page = inspect_real_pdf_structure(single_column_pdf()).pages[0]
        heading, body = page.blocks[0], page.blocks[1]

        self.assertGreater(heading.heading_score, body.heading_score)
        self.assertEqual(heading.heading_features.bold, 1.0)
        self.assertGreater(heading.heading_features.font_scale, 0.0)

    def test_canonical_heading_functions_are_used(self):
        with patch.object(
            heading_detection,
            "heading_score",
            wraps=heading_detection.heading_score,
        ) as score, patch.object(
            heading_detection,
            "is_heading",
            wraps=heading_detection.is_heading,
        ) as is_heading:
            result = inspect_real_pdf_structure(single_column_pdf())

        self.assertEqual(score.call_count, result.total_blocks * 2)
        self.assertEqual(is_heading.call_count, result.total_blocks)

    def test_numbering_feature_is_deterministic_and_conservative(self):
        data = styled_text_pdf(
            [[
                (72, 740, "1. Heading", 12, False),
                (72, 710, "1.2 Nested heading", 12, False),
                (72, 680, "CHAPTER 1", 12, False),
                (72, 650, "2026 results are ordinary prose", 12, False),
            ]]
        )
        first = inspect_real_pdf_structure(data)
        second = inspect_real_pdf_structure(data)
        values = tuple(
            signal.heading_features.numbering for signal in first.pages[0].blocks
        )

        self.assertEqual(values, (1.0, 1.0, 1.0, 0.0))
        self.assertEqual(first, second)

    def test_canonical_native_block_provenance_validates_every_block(self):
        with patch.object(
            block_provenance,
            "validate",
            wraps=block_provenance.validate,
        ) as validate:
            result = inspect_real_pdf_structure(single_column_pdf())

        self.assertEqual(validate.call_count, result.total_blocks)
        for call in validate.call_args_list:
            block_id, anchor_ids, method = call.args
            self.assertTrue(block_id)
            self.assertEqual(len(anchor_ids), 1)
            self.assertEqual(method, PROVENANCE_METHOD)

    def test_single_column_preserves_baseline_order(self):
        page = inspect_real_pdf_structure(single_column_pdf()).pages[0]

        self.assertFalse(page.column_order_applied)
        self.assertEqual(page.fallback_reason, "single_column")
        self.assertEqual(page.structure_order, page.baseline_order)
        self.assertEqual(page.column_count, 1)

    def test_clean_two_columns_use_canonical_groups_and_column_order(self):
        with patch.object(
            multicolumn_layout,
            "detect_columns",
            wraps=multicolumn_layout.detect_columns,
        ) as detect:
            page = inspect_real_pdf_structure(two_column_pdf()).pages[0]

        self.assertGreaterEqual(detect.call_count, 2)
        self.assertEqual(page.column_count, 2)
        self.assertTrue(page.column_order_applied)
        self.assertIsNone(page.fallback_reason)
        flattened = tuple(region_id for group in page.column_groups for region_id in group)
        self.assertEqual(set(flattened), set(page.baseline_order))
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(
            page.structure_order,
            validate_order(page.baseline_order, page.structure_order),
        )
        self.assertEqual(
            page.structure_order_edges,
            tuple(zip(page.structure_order, page.structure_order[1:])),
        )

    def test_ambiguous_overlapping_columns_fall_back(self):
        data = styled_text_pdf(
            [[
                (60, 730, "Overlapping first", 12, False),
                (90, 700, "Overlapping second", 12, False),
            ]]
        )
        fake_groups = (("p0001-r0001",), ("p0001-r0002",))
        with patch.object(
            multicolumn_layout,
            "detect_columns",
            return_value=fake_groups,
        ):
            page = inspect_real_pdf_structure(data).pages[0]

        self.assertFalse(page.column_order_applied)
        self.assertEqual(page.fallback_reason, "ambiguous_column_overlap")
        self.assertEqual(page.structure_order, page.baseline_order)

    def test_repeated_runtime_and_safe_serialization_are_deterministic(self):
        data = two_column_pdf()
        first = inspect_real_pdf_structure(data)
        second = inspect_real_pdf_structure(data)

        self.assertEqual(first, second)
        self.assertEqual(first.to_safe_dict(), second.to_safe_dict())
        self.assertEqual(first.heading_candidate_count, second.heading_candidate_count)

    def test_safe_serialization_has_hash_and_count_without_text(self):
        marker = "STRUCTURE_TEXT_MUST_NOT_BE_SERIALIZED"
        result = inspect_real_pdf_structure(
            styled_text_pdf([[(72, 720, marker, 12, False)]])
        )
        safe = result.to_safe_dict()
        serialized = json.dumps(safe, sort_keys=True)
        block = safe["pages"][0]["blocks"][0]

        self.assertNotIn(marker, serialized)
        self.assertEqual(block["char_count"], len(marker))
        self.assertEqual(
            block["text_sha256"],
            hashlib.sha256(marker.encode("utf-8")).hexdigest(),
        )

    def test_malformed_and_encrypted_pdf_fail_closed(self):
        with self.assertRaises(RealPdfStructureRuntimeError):
            inspect_real_pdf_structure(b"%PDF-1.7\nmalformed")

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("structure-password")
        output = BytesIO()
        writer.write(output)
        with self.assertRaises(RealPdfStructureRuntimeError):
            inspect_real_pdf_structure(output.getvalue())

    def test_task_010_source_linked_runtime_remains_functional(self):
        result = inspect_real_pdf_text(single_column_pdf())
        self.assertEqual(result.page_count, 1)
        self.assertEqual(result.total_blocks, 3)
        self.assertEqual(
            result.pages[0].ordered_region_ids,
            tuple(
                item.region.region_id
                for item in result.pages[0].source_linked_blocks
            ),
        )


class RealPdfStructureCliTests(unittest.TestCase):
    def run_cli(self, data: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "structure.pdf"
            path.write_bytes(data)
            return subprocess.run(
                [sys.executable, str(CLI), str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_safe_cli_output_is_deterministic_and_contains_no_text(self):
        marker = "CLI_STRUCTURE_TEXT_MUST_NOT_APPEAR"
        data = styled_text_pdf([[(72, 720, marker, 18, True)]])
        first = self.run_cli(data)
        second = self.run_cli(data)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout.encode(), second.stdout.encode())
        self.assertNotIn(marker, first.stdout)
        parsed = json.loads(first.stdout)
        self.assertEqual(parsed["heading_feature_policy"], HEADING_FEATURE_POLICY)
        self.assertEqual(parsed["structure_order_policy"], STRUCTURE_ORDER_POLICY)
        self.assertIn("text_sha256", parsed["pages"][0]["blocks"][0])
        self.assertIn("char_count", parsed["pages"][0]["blocks"][0])
        self.assertEqual(first.stderr, "")

    def test_cli_invalid_pdf_has_no_success_json(self):
        completed = self.run_cli(b"not a PDF")
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("PDF structure inspection failed", completed.stderr)


if __name__ == "__main__":
    unittest.main()
