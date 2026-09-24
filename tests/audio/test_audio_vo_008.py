from dataclasses import replace
import unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.voice_selection import *
from bie.audio.tts_contract import *
from tests.audio.tts_test_support import plan,TestProvider

class VoiceSelection(unittest.TestCase):
    def setUp(self):self.p=plan();self.provider=TestProvider();self.c=self.provider.catalog();self.policy=SelectionPolicy(('fixture-provider',),('fixture',))
    def choose(self,**kw):return select_voices(self.p,self.c,kw.pop('policy',self.policy),**kw)
    def test_deterministic_selection(self):self.assertEqual(self.choose(),self.choose())
    def test_one_voice_for_persona(self):self.assertEqual(len(self.choose().personas),1)
    def test_default_choice_is_declared(self):self.assertEqual(self.choose().personas[0].voice,self.c.voices[0])
    def test_provider_allowlist(self):
        with self.assertRaisesRegex(AudioError,'NO_COMPATIBLE'):self.choose(policy=SelectionPolicy(('unconfigured',),('fixture',)))
    def test_neural_quality_not_downgraded(self):
        with self.assertRaisesRegex(AudioError,'NO_COMPATIBLE'):self.choose(policy=SelectionPolicy(('fixture-provider',),('neural',)))
    def test_phoneme_requirements_no_fallback(self):
        span=replace(self.p.segments[0].spans[0],kind='TERM',phonemes='test',alphabet='ipa');s=replace(self.p.segments[0],spans=(span,));p=replace(self.p,segments=(s,))
        with self.assertRaisesRegex(AudioError,'NO_COMPATIBLE'):select_voices(p,self.c,self.policy)
    def test_preferred_voice(self):
        other=replace(self.c.voices[0],voice_id='fixture-other');self.c=VoiceCatalog('1',tuple(sorted((*self.c.voices,other),key=lambda v:v.voice_id)))
        s=self.choose(policy=replace(self.policy,preferred_voices=('fixture-other',)));self.assertEqual(s.personas[0].voice,other)
    def test_prior_voice_continuity(self):
        initial=self.choose();other=replace(self.c.voices[0],voice_id='fixture-better');self.c=VoiceCatalog('2',tuple(sorted((*self.c.voices,other),key=lambda v:v.voice_id)))
        s=self.choose(policy=replace(self.policy,preferred_voices=('fixture-better',)),prior=initial);self.assertEqual(s.personas[0].voice,initial.personas[0].voice)
    def test_missing_prior_voice_blocked(self):
        old=self.choose();self.c=VoiceCatalog('2',(replace(self.c.voices[0],model_revision='new'),))
        with self.assertRaisesRegex(AudioError,'CONTINUITY'):self.choose(prior=old)
    def test_stale_source_selection(self):
        s=self.choose();p=replace(self.p,preparation_fingerprint=fingerprint('revised'))
        with self.assertRaisesRegex(AudioError,'STALE_VOICE'):requests_for(p,self.c,s)
    def test_stale_catalog_selection(self):
        s=self.choose()
        with self.assertRaisesRegex(AudioError,'STALE_VOICE'):requests_for(self.p,VoiceCatalog('2',self.c.voices),s)
    def test_edited_selection_count(self):
        s=self.choose();s=replace(s,personas=(replace(s.personas[0],candidate_count=999),))
        with self.assertRaisesRegex(AudioError,'EDITED_VOICE'):requests_for(self.p,self.c,s)
    def test_upstream_review_not_waived(self):
        p=replace(self.p,review_reasons=('UNRESOLVED_SYMBOL',))
        with self.assertRaisesRegex(AudioError,'UPSTREAM_REVIEW'):select_voices(p,self.c,self.policy)
    def test_unknown_primary_language_not_guessed(self):
        p=plan('यह एक उदाहरण है।','hi')
        with self.assertRaisesRegex(AudioError,'NO_COMPATIBLE'):select_voices(p,self.c,self.policy)
    def test_selection_records_catalog(self):self.assertEqual(self.choose().catalog_fingerprint,self.c.fingerprint())
    def test_boolean_policy(self):
        with self.assertRaises(AudioError):replace(self.policy,require_same_voice_code_switching=1)
