"""Actual installed eSpeak tests. Missing deployment is a failure, never a fake PASS."""
from dataclasses import replace
from threading import Event
from pathlib import Path
from unittest.mock import patch
import hashlib,tempfile,unittest,xml.etree.ElementTree as ET
from bie.audio.common import AudioError
from bie.audio.preparation_bridge import from_v144,from_v204
from bie.audio.multilingual_terms import LanguageTerm,apply_languages
from bie.audio.espeak_provider import EspeakProvider
from bie.audio.tts_generation import generate_speech
from bie.audio.tts_cache import TTSCache
from bie.audio.tts_contract import ProviderFailure,SynthesisSettings
from bie.audio.voice_selection import *
from tests.audio.audio_test_support import utterance,empty_options

class RealLocalSpeech(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.backend=EspeakProvider()
    def request(self,p):
        c=self.backend.catalog();s=select_voices(p,c,SelectionPolicy(('espeak-local',),('technical_formant',),require_same_voice_code_switching=False))
        return requests_for(p,c,s)[0]
    def test_actual_english_waveform(self):
        p=from_v144((utterance('Electric charges exert forces on one another.'),),**empty_options());a=generate_speech(self.request(p),self.backend)
        self.assertGreater(a.info.duration_seconds,1);self.assertGreater(a.info.nonzero_samples,1000);self.assertIn('LOCAL_FORMANT_SPEECH_NOT_CINEMATIC_ACCEPTANCE',a.diagnostics)
    def test_actual_hindi_waveform(self):
        p=from_v144((utterance('विद्युत आवेश एक दूसरे पर बल लगाते हैं।','hi'),),**empty_options('hi'));a=generate_speech(self.request(p),self.backend)
        self.assertGreater(a.info.duration_seconds,1);self.assertGreater(a.info.nonzero_samples,1000)
    def test_actual_mixed_language_waveform(self):
        u=utterance('यह photosynthesis का उदाहरण है।','hi');p=from_v144((u,),**empty_options('hi'));a=u.text.index('photosynthesis')
        p=apply_languages(p,(LanguageTerm(u.utterance_id,u.fingerprint(),a,a+14,'photosynthesis','photosynthesis','en',('source:term',),'term:mixed'),))
        r=self.request(p);markup=self.backend.serialize(r);self.assertIn(b'name="hi"',markup);self.assertIn(b'name="en"',markup)
        self.assertGreater(generate_speech(r,self.backend).info.nonzero_samples,1000)
    def test_identical_requests_repeat_raw_audio(self):
        p=from_v144((utterance('This is the same source text.'),),**empty_options());r=self.request(p)
        a=generate_speech(r,self.backend);b=generate_speech(r,self.backend);self.assertEqual(a.wav_bytes,b.wav_bytes)
    def test_real_cache_no_second_synthesis(self):
        p=from_v144((utterance('The cache retains the verified recording.'),),**empty_options());r=self.request(p)
        with tempfile.TemporaryDirectory() as td:
            c=TTSCache(td,namespace='real-test');before=self.backend.invocations;a=c.get_or_generate(r,self.backend);b=c.get_or_generate(r,self.backend)
            self.assertEqual(self.backend.invocations,before+1);self.assertTrue(b.cache_hit);self.assertEqual(a.asset.wav_bytes,b.asset.wav_bytes)
    def test_literal_xml_cannot_create_audio_tag(self):
        # Literal narration is serialized as text, never arbitrary source SSML.
        p=from_v144((utterance('The teacher says hello.'),),**empty_options());r=self.request(p)
        s=r.segment.spans[0];raw='<audio src="file:///etc/passwd"/> hello'
        s=replace(s,original=raw,spoken=raw,end=len(raw));segment=replace(r.segment,display_text=raw,end=len(raw),spans=(s,));r=replace(r,segment=segment)
        xml=self.backend.serialize(r);root=ET.fromstring(xml);self.assertEqual(len(list(root.iter('audio'))),0);self.assertEqual(''.join(root.itertext()),raw)
    def test_wrong_runtime_rejected_before_speech(self):
        p=from_v144((utterance(),),**empty_options());r=self.request(p)
        with patch.object(self.backend,'_snapshot',return_value={'changed':True}):
            with self.assertRaisesRegex(ProviderFailure,'RUNTIME_CHANGED'):self.backend.synthesize(r)
    def test_missing_executable_is_not_synthetic_fallback(self):
        with self.assertRaises((ProviderFailure,OSError)):EspeakProvider('/nonexistent/bie/espeak')

    def test_real_child_timeout_is_failure(self):
        backend=EspeakProvider(timeout_seconds=0.000001)
        p=from_v144((utterance('The worker must terminate within its time budget.'),),**empty_options())
        r=self.request(p)
        with self.assertRaisesRegex(ProviderFailure,'TIMEOUT'):backend.synthesize(r)
    def test_real_output_limit_is_failure(self):
        backend=EspeakProvider(max_output_bytes=1000)
        p=from_v144((utterance('The complete audio exceeds this deliberately tiny byte budget.'),),**empty_options())
        with self.assertRaisesRegex(ProviderFailure,'OUTPUT'):backend.synthesize(self.request(p))
    def test_runtime_change_blocks_cache_hit(self):
        p=from_v144((utterance('Model changes invalidate reuse.'),),**empty_options());r=self.request(p)
        with tempfile.TemporaryDirectory() as td:
            cache=TTSCache(td,namespace='identity-test');cache.get_or_generate(r,self.backend)
            with patch.object(self.backend,'_snapshot',return_value={'changed':True}):
                with self.assertRaisesRegex(ProviderFailure,'RUNTIME_CHANGED'):cache.get_or_generate(r,self.backend)
    def test_real_cancel_before_exec(self):
        p=from_v144((utterance(),),**empty_options());e=Event();e.set()
        with self.assertRaisesRegex(ProviderFailure,'CANCELLED'):self.backend.synthesize(self.request(p),cancellation=e)
