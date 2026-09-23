from __future__ import annotations

from collections import Counter
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

from bie.document_intelligence.pypdf_outline_adapter import (
    NativeOutlineDocument,
    NativeOutlineEntry,
    PyPdfOutlineAdapter,
    PyPdfOutlineAdapterError,
)
from bie.document_intelligence.real_pdf_hierarchy_runtime import (
    inspect_real_pdf_hierarchy,
)
from bie.document_intelligence.real_pdf_toc_runtime import (
    TOC_RECONCILIATION_POLICY,
    RealPdfTocRuntimeError,
    inspect_real_pdf_toc,
)
import bie.document_intelligence.real_pdf_toc_runtime as toc_runtime
from structural_pdf_fixtures import hierarchy_pdf, hierarchy_pdf_with_outline


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "inspect_real_pdf_toc.py"


class RealPdfTocRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = hierarchy_pdf_with_outline()
        cls.result = inspect_real_pdf_toc(cls.data)

    def test_01_outline_adapter_reads_native_entries(self):
        document = PyPdfOutlineAdapter().inspect(self.data)
        self.assertEqual(document.page_count, 5)
        self.assertEqual(len(document.entries), 5)

    def test_02_outline_flattening_preserves_source_order(self):
        entries = PyPdfOutlineAdapter().inspect(self.data).entries
        self.assertEqual([entry.order for entry in entries], [1, 2, 3, 4, 5])
        self.assertEqual(
            [entry.title for entry in entries],
            [
                "CHAPTER 1 Foundation",
                "1.1 First Section",
                "1.1.1 First Subsection",
                "CHAPTER 2 Continuation",
                "2.1 Second Section",
            ],
        )

    def test_03_nested_outlines_expose_deterministic_depth(self):
        entries = PyPdfOutlineAdapter().inspect(self.data).entries
        self.assertEqual([entry.depth for entry in entries], [0, 1, 2, 0, 1])

    def test_04_destination_pages_are_one_based(self):
        entries = PyPdfOutlineAdapter().inspect(self.data).entries
        self.assertEqual([entry.destination_page for entry in entries], [1, 2, 3, 4, 5])

    def test_05_pdf_without_outline_returns_empty_entries(self):
        document = PyPdfOutlineAdapter().inspect(hierarchy_pdf())
        self.assertEqual(document.entries, ())
        result = inspect_real_pdf_toc(hierarchy_pdf())
        self.assertEqual(result.outline_status, "no_native_outline")
        self.assertEqual(result.native_outline_entry_count, 0)

    def test_06_malformed_pdf_fails_closed(self):
        with self.assertRaises(PyPdfOutlineAdapterError):
            PyPdfOutlineAdapter().inspect(b"%PDF-1.7\nmalformed")

    def test_07_encrypted_pdf_fails_closed(self):
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.encrypt("toc-password")
        output = BytesIO()
        writer.write(output)
        with self.assertRaises(PyPdfOutlineAdapterError):
            PyPdfOutlineAdapter().inspect(output.getvalue())

    def test_08_runtime_composes_task_014_hierarchy_first(self):
        with patch.object(
            toc_runtime,
            "inspect_real_pdf_hierarchy",
            wraps=inspect_real_pdf_hierarchy,
        ) as inspect_hierarchy:
            inspect_real_pdf_toc(self.data)
        inspect_hierarchy.assert_called_once_with(self.data)

    def test_09_page_count_inconsistency_fails_closed(self):
        wrong = NativeOutlineDocument(page_count=6, entries=())
        with patch.object(
            toc_runtime.PyPdfOutlineAdapter, "inspect", return_value=wrong
        ):
            with self.assertRaises(RealPdfTocRuntimeError):
                inspect_real_pdf_toc(hierarchy_pdf())

    def test_10_materialized_chapters_become_detected_nodes(self):
        chapter_matches = [
            match for match in self.result.matches if match.detected_level == "chapter"
        ]
        self.assertEqual(len(chapter_matches), 2)

    def test_11_materialized_sections_become_detected_nodes(self):
        section_matches = [
            match for match in self.result.matches if match.detected_level == "section"
        ]
        self.assertEqual(len(section_matches), 2)

    def test_12_materialized_subsections_become_detected_nodes(self):
        subsection_matches = [
            match
            for match in self.result.matches
            if match.detected_level == "subsection"
        ]
        self.assertEqual(len(subsection_matches), 1)

    def test_13_canonical_reconciliation_is_invoked(self):
        with patch.object(
            toc_runtime.toc_reconciliation,
            "reconcile",
            wraps=toc_runtime.toc_reconciliation.reconcile,
        ) as reconcile:
            inspect_real_pdf_toc(self.data)
        reconcile.assert_called_once()

    def test_14_exact_title_matches_produce_reconciliation_matches(self):
        self.assertEqual(self.result.reconciliation_match_count, 5)
        self.assertEqual(self.result.unmatched_outline_count, 0)

    def test_15_case_insensitive_canonical_matching_is_preserved(self):
        data = hierarchy_pdf_with_outline(
            (("chapter 1 foundation", 0, None),)
        )
        result = inspect_real_pdf_toc(data)
        self.assertEqual(result.reconciliation_match_count, 1)
        self.assertEqual(result.matches[0].detected_level, "chapter")

    def test_16_unmatched_outline_entry_remains_unmatched(self):
        data = hierarchy_pdf_with_outline(
            (("Appendix not represented in hierarchy", 4, None),)
        )
        result = inspect_real_pdf_toc(data)
        self.assertEqual(result.reconciliation_match_count, 0)
        self.assertEqual(result.unmatched_outline_count, 1)
        self.assertEqual(
            result.unmatched_outline_entries[0].reason_code,
            "no_detected_title_match",
        )

    def test_17_duplicate_detected_title_is_ambiguous(self):
        hierarchy = inspect_real_pdf_hierarchy(hierarchy_pdf())
        duplicate_title = hierarchy.chapters[0].chapter.title
        duplicate_section = replace(
            hierarchy.sections[0],
            section=replace(hierarchy.sections[0].section, title=duplicate_title),
        )
        hierarchy = replace(
            hierarchy,
            sections=(duplicate_section,) + hierarchy.sections[1:],
        )
        data = hierarchy_pdf_with_outline(((duplicate_title, 0, None),))
        with patch.object(
            toc_runtime, "inspect_real_pdf_hierarchy", return_value=hierarchy
        ):
            result = inspect_real_pdf_toc(data)
        self.assertEqual(result.ambiguous_detected_title_count, 1)
        self.assertEqual(result.reconciliation_match_count, 0)
        self.assertEqual(
            result.unmatched_outline_entries[0].reason_code,
            "ambiguous_detected_title",
        )

    def test_18_ambiguous_title_is_excluded_from_canonical_matching(self):
        hierarchy = inspect_real_pdf_hierarchy(hierarchy_pdf())
        duplicate_title = hierarchy.chapters[0].chapter.title
        hierarchy = replace(
            hierarchy,
            sections=(
                replace(
                    hierarchy.sections[0],
                    section=replace(
                        hierarchy.sections[0].section, title=duplicate_title
                    ),
                ),
            )
            + hierarchy.sections[1:],
        )
        data = hierarchy_pdf_with_outline(((duplicate_title, 0, None),))
        with (
            patch.object(
                toc_runtime, "inspect_real_pdf_hierarchy", return_value=hierarchy
            ),
            patch.object(
                toc_runtime.toc_reconciliation,
                "reconcile",
                wraps=toc_runtime.toc_reconciliation.reconcile,
            ) as reconcile,
        ):
            inspect_real_pdf_toc(data)
        detected_input = reconcile.call_args.args[1]
        self.assertNotIn(
            duplicate_title.casefold(),
            {item["title"].casefold() for item in detected_input},
        )

    def test_19_unresolved_outline_page_is_retained_safely(self):
        data = hierarchy_pdf_with_outline(
            (("CHAPTER 1 Foundation", None, None),)
        )
        result = inspect_real_pdf_toc(data)
        self.assertEqual(result.native_outline_entry_count, 1)
        self.assertEqual(result.outline_resolvable_page_count, 0)
        self.assertEqual(
            result.unmatched_outline_entries[0].reason_code,
            "outline_page_unresolved",
        )

    def test_20_matched_page_diagnostics_are_deterministic(self):
        self.assertEqual(self.result.exact_page_match_count, 5)
        self.assertEqual(self.result.page_delta_distribution, ((0, 5),))
        self.assertTrue(all(match.exact_page_match for match in self.result.matches))

    def test_21_safe_serialization_contains_no_outline_title(self):
        safe_json = json.dumps(self.result.to_safe_dict(), sort_keys=True)
        for entry in PyPdfOutlineAdapter().inspect(self.data).entries:
            self.assertNotIn(entry.title, safe_json)

    def test_22_safe_serialization_contains_no_hierarchy_title(self):
        hierarchy = inspect_real_pdf_hierarchy(self.data)
        safe_json = json.dumps(self.result.to_safe_dict(), sort_keys=True)
        titles = [item.chapter.title for item in hierarchy.chapters]
        titles.extend(item.section.title for item in hierarchy.sections)
        titles.extend(item.title for item in hierarchy.subsections)
        for title in titles:
            self.assertNotIn(title, safe_json)

    def test_23_safe_serialization_exposes_title_hash_and_char_count(self):
        entries = PyPdfOutlineAdapter().inspect(self.data).entries
        safe_matches = self.result.to_safe_dict()["matches"]
        for entry, safe in zip(entries, safe_matches, strict=True):
            self.assertEqual(safe["char_count"], len(entry.title))
            self.assertEqual(
                safe["title_sha256"],
                hashlib.sha256(entry.title.encode("utf-8")).hexdigest(),
            )

    def test_24_repeated_runtime_output_is_deterministic(self):
        first = inspect_real_pdf_toc(self.data)
        second = inspect_real_pdf_toc(self.data)
        self.assertEqual(first, second)
        self.assertEqual(first.to_safe_dict(), second.to_safe_dict())
        self.assertEqual(first.toc_reconciliation_policy, TOC_RECONCILIATION_POLICY)

    def test_25_safe_cli_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory) / "toc.pdf"
            pdf.write_bytes(self.data)
            command = [sys.executable, str(CLI), str(pdf)]
            first = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, check=False
            )
            second = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, check=False
            )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout.encode(), second.stdout.encode())
        self.assertEqual(first.stderr, "")
        parsed = json.loads(first.stdout)
        self.assertEqual(parsed["toc_reconciliation_policy"], TOC_RECONCILIATION_POLICY)
        for entry in PyPdfOutlineAdapter().inspect(self.data).entries:
            self.assertNotIn(entry.title, first.stdout)

    def test_26_no_native_outline_safe_output_is_deterministic(self):
        first = inspect_real_pdf_toc(hierarchy_pdf()).to_safe_dict()
        second = inspect_real_pdf_toc(hierarchy_pdf()).to_safe_dict()
        self.assertEqual(first, second)
        self.assertEqual(first["outline_status"], "no_native_outline")
        self.assertEqual(first["matches"], [])
        self.assertEqual(first["unmatched_outline_entries"], [])

    def test_27_task_014_hierarchy_runtime_remains_functional(self):
        result = inspect_real_pdf_hierarchy(hierarchy_pdf())
        self.assertEqual(result.page_count, 5)
        self.assertEqual(result.materialized_chapter_count, 2)
        self.assertEqual(result.materialized_section_count, 2)
        self.assertEqual(result.materialized_subsection_count, 1)
        self.assertEqual(Counter(item.proposed_level for item in result.candidates), {
            "chapter": 2,
            "section": 2,
            "subsection": 1,
        })


if __name__ == "__main__":
    unittest.main()
