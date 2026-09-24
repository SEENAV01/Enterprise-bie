import unittest
from dataclasses import replace
import numpy as np
from bie.audio.common import AudioError
from bie.audio.mix_contract import MixBuffer,SampleSpan
from bie.audio.sfx_mixing import place_stems,silence_music_windows,sum_buses
from .mix_test_support import constant,stem
class StemTests(unittest.TestCase):
 def place(self,items,**kw):return place_stems(tuple(items),rate=22050,channels=kw.pop('channels',1),frames=kw.pop('frames',4000),role=kw.pop('role','sfx'),**kw)
 def test_exact_placement(self):o,_=self.place([stem(constant(),start_sample=1000)]);self.assertTrue(np.all(o.array()[:1000]==0));self.assertTrue(np.all(o.array()[1000:2000]==.1));self.assertTrue(np.all(o.array()[2000:]==0))
 def test_trim(self):o,_=self.place([stem(constant(),trim_start=100,trim_end=200)]);self.assertTrue(np.all(o.array()[:100]==.1));self.assertTrue(np.all(o.array()[100:]==0))
 def test_explicit_repeat(self):o,_=self.place([stem(constant(),repeat=2)]);self.assertEqual(np.count_nonzero(o.array()),2000)
 def test_extension_blocked(self):
  with self.assertRaisesRegex(AudioError,'EXTENSION'):self.place([stem(constant(),start_sample=3500)])
 def test_rate_mismatch(self):
  with self.assertRaises(AudioError):self.place([stem(constant(rate=10000))])
 def test_no_implicit_downmix(self):
  with self.assertRaises(AudioError):self.place([stem(constant(channels=2))])
 def test_no_implicit_upmix(self):
  with self.assertRaises(AudioError):self.place([stem(constant())],channels=2)
 def test_dual_mono(self):o,_=self.place([stem(constant(),channel_map='mono_dual')],channels=2);np.testing.assert_array_equal(o.array()[:,0],o.array()[:,1])
 def test_equal_power_center(self):o,_=self.place([stem(constant(),channel_map='mono_equal_power')],channels=2);self.assertAlmostEqual(o.array()[50,0],.1/2**.5);self.assertAlmostEqual(o.array()[50,1],.1/2**.5)
 def test_equal_power_left(self):o,_=self.place([stem(constant(),channel_map='mono_equal_power',pan=-1)],channels=2);self.assertAlmostEqual(o.array()[50,0],.1);self.assertEqual(o.array()[50,1],0)
 def test_unused_pan_reject(self):
  with self.assertRaises(AudioError):stem(constant(),pan=.5)
 def test_required_rights_and_refs(self):
  for kw in ({'rights_ref':''},{'source_refs':()}):
   with self.subTest(kw=kw),self.assertRaises(AudioError):stem(constant(),**kw)
 def test_duplicate_ids(self):
  with self.assertRaises(AudioError):self.place([stem(constant()),stem(constant())])
 def test_stable_sum_order(self):a=stem(constant(value=.3),asset_id='a');b=stem(constant(value=.4),asset_id='b');self.assertEqual(self.place([a,b])[0].f64le,self.place([b,a])[0].f64le)
 def test_headroom_not_clamped(self):o,_=self.place([stem(constant(value=.9),asset_id='a'),stem(constant(value=.9),asset_id='b')]);self.assertAlmostEqual(o.sample_peak,1.8)
 def test_antiphase_cancellation(self):o,_=self.place([stem(constant(value=.2),asset_id='a'),stem(constant(value=-.2),asset_id='b')]);self.assertEqual(o.sample_peak,0)
 def test_fades(self):o,_=self.place([stem(constant(),fade_in_samples=100,fade_out_samples=100)]);self.assertEqual(o.array()[0,0],0);self.assertEqual(o.array()[999,0],0);self.assertAlmostEqual(o.array()[500,0],.1)
 def test_invalid_fades(self):
  with self.assertRaises(AudioError):stem(constant(),fade_in_samples=600,fade_out_samples=600)
 def test_invalid_trim_repeat(self):
  for kw in ({'trim_start':100,'trim_end':100},{'repeat':True},{'repeat':0}):
   with self.subTest(kw=kw),self.assertRaises(AudioError):stem(constant(),**kw)
 def test_protected_pause_blocks_sfx(self):
  with self.assertRaises(AudioError):self.place([stem(constant())],protected_silence=(SampleSpan(50,80,'pause',('source',)),))
 def test_music_is_zero_in_pause(self):m=constant(4000);o,r=silence_music_windows(m,(SampleSpan(1000,1500,'pause',('source',)),),fade_samples=100);self.assertTrue(np.all(o.array()[1000:1500]==0));self.assertEqual(o.frames,m.frames)
 def test_roles_not_confused(self):o,r=self.place([stem(constant(),role='music')]);self.assertEqual(o.sample_peak,0);self.assertFalse(r['product_accepted'])
 def test_unknown_bus_role(self):
  with self.assertRaises(AudioError):self.place([],role='narration')
 def test_clock_mismatch_on_bus_sum(self):
  with self.assertRaises(AudioError):sum_buses(constant(),constant(2000),constant())
 def test_receipt_keeps_sources(self):_,r=self.place([stem(constant())]);self.assertEqual(r['stems'][0]['rights_ref'],'synthetic:own-generated');self.assertEqual(r['stems'][0]['source_refs'],('synthetic:test',))
