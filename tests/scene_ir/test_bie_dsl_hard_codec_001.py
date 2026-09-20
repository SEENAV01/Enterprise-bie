import unittest,json
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.unified_scene_ir_codec import *
class T(unittest.TestCase):
 def make(self):
  e=UnifiedElement("e","text",{"text":"Hello"},("s",),("r",))
  t=UnifiedTrack("t","e","reveal",0,100,{},("s",),("r",))
  return UnifiedSceneIRDocument("scene","1.0.0","Title",100,(e,),(t,),("s",),("r",))
 def test_roundtrip(self):self.assertEqual(roundtrip_scene_ir(self.make()).fingerprint,self.make().fingerprint)
 def test_json_deterministic(self):self.assertEqual(encode_scene_ir(self.make()),encode_scene_ir(self.make()))
 def test_unknown_root(self):
  d=self.make().to_dict();d["mystery"]=1
  with self.assertRaises(SceneIRCodecError):decode_scene_ir(d)
 def test_unknown_element_field(self):
  d=self.make().to_dict();d["elements"][0]["mystery"]=1
  with self.assertRaises(SceneIRCodecError):decode_scene_ir(d)
 def test_accept_true_rejected(self):
  d=self.make().to_dict();d["accepted"]=True
  with self.assertRaises(SceneIRCodecError):decode_scene_ir(d)
 def test_bad_fingerprint(self):
  d=self.make().to_dict();d["fingerprint"]="0"*64
  with self.assertRaises(SceneIRCodecError):decode_scene_ir(d)
