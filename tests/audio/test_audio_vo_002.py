import unittest,xml.etree.ElementTree as ET
from dataclasses import replace,FrozenInstanceError
from bie.audio.lexicon import *
from bie.audio.common import AudioError

def entry(surface='Coulomb',spoken='koo lom',**kw):return Lexeme(kw.pop('entry_id','e1'),surface,kw.pop('language','en'),spoken,('source:lexicon',),**kw)

class LexiconTests(unittest.TestCase):
    def test_alias_applies(self):self.assertEqual(resolve(build_lexicon('v1',(entry(),)),'Coulomb','en').spoken,'koo lom')
    def test_case_sensitive_default(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):resolve(build_lexicon('v',(entry(),)),'coulomb','en')
    def test_case_insensitive_explicit(self):self.assertEqual(resolve(build_lexicon('v',(entry(case_sensitive=False),)),'COULOMB','en').surface,'COULOMB')
    def test_longest_phrase(self):
        lex=build_lexicon('v',(entry('New Delhi','new delhi'),entry('Delhi','dilli',entry_id='e2')))
        self.assertEqual([(a,b) for a,b,r in matches(lex,'New Delhi Delhi','en')],[(0,9),(10,15)])
    def test_no_subword(self):self.assertEqual(matches(build_lexicon('v',(entry('ion','eye on'),)),'action lion','en'),())
    def test_unicode_combining_boundary(self):self.assertEqual(matches(build_lexicon('v',(entry('e','ee'),)),'e\u0301 e','en')[0][:2],(3,4))
    def test_hindi_offsets(self):
        lex=build_lexicon('v',(entry('आवेश','आवेश',language='hi'),));self.assertEqual(matches(lex,'यह आवेश है','hi')[0][:2],(3,7))
    def test_language_no_silent_fallback(self):
        with self.assertRaisesRegex(AudioError,'NOT_FOUND'):resolve(build_lexicon('v',(entry(),)),'Coulomb','en-IN')
    def test_primary_fallback_explicit(self):self.assertEqual(resolve(build_lexicon('v',(entry(),)),'Coulomb','en-IN',allow_primary_language=True).spoken,'koo lom')
    def test_regional_precedence(self):
        lex=build_lexicon('v',(entry(),entry(spoken='regional',entry_id='e2',language='en-IN')))
        self.assertEqual(resolve(lex,'Coulomb','en-IN',allow_primary_language=True).spoken,'regional')
    def test_domain_override(self):
        lex=build_lexicon('v',(entry(),entry(spoken='physics form',entry_id='e2',domain='physics')))
        self.assertEqual(resolve(lex,'Coulomb','en',domain='physics').spoken,'physics form')
    def test_homograph_requires_sense(self):
        lex=build_lexicon('v',(entry('lead','led',sense='metal'),entry('lead','leed',entry_id='e2',sense='guide')))
        with self.assertRaisesRegex(AudioError,'SENSE_REQUIRED'):resolve(lex,'lead','en')
        self.assertEqual(resolve(lex,'lead','en',sense='metal').spoken,'led')
    def test_duplicate_scope_reject(self):
        with self.assertRaisesRegex(AudioError,'DUPLICATE_LEXICON_SCOPE'):build_lexicon('v',(entry(),entry(entry_id='e2')))
    def test_duplicate_id_reject(self):
        with self.assertRaisesRegex(AudioError,'DUPLICATE_LEXICON_ID'):build_lexicon('v',(entry(),entry('Ohm')))
    def test_case_rule_ambiguity(self):
        lex=build_lexicon('v',(entry(),entry(spoken='other',entry_id='e2',case_sensitive=False)))
        with self.assertRaisesRegex(AudioError,'AMBIGUOUS'):resolve(lex,'Coulomb','en')
    def test_no_blank_pronunciation(self):
        with self.assertRaises(AudioError):entry(spoken=' ')
    def test_phonemes_preserved_as_requirement(self):
        r=resolve(build_lexicon('v',(entry(spoken='kuːlɒm',mode='PHONEME',alphabet='ipa'),)),'Coulomb','en')
        self.assertEqual(r.phonemes,'kuːlɒm');self.assertEqual(r.spoken,'Coulomb')
    def test_unknown_alphabet(self):
        with self.assertRaises(AudioError):entry(mode='PHONEME',alphabet='arbitrary')
    def test_pls_xml_escape(self):
        lex=build_lexicon('v',(entry('A&B','a < b'),));s=export_pls(lex,'en');root=ET.fromstring(s)
        self.assertIn('&amp;',s);self.assertIn('&lt;',s);self.assertEqual(root[0][0].text,'A&B');self.assertEqual(root[0][1].text,'a < b')
    def test_pls_ambiguous_export_reject(self):
        with self.assertRaisesRegex(AudioError,'SENSE_REQUIRED'):export_pls(build_lexicon('v',(entry('lead','led',sense='metal'),)),'en')
    def test_order_independent_identity(self):
        a,b=entry(),entry('Ohm','ohm',entry_id='e2');self.assertEqual(build_lexicon('v',(a,b)).fingerprint(),build_lexicon('v',(b,a)).fingerprint())
    def test_version_invalidates_identity(self):self.assertNotEqual(build_lexicon('v1',(entry(),)).fingerprint(),build_lexicon('v2',(entry(),)).fingerprint())
    def test_evidence_required(self):
        with self.assertRaises(AudioError):replace(entry(),evidence_refs=())
    def test_frozen_data(self):
        with self.assertRaises(FrozenInstanceError):entry().pronunciation='other'
