import unittest
import numpy as np
from dataclasses import replace
from bie.audio.common import AudioError
from bie.audio.mix_contract import MixBuffer,db_gain
from bie.audio.music_ducking import DuckingPolicy,build_duck_envelope,duck_music
from .mix_test_support import constant
class DuckingTests(unittest.TestCase):
 def setUp(self):
  a=np.zeros((30000,1));a[10000:13000]=.2;self.voice=MixBuffer.from_array(a,10000);self.policy=DuckingPolicy(attack_ms=100,hold_ms=100,release_ms=200);self.env,self.win=build_duck_envelope(self.voice,self.policy)
 def test_activity_detected(self):self.assertEqual(len(self.win),1);self.assertEqual(self.win[0].active_start,10000)
 def test_depth(self):self.assertAlmostEqual(self.env[11000],db_gain(-15))
 def test_silent_bed_not_ducked(self):e,w=build_duck_envelope(constant(frames=30000,value=0,rate=10000));self.assertEqual(len(w),0);self.assertTrue(np.all(e==1))
 def test_attack_is_preduck_not_latency(self):self.assertEqual(self.win[0].attack_start,9000);self.assertEqual(self.env[8999],1)
 def test_monotonic_attack(self):self.assertTrue(np.all(np.diff(self.env[9000:10001])<=0))
 def test_hold(self):self.assertAlmostEqual(self.env[13999],db_gain(-15))
 def test_monotonic_release(self):self.assertTrue(np.all(np.diff(self.env[14000:16001])>=0))
 def test_return_to_unity(self):self.assertEqual(self.env[16000],1)
 def test_zero_attack(self):e,w=build_duck_envelope(self.voice,replace(self.policy,attack_ms=0));self.assertEqual(w[0].attack_start,10000);self.assertAlmostEqual(e[10000],db_gain(-15))
 def test_overlapping_windows_merge(self):a=self.voice.array().copy();a[14500:15000]=.2;_,w=build_duck_envelope(MixBuffer.from_array(a,10000),self.policy);self.assertEqual(len(w),1)
 def test_long_pause_separate(self):a=self.voice.array().copy();a[24000:25000]=.2;_,w=build_duck_envelope(MixBuffer.from_array(a,10000),self.policy);self.assertEqual(len(w),2)
 def test_stereo_antiphase_energy(self):a=np.concatenate((self.voice.array(),-self.voice.array()),axis=1);e,w=build_duck_envelope(MixBuffer.from_array(a,10000),self.policy);np.testing.assert_array_equal(e,self.env)
 def test_linked_stereo_duck(self):m=MixBuffer.from_array(np.tile([.1,.2],(30000,1)),10000);o,_=duck_music(m,self.voice,self.policy);np.testing.assert_allclose(o.array()[:,1],2*o.array()[:,0])
 def test_exact_length_and_clock(self):o,r=duck_music(constant(30000,.1,10000),self.voice,self.policy);self.assertEqual(o.frames,30000);self.assertEqual(o.sample_rate,10000);self.assertEqual(r['time_transform'],'IDENTITY')
 def test_clock_mismatch(self):
  with self.assertRaises(AudioError):duck_music(constant(30000),self.voice)
 def test_partial_last_window(self):a=np.zeros((1001,1));a[-1]=1;e,w=build_duck_envelope(MixBuffer.from_array(a,10000));self.assertEqual(len(e),1001);self.assertTrue(w)
 def test_invalid_policy(self):
  for kw in ({'reduction_db':0},{'window_ms':0},{'attack_ms':True},{'threshold_dbfs':float('nan')},{'release_ms':0}):
   with self.subTest(kw=kw),self.assertRaises(AudioError):DuckingPolicy(**kw)
 def test_hash_repeatable(self):m=constant(30000,.1,10000);a,r=duck_music(m,self.voice,self.policy);b,s=duck_music(m,self.voice,self.policy);self.assertEqual(a.f64le,b.f64le);self.assertEqual(r,s)
 def test_source_unchanged(self):h=self.voice.sha256;duck_music(constant(30000,.1,10000),self.voice,self.policy);self.assertEqual(h,self.voice.sha256)
 def test_no_speech_recognition_claim(self):_,r=duck_music(constant(30000,.1,10000),self.voice);self.assertIn('not ASR',r['detector']);self.assertFalse(r['product_accepted'])
