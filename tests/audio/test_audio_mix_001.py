import unittest,threading,tempfile,shutil,hashlib
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import numpy as np
from bie.audio.mix_contract import MixBuffer,dbfs
from bie.audio.mix_meter import FFmpegMeter
from bie.audio.loudness_normalization import LoudnessPolicy,normalize_loudness
from bie.audio.tts_contract import AudioFormat
from bie.audio.common import AudioError
from .mix_test_support import tone,constant
class LoudnessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.meter=FFmpegMeter();cls.pcm=tone()
 def test_actual_input_meter(self):
  r=self.meter.measure(self.pcm);self.assertTrue(-80<r.integrated_lufs<0);self.assertAlmostEqual(r.sample_peak_dbfs,dbfs(self.pcm.sample_peak));self.assertEqual(r.pcm_fingerprint,self.pcm.fingerprint())
 def test_target_reached(self):
  _,r=normalize_loudness(self.pcm,self.meter);self.assertTrue(r['target_reached']);self.assertLessEqual(abs(r['after']['integrated_lufs']+23),.5)
 def test_constant_gain_no_time_change(self):
  out,r=normalize_loudness(self.pcm,self.meter);self.assertEqual(out.frames,self.pcm.frames);self.assertEqual(out.sample_rate,self.pcm.sample_rate);np.testing.assert_allclose(out.array(),self.pcm.array()*10**(r['applied_gain_db']/20));self.assertFalse(r['dynamic_compression_applied'])
 def test_double_amplitude_six_lu(self):self.assertAlmostEqual(self.meter.measure(self.pcm.gain(6.0206)).integrated_lufs-self.meter.measure(self.pcm).integrated_lufs,6.02,delta=.05)
 def test_explicit_dual_mono(self):self.assertAlmostEqual(self.meter.measure(self.pcm,dual_mono=True).integrated_lufs-self.meter.measure(self.pcm).integrated_lufs,3.01,delta=.05)
 def test_dual_mono_stereo_rejected(self):
  with self.assertRaises(AudioError):self.meter.measure(tone(channels=2),dual_mono=True)
 def test_quiet_constrained_review(self):
  _,r=normalize_loudness(tone(amp=.001),self.meter,LoudnessPolicy(max_boost_db=0));self.assertFalse(r['target_reached']);self.assertTrue(r['requires_review'])
 def test_quiet_fail_policy(self):
  with self.assertRaises(AudioError):normalize_loudness(tone(amp=.001),self.meter,LoudnessPolicy(max_boost_db=0,unreachable='fail'))
 def test_silence_unmeasurable(self):
  zero=constant(frames=44100,value=0);self.assertIsNone(self.meter.measure(zero).integrated_lufs)
  with self.assertRaises(AudioError):normalize_loudness(zero,self.meter)
 def test_short_audio_not_fake_loudness(self):
  with self.assertRaises(AudioError):normalize_loudness(tone(frames=100),self.meter)
 def test_attenuation_limit(self):
  with self.assertRaises(AudioError):normalize_loudness(tone(amp=.9),self.meter,LoudnessPolicy(max_attenuation_db=0))
 def test_cancellation(self):
  c=threading.Event();c.set()
  with self.assertRaisesRegex(AudioError,'CANCELLED'):self.meter.measure(self.pcm,cancellation=c)
 def test_deadline(self):
  with self.assertRaisesRegex(AudioError,'TIMEOUT'):FFmpegMeter(timeout_s=.01).measure(tone(frames=220500))
 def test_missing_executable(self):
  with self.assertRaises(AudioError):FFmpegMeter('/nonexistent/bie/ffmpeg')
 def test_changed_executable(self):
  with patch.object(self.meter,'_sha',return_value='0'*64):
   with self.assertRaises(AudioError):self.meter.measure(self.pcm)
 def test_input_fields_not_filter_output(self):
  log='{"input_i":"-30","input_tp":"-10","input_lra":"0","input_thresh":"-40","output_i":"-23"}'
  with patch.object(self.meter,'_run',return_value=log):self.assertEqual(self.meter.measure(self.pcm).integrated_lufs,-30)
 def test_bad_report(self):
  for log in ('{}','garbage','{"input_i":"nan"}'):
   with self.subTest(log=log),patch.object(self.meter,'_run',return_value=log):
    with self.assertRaises(AudioError):self.meter.measure(self.pcm)
 def test_policy_nonfinite(self):
  for value in (float('nan'),float('inf'),True,-100,0):
   with self.subTest(value=value),self.assertRaises(AudioError):LoudnessPolicy(target_lufs=value)
 def test_policy_unsupported(self):
  with self.assertRaises(AudioError):LoudnessPolicy(unreachable='ignore')
 def test_pcm_finite(self):
  for x in (float('nan'),float('inf'),257):
   with self.subTest(x=x),self.assertRaises(AudioError):constant(value=x)
 def test_pcm_shape(self):
  for arr in (np.ones(5),np.ones((5,3)),np.empty((0,1)),np.array([['a']])):
   with self.subTest(shape=arr.shape),self.assertRaises((AudioError,ValueError)):MixBuffer.from_array(arr,22050)
 def test_pcm_no_silent_clipping(self):
  with self.assertRaisesRegex(AudioError,'WOULD_CLIP'):constant(value=1.1).to_wav()
 def test_pcm_roundtrip(self):
  raw=(np.arange(-300,300)/32768)[:,None];p=MixBuffer.from_array(raw,22050);np.testing.assert_array_equal(MixBuffer.from_wav(p.to_wav(),AudioFormat()).array(),raw)
 def test_immutable_source(self):
  h=self.pcm.sha256;normalize_loudness(self.pcm,self.meter);self.assertEqual(h,self.pcm.sha256)
  with self.assertRaises(ValueError):self.pcm.array()[0]=1
 def test_meter_is_not_acceptance(self):
  _,r=normalize_loudness(self.pcm,self.meter);self.assertFalse(r['product_accepted']);self.assertIn('not full host attestation',self.meter.identity['scope'])
