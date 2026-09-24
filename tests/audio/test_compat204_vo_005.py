from dataclasses import replace
import unittest
from bie.audio.compat204.contracts import AudioError
from bie.audio.compat204.pronunciation_lexicon import Lexicon
from bie.audio.compat204.acronym_pronunciation import *
from tests.audio.compat204_support import rule

class AcronymTests(unittest.TestCase):
    def test_dna_letters(self):
        p=pronounce_acronym('DNA',language='en',domain='biology',lexicon=Lexicon('l','1',(rule(),)))
        self.assertEqual(p.spoken_text,'dee en ay')
    def test_word_mode(self):
        p=pronounce_acronym('NASA',language='en',domain='space',lexicon=Lexicon('l','1',(rule('NASA',mode='word',spoken='nassa'),)))
        self.assertEqual(p.spoken_text,'nassa');self.assertEqual(p.mode,'word')
    def test_expansion_is_supplied_not_invented(self):
        p=pronounce_acronym('AI',language='en',domain='technology',lexicon=Lexicon('l','1',(rule('AI',mode='expansion',spoken='artificial intelligence'),)))
        self.assertEqual(p.spoken_text,'artificial intelligence')
    def test_unknown_ai_no_guess(self):
        self.assertRaisesRegex(AudioError,'UNKNOWN_ACRONYM',pronounce_acronym,'AI',language='en',domain='technology',lexicon=Lexicon('l','1'))
    def test_dotted_initialism(self):self.assertEqual(spell_initialism('U.S.A.','en'),'you ess ay')
    def test_digits_retained(self):self.assertEqual(spell_initialism('B2B','en'),'bee two bee')
    def test_us_z(self):self.assertEqual(spell_initialism('XYZ','en-US'),'ex why zee')
    def test_india_z(self):self.assertEqual(spell_initialism('XYZ','en-IN'),'ex why zed')
    def test_uk_z(self):self.assertEqual(spell_initialism('XYZ','en-GB'),'ex why zed')
    def test_lowercase_not_initialism(self):self.assertRaisesRegex(AudioError,'SHAPE',spell_initialism,'us','en')
    def test_punctuation_not_silently_discarded(self):self.assertRaisesRegex(AudioError,'SHAPE',spell_initialism,'R&D','en')
    def test_unsupported_language(self):self.assertRaisesRegex(AudioError,'LANGUAGE_UNSUPPORTED',spell_initialism,'DNA','hi')
    def test_candidates_do_not_match_substrings(self):self.assertEqual(acronym_candidates('xDNAy'),())
    def test_candidates_preserve_caps_word_ambiguity(self):self.assertEqual(acronym_candidates('READ DNA.'),((0,4,'READ'),(5,8,'DNA')))
    def test_dotted_candidate_exact(self):self.assertEqual(acronym_candidates('Use U.S.A. now'),((4,10,'U.S.A.'),))
    def test_possessive_not_consumed(self):self.assertEqual(acronym_candidates("DNA's role"),((0,3,'DNA'),))
    def test_singular_letter_not_assumed_acronym(self):self.assertEqual(acronym_candidates('A force F'),())
    def test_domain_disambiguation(self):
        a=rule('MS',mode='expansion',spoken='mass spectrometry',rule_id='a',domain='chemistry')
        b=rule('MS',mode='expansion',spoken='multiple sclerosis',rule_id='b',domain='medicine')
        l=Lexicon('l','1',(a,b))
        self.assertEqual(pronounce_acronym('MS',language='en',domain='chemistry',lexicon=l).spoken_text,'mass spectrometry')
    def test_domain_unknown_not_guess(self):
        l=Lexicon('l','1',(rule('MS',mode='word',spoken='em ess',domain='chemistry'),))
        self.assertRaisesRegex(AudioError,'UNKNOWN',pronounce_acronym,'MS',language='en',domain='other',lexicon=l)
    def test_ipa_survives_word_rule(self):
        r=rule('NASA',mode='word',spoken='nassa',phoneme='ˈnæsə',alphabet='ipa')
        p=pronounce_acronym('NASA',language='en',domain='d',lexicon=Lexicon('l','1',(r,)))
        self.assertEqual(p.phoneme,'ˈnæsə');self.assertEqual(p.alphabet,'ipa')
    def test_rule_source_and_identity(self):
        r=rule();p=pronounce_acronym('DNA',language='en',domain='biology',lexicon=Lexicon('l','1',(r,)))
        self.assertEqual(p.rule_identity,r.identity);self.assertEqual(p.source_refs,r.source_refs)
    def test_cannot_mix_letters_and_alias(self):self.assertRaisesRegex(AudioError,'LETTERS_ALIAS',replace(rule(),spoken='DNA').validate)
    def test_no_audio_claim(self):self.assertFalse(pronounce_acronym('DNA',language='en',domain='d',lexicon=Lexicon('l','1',(rule(),))).audio_generated)

    def test_dotted_tail_candidate(self):self.assertEqual(acronym_candidates('D.N.A'),((0,5,'D.N.A'),))

    def test_explicit_mixed_case_initialism(self):
        l=Lexicon('l','1',(rule('PhD'),))
        self.assertEqual(pronounce_acronym('PhD',language='en',domain='education',lexicon=l).spoken_text,'pee aitch dee')
