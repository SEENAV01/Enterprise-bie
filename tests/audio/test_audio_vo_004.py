import unittest
from dataclasses import replace
from bie.audio.symbol_pronunciation import *
from bie.audio.common import AudioError

class SymbolPronunciationTests(unittest.TestCase):
    def test_comparison_default(self):self.assertEqual(pronounce_symbol('≤','en',standard_symbols()).spoken,'less than or equal to')
    def test_negation_retained(self):self.assertIn('not equal',pronounce_symbol('≠','en',standard_symbols()).spoken)
    def test_hindi_convention(self):self.assertEqual(pronounce_symbol('%','hi',standard_symbols('hi')).spoken,'प्रतिशत')
    def test_ambiguous_mu_not_guessed(self):
        t=make_table('v',(SymbolRule('µ','en','micro','micro',('e1',)),SymbolRule('µ','en','coefficient','mu',('e2',))))
        with self.assertRaisesRegex(AudioError,'SENSE_REQUIRED'):pronounce_symbol('µ','en',t)
        self.assertEqual(pronounce_symbol('µ','en',t,sense='coefficient').spoken,'mu')
    def test_unit_vs_variable_case(self):
        t=make_table('v',(SymbolRule('N','en','unit','newtons',('source:unit',)),SymbolRule('n','en','variable','en',('source:variable',))))
        self.assertNotEqual(pronounce_symbol('N','en',t).spoken,pronounce_symbol('n','en',t).spoken)
    def test_domain_exact(self):
        t=make_table('v',(SymbolRule('m','en','symbol','em',('e',)),SymbolRule('m','en','unit','metres',('e',),'physics')))
        self.assertEqual(pronounce_symbol('m','en',t,domain='physics').spoken,'metres')
    def test_unknown_symbol_block(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_symbol('°','en',standard_symbols())
    def test_degree_requires_context(self):
        t=make_table('v',(SymbolRule('°','en','angle','degrees',('e',)),SymbolRule('°','en','temperature','degrees Celsius',('e',))))
        with self.assertRaisesRegex(AudioError,'SENSE_REQUIRED'):pronounce_symbol('°','en',t)
    def test_wrong_language_block(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_symbol('≤','hi',standard_symbols())
    def test_wrong_sense_block(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_symbol('%','en',standard_symbols(),sense='modulo')
    def test_no_unit_inference(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_symbol('kg','en',standard_symbols())
    def test_explicit_compound_unit(self):
        t=make_table('v',(SymbolRule('m/s²','en','acceleration','metres per second squared',('book:p1',)),))
        r=pronounce_symbol('m/s²','en',t);self.assertEqual(r.surface,'m/s²');self.assertEqual(r.source_refs,('book:p1',))
    def test_duplicates(self):
        r=SymbolRule('x','en','variable','ex',('e',))
        with self.assertRaisesRegex(AudioError,'DUPLICATE'):make_table('v',(r,r))
    def test_empty_evidence(self):
        with self.assertRaises(AudioError):SymbolRule('x','en','variable','ex',())
    def test_no_malformed_table(self):
        with self.assertRaises(AudioError):make_table('v',[])
    def test_source_hash_versioned(self):
        a=standard_symbols();b=replace(a,version='changed');self.assertNotEqual(a.fingerprint(),b.fingerprint())
    def test_deterministic_order(self):
        rs=standard_symbols().rules;self.assertEqual(make_table('v',rs).fingerprint(),make_table('v',rs[::-1]).fingerprint())
    def test_invalid_language(self):
        with self.assertRaises(AudioError):SymbolRule('x','en us','var','ex',('e',))
