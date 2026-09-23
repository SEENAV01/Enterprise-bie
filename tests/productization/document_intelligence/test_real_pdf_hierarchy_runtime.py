from __future__ import annotations

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
    chapter_structure,
    section_structure,
    subsection_structure,
)
from bie.document_intelligence.real_pdf_hierarchy_runtime import (
    HIERARCHY_POLICY,
    RealPdfHierarchyRuntimeError,
    inspect_real_pdf_hierarchy,
)
from bie.document_intelligence.real_pdf_structure_runtime import (
    inspect_real_pdf_structure,
)
import bie.document_intelligence.real_pdf_hierarchy_runtime as hierarchy_runtime
from structural_pdf_fixtures import hierarchy_pdf, styled_text_pdf


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "inspect_real_pdf_hierarchy.py"


def single_heading_pdf(text: str) -> bytes:
    return styled_text_pdf(
        [[
            (72, 740, text, 22, True),
            (72, 680, "Ordinary fixture body line one.", 12, False),
            (72, 660, "Ordinary fixture body line two.", 12, False),
            (72, 640, "Ordinary fixture body line three.", 12, False),
        ]]
    )


class RealPdfHierarchyRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = hierarchy_pdf()
        cls.result = inspect_real_pdf_hierarchy(cls.data)

    def test_01_runtime_composes_task_012_structure_inspection(self):
        with patch.object(
            hierarchy_runtime,
            "inspect_real_pdf_structure",
            wraps=inspect_real_pdf_structure,
        ) as inspect_structure:
            result = inspect_real_pdf_hierarchy(self.data)

        inspect_structure.assert_called_once()
        self.assertEqual(result.total_blocks, 20)

    def test_02_heading_candidates_follow_page_and_structure_order(self):
        self.assertEqual(
            [(candidate.page, candidate.global_order) for candidate in self.result.candidates],
            [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
        )
        for candidate in self.result.candidates:
            page = inspect_real_pdf_structure(self.data).pages[candidate.page - 1]
            self.assertEqual(
                page.structure_order[candidate.structure_order_position - 1],
                candidate.region_id,
            )

    def test_03_chapter_keyword_classification_is_deterministic(self):
        result = inspect_real_pdf_hierarchy(single_heading_pdf("CHAPTER 7 Evidence"))
        candidate = result.candidates[0]
        self.assertEqual(candidate.numbering, (7,))
        self.assertEqual(candidate.proposed_level, "chapter")

    def test_04_one_component_numeric_heading_is_chapter_candidate(self):
        candidate = inspect_real_pdf_hierarchy(
            single_heading_pdf("3. Numeric Chapter")
        ).candidates[0]
        self.assertEqual((candidate.numbering, candidate.proposed_level), ((3,), "chapter"))

    def test_05_two_component_numbering_is_section_candidate(self):
        candidate = inspect_real_pdf_hierarchy(
            single_heading_pdf("3.2 Numeric Section")
        ).candidates[0]
        self.assertEqual((candidate.numbering, candidate.proposed_level), ((3, 2), "section"))

    def test_06_three_or_more_components_are_subsection_candidates(self):
        candidate = inspect_real_pdf_hierarchy(
            single_heading_pdf("3.2.1.4 Deep Subsection")
        ).candidates[0]
        self.assertEqual(candidate.numbering, (3, 2, 1, 4))
        self.assertEqual(candidate.proposed_level, "subsection")

    def test_07_unnumbered_heading_abstains(self):
        candidate = inspect_real_pdf_hierarchy(
            single_heading_pdf("Unnumbered Overview")
        ).candidates[0]
        self.assertEqual(candidate.resolution_status, "unresolved")
        self.assertEqual(candidate.reason_code, "unnumbered_heading")

    def test_08_unsupported_numbering_abstains_safely(self):
        candidate = inspect_real_pdf_hierarchy(
            single_heading_pdf("IV. Roman Heading")
        ).candidates[0]
        self.assertEqual(candidate.resolution_status, "unresolved")
        self.assertEqual(candidate.reason_code, "unsupported_numbering")

    def test_09_source_derived_ids_are_deterministic(self):
        first = inspect_real_pdf_hierarchy(self.data)
        second = inspect_real_pdf_hierarchy(self.data)
        self.assertEqual(
            [candidate.candidate_id for candidate in first.candidates],
            [candidate.candidate_id for candidate in second.candidates],
        )
        for candidate in first.candidates:
            self.assertTrue(candidate.candidate_id.endswith(candidate.region_id))

    def test_10_duplicate_numbering_is_handled_deterministically(self):
        data = styled_text_pdf(
            [
                [(72, 740, "CHAPTER 1 First", 22, True), (72, 680, "Body one.", 12, False), (72, 660, "Body two.", 12, False)],
                [(72, 740, "1. Duplicate", 22, True), (72, 680, "Body one.", 12, False), (72, 660, "Body two.", 12, False)],
            ]
        )
        result = inspect_real_pdf_hierarchy(data)
        self.assertEqual(result.materialized_chapter_count, 0)
        self.assertEqual(
            [candidate.reason_code for candidate in result.candidates],
            ["duplicate_numbering", "duplicate_numbering"],
        )

    def test_11_canonical_chapters_are_created_only_when_representable(self):
        self.assertEqual(self.result.materialized_chapter_count, 2)
        self.assertTrue(all(isinstance(item.chapter, chapter_structure.Chapter) for item in self.result.chapters))
        self.assertEqual(
            [(item.chapter.start_page, item.chapter.end_page) for item in self.result.chapters],
            [(1, 3), (4, 5)],
        )

    def test_12_canonical_chapter_validate_is_invoked(self):
        with patch.object(
            chapter_structure, "validate", wraps=chapter_structure.validate
        ) as validate:
            inspect_real_pdf_hierarchy(self.data)
        validate.assert_called_once()

    def test_13_section_parent_is_resolved_by_numbering_prefix(self):
        self.assertEqual(self.result.materialized_section_count, 2)
        first = self.result.sections[0]
        self.assertEqual(first.numbering, (1, 1))
        self.assertEqual(first.section.chapter_id, self.result.chapters[0].chapter.chapter_id)

    def test_14_missing_chapter_parent_does_not_attach_arbitrarily(self):
        result = inspect_real_pdf_hierarchy(single_heading_pdf("2.1 Orphan Section"))
        self.assertEqual(result.materialized_section_count, 0)
        self.assertEqual(result.candidates[0].reason_code, "missing_chapter_parent")

    def test_15_canonical_section_validate_is_invoked(self):
        with patch.object(
            section_structure, "validate", wraps=section_structure.validate
        ) as validate:
            inspect_real_pdf_hierarchy(self.data)
        validate.assert_called_once()

    def test_16_subsection_parent_is_resolved_by_numbering_prefix(self):
        self.assertEqual(self.result.materialized_subsection_count, 1)
        subsection = self.result.subsections[0]
        self.assertEqual(subsection.numbering, (1, 1, 1))
        self.assertEqual(subsection.section_id, self.result.sections[0].section.section_id)

    def test_17_missing_section_parent_abstains(self):
        result = inspect_real_pdf_hierarchy(single_heading_pdf("2.1.1 Orphan Subsection"))
        self.assertEqual(result.materialized_subsection_count, 0)
        self.assertEqual(result.candidates[0].reason_code, "missing_section_parent")

    def test_18_canonical_subsection_validate_is_invoked(self):
        with patch.object(
            subsection_structure, "validate", wraps=subsection_structure.validate
        ) as validate:
            inspect_real_pdf_hierarchy(self.data)
        validate.assert_called_once()

    def test_19_chapter_ranges_do_not_overlap(self):
        ranges = [
            (item.chapter.start_page, item.chapter.end_page)
            for item in self.result.chapters
        ]
        self.assertTrue(
            all(current[1] < following[0] for current, following in zip(ranges, ranges[1:]))
        )

    def test_20_safe_serialization_contains_no_heading_text(self):
        safe_json = json.dumps(self.result.to_safe_dict(), sort_keys=True)
        for candidate in self.result.candidates:
            self.assertNotIn(candidate.text, safe_json)

    def test_21_safe_serialization_contains_hash_and_character_count(self):
        safe_candidates = self.result.to_safe_dict()["candidates"]
        for candidate, safe in zip(self.result.candidates, safe_candidates, strict=True):
            self.assertEqual(safe["char_count"], len(candidate.text))
            self.assertEqual(
                safe["text_sha256"],
                hashlib.sha256(candidate.text.encode("utf-8")).hexdigest(),
            )

    def test_22_repeated_runtime_output_is_deterministic(self):
        first = inspect_real_pdf_hierarchy(self.data)
        second = inspect_real_pdf_hierarchy(self.data)
        self.assertEqual(first, second)
        self.assertEqual(first.to_safe_dict(), second.to_safe_dict())
        self.assertEqual(first.hierarchy_policy, HIERARCHY_POLICY)

    def test_23_safe_cli_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "hierarchy.pdf"
            pdf.write_bytes(self.data)
            command = [sys.executable, str(CLI), str(pdf)]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout.encode(), second.stdout.encode())
        self.assertEqual(first.stderr, "")
        parsed = json.loads(first.stdout)
        self.assertEqual(parsed["hierarchy_policy"], HIERARCHY_POLICY)
        for candidate in self.result.candidates:
            self.assertNotIn(candidate.text, first.stdout)

    def test_24_malformed_pdf_fails_closed(self):
        with self.assertRaises(RealPdfHierarchyRuntimeError):
            inspect_real_pdf_hierarchy(b"%PDF-1.7\nmalformed")

    def test_25_encrypted_pdf_fails_closed(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("hierarchy-password")
        output = BytesIO()
        writer.write(output)
        with self.assertRaises(RealPdfHierarchyRuntimeError):
            inspect_real_pdf_hierarchy(output.getvalue())

    def test_26_task_012_runtime_remains_functional(self):
        result = inspect_real_pdf_structure(self.data)
        self.assertEqual(result.page_count, 5)
        self.assertEqual(result.total_blocks, 20)
        self.assertEqual(result.heading_candidate_count, 5)

    def test_27_same_page_chapter_boundaries_abstain(self):
        data = styled_text_pdf(
            [[
                (72, 750, "CHAPTER 1 First", 22, True),
                (72, 710, "CHAPTER 2 Second", 22, True),
                (72, 650, "Ordinary body one.", 12, False),
                (72, 630, "Ordinary body two.", 12, False),
                (72, 610, "Ordinary body three.", 12, False),
            ]]
        )
        result = inspect_real_pdf_hierarchy(data)
        self.assertEqual(result.materialized_chapter_count, 0)
        self.assertEqual(
            [candidate.reason_code for candidate in result.candidates],
            ["ambiguous_chapter_boundary", "ambiguous_chapter_boundary"],
        )

    def test_28_cli_invalid_pdf_has_no_fake_success_json(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "invalid.pdf"
            pdf.write_bytes(b"not a PDF")
            completed = subprocess.run(
                [sys.executable, str(CLI), str(pdf)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")
        self.assertIn("PDF hierarchy inspection failed", completed.stderr)


if __name__ == "__main__":
    unittest.main()
