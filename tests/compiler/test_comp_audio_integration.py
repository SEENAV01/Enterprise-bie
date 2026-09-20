import unittest
from bie.compiler.voiceover_compiler import compile_voiceover_track
from bie.compiler.captions_compiler import compile_captions
from bie.compiler.subtitle_compiler import compile_subtitles
from bie.compiler.audio_cue_sync_compiler import compile_audio_cue_manifest
from bie.compiler.music_sfx_hooks_compiler import compile_music_sfx_hooks
from bie.compiler.deterministic_codegen import plan_deterministic_codegen

class T(unittest.TestCase):
 def test_audio_artifacts_join_codegen(self):
  voice=compile_voiceover_track({"track_id":"v","resolved_asset_path":"audio/voice.mp3","start_ms":0,"duration_ms":2000,"source_refs":["s"],"reasoning_refs":["r"]})
  captions=[{"text":"Hello","startMs":0,"endMs":1000,"timestampMs":None,"confidence":0.9},{"text":"World","startMs":1000,"endMs":2000,"timestampMs":None,"confidence":0.9}]
  cap,_=compile_captions(captions)
  srt,vtt=compile_subtitles(captions)
  sync,_=compile_audio_cue_manifest([{"cue_id":"a","start_ms":0,"end_ms":1000}],[{"cue_id":"a","start_ms":0,"end_ms":1000}],fps=30)
  hooks=compile_music_sfx_hooks([{"hook_id":"music","kind":"music","resolved_asset_path":"audio/music.mp3","start_ms":0,"duration_ms":2000,"volume":0.2}])
  arts=[voice,cap,srt,vtt,sync,hooks]
  cg=plan_deterministic_codegen(scene_fingerprint="a"*64,compiler_version="1.0.0",deterministic_seed=9,component_snapshot=(("audio","v1"),),files=[(x.path,x.content) for x in arts])
  self.assertEqual(len(cg.files),6)
  self.assertFalse(cg.accepted)

 def test_audio_assets_must_be_resolved(self):
  with self.assertRaises(Exception):
   compile_voiceover_track({"track_id":"v","resolved_asset_path":"asset://v","duration_ms":1000,"source_refs":["s"],"reasoning_refs":["r"]})
