from dataclasses import replace
from pathlib import Path
from threading import Event
from unittest.mock import patch
import copy,json,tempfile,unittest
from bie.audio.common import AudioError,fingerprint
from bie.audio.sync_contract import *
from bie.audio.word_timestamps import reported_word_timings,align_espeak_asset,serialize_map,_run_worker
from bie.audio.timed_espeak_provider import TimedEspeakProvider,align_timed_asset,words_from_marks,lexical_ranges
from bie.audio.espeak_provider import EspeakProvider
from bie.audio.tts_generation import generate_speech
from bie.audio.tts_cache import TTSCache
from bie.audio.voice_selection import SelectionPolicy,select_voices,requests_for
from tests.audio.sync_test_support import fixture
from tests.audio.tts_test_support import plan

class WordContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p,cls.assets,cls.timings=fixture();cls.a=cls.assets[0];cls.t=cls.timings[0]
    def test_reported_never_measured(self):
        t=replace(self.t,basis='REPORTED_UNVERIFIED')
        with self.assertRaisesRegex(AudioError,'MEASURED'):validate_alignment(self.a,t)
    def test_reported_validates_source(self):self.assertIs(validate_alignment(self.a,self.t,require_measured=False),self.t)
    def test_media_edit_rejected(self):
        b=bytearray(self.a.wav_bytes);b[-1]^=1
        with self.assertRaisesRegex(AudioError,'ASSET_'):validate_alignment(replace(self.a,wav_bytes=bytes(b)),self.t,require_measured=False)
    def test_request_revision_rejected(self):
        a=replace(self.a,request=replace(self.a.request,plan_fingerprint=fingerprint('new plan')))
        with self.assertRaisesRegex(AudioError,'STALE'):validate_alignment(a,self.t,require_measured=False)
    def test_missing_word_rejected(self):
        t=replace(self.t,words=self.t.words[:-1])
        with self.assertRaisesRegex(AudioError,'COVERAGE'):validate_alignment(self.a,t,require_measured=False)
    def test_changed_word_rejected(self):
        w=replace(self.t.words[0],spoken='Omega');t=replace(self.t,words=(w,)+self.t.words[1:])
        with self.assertRaisesRegex(AudioError,'SOURCE_CHANGED'):validate_alignment(self.a,t,require_measured=False)
    def test_source_refs_preserved(self):self.assertEqual(self.t.words[0].source[0].source_refs,('source:p1',))
    def test_source_rule_edit_rejected(self):
        w=replace(self.t.words[0],source=(replace(self.t.words[0].source[0],rule_fingerprint=fingerprint('wrong')),));t=replace(self.t,words=(w,)+self.t.words[1:])
        with self.assertRaisesRegex(AudioError,'SOURCE_CHANGED'):validate_alignment(self.a,t,require_measured=False)
    def test_outside_audio_rejected(self):
        with self.assertRaisesRegex(AudioError,'BOUNDS'):replace(self.t,words=(replace(self.t.words[0],end_sample=999999),)+self.t.words[1:])
    def test_negative_time_rejected(self):
        with self.assertRaises(AudioError):replace(self.t.words[0],start_sample=-1)
    def test_zero_duration_rejected(self):
        with self.assertRaises(AudioError):replace(self.t.words[0],end_sample=self.t.words[0].start_sample)
    def test_bool_time_rejected(self):
        with self.assertRaises(AudioError):replace(self.t.words[0],start_sample=True)
    def test_overlap_rejected(self):
        with self.assertRaises(AudioError):replace(self.t,words=(self.t.words[0],replace(self.t.words[1],start_sample=101),self.t.words[2]))
    def test_ordinal_rejected(self):
        with self.assertRaises(AudioError):replace(self.t,words=(replace(self.t.words[0],index=4),)+self.t.words[1:])
    def test_bad_schema_rejected(self):
        with self.assertRaises(AudioError):replace(self.t,schema_version='future')
    def test_reported_rows_typed(self):
        with self.assertRaises(AudioError):reported_word_timings(self.a,[[0,5,0,10]])
    def test_unicode_combining_preserved(self):
        ranges=lexical_ranges('बल दिशा में');self.assertEqual(tuple('बल दिशा में'[a:b] for a,b in ranges),('बल','दिशा','में'))
    def test_sample_round_half_up(self):self.assertEqual(samples_for_ms(1,22050),22);self.assertEqual(samples_for_ms(10,22050),221)
    def test_no_acoustic_acceptance(self):self.assertFalse(self.t.receipt()['acoustic_alignment_verified']);self.assertFalse(self.t.receipt()['product_accepted'])

class RealTimedSpeech(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider=TimedEspeakProvider();cls.p=plan('First sentence. Keep all the words. dee en ay.');cat=cls.provider.catalog()
        cls.request=requests_for(cls.p,cat,select_voices(cls.p,cat,SelectionPolicy((cls.provider.provider_id,),('technical_formant',))))[0]
        cls.asset=generate_speech(cls.request,cls.provider);cls.aligned,cls.evidence=align_timed_asset(cls.asset,cls.provider)
    def test_native_speech_and_all_marks(self):
        self.assertEqual(tuple(w.spoken for w in self.aligned.words),('First','sentence','Keep','all','the','words','dee','en','ay'))
        self.assertTrue(self.evidence['marked_synthesis_replay_pcm_equal'])
    def test_same_pcm_replay(self):
        again,e=align_timed_asset(self.asset,self.provider);self.assertEqual(again,self.aligned);self.assertEqual(e,self.evidence)
    def test_actual_hindi(self):
        p=plan('बल दिशा में लगता है।','hi');cat=self.provider.catalog();r=requests_for(p,cat,select_voices(p,cat,SelectionPolicy((self.provider.provider_id,),('technical_formant',))))[0]
        a=generate_speech(r,self.provider);t,_=align_timed_asset(a,self.provider)
        self.assertEqual([w.spoken for w in t.words],['बल','दिशा','में','लगता','है'])
    def test_old_provider_not_silently_replaced(self):
        old=EspeakProvider();self.assertNotEqual(old.runtime,self.provider.runtime);self.assertNotEqual(old.provider_id,self.provider.provider_id)
        with self.assertRaisesRegex(AudioError,'TIMED_PROVIDER'):align_timed_asset(self.asset,old)
    def test_corrupt_pcm_cannot_take_other_timings(self):
        report,wav,ranges,markup=self.provider._native(self.request);bad=bytearray(wav);bad[50]^=1
        with patch.object(self.provider,'_native',return_value=(report,bytes(bad),ranges,markup)):
            with self.assertRaisesRegex(AudioError,'PCM_MISMATCH'):align_timed_asset(self.asset,self.provider)
    def test_missing_mark_rejected(self):
        report=copy.deepcopy(self.evidence);report['events']=[e for e in report['events'] if e.get('mark')!='bie_w0_start']
        with self.assertRaisesRegex(AudioError,'COVERAGE'):words_from_marks(self.request.segment,report,lexical_ranges(self.request.segment.spoken_text),self.aligned.provider_samples,22050)
    def test_reordered_marks_rejected(self):
        report=copy.deepcopy(self.evidence);report['events'].reverse()
        with self.assertRaisesRegex(AudioError,'ORDER'):words_from_marks(self.request.segment,report,lexical_ranges(self.request.segment.spoken_text),self.aligned.provider_samples,22050)
    def test_unknown_mark_rejected(self):
        report=copy.deepcopy(self.evidence);report['events'].append({'type':3,'audio_ms':0,'mark':'unexpected'})
        with self.assertRaises(AudioError):words_from_marks(self.request.segment,report,lexical_ranges(self.request.segment.spoken_text),self.aligned.provider_samples,22050)
    def test_cancellation_no_timing(self):
        cancel=Event();cancel.set()
        with self.assertRaisesRegex(AudioError,'CANCELLED'):align_timed_asset(self.asset,self.provider,cancellation=cancel)
    def test_worker_deadline_enforced(self):
        with self.assertRaisesRegex(AudioError,'TIMEOUT'):_run_worker({},timeout_seconds=.000001,cancellation=Event())
    def test_cache_waveform_and_timing_bind(self):
        with tempfile.TemporaryDirectory() as td:
            cache=TTSCache(td,namespace='timed-test');a=cache.get_or_generate(self.request,self.provider);b=cache.get_or_generate(self.request,self.provider)
            self.assertFalse(a.cache_hit);self.assertTrue(b.cache_hit)
            t,_=align_timed_asset(b.asset,self.provider);self.assertEqual(t.media_sha256,b.asset.info.sha256)
    def test_mark_positions_are_not_claimed_as_phonetic_offsets(self):
        self.assertTrue(all(w.end_basis=='ENGINE_MARK_BOUNDARY' for w in self.aligned.words));self.assertFalse(self.aligned.receipt()['acoustic_alignment_verified'])
