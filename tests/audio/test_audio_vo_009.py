from dataclasses import replace
from threading import Event
import unittest,hashlib,struct
from bie.audio.common import AudioError,fingerprint
from bie.audio.tts_contract import ProviderFailure
from bie.audio.tts_generation import generate_speech
from bie.audio.pcm_audio import validate_wav
from tests.audio.tts_test_support import request

class Generation(unittest.TestCase):
    def setUp(self):self.r,self.p=request()
    def test_real_invocation_contract(self):
        a=generate_speech(self.r,self.p);self.assertEqual(self.p.calls,1);self.assertGreater(a.info.samples_per_channel,0)
    def test_fixture_honesty(self):self.assertIn('NOT_SPEECH_TEST_DOUBLE',generate_speech(self.r,self.p).diagnostics)
    def test_wrong_request_binding_rejected(self):
        self.p.mutate=lambda a:replace(a,request_fingerprint=fingerprint('other'))
        with self.assertRaisesRegex(ProviderFailure,'RECEIPT_MISMATCH'):generate_speech(self.r,self.p)
    def test_wrong_runtime_rejected(self):
        self.p.mutate=lambda a:replace(a,runtime_fingerprint=fingerprint('other'))
        with self.assertRaisesRegex(ProviderFailure,'RECEIPT_MISMATCH'):generate_speech(self.r,self.p)
    def test_wrong_voice_rejected(self):
        self.p.mutate=lambda a:replace(a,voice_fingerprint=fingerprint('other'))
        with self.assertRaisesRegex(ProviderFailure,'RECEIPT_MISMATCH'):generate_speech(self.r,self.p)
    def test_malformed_wav_rejected(self):
        self.p.mutate=lambda a:replace(a,wav_bytes=b'not a waveform')
        with self.assertRaises(AudioError):generate_speech(self.r,self.p)
    def test_retry_only_retryable_failure(self):
        self.p.failures=[ProviderFailure('TRANSIENT',retryable=True)];a=generate_speech(self.r,self.p,retry_delay_seconds=0);self.assertEqual(a.attempts,2)
    def test_permanent_not_retried(self):
        self.p.failures=[ProviderFailure('PERMANENT')]
        with self.assertRaises(ProviderFailure):generate_speech(self.r,self.p)
        self.assertEqual(self.p.calls,1)
    def test_retries_bounded(self):
        self.p.failures=[ProviderFailure('TRANSIENT',retryable=True)]*4
        with self.assertRaises(ProviderFailure):generate_speech(self.r,self.p,max_attempts=2,retry_delay_seconds=0)
        self.assertEqual(self.p.calls,2)
    def test_cancelled_before_call(self):
        stop=Event();stop.set()
        with self.assertRaisesRegex(ProviderFailure,'CANCELLED'):generate_speech(self.r,self.p,cancellation=stop)
        self.assertEqual(self.p.calls,0)
    def test_requested_pause_exact_samples(self):
        s=replace(self.r.segment,pause_after_ms=250,pause_refs=('source:pause',));r=replace(self.r,segment=s);a=generate_speech(r,self.p)
        self.assertEqual(a.requested_pause_samples,5513);info,raw=validate_wav(a.wav_bytes,r.settings.format)
        self.assertEqual(raw[-5513*2:],b'\0'*(5513*2));self.assertEqual(info.samples_per_channel,2205+5513)
    def test_no_fabricated_word_alignment(self):
        r=generate_speech(self.r,self.p).receipt();self.assertIs(r['word_timestamps_verified'],False);self.assertIs(r['pronunciation_verified'],False)
    def test_product_not_accepted(self):self.assertIs(generate_speech(self.r,self.p).receipt()['product_accepted'],False)
    def test_speech_hash_exact(self):
        a=generate_speech(self.r,self.p);self.assertEqual(a.info.sha256,hashlib.sha256(a.wav_bytes).hexdigest())
    def test_invalid_attempts(self):
        with self.assertRaises(AudioError):generate_speech(self.r,self.p,max_attempts=True)
    def test_catalog_changes_blocked(self):
        self.p.voices=replace(self.p.voices,revision='2')
        with self.assertRaisesRegex(ProviderFailure,'CATALOG_CHANGED'):generate_speech(self.r,self.p)
