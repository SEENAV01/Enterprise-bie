"""Structural, source-linked math observations; never mathematical truth claims."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.productization.document_intelligence.structural_pdf_fixtures import structural_pdf
from bie.document_intelligence.real_pdf_text_runtime import inspect_real_pdf_text
from bie.qa.math_v2.native_pdf_bridge import inspect_selected_native_pdf_math_line
from bie.qa.release_v2.contracts import ContractError


def fixture(text='x * y + z'):
    return structural_pdf(1, text_pages={0}, text=text)


class NativePdfMathBridgeTests(unittest.TestCase):
    def test_selected_expression_is_bound_to_exact_source(self):
        data = fixture()
        item = inspect_selected_native_pdf_math_line(data, 'p0001-b0001')
        source = inspect_real_pdf_text(data).pages[0].source_linked_blocks[0]
        self.assertEqual(item.source_hash, hashlib.sha256(data).hexdigest())
        self.assertEqual(item.byte_length, len(data))
        self.assertEqual((item.page, item.block_id, item.region_id, item.box),
                         (source.block.page, source.block.block_id, source.region.region_id, source.region.box))
        self.assertEqual(item.text_sha256, hashlib.sha256(source.block.text.encode()).hexdigest())
        self.assertEqual(item.char_count, len(source.block.text))
        self.assertEqual(item.kind, 'expression')
        self.assertEqual(len(item.expression_digests), 1)

    def test_equation_uses_two_native_expression_sides(self):
        item = inspect_selected_native_pdf_math_line(fixture('x + 2 = 4'), 'p0001-b0001')
        self.assertEqual(item.kind, 'equation')
        self.assertEqual(len(item.expression_digests), 2)
        self.assertNotEqual(*item.expression_digests)

    def test_precedence_and_full_consumption_change_the_digest(self):
        a = inspect_selected_native_pdf_math_line(fixture('x * y + z'), 'p0001-b0001')
        b = inspect_selected_native_pdf_math_line(fixture('x * y'), 'p0001-b0001')
        self.assertNotEqual(a.expression_digests, b.expression_digests)

    def test_repeated_safe_observation_is_deterministic(self):
        data = fixture()
        self.assertEqual(inspect_selected_native_pdf_math_line(data, 'p0001-b0001').to_safe_dict(),
                         inspect_selected_native_pdf_math_line(data, 'p0001-b0001').to_safe_dict())

    def test_safe_output_has_no_formula_or_source_text(self):
        result = inspect_selected_native_pdf_math_line(fixture('x + 2 = 4'), 'p0001-b0001').to_safe_dict()
        self.assertNotIn('x + 2', str(result))
        self.assertNotIn('text', result)
        self.assertFalse(result['mathematical_truth_proven'])
        self.assertFalse(result['automatic_formula_detection'])

    def test_upstream_canonical_text_runtime_is_invoked(self):
        data = fixture()
        with patch('bie.qa.math_v2.native_pdf_bridge.inspect_real_pdf_text', wraps=inspect_real_pdf_text) as upstream:
            inspect_selected_native_pdf_math_line(data, 'p0001-b0001')
        upstream.assert_called_once_with(data)

    def test_native_to_qa_adapter_is_invoked(self):
        from bie.qa.math_v2 import native_pdf_bridge as bridge
        with patch.object(bridge, 'import_node', wraps=bridge.import_node) as adapter:
            inspect_selected_native_pdf_math_line(fixture(), 'p0001-b0001')
        adapter.assert_called_once()

    def test_unsupported_parentheses_abstain(self):
        with self.assertRaisesRegex(ContractError, 'UNSUPPORTED_NATIVE_PDF_MATH_SYNTAX'):
            inspect_selected_native_pdf_math_line(fixture('(x + 2)'), 'p0001-b0001')

    def test_unsupported_relation_abstains(self):
        with self.assertRaisesRegex(ContractError, 'UNSUPPORTED_NATIVE_PDF_MATH_SYNTAX|UNSUPPORTED_NATIVE_PDF_MATH_RELATION'):
            inspect_selected_native_pdf_math_line(fixture('x > 2'), 'p0001-b0001')

    def test_incomplete_expression_rejected(self):
        with self.assertRaisesRegex(ContractError, 'UNSUPPORTED_NATIVE_PDF_MATH_SYNTAX'):
            inspect_selected_native_pdf_math_line(fixture('x +'), 'p0001-b0001')

    def test_multiple_equals_rejected(self):
        with self.assertRaisesRegex(ContractError, 'UNSUPPORTED_NATIVE_PDF_MATH_RELATION'):
            inspect_selected_native_pdf_math_line(fixture('x = 2 = 3'), 'p0001-b0001')

    def test_nonexistent_block_cannot_be_fabricated(self):
        with self.assertRaisesRegex(ContractError, 'NATIVE_PDF_MATH_BLOCK_NOT_UNIQUE'):
            inspect_selected_native_pdf_math_line(fixture(), 'p0001-b0002')

    def test_invalid_block_id_rejected(self):
        with self.assertRaisesRegex(ContractError, 'INVALID_NATIVE_PDF_MATH_BLOCK_ID'):
            inspect_selected_native_pdf_math_line(fixture(), '../p0001-b0001')

    def test_blank_page_has_no_selected_math(self):
        with self.assertRaisesRegex(ContractError, 'NATIVE_PDF_MATH_BLOCK_NOT_UNIQUE'):
            inspect_selected_native_pdf_math_line(structural_pdf(1), 'p0001-b0001')

    def test_malformed_pdf_fails_closed(self):
        with self.assertRaises(ValueError):
            inspect_selected_native_pdf_math_line(b'not a PDF', 'p0001-b0001')


if __name__ == '__main__':
    unittest.main()
