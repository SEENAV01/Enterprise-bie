import unittest
from bie.compiler.voiceover_compiler import *
class T(unittest.TestCase):
 def x(self):return {"track_id":"vo","resolved_asset_path":"audio/voice.mp3","start_ms":100,"duration_ms":2000,"trim_before_ms":50,"volume":0.9,"source_refs":["s"],"reasoning_refs":["r"]}
 def test_audio(self):self.assertIn("<Audio",compile_voiceover_track(self.x()).content)
 def test_media(self):self.assertEqual(compile_voiceover_track(self.x()).required_dependencies,("@remotion/media",))
 def test_static(self):self.assertIn("staticFile",compile_voiceover_track(self.x()).content)
 def test_asset(self):self.assertEqual(compile_voiceover_track(self.x()).asset_paths,("audio/voice.mp3",))
 def test_unresolved(self):
  x=self.x();x["resolved_asset_path"]="asset://voice"
  with self.assertRaises(AudioCompilerError):compile_voiceover_track(x)
 def test_not_accepted(self):self.assertFalse(compile_voiceover_track(self.x()).accepted)
