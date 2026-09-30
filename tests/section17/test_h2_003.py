import unittest,json,copy
from unittest.mock import patch
from bie.evaluation.benchmarks.models import BenchmarkError
from bie.evaluation.benchmarks.av.probe import inspect,fraction,input_args
from bie.evaluation.benchmarks.av.process import Deadline
from bie.evaluation.benchmarks.av.custody import Limits
from h2_support import media
class H2003(unittest.TestCase):
 def setUp(self):self.raw={'streams':[{'index':0,'codec_type':'video','width':64,'height':36,'avg_frame_rate':'4/1','codec_name':'h264','pix_fmt':'yuv420p','sample_aspect_ratio':'1:1'}],'format':{'duration':'2','format_name':'mov,mp4,m4a,3gp,3g2,mj2'}}
 def probe(self,limits=Limits()):
  with patch('bie.evaluation.benchmarks.av.probe.capture',return_value=(json.dumps(self.raw).encode(),{})):return inspect(media('mp4'),limits,Deadline(3))[0]
 def test_actual_probe(self):m,c=inspect(media(),Limits(),Deadline(5));self.assertEqual((m['width'],m['height'],m['audio']['rate']),(64,36,16000))
 def test_zero_video(self):
  self.raw['streams']=[]
  with self.assertRaises(BenchmarkError):self.probe()
 def test_duplicate_video(self):
  self.raw['streams']*=2
  with self.assertRaises(BenchmarkError):self.probe()
 def test_ambiguous_audio(self):
  self.raw['streams']+=[{'codec_type':'audio'}]*2
  with self.assertRaises(BenchmarkError):self.probe()
 def test_embedded_subtitle_blocked(self):
  self.raw['streams'].append({'codec_type':'subtitle'})
  with self.assertRaises(BenchmarkError):self.probe()
 def test_resolution_budget(self):
  with self.assertRaises(BenchmarkError):self.probe(Limits(max_width=32))
 def test_duration_budget(self):
  with self.assertRaises(BenchmarkError):self.probe(Limits(max_duration_s=1))
 def test_hdr_rejected(self):
  self.raw['streams'][0]['color_transfer']='smpte2084'
  with self.assertRaises(BenchmarkError):self.probe()
 def test_rotation_rejected(self):
  self.raw['streams'][0]['side_data_list']=[{'rotation':90}]
  with self.assertRaises(BenchmarkError):self.probe()
 def test_nonsquare_pixel_rejected(self):
  self.raw['streams'][0]['sample_aspect_ratio']='2:1'
  with self.assertRaises(BenchmarkError):self.probe()
 def test_fps_zero(self):
  self.raw['streams'][0]['avg_frame_rate']='0/0'
  with self.assertRaises(BenchmarkError):self.probe()
 def test_unsupported_pixel_depth(self):
  self.raw['streams'][0]['pix_fmt']='yuv420p10le'
  with self.assertRaises(BenchmarkError):self.probe()
 def test_fraction_rational_exact(self):self.assertEqual(str(fraction('30000/1001')),'30000/1001')
 def test_fraction_nonfinite_boolean(self):
  for x in (True,'NaN','inf','1/0','3'*81):
   with self.subTest(x=x),self.assertRaises(BenchmarkError):fraction(x)
 def test_protocols_no_network_or_playlists(self):
  args=input_args(media());self.assertIn('file,pipe',args);self.assertIn('matroska,webm,mov',args);self.assertNotIn('http',str(args))
 def test_unknown_video_codec(self):
  self.raw['streams'][0]['codec_name']='unknown'
  with self.assertRaises(BenchmarkError):self.probe()
