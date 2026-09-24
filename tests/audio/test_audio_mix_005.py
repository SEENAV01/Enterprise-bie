import unittest
from dataclasses import replace
from unittest.mock import patch
import numpy as np
from bie.audio.common import AudioError
from bie.audio.mix_contract import MixBuffer
from bie.audio.mix_meter import FFmpegMeter
from bie.audio.peak_control import PeakPolicy,control_peaks
from bie.audio.tts_contract import AudioFormat
from .mix_test_support import tone,constant
class PeakTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.meter=FFmpegMeter()
 def test_overrange_control_not_clip(self):w,r=control_peaks(tone(amp=1.8),self.meter);self.assertLessEqual(r['after']['true_peak_dbtp'],-1);self.assertEqual(r['hard_clipped_samples'],0);self.assertLess(r['applied_gain_db'],0)
 def test_safe_source_not_boosted(self):_,r=control_peaks(tone(),self.meter);self.assertEqual(r['applied_gain_db'],0)
 def test_length_rate_and_latency(self):p=tone();w,r=control_peaks(p,self.meter);o=MixBuffer.from_wav(w,AudioFormat());self.assertEqual(o.frames,p.frames);self.assertEqual(r['latency_samples'],0)
 def test_negative_full_scale_not_wrap(self):w,r=control_peaks(constant(44100,-1),self.meter);o=MixBuffer.from_wav(w,AudioFormat());self.assertLess(o.array()[0,0],0);self.assertLess(abs(o.array()[0,0]),1)
 def test_linked_stereo_ratio(self):p=tone(channels=2,amp=1.8);a=p.array().copy();a[:,1]*=.5;w,r=control_peaks(MixBuffer.from_array(a,22050),self.meter);o=MixBuffer.from_wav(w,AudioFormat(22050,2));self.assertLessEqual(np.max(np.abs(o.array()[:,1]-.5*o.array()[:,0])),1/32768)
 def test_intersample_peak_measured(self):a=.9*np.sin(np.arange(96000)*np.pi/2+np.pi/4);p=MixBuffer.from_array(a[:,None],48000);before=self.meter.measure(p);self.assertGreater(before.true_peak_dbtp-before.sample_peak_dbfs,1);_,r=control_peaks(p,self.meter,PeakPolicy(ceiling_dbtp=-3));self.assertLessEqual(r['after']['true_peak_dbtp'],-3)
 def test_rounding_error_bounded(self):p=tone();w,r=control_peaks(p,self.meter);o=MixBuffer.from_wav(w,AudioFormat());self.assertLessEqual(np.max(np.abs(o.array()-p.array()*10**(r['applied_gain_db']/20))),.5001/32768)
 def test_attenuation_budget(self):
  with self.assertRaises(AudioError):control_peaks(tone(amp=1.8),self.meter,PeakPolicy(maximum_attenuation_db=0))
 def test_invalid_policy(self):
  for kw in ({'ceiling_dbtp':0},{'guard_db':0},{'guard_db':True},{'maximum_attenuation_db':float('nan')}):
   with self.subTest(kw=kw),self.assertRaises(AudioError):PeakPolicy(**kw)
 def test_silent_signal_safe(self):w,r=control_peaks(constant(44100,0),self.meter);self.assertIsNone(r['after']['true_peak_dbtp']);self.assertEqual(MixBuffer.from_wav(w,AudioFormat()).sample_peak,0)
 def test_encoded_output_meter_binding(self):w,r=control_peaks(tone(),self.meter);p=MixBuffer.from_wav(w,AudioFormat());self.assertEqual(r['after']['pcm_fingerprint'],p.fingerprint())
 def test_source_immutable(self):p=tone();h=p.sha256;control_peaks(p,self.meter);self.assertEqual(h,p.sha256)
 def test_reproducible_bytes(self):p=tone();a,r=control_peaks(p,self.meter);b,s=control_peaks(p,self.meter);self.assertEqual(a,b);self.assertEqual(r,s)
 def test_bad_final_meter_rejected(self):
  p=tone();before=self.meter.measure(p)
  with patch.object(self.meter,'measure',side_effect=(before,replace(before,true_peak_dbtp=1))):
   with self.assertRaises(AudioError):control_peaks(p,self.meter)
 def test_not_acceptance(self):_,r=control_peaks(tone(),self.meter);self.assertFalse(r['product_accepted']);self.assertIn('constant attenuation',r['algorithm'])
