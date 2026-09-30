import unittest,copy
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.timeline import Timeline,consistency
from bie.evaluation.benchmarks.av.custody import Limits
class H2006(unittest.TestCase):
 def setUp(self):self.m={'width':64,'height':36,'fps':'4','duration_s':'2','audio':{'rate':16000}};self.t=Timeline('video',self.m,Limits())
 def line(self,pts,duration='.25',w=64):return f'media_type=video|best_effort_timestamp_time={pts}|duration_time={duration}|width={w}|height=36'
 def test_exact_timeline(self):
  for n in range(8):self.t.line(self.line(n/4))
  r=self.t.finish();self.assertEqual((r['frames'],r['start_s'],r['end_s'],r['max_gap_s']),(8,0,2,0))
 def test_missing_pts(self):
  with self.assertRaises(BenchmarkError):self.t.line('media_type=video|width=64|height=36')
 def test_negative_pts(self):
  with self.assertRaises(BenchmarkError):self.t.line(self.line(-.25))
 def test_duplicate_pts(self):
  self.t.line(self.line(0))
  with self.assertRaises(BenchmarkError):self.t.line(self.line(0))
 def test_backward_pts(self):
  self.t.line(self.line(.5))
  with self.assertRaises(BenchmarkError):self.t.line(self.line(.25))
 def test_gap_measured(self):self.t.line(self.line(0));self.t.line(self.line(.5));self.assertEqual(self.t.finish()['max_gap_s'],.25)
 def test_overlap_measured(self):self.t.line(self.line(0,duration='.5'));self.t.line(self.line(.25));self.assertEqual(self.t.finish()['max_overlap_s'],.25)
 def test_missing_duration_fallback_explicit_cfr(self):self.t.line(self.line(0,duration='0'));self.assertEqual(self.t.finish()['end_s'],.25)
 def test_resolution_change(self):
  with self.assertRaises(BenchmarkError):self.t.line(self.line(0,w=32))
 def test_timing_count_budget(self):
  t=Timeline('video',self.m,Limits(max_frames=1));t.line(self.line(0))
  with self.assertRaises(BenchmarkError):t.line(self.line(.25))
 def test_audio_uses_sample_count(self):
  t=Timeline('audio',self.m,Limits());t.line('media_type=audio|best_effort_timestamp_time=0|nb_samples=1600');r=t.finish();self.assertEqual(r['samples'],1600);self.assertEqual(r['end_s'],.1)
 def test_invalid_audio_samples(self):
  with self.assertRaises(BenchmarkError):Timeline('audio',self.m,Limits()).line('media_type=audio|best_effort_timestamp_time=0|nb_samples=-1')
 def test_decoded_timing_count_must_match(self):
  with self.assertRaises(BenchmarkError):consistency(self.m,{'decoded_frames':8},{'frames':7},None,None)
 def test_missing_audio_timing(self):
  with self.assertRaises(BenchmarkError):consistency(self.m,{'decoded_frames':8},{'frames':8},{},None)
 def test_audio_pts_sample_count_mismatch(self):
  vt={'frames':8,'start_s':0,'end_s':2,'max_gap_s':0,'max_overlap_s':0,'max_step_error_s':0}
  with self.assertRaises(BenchmarkError):consistency(self.m,{'decoded_frames':8},vt,{'samples_per_channel':32000},{'samples':31999})
 def test_variable_fps_detected(self):
  vt={'frames':8,'start_s':0,'end_s':2,'max_gap_s':0,'max_overlap_s':0,'max_step_error_s':.1}
  self.assertIn('NONCONSTANT_FRAME_RATE',consistency(self.m,{'decoded_frames':8},vt,None,None))
 def test_unknown_timeline_kind(self):
  with self.assertRaises(BenchmarkError):Timeline('subtitle',self.m,Limits())
