import unittest
from dataclasses import replace
from bie.audio.acronym_pronunciation import *
from bie.audio.common import AudioError

class AcronymPronunciationTests(unittest.TestCase):
    def table(self,*rules):return make_acronyms('v',tuple(rules))
    def test_initialism_actual_letters(self):
        t=self.table(AcronymRule('DNA','en','LETTERS',('e',)));self.assertEqual(pronounce_acronym('DNA','en',t).spoken,'dee en ay')
    def test_word_mode(self):
        t=self.table(AcronymRule('NASA','en','WORD',('e',),'nasa'));self.assertEqual(pronounce_acronym('NASA','en',t).spoken,'nasa')
    def test_expansion_mode(self):
        t=self.table(AcronymRule('GDP','en','EXPANSION',('book:p1',),'gross domestic product'));self.assertEqual(pronounce_acronym('GDP','en',t).spoken,'gross domestic product')
    def test_hindi_letters(self):
        t=self.table(AcronymRule('AI','hi','LETTERS',('e',)));self.assertEqual(pronounce_acronym('AI','hi',t).spoken,'ए आई')
    def test_dotted_initialism(self):
        t=self.table(AcronymRule('U.S.A.','en','LETTERS',('e',)));self.assertEqual(pronounce_acronym('U.S.A.','en',t).spoken,'you ess ay')
    def test_not_lowercase_word_us(self):
        t=self.table(AcronymRule('US','en','LETTERS',('e',)))
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_acronym('us','en',t)
    def test_no_invented_expansion(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_acronym('XYZ','en',self.table())
    def test_no_guess_word_vs_letters(self):
        t=self.table(AcronymRule('NASA','en','LETTERS',('e',)));self.assertEqual(pronounce_acronym('NASA','en',t).spoken,'en ay ess ay')
    def test_conflicting_modes(self):
        with self.assertRaisesRegex(AudioError,'CONFLICTING'):self.table(AcronymRule('AI','en','LETTERS',('e',)),AcronymRule('AI','en','WORD',('e',),'ai'))
    def test_domain_specific_expansion(self):
        t=self.table(AcronymRule('ML','en','LETTERS',('e',)),AcronymRule('ML','en','EXPANSION',('e2',),'machine learning','computing'))
        self.assertEqual(pronounce_acronym('ML','en',t,domain='computing').spoken,'machine learning')
    def test_bad_surface(self):
        for s in ('aI','A','A1','A.','A I','NASA<script>'):
            with self.subTest(s=s),self.assertRaises(AudioError):AcronymRule(s,'en','LETTERS',('e',))
    def test_no_letters_override(self):
        with self.assertRaises(AudioError):AcronymRule('AI','en','LETTERS',('e',),'artificial intelligence')
    def test_expansion_evidence_required(self):
        with self.assertRaises(AudioError):AcronymRule('AI','en','EXPANSION',(),'artificial intelligence')
    def test_blank_word_reject(self):
        with self.assertRaises(AudioError):AcronymRule('AI','en','WORD',('e',),' ')
    def test_language_no_silent_fallback(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):pronounce_acronym('AI','hi',self.table(AcronymRule('AI','en','LETTERS',('e',))))
    def test_phonology_unsupported_letter_language(self):
        with self.assertRaisesRegex(AudioError,'LETTER_LANGUAGE'):pronounce_acronym('AI','fr',self.table(AcronymRule('AI','fr','LETTERS',('e',))))
    def test_revision_hash_changes(self):
        r=AcronymRule('AI','en','LETTERS',('e',));self.assertNotEqual(self.table(r).fingerprint(),self.table(replace(r,mode='EXPANSION',reading='artificial intelligence')).fingerprint())
    def test_table_order_deterministic(self):
        a,b=AcronymRule('AI','en','LETTERS',('e',)),AcronymRule('DNA','en','LETTERS',('e',));self.assertEqual(self.table(a,b).fingerprint(),self.table(b,a).fingerprint())
