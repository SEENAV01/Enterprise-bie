import unittest
from dataclasses import replace
import numpy as np
from bie.audio.common import AudioError
from bie.audio.mix_contract import MixBuffer,SampleSpan
from bie.audio.silence_trim import TrimPolicy,plan_silence_trim,apply_silence_trim
class TrimTests(unittest.TestCase):
 def setUp(self):a=np.zeros((10000,1));a[2000:8000]=.1;self.pcm=MixBuffer.from_array(a,10000);self.policy=TrimPolicy(padding_ms=0,minimum_silence_ms=0)
 def test_exact_edges(self):p=plan_silence_trim(self.pcm,self.policy);self.assertEqual((p.keep_start,p.keep_end),(2000,8000));o,_=apply_silence_trim(self.pcm,p);self.assertEqual(o.frames,6000)
 def test_internal_pause_not_deleted(self):a=self.pcm.array().copy();a[4000:5000]=0;x=MixBuffer.from_array(a,10000);o,_=apply_silence_trim(x,plan_silence_trim(x,self.policy));self.assertEqual(o.frames,6000);self.assertTrue(np.all(o.array()[2000:3000]==0))
 def test_padding(self):p=plan_silence_trim(self.pcm,replace(self.policy,padding_ms=20));self.assertEqual((p.keep_start,p.keep_end),(1800,8200))
 def test_cap(self):p=plan_silence_trim(self.pcm,replace(self.policy,max_edge_ms=50));self.assertEqual((p.keep_start,p.keep_end),(500,9500))
 def test_minimum(self):p=plan_silence_trim(self.pcm,replace(self.policy,minimum_silence_ms=300));self.assertEqual(p.output_frames,10000)
 def test_protected_word(self):p=plan_silence_trim(self.pcm,self.policy,(SampleSpan(1000,3000,'word',('source',)),));self.assertEqual(p.keep_start,1000)
 def test_protected_final_pause(self):p=plan_silence_trim(self.pcm,self.policy,(SampleSpan(8000,10000,'pause',('source',)),));self.assertEqual(p.keep_end,10000)
 def test_nonzero_breath_preserved(self):a=self.pcm.array().copy();a[500]=1/32768;x=MixBuffer.from_array(a,10000);self.assertEqual(plan_silence_trim(x,self.policy).keep_start,500)
 def test_all_silent_not_fake_trim(self):
  with self.assertRaises(AudioError):plan_silence_trim(MixBuffer.from_array(np.zeros((10000,1)),10000))
 def test_disabled(self):p=plan_silence_trim(self.pcm,replace(self.policy,enabled=False));self.assertEqual(p.output_frames,10000)
 def test_zero_cap(self):p=plan_silence_trim(self.pcm,replace(self.policy,max_edge_ms=0));self.assertEqual(p.output_frames,10000)
 def test_stereo_either_channel_protects(self):a=np.repeat(self.pcm.array(),2,axis=1);a[1000,1]=.1;self.assertEqual(plan_silence_trim(MixBuffer.from_array(a,10000),self.policy).keep_start,1000)
 def test_negative_signal_preserved(self):a=-self.pcm.array();self.assertEqual(plan_silence_trim(MixBuffer.from_array(a,10000),self.policy).keep_start,2000)
 def test_sample_mapping(self):p=plan_silence_trim(self.pcm,self.policy);self.assertEqual(p.map_sample(4000),2000)
 def test_outside_bound(self):
  with self.assertRaises(AudioError):plan_silence_trim(self.pcm,self.policy).map_sample(0)
 def test_changed_plan(self):
  with self.assertRaises(AudioError):apply_silence_trim(self.pcm,replace(plan_silence_trim(self.pcm,self.policy),keep_start=2100))
 def test_changed_source(self):
  with self.assertRaises(AudioError):apply_silence_trim(self.pcm.gain(1),plan_silence_trim(self.pcm,self.policy))
 def test_span_outside(self):
  with self.assertRaises(AudioError):plan_silence_trim(self.pcm,self.policy,(SampleSpan(0,10001,'bad',('source',)),))
 def test_invalid_policy(self):
  for kw in ({'padding_ms':-1},{'enabled':1},{'minimum_silence_ms':True}):
   with self.subTest(kw=kw),self.assertRaises(AudioError):TrimPolicy(**kw)
 def test_original_bytes_unchanged(self):h=self.pcm.sha256;apply_silence_trim(self.pcm,plan_silence_trim(self.pcm,self.policy));self.assertEqual(h,self.pcm.sha256)
 def test_no_acoustic_claim(self):_,r=apply_silence_trim(self.pcm,plan_silence_trim(self.pcm,self.policy));self.assertFalse(r['acoustic_silence_detection']);self.assertEqual(r['internal_samples_deleted'],0)
