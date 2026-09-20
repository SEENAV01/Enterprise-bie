import unittest
from bie.compiler.subtitle_compiler import *
class T(unittest.TestCase):
 def c(self):return [{"text":"Hello","startMs":0,"endMs":1234,"timestampMs":None,"confidence":None}]
 def test_srt(self):self.assertIn("00:00:00,000 --> 00:00:01,234",captions_to_srt(self.c()))
 def test_vtt(self):self.assertTrue(captions_to_webvtt(self.c()).startswith("WEBVTT"))
 def test_vtt_time(self):self.assertIn("00:00:00.000 --> 00:00:01.234",captions_to_webvtt(self.c()))
 def test_paths(self):self.assertEqual([x.path for x in compile_subtitles(self.c())],["public/captions/subtitles.srt","public/captions/subtitles.vtt"])
 def test_text(self):self.assertIn("Hello",captions_to_srt(self.c()))
 def test_deterministic(self):self.assertEqual(captions_to_webvtt(self.c()),captions_to_webvtt(self.c()))
