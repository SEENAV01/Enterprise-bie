import unittest
from bie.audio.compat204.contracts import AudioError
from bie.audio.compat204.symbol_pronunciation import *
from bie.audio.compat204.pronunciation_lexicon import Lexicon
from tests.audio.compat204_support import rule

class SymbolTests(unittest.TestCase):
    def say(self,s,role,**kw):return pronounce_symbol(s,role=role,language=kw.pop('language','en'),domain='physics',**kw)
    def test_mu_name(self):self.assertEqual(self.say('μ','greek_name').spoken_text,'mu')
    def test_mu_prefix(self):self.assertEqual(self.say('μ','si_prefix').spoken_text,'micro')
    def test_micro_sign(self):self.assertEqual(self.say('µ','si_prefix').spoken_text,'micro')
    def test_multiplication(self):self.assertEqual(self.say('×','multiplication').spoken_text,'times')
    def test_dimension(self):self.assertEqual(self.say('×','dimensions').spoken_text,'by')
    def test_minus(self):self.assertEqual(self.say('-','minus').spoken_text,'minus')
    def test_range(self):self.assertEqual(self.say('-','range').spoken_text,'to')
    def test_division(self):self.assertEqual(self.say('/','division').spoken_text,'divided by')
    def test_unit_per(self):self.assertEqual(self.say('/','per').spoken_text,'per')
    def test_temperature(self):self.assertEqual(self.say('°C','temperature').spoken_text,'degrees Celsius')
    def test_rupee(self):self.assertEqual(self.say('₹','currency').spoken_text,'rupees')
    def test_delta_change(self):self.assertEqual(self.say('Δ','change').spoken_text,'change in')
    def test_delta_name(self):self.assertEqual(self.say('Δ','greek_name').spoken_text,'capital delta')
    def test_omega_unit(self):self.assertEqual(self.say('Ω','unit').spoken_text,'ohms')
    def test_omega_name(self):self.assertEqual(self.say('Ω','greek_name').spoken_text,'capital omega')
    def test_arrow_direction(self):self.assertEqual(self.say('→','direction').spoken_text,'to')
    def test_arrow_limit(self):self.assertEqual(self.say('→','limit').spoken_text,'tends to')
    def test_blank_role_rejected(self):self.assertRaisesRegex(AudioError,'INVALID_TEXT',self.say,'μ','')
    def test_wrong_role_rejected(self):self.assertRaisesRegex(AudioError,'ROLE_UNSUPPORTED',self.say,'μ','ohms')
    def test_unknown_symbol_rejected(self):self.assertRaisesRegex(AudioError,'ROLE_UNSUPPORTED',self.say,'☯','name')
    def test_locale_no_silent_fallback(self):self.assertRaisesRegex(AudioError,'LANGUAGE_UNSUPPORTED',self.say,'μ','greek_name',language='hi')
    def test_exact_locale_rule_supported(self):
        l=Lexicon('l','1',(rule('μ','symbol','alias','म्यू',role='greek_name',language='hi'),))
        self.assertEqual(self.say('μ','greek_name',language='hi',lexicon=l).spoken_text,'म्यू')
    def test_rule_identity_source_preserved(self):
        r=rule('μ','symbol','alias','moo',role='greek_name');l=Lexicon('l','1',(r,));p=self.say('μ','greek_name',lexicon=l)
        self.assertEqual(p.rule_identity,r.identity);self.assertEqual(p.source_refs,r.source_refs)
    def test_explicit_unknown_rule_does_not_fallback(self):
        self.assertRaisesRegex(AudioError,'EXPLICIT_RULE',self.say,'μ','greek_name',lexicon=Lexicon('l','1'),rule_id='missing')
    def test_policy_identity_separates_meanings(self):self.assertNotEqual(self.say('μ','greek_name').rule_identity,self.say('μ','si_prefix').rule_identity)
    def test_pronunciation_not_semantic_verification(self):self.assertFalse(self.say('⇒','implication').interpretation_verified)
    def test_no_audio(self):self.assertFalse(self.say('%','percentage').audio_generated)
