import unittest,json
from bie.compiler.audio_cue_sync_compiler import *
class T(unittest.TestCase):
 def cues(self):return [{"cue_id":"a","start_ms":0,"end_ms":1000},{"cue_id":"b","start_ms":1000,"end_ms":2000}]
 def segs(self):return [{"cue_id":"a","start_ms":20,"end_ms":1020},{"cue_id":"b","start_ms":1000,"end_ms":2000}]
 def test_pass(self):self.assertTrue(verify_audio_cue_sync(self.cues(),self.segs(),tolerance_ms=50).passed)
 def test_warning(self):self.assertTrue(verify_audio_cue_sync(self.cues(),self.segs(),tolerance_ms=50).warnings)
 def test_drift_block(self):
  x=self.segs();x[0]["start_ms"]=200;self.assertFalse(verify_audio_cue_sync(self.cues(),x,tolerance_ms=50).passed)
 def test_missing(self):self.assertFalse(verify_audio_cue_sync(self.cues(),self.segs()[:1]).passed)
 def test_frames(self):
  a,r=compile_audio_cue_manifest(self.cues(),self.segs(),fps=30,tolerance_ms=50);d=json.loads(a.content);self.assertEqual(d["entries"][1]["startFrame"],30)
 def test_not_accepted(self):self.assertFalse(verify_audio_cue_sync(self.cues(),self.segs()).accepted)
