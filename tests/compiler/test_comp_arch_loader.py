import unittest,tempfile,json
from pathlib import Path
from bie.scene_ir.unified_scene_ir_contract import *
from bie.compiler.scene_ir_loader import *
class T(unittest.TestCase):
 def doc(self):
  e=UnifiedElement("e","text",{"text":"Hello"},("s",),("r",));t=UnifiedTrack("t","e","reveal",0,10,{},("s",),("r",))
  return UnifiedSceneIRDocument("scene","1.0.0","T",10,(e,),(t,),("s",),("r",))
 def test_typed(self):
  r=load_scene_ir_payload(self.doc());self.assertTrue(r.validation_passed);self.assertEqual(r.scene_fingerprint,self.doc().fingerprint)
 def test_mapping(self):self.assertEqual(load_scene_ir_payload(self.doc().to_dict()).scene_id,"scene")
 def test_json(self):self.assertEqual(load_scene_ir_payload(json.dumps(self.doc().to_dict())).scene_id,"scene")
 def test_file(self):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);p=td/"scene.json";p.write_text(json.dumps(self.doc().to_dict()),encoding="utf-8")
   self.assertEqual(load_scene_ir_file(p,td).source_kind,"file")
 def test_escape(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   p=Path(a)/"x.json";p.write_text("{}",encoding="utf-8")
   with self.assertRaises(SceneIRLoadError):load_scene_ir_file(p,b)
 def test_not_accepted(self):self.assertFalse(load_scene_ir_payload(self.doc()).accepted)
