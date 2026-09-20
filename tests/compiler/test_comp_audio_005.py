import unittest
from bie.compiler.music_sfx_hooks_compiler import *
class T(unittest.TestCase):
 def h(self):return [{"hook_id":"music","kind":"music","resolved_asset_path":"audio/music.mp3","start_ms":0,"duration_ms":5000,"volume":0.4,"loop":True,"duck_under_voiceover":True},{"hook_id":"ding","kind":"sfx","resolved_asset_path":"audio/ding.wav","start_ms":1000,"duration_ms":500,"volume":1.0}]
 def test_audio(self):self.assertEqual(compile_music_sfx_hooks(self.h()).content.count("<Audio"),2)
 def test_loop(self):self.assertIn("loop={true}",compile_music_sfx_hooks(self.h()).content)
 def test_assets(self):self.assertEqual(set(compile_music_sfx_hooks(self.h()).asset_paths),{"audio/music.mp3","audio/ding.wav"})
 def test_warning(self):self.assertTrue(compile_music_sfx_hooks(self.h()).warnings)
 def test_duplicate(self):
  h=self.h();h.append(dict(h[0]))
  with self.assertRaises(AudioCompilerError):compile_music_sfx_hooks(h)
 def test_kind(self):
  h=self.h();h[0]["kind"]="voice"
  with self.assertRaises(AudioCompilerError):compile_music_sfx_hooks(h)
