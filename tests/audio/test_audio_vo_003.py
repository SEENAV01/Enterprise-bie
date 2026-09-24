import unittest
from bie.audio.math_pronunciation import *
from bie.audio.common import AudioError

class MathPronunciationTests(unittest.TestCase):
    def test_simple_relation(self):self.assertEqual(pronounce_math('x+2=3').reading.spoken,'x plus two equals three')
    def test_nested_fraction_structure(self):
        r=pronounce_math(r'\frac{a+b}{\sqrt{x^2+1}}');self.assertIn('numerator a plus b denominator square root',r.reading.spoken);self.assertEqual(r.ast.kind,'fraction')
    def test_negative_power_precedence(self):
        a=parse_math('-x^2');self.assertEqual(a.kind,'unary');self.assertEqual(a.children[0].kind,'script')
    def test_grouped_negative(self):
        a=parse_math('(-x)^2');self.assertEqual(a.kind,'script');self.assertEqual(a.children[0].kind,'group')
    def test_right_side_fraction_group(self):self.assertIn('denominator b plus c',pronounce_math('a/(b+c)').reading.spoken)
    def test_left_associative_fraction(self):self.assertEqual(parse_math('a/b/c').children[0].kind,'fraction')
    def test_numeric_implicit_multiplication(self):self.assertEqual(pronounce_math('2x').reading.spoken,'two times x')
    def test_function_application_not_guessed(self):
        with self.assertRaisesRegex(AudioError,'JUXTAPOSITION'):pronounce_math('f(x)')
    def test_multi_letter_not_split_into_product(self):
        with self.assertRaisesRegex(AudioError,'MULTILETTER'):pronounce_math('sin(x)')
    def test_function_explicit_command(self):self.assertEqual(pronounce_math(r'\sin(x)').reading.spoken,'sine of x end function')
    def test_greek_unicode_command_same_reading(self):self.assertEqual(pronounce_math('π+α').reading.spoken,pronounce_math(r'\pi+\alpha').reading.spoken)
    def test_comparison_semantics(self):
        for s,word in [('x≤2','less than or equal to'),('x≠2','not equal to'),('x≈2','approximately')]:
            with self.subTest(s=s):self.assertIn(word,pronounce_math(s).reading.spoken)
    def test_subscript_not_power(self):self.assertEqual(pronounce_math('x_1').reading.spoken,'x subscript one end subscript')
    def test_negative_exponent_group(self):self.assertIn('power negative two end power',pronounce_math('x^{-2}').reading.spoken)
    def test_multidigit_script_requires_group(self):
        with self.assertRaisesRegex(AudioError,'SCRIPT_GROUP'):pronounce_math('x^23')
        self.assertIn('twenty three',pronounce_math('x^{23}').reading.spoken)
    def test_trailing_tokens_rejected(self):
        with self.assertRaises(AudioError):pronounce_math('x+2)')
    def test_no_ignored_macro(self):
        for x in (r'\input{secret}',r'\href{bad}{x}',r'\text{x}',r'\sum{x}'):
            with self.subTest(x=x),self.assertRaisesRegex(AudioError,'UNSUPPORTED_MATH_COMMAND'):pronounce_math(x)
    def test_empty_unbalanced_and_wrong_fraction(self):
        for x in ('','()','(x}',r'\frac{x}',r'\sqrt x','x+','x^^2'):
            with self.subTest(x=x),self.assertRaises((AudioError,ValueError)):pronounce_math(x)
    def test_depth_budget(self):
        with self.assertRaisesRegex(AudioError,'DEPTH'):pronounce_math('('*40+'x'+')'*40)
    def test_decimal_and_leading_zeros_preserved(self):self.assertEqual(pronounce_math('02.50').reading.spoken,'digits zero two point five zero')
    def test_scientific_notation(self):self.assertIn('times ten to the power negative three',pronounce_math('1.20e-3').reading.spoken)
    def test_hindi_reading(self):self.assertEqual(pronounce_math('x^2+2','hi').reading.spoken,'एक्स का वर्ग धन दो')
    def test_unknown_locale_rejected(self):
        with self.assertRaisesRegex(AudioError,'LANGUAGE_NOT_SUPPORTED'):pronounce_math('x','xx')
    def test_full_span_source_binding(self):
        s=r'\frac{x}{y}';r=pronounce_math(s,evidence_refs=('book:p2',));self.assertEqual(r.expression,s);self.assertEqual((r.ast.start,r.ast.end),(0,len(s)));self.assertEqual(r.reading.source_refs,('book:p2',));self.assertFalse(r.mathematical_validity_verified)
    def test_hindi_large_integer_digit_mode(self):self.assertEqual(pronounce_math('123','hi').reading.spoken,'अंक एक दो तीन')
    def test_power_grouping_and_no_cas(self):
        r=pronounce_math('x^2+x^2');self.assertEqual(r.reading.spoken,'x squared plus x squared');self.assertFalse(r.audio_verified)
