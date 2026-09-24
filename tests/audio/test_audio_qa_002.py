import unittest,json,struct
from dataclasses import replace
from unittest.mock import patch
import numpy as np
from bie.audio.qa_clipping import clipping_qa,ClippingPolicy,longest_run
from bie.audio.mix_meter import FFmpegMeter
from bie.audio.mix_contract import MixBuffer
from bie.audio.tts_contract import AudioFormat
from bie.audio.pcm_audio import encode_pcm
from bie.audio.common import AudioError
from .mix_test_support import tone

class ClippingQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.meter=FFmpegMeter();cls.wav=tone().to_wav()
    def test_real_native_safe_tone_passes(self):self.assertEqual(clipping_qa(self.wav,AudioFormat(),meter=self.meter).status,'PASS')
    def test_actual_pcm_measurement_bound(self):
        r=clipping_qa(self.wav,AudioFormat(),meter=self.meter);self.assertEqual(json.loads(r.metrics_json)['measurement']['frames'],44100)
    def test_native_meter_identity_recorded(self):self.assertIn('executable_sha256',json.loads(clipping_qa(self.wav,AudioFormat(),meter=self.meter).metrics_json)['meter_identity'])
    def test_true_peak_threshold_enforced(self):self.assertEqual(clipping_qa(tone(amp=.9).to_wav(),AudioFormat(),ClippingPolicy(-10),meter=self.meter).status,'FAIL')
    def test_silence_not_pass(self):self.assertEqual(clipping_qa(encode_pcm(b'\0'*88200,AudioFormat()),AudioFormat(),meter=self.meter).status,'FAIL')
    def test_positive_rail_run(self):
        x=np.zeros(44100,dtype='<i2');x[10:100]=32767
        r=clipping_qa(encode_pcm(x.tobytes(),AudioFormat()),AudioFormat(),meter=self.meter);self.assertIn('PCM_RAIL_RUN',[f.code for f in r.findings])
    def test_negative_rail_run(self):
        x=np.zeros(44100,dtype='<i2');x[10:100]=-32768
        r=clipping_qa(encode_pcm(x.tobytes(),AudioFormat()),AudioFormat(),meter=self.meter);self.assertEqual(json.loads(r.metrics_json)['channels'][0]['longest_same_rail_run'],90)
    def test_isolated_rail_contact_not_claimed_sustained(self):
        x=np.zeros(44100,dtype='<i2');x[300]=32767
        r=clipping_qa(encode_pcm(x.tobytes(),AudioFormat()),AudioFormat(),meter=self.meter);self.assertIn('PCM_RAIL_CONTACT',[f.code for f in r.findings]);self.assertNotIn('PCM_RAIL_RUN',[f.code for f in r.findings])
    def test_stereo_individual_channels(self):
        x=np.zeros((44100,2),dtype='<i2');x[40:80,1]=-32768
        r=clipping_qa(encode_pcm(x.tobytes(),AudioFormat(channels=2)),AudioFormat(channels=2),meter=self.meter);rows=json.loads(r.metrics_json)['channels'];self.assertEqual(rows[0]['rail_contacts'],0);self.assertEqual(rows[1]['rail_contacts'],40)
    def test_wrong_format_rejected(self):
        with self.assertRaises(AudioError):clipping_qa(self.wav,AudioFormat(channels=2),meter=self.meter)
    def test_truncated_wav_rejected(self):
        with self.assertRaises(AudioError):clipping_qa(self.wav[:-2],AudioFormat(),meter=self.meter)
    def test_nan_policy_rejected(self):
        with self.assertRaises(AudioError):ClippingPolicy(float('nan'))
    def test_bool_policy_rejected(self):
        with self.assertRaises(AudioError):ClippingPolicy(rail_run_samples=True)
    def test_meter_wrong_binding_rejected(self):
        m=self.meter.measure(MixBuffer.from_wav(self.wav,AudioFormat()))
        with patch.object(self.meter,'measure',return_value=replace(m,pcm_fingerprint='sha256:'+'0'*64)):
            with self.assertRaises(AudioError):clipping_qa(self.wav,AudioFormat(),meter=self.meter)
    def test_meter_failure_not_hidden(self):
        with patch.object(self.meter,'measure',side_effect=AudioError('MIX_METER_TIMEOUT')):
            with self.assertRaises(AudioError):clipping_qa(self.wav,AudioFormat(),meter=self.meter)
    def test_measurement_does_not_rewrite_audio(self):
        before=self.wav;clipping_qa(self.wav,AudioFormat(),meter=self.meter);self.assertEqual(before,self.wav)
    def test_runs_edges(self):
        for values,expected in (([1,1,0,1],2),([0,0],0),([1]*7,7),([0,1,1],2)):
            self.assertEqual(longest_run(np.array(values,dtype=bool)),expected)
    def test_formal_certification_not_claimed(self):self.assertFalse(json.loads(clipping_qa(self.wav,AudioFormat(),meter=self.meter).metrics_json)['formal_meter_certification'])
