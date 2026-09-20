import unittest,json
from bie.compiler.remotion_composition_discovery import *
class T(unittest.TestCase):
 def src(self):return '<Composition id={"Lesson"} component={Scene} width={1920} height={1080} fps={30} durationInFrames={300} />'
 def test_static(self):self.assertTrue(discover_compositions_static(self.src()).passed)
 def test_id(self):self.assertEqual(discover_compositions_static(self.src()).compositions[0].composition_id,"Lesson")
 def test_metadata(self):self.assertEqual(discover_compositions_static(self.src()).compositions[0].duration_in_frames,300)
 def test_json(self):self.assertEqual(parse_remotion_compositions_json(json.dumps([{"id":"A"}]))[0].composition_id,"A")
 def test_command(self):self.assertEqual(remotion_discovery_command("src/index.ts")[1:3],("remotion","compositions"))
 def test_empty(self):self.assertFalse(discover_compositions_static("const x=1;").passed)
 def test_not_empirical(self):self.assertFalse(discover_compositions_static(self.src()).empirical_cli)
