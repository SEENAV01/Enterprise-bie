import unittest
from bie.audio.compat204.contracts import AudioError
from bie.audio.compat204.math_pronunciation import *

class MathTests(unittest.TestCase):
    def test_energy_equation(self):
        self.assertEqual(pronounce_math('E=mc^2').spoken_text,'capital e equals m times c squared')
    def test_fraction_scope(self):
        self.assertEqual(pronounce_math(r'\frac{a+b}{c-d}').spoken_text,'start fraction numerator a plus b denominator c minus d end fraction')
    def test_nested_fraction_scope(self):
        p=pronounce_math(r'\frac{a}{\frac{b}{c}}');self.assertEqual(p.spoken_text.count('start fraction'),2);self.assertEqual(p.spoken_text.count('end fraction'),2)
    def test_unary_precedence(self):
        p=pronounce_math('-x^2');self.assertEqual(p.tree.kind,'unary');self.assertEqual(p.tree.children[0].kind,'power')
    def test_grouped_negative_differs(self):
        a,b=pronounce_math('-x^2'),pronounce_math('(-x)^2');self.assertNotEqual(a.tree,b.tree);self.assertNotEqual(a.spoken_text,b.spoken_text)
    def test_root_scope(self):
        self.assertEqual(pronounce_math(r'\sqrt{x+1}').spoken_text,'square root of x plus one end root')
    def test_indexed_root(self):
        self.assertIn('root with index three',pronounce_math(r'\sqrt[3]{x}').spoken_text)
    def test_subscript_not_lost(self):
        self.assertIn('subscript one end subscript',pronounce_math(r'q_1').spoken_text)
    def test_subscript_power(self):
        self.assertEqual(pronounce_math(r'x_1^2').spoken_text,'x subscript one end subscript squared')
    def test_comparison_not_equivalence(self):
        self.assertEqual(pronounce_math('a<=b').spoken_text,'a is less than or equal to b')
    def test_inequality(self):
        self.assertIn('is not equal to',pronounce_math(r'x\neq y').spoken_text)
    def test_approximation_retained(self):
        self.assertIn('approximately',pronounce_math(r'x\approx y').spoken_text)
    def test_greek_latex(self):
        self.assertEqual(pronounce_math(r'\alpha+\beta').spoken_text,'alpha plus beta')
    def test_greek_unicode(self):
        self.assertEqual(pronounce_math('α+β').spoken_text,'alpha plus beta')
    def test_unicode_minus(self):
        self.assertEqual(pronounce_math('−2').spoken_text,'negative two')
    def test_decimal_precision(self):
        self.assertEqual(number_words('0.050'),'zero point zero five zero')
    def test_leading_zeros(self):
        self.assertEqual(number_words('007'),'zero zero seven')
    def test_large_integer_no_float_rounding(self):
        raw='12345678901234567890';self.assertEqual(number_words(raw),' '.join(DIGITS[int(x)] for x in raw))
    def test_vector_accent(self):
        self.assertEqual(pronounce_math(r'\vec{F}').spoken_text,'vector capital f end accent')
    def test_sum_limits_scope(self):
        self.assertEqual(pronounce_math(r'\sum_{i=1}^{n}{i^2}').spoken_text,'sum from i equals one to n of i squared end sum')
    def test_product_limits(self):
        self.assertTrue(pronounce_math(r'\prod_{i=1}^{n}{i}').spoken_text.startswith('product from i equals one'))
    def test_function_argument_scope(self):
        self.assertEqual(pronounce_math(r'\sin{x+y}').spoken_text,'sine of x plus y end function')
    def test_function_ungrouped_rejected(self):
        self.assertRaisesRegex(AudioError,'FUNCTION_GROUP',pronounce_math,r'\sin x')
    def test_ambiguous_function_rejected(self):
        self.assertRaisesRegex(AudioError,'FUNCTION_AMBIGUITY',pronounce_math,'f(x)')
    def test_unknown_command_rejected(self):
        self.assertRaisesRegex(AudioError,'MATH_UNSUPPORTED',pronounce_math,r'\unknown{x}')
    def test_no_eval_or_file_command(self):
        self.assertRaises(AudioError,pronounce_math,r'\input{/etc/passwd}')
    def test_unmatched_bracket(self):
        self.assertRaisesRegex(AudioError,'MATH_SYNTAX',pronounce_math,'(x+y')
    def test_empty_denominator(self):
        self.assertRaises(AudioError,pronounce_math,r'\frac{x}{}')
    def test_trailing_tokens_not_discarded(self):
        self.assertRaisesRegex(AudioError,'TRAILING',pronounce_math,'x}')
    def test_ambiguous_power_chain(self):
        self.assertRaisesRegex(AudioError,'AMBIGUOUS_MATH_SCRIPT',pronounce_math,'x^2^3')
    def test_bounded_recursion(self):
        self.assertRaisesRegex(AudioError,'DEPTH',pronounce_math,'('*30+'x'+')'*30)
    def test_bounded_input(self):
        self.assertRaisesRegex(AudioError,'INVALID_TEXT',pronounce_math,'x'*4097)
    def test_bounded_tokens(self):
        self.assertRaisesRegex(AudioError,'TOKEN_LIMIT',pronounce_math,'x+'*300+'x')
    def test_unsupported_locale_not_english_fallback(self):
        self.assertRaisesRegex(AudioError,'LANGUAGE_UNSUPPORTED',pronounce_math,'x+1',language='hi')
    def test_flags_not_proof_or_audio(self):
        p=pronounce_math('2=3');self.assertFalse(p.mathematical_truth_verified);self.assertFalse(p.audio_generated)
    def test_expression_identity_preserved(self):
        p=pronounce_math('a + b');self.assertEqual(p.original_expression,'a + b');self.assertNotEqual(p.identity,pronounce_math('a+b').identity)
    def test_chained_relation_retained(self):
        self.assertEqual(pronounce_math('0<x<1').spoken_text,'zero is less than x is less than one')
    def test_syntax_whitespace_does_not_change_spoken_math(self):
        self.assertEqual(pronounce_math(r'x\, + y').spoken_text,pronounce_math('x+y').spoken_text)

    def test_ascii_scientific_notation(self):
        self.assertEqual(pronounce_math('1e-3').spoken_text,'one times ten to the power of negative three end power')
    def test_plain_sine_not_multiplication(self):
        self.assertEqual(pronounce_math('sin(x)').spoken_text,'sine of x end function')
    def test_multidigit_unbraced_power_not_misread(self):
        self.assertRaisesRegex(AudioError,'SCRIPT_BRACES',pronounce_math,'x^23')
    def test_multidigit_braced_power(self):
        self.assertEqual(pronounce_math('x^{23}').spoken_text,'x to the power of twenty three end power')
    def test_unbraced_multidigit_root_not_misread(self):
        self.assertRaisesRegex(AudioError,'ROOT_BRACES',pronounce_math,r'\sqrt12')
