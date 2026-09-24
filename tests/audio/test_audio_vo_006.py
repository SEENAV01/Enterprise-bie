from dataclasses import replace
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.multilingual_terms import LanguageTerm,apply_languages
from bie.audio.preparation_bridge import from_v144
from tests.audio.audio_test_support import utterance,empty_options

class Multilingual(unittest.TestCase):
    def setUp(self):
        self.u=utterance('यह photosynthesis का उदाहरण है।','hi');self.p=from_v144((self.u,),**empty_options('hi'))
        a=self.u.text.index('photosynthesis');self.t=LanguageTerm(self.u.utterance_id,self.u.fingerprint(),a,a+14,'photosynthesis','photosynthesis','en',('source:term',),'term:one')
    def test_switch_keeps_original(self):
        out=apply_languages(self.p,(self.t,));self.assertEqual(out.segments[0].display_text,self.u.text)
    def test_switch_keeps_speech(self):self.assertEqual(apply_languages(self.p,(self.t,)).segments[0].spoken_text,self.p.segments[0].spoken_text)
    def test_switch_has_real_language_runs(self):self.assertEqual(apply_languages(self.p,(self.t,)).segments[0].languages,('en','hi'))
    def test_exact_term_refs(self):
        s=apply_languages(self.p,(self.t,)).segments[0].spans[1];self.assertIn('source:term',s.source_refs);self.assertEqual(s.language,'en')
    def test_no_term_does_not_guess(self):self.assertEqual(apply_languages(self.p,()).segments[0].languages,('hi',))
    def test_repeatable(self):self.assertEqual(apply_languages(self.p,(self.t,)),apply_languages(self.p,(self.t,)))
    def test_identity_changes(self):self.assertNotEqual(apply_languages(self.p,(self.t,)).fingerprint(),self.p.fingerprint())
    def test_stale_utterance(self):
        with self.assertRaisesRegex(AudioError,'STALE_LANGUAGE_TERM'):apply_languages(self.p,(replace(self.t,utterance_fingerprint=fingerprint('old')),))
    def test_stale_plan(self):
        with self.assertRaisesRegex(AudioError,'STALE_LANGUAGE_PLAN'):apply_languages(self.p,(self.t,),expected_plan=fingerprint('old'))
    def test_wrong_surface(self):
        with self.assertRaisesRegex(AudioError,'LANGUAGE_TERM_TEXT'):apply_languages(self.p,(replace(self.t,original='PHOTOSYNTHESIS'),))
    def test_wrong_reading_not_translation(self):
        with self.assertRaisesRegex(AudioError,'SPEECH_MISMATCH'):apply_languages(self.p,(replace(self.t,expected_spoken='something else'),))
    def test_unknown_utterance(self):
        with self.assertRaisesRegex(AudioError,'UNKNOWN_LANGUAGE_TERM'):apply_languages(self.p,(replace(self.t,utterance_id='absent'),))
    def test_duplicate_decision(self):
        with self.assertRaisesRegex(AudioError,'DUPLICATE_LANGUAGE_DECISION'):apply_languages(self.p,(self.t,self.t))
    def test_overlapping(self):
        with self.assertRaisesRegex(AudioError,'OVERLAPPING'):apply_languages(self.p,(self.t,replace(self.t,decision_id='different')))
    def test_missing_provenance(self):
        with self.assertRaises(AudioError):replace(self.t,evidence_refs=())
    def test_boolean_offset(self):
        with self.assertRaises(AudioError):replace(self.t,start=True)
    def test_invalid_locale(self):
        with self.assertRaises(AudioError):replace(self.t,spoken_language='--voice=other')
    def test_bound_source_length(self):
        with self.assertRaises(AudioError):replace(self.t,end=self.t.end+1)
    def test_review_preserved(self):
        p=replace(self.p,review_reasons=('UPSTREAM_REVIEW',));out=apply_languages(p,(self.t,));self.assertEqual(out.review_reasons,p.review_reasons)
    def test_alias_language_preserved(self):
        from bie.audio.lexicon import build_lexicon,Lexeme
        opt=empty_options('hi');opt['lexicon']=build_lexicon('terms',(Lexeme('term:p','photosynthesis','hi','photo synthesis',('source:term',)),))
        p=from_v144((self.u,),**opt);out=apply_languages(p,(replace(self.t,expected_spoken='photo synthesis'),));self.assertIn('photo synthesis',out.segments[0].spoken_text)
