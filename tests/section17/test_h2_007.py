import unittest,hashlib
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.captions import parse,intervals,coverage,alignment
class H2007(unittest.TestCase):
 def srt(self,text='Hello',start='00:00:00,000',end='00:00:02,000'):return f'1\n{start} --> {end}\n{text}\n'.encode()
 def test_srt_hindi_text_hash(self):r=parse(self.srt('नमस्ते'),'srt',2);self.assertEqual(r['text_sha256'],hashlib.sha256('नमस्ते'.encode()).hexdigest())
 def test_vtt_plain(self):r=parse(b'WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nHello\n','vtt',2);self.assertEqual(len(r['cues']),1)
 def test_windows_crlf(self):self.assertEqual(parse(self.srt().replace(b'\n',b'\r\n'),'srt',2)['cues'][0]['text'],'Hello')
 def test_overlap_rejected(self):
  b=self.srt()+b'\n2\n00:00:01,000 --> 00:00:02,000\nAgain\n'
  with self.assertRaises(BenchmarkError):parse(b,'srt',2)
 def test_time_outside_media(self):
  with self.assertRaises(BenchmarkError):parse(self.srt(end='00:00:03,000'),'srt',2)
 def test_markup_not_silently_removed(self):
  with self.assertRaises(BenchmarkError):parse(self.srt('<b>Hello</b>'),'srt',2)
 def test_vtt_settings_blocked(self):
  with self.assertRaises(BenchmarkError):parse(b'WEBVTT\n\n00:00:00.000 --> 00:00:02.000 line:10%\nHello','vtt',2)
 def test_invalid_minutes(self):
  with self.assertRaises(BenchmarkError):parse(self.srt(start='00:60:00,000'),'srt',2)
 def test_sequence_gap(self):
  with self.assertRaises(BenchmarkError):parse(self.srt().replace(b'1\n',b'2\n',1),'srt',2)
 def test_empty_caption(self):
  with self.assertRaises(BenchmarkError):parse(self.srt(''),'srt',2)
 def test_invalid_utf8(self):
  with self.assertRaises(BenchmarkError):parse(b'\xff','srt',2)
 def test_coverage_intersections(self):self.assertAlmostEqual(coverage([[0,2],[3,4]],[[0,1],[2,3.5]]),.5)
 def test_no_denominator_is_none(self):self.assertIsNone(coverage([],[]))
 def test_required_intervals_not_overlapping(self):
  with self.assertRaises(BenchmarkError):intervals([[0,2],[1,3]],3)
 def test_activity_offset_respected(self):r=alignment(None,[[1,2]],{'activity_intervals_relative_s':[[0,1]]},1);self.assertEqual(r['decoded_activity_coverage_of_declared_narration'],1)
 def test_no_asr_or_pronunciation_claim(self):r=alignment(parse(self.srt(),'srt',2),[[0,2]],None,0);self.assertFalse(r['speech_content_verified']);self.assertFalse(r['pronunciation_verified'])
