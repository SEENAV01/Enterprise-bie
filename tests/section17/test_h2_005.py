import unittest,struct,math,hashlib
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.audio import AudioAccumulator,decode_audio
from bie.evaluation.benchmarks.av.process import Deadline
from bie.evaluation.benchmarks.av.probe import inspect
from bie.evaluation.benchmarks.av.custody import Limits
from h2_support import media
class H2005(unittest.TestCase):
 def acc(self,values,channels=1,rate=100):a=AudioAccumulator(rate,channels,10);a.feed(struct.pack('<'+'f'*len(values),*values));return a.finish()
 def test_exact_sample_count(self):self.assertEqual(self.acc([.1]*125)['samples_per_channel'],125)
 def test_partial_final_window_included(self):r=self.acc([.1]*15);self.assertEqual(r['windows'],2);self.assertEqual(r['samples_per_channel'],15)
 def test_per_channel_no_antiphase_downmix(self):r=self.acc([.1,-.1]*100,2);self.assertEqual(r['silent_samples_per_channel'],[0,0]);self.assertGreater(r['rms_per_channel'][0],.09)
 def test_silent_channel_not_hidden(self):r=self.acc([.1,0]*100,2);self.assertEqual(r['silent_samples_per_channel'],[0,100])
 def test_clipping_positive_and_negative(self):r=self.acc([1,-1,.1]);self.assertEqual(r['clipped_samples_per_channel'],[2])
 def test_silence_all_samples(self):self.assertEqual(self.acc([0]*100)['silent_samples_per_channel'],[100])
 def test_rms_computation(self):self.assertAlmostEqual(self.acc([.5]*20)['rms_per_channel'][0],.5)
 def test_nan_sample_rejected(self):
  with self.assertRaises(BenchmarkError):self.acc([float('nan')])
 def test_infinite_sample_rejected(self):
  with self.assertRaises(BenchmarkError):self.acc([float('inf')])
 def test_partial_interleaved_sample(self):
  with self.assertRaises(BenchmarkError):self.acc([1,1,1],channels=2)
 def test_empty_decode(self):
  with self.assertRaises(BenchmarkError):self.acc([])
 def test_sample_budget(self):
  a=AudioAccumulator(100,1,1)
  with self.assertRaises(BenchmarkError):a.feed(struct.pack('<110f',*([.1]*110)))
 def test_arbitrary_byte_splits_same_hash(self):
  data=struct.pack('<25f',*([.1]*25));a=AudioAccumulator(100,1,1)
  for b in data:a.feed(bytes([b]))
  self.assertEqual(a.finish()['decoded_sha256'],hashlib.sha256(data).hexdigest())
 def test_activity_merging_and_silence_split(self):self.assertEqual(self.acc([.1]*20+[0]*10+[.1]*10)['activity_intervals_relative_s'],[[0,.2],[.3,.4]])
 def test_original_rate_channels_actual(self):
  p=media('antiphase');d=Deadline(8);m,c=inspect(p,Limits(),d);r,c=decode_audio(p,m,Limits(),d)
  self.assertEqual((r['rate'],r['channels'],r['samples_per_channel']),(16000,2,32000));self.assertEqual(r['silent_samples_per_channel'],[0,0]);self.assertNotIn('-ac',c['argv']);self.assertNotIn('-ar',c['argv'])
 def test_no_audio_explicit_none(self):self.assertEqual(decode_audio(media(),{'audio':None},Limits(),Deadline(1)),(None,None))
 def test_invalid_audio_constructor_values(self):
  for rate,ch,dur in ((0,1,1),(100,0,1),(True,1,1),(100,1,0),(100,33,1)):
   with self.subTest(rate=rate,ch=ch,dur=dur),self.assertRaises(BenchmarkError):AudioAccumulator(rate,ch,dur)
 def test_invalid_audio_window(self):
  with self.assertRaises(BenchmarkError):AudioAccumulator(100,1,1,window_ms=0)
