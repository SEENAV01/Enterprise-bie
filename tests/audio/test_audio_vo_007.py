from dataclasses import replace
import unittest,struct
from bie.audio.common import AudioError,fingerprint
from bie.audio.tts_contract import *
from bie.audio.pcm_audio import validate_wav,encode_pcm
from tests.audio.tts_test_support import request

class ProviderContracts(unittest.TestCase):
    def setUp(self):self.r,self.p=request()
    def test_request_fingerprint_repeatable(self):self.assertEqual(self.r.fingerprint(),self.r.fingerprint())
    def test_provider_neutral_protocol(self):self.assertIsInstance(self.p,SpeechProvider)
    def test_provider_change_changes_identity(self):self.assertNotEqual(replace(self.r,voice=replace(self.r.voice,model_revision='2')).fingerprint(),self.r.fingerprint())
    def test_boolean_rate(self):
        with self.assertRaises(AudioError):SynthesisSettings(rate_wpm=True)
    def test_rate_limits(self):
        for r in (79,301):
            with self.assertRaises(AudioError):SynthesisSettings(rate_wpm=r)
    def test_boolean_channels(self):
        with self.assertRaises(AudioError):AudioFormat(channels=True)
    def test_unsupported_encoding(self):
        with self.assertRaises(AudioError):AudioFormat(encoding='mp3')
    def test_unsupported_format(self):
        with self.assertRaisesRegex(AudioError,'FORMAT'):replace(self.r,settings=SynthesisSettings(format=AudioFormat(sample_rate=16000)))
    def test_unsupported_style_no_silent_ignore(self):
        with self.assertRaisesRegex(AudioError,'STYLE'):replace(self.r,settings=SynthesisSettings(style='cinematic'))
    def test_ipa_capability_required(self):
        span=replace(self.r.segment.spans[0],kind='TERM',phonemes='test',alphabet='ipa')
        with self.assertRaisesRegex(AudioError,'PHONEMES'):replace(self.r,segment=replace(self.r.segment,spans=(span,)))
    def test_length_limit(self):
        with self.assertRaisesRegex(AudioError,'REQUEST_LIMIT'):replace(self.r,voice=replace(self.r.voice,max_chars=2))
    def test_duplicate_locale(self):
        with self.assertRaises(AudioError):replace(self.r.voice,locales=self.r.voice.locales*2)
    def test_catalog_unique(self):
        with self.assertRaises(AudioError):VoiceCatalog('1',(self.r.voice,self.r.voice))
    def test_request_version(self):
        with self.assertRaises(AudioError):replace(self.r,version='future')
    def test_request_source_digest(self):
        with self.assertRaises(AudioError):replace(self.r,plan_fingerprint='bad')
    def test_format_signal_info(self):
        data=encode_pcm(struct.pack('<hhhh',0,23,-25,0),AudioFormat());info,raw=validate_wav(data,AudioFormat());self.assertEqual((info.peak,info.samples_per_channel),(25,4))
    def test_zero_signal_rejected(self):
        with self.assertRaisesRegex(AudioError,'EMPTY_AUDIO'):validate_wav(encode_pcm(b'\0'*100,AudioFormat()),AudioFormat())
    def test_truncated_wav_rejected(self):
        data=encode_pcm(b'\x01\0'*100,AudioFormat())
        with self.assertRaises(AudioError):validate_wav(data[:-2],AudioFormat())
    def test_trailing_data_rejected(self):
        data=encode_pcm(b'\x01\0'*100,AudioFormat())
        with self.assertRaises(AudioError):validate_wav(data+b'garbage',AudioFormat())
    def test_wrong_sample_rate_rejected(self):
        data=encode_pcm(b'\x01\0'*100,AudioFormat())
        with self.assertRaisesRegex(AudioError,'FORMAT'):validate_wav(data,AudioFormat(sample_rate=16000))
