import unittest,hashlib
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.video import VideoAccumulator,decode_video
from bie.evaluation.benchmarks.av.probe import inspect
from bie.evaluation.benchmarks.av.custody import Limits
from bie.evaluation.benchmarks.av.process import Deadline
from h2_support import media
class H2004(unittest.TestCase):
 def acc(self,data,max_frames=10):a=VideoAccumulator(1,1,max_frames);a.feed(data);return a.finish()
 def test_all_frames_count(self):self.assertEqual(self.acc(b'abc'*5)['decoded_frames'],5)
 def test_full_byte_hash(self):self.assertEqual(self.acc(b'abcxyz')['decoded_sha256'],hashlib.sha256(b'abcxyz').hexdigest())
 def test_chunk_boundaries(self):
  a=VideoAccumulator(1,1,10)
  for x in b'abcxyz':a.feed(bytes([x]))
  self.assertEqual(a.finish(),self.acc(b'abcxyz'))
 def test_partial_frame_rejected(self):
  with self.assertRaises(BenchmarkError):self.acc(b'ab')
 def test_empty_decode_rejected(self):
  with self.assertRaises(BenchmarkError):self.acc(b'')
 def test_frame_budget_no_truncation(self):
  with self.assertRaises(BenchmarkError):self.acc(b'abc'*3,2)
 def test_black_frame_detection(self):self.assertEqual(self.acc(bytes([0,0,0]))['dark_frames'],1)
 def test_bright_frame_not_black(self):self.assertEqual(self.acc(bytes([255,255,255]))['dark_frames'],0)
 def test_dark_code_boundary(self):self.assertEqual(self.acc(bytes([16,16,16,17,17,17]))['dark_frames'],1)
 def test_identical_frame_run(self):r=self.acc(b'abc'*4);self.assertEqual(r['same_transitions'],3);self.assertEqual(r['max_same_run_transitions'],3)
 def test_freeze_run_reset(self):self.assertEqual(self.acc(b'abcabcxyzabcabcabc')['max_same_run_transitions'],2)
 def test_first_and_last_hashes(self):r=self.acc(b'abcxyz');self.assertEqual(r['first_frame_sha256'],hashlib.sha256(b'abc').hexdigest());self.assertEqual(r['last_frame_sha256'],hashlib.sha256(b'xyz').hexdigest())
 def test_frame_chain_order_sensitive(self):self.assertNotEqual(self.acc(b'abcxyz')['frame_chain_sha256'],self.acc(b'xyzabc')['frame_chain_sha256'])
 def test_actual_video_all_pixels(self):
  p=media();d=Deadline(8);m,c=inspect(p,Limits(),d);r,c=decode_video(p,m,Limits(),d);self.assertEqual(r['decoded_frames'],8);self.assertEqual(c['stdout_bytes'],64*36*3*8)
  self.assertNotIn('-t',c['argv']);self.assertNotIn('-vf',c['argv']);self.assertIn('passthrough',c['argv'])
 def test_actual_decoded_byte_budget(self):
  p=media();d=Deadline(5);m,c=inspect(p,Limits(),d)
  with self.assertRaises(BenchmarkError):decode_video(p,m,Limits(max_decoded_bytes=1000),d)
 def test_invalid_dimensions_rejected_at_constructor(self):
  for w,h in ((0,1),(-1,1),(True,1),(1,0),(7681,1)):
   with self.subTest(w=w,h=h),self.assertRaises(BenchmarkError):VideoAccumulator(w,h,10)
 def test_invalid_frame_limit_rejected_at_constructor(self):
  with self.assertRaises(BenchmarkError):VideoAccumulator(1,1,0)
