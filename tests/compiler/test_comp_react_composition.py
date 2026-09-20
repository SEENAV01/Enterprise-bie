import unittest
from bie.compiler.composition_emitter import *
class T(unittest.TestCase):
 def test_emit(self):
  c=emit_composition(composition_id="Lesson",width=1920,height=1080,fps=30,duration_in_frames=300);self.assertIn("<Composition",c.content)
 def test_dimensions(self):self.assertIn("width={1920}",emit_composition(composition_id="L",width=1920,height=1080,fps=30,duration_in_frames=10).content)
 def test_props(self):self.assertIn('"topic": "Force"',emit_composition(composition_id="L",width=1,height=1,fps=1,duration_in_frames=1,default_props={"topic":"Force"}).content)
 def test_invalid(self):
  with self.assertRaises(ReactEmitterError):emit_composition(composition_id="L",width=0,height=1,fps=1,duration_in_frames=1)
 def test_scene_import(self):self.assertIn('from "./Scene"',emit_composition(composition_id="L",width=1,height=1,fps=1,duration_in_frames=1).content)
 def test_hash(self):self.assertEqual(len(emit_composition(composition_id="L",width=1,height=1,fps=1,duration_in_frames=1).sha256),64)
