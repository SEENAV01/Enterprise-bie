"""Regression controls for the Section 16 native expression-parser repair."""
import unittest

from bie.math_intelligence.expression_ast import Node, parse_expression
from bie.qa.math_v2.adapters import import_node
from bie.qa.math_v2.expression import parse as independent_parse
from bie.qa.release_v2.contracts import ContractError


class NativeMathParserRepairTests(unittest.TestCase):
    def test_previously_truncated_tail_is_present(self):
        node = parse_expression(['x', '*', 'y', '+', 'z'])
        self.assertEqual(node.value, '+')
        self.assertEqual(node.children[0].value, '*')
        self.assertEqual(node.children[1], Node('atom', 'z'))
        self.assertEqual(import_node(node, 'x*y+z'), independent_parse('x*y+z'))

    def test_right_associative_power(self):
        node = parse_expression(['x', '^', 'y', '^', 'z'])
        self.assertEqual(node.value, '^')
        self.assertEqual(node.children[1].value, '^')

    def test_left_associative_subtraction(self):
        node = parse_expression(['x', '-', 'y', '-', 'z'])
        self.assertEqual(node.value, '-')
        self.assertEqual(node.children[0].value, '-')

    def test_parentheses_are_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            parse_expression(['(', 'x', '+', 'y', ')'])

    def test_trailing_atom_rejected(self):
        with self.assertRaises(ValueError):
            parse_expression(['x', '+', 'y', 'z'])

    def test_missing_right_operand_rejected(self):
        with self.assertRaises(ValueError):
            parse_expression(['x', '+'])

    def test_operator_cannot_be_an_atom(self):
        with self.assertRaises(ValueError):
            parse_expression(['x', '+', '*', 'y'])

    def test_multi_token_atom_rejected(self):
        with self.assertRaises(ValueError):
            parse_expression(['x+y'])

    def test_nonlist_and_boolean_tokens_rejected(self):
        for tokens in (('x',), ['x', '+', True], []):
            with self.subTest(tokens=tokens), self.assertRaises(ValueError):
                parse_expression(tokens)

    def test_independent_adapter_rejects_source_mismatch(self):
        node = parse_expression(['x', '+', 'y'])
        with self.assertRaisesRegex(ContractError, 'NATIVE_SOURCE_PARSE_MISMATCH'):
            import_node(node, 'x+y+z')


if __name__ == '__main__':
    unittest.main()
