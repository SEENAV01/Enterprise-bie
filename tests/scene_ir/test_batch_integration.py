import unittest
from bie.scene_ir.scene_ir_contract import *
from bie.scene_ir.scene_ir_json_schema import *
from bie.scene_ir.scene_ir_semver import *
from bie.scene_ir.scene_ir_migration import *
class TestIntegration(unittest.TestCase):
 def test_ani_shape_to_ir(self):
  ani={"track_id":"t1","action":"reveal","target_ids":["v1"],"start_ms":0,"end_ms":500,"source_refs":["src"],"reasoning_refs":["r"]}
  e=SceneElement("v1","diagram",("src",),("r",),{"semantic_id":"x"},{"alt":"diagram"})
  t=SceneTrack(ani["track_id"],ani["target_ids"][0],ani["action"],ani["start_ms"],ani["end_ms"],{},tuple(ani["source_refs"]),tuple(ani["reasoning_refs"]))
  s=SceneIR("scene","1.0.0","Example",500,(e,),(t,),("src",),("r",),("reveal",))
  self.assertTrue(s.ir_fingerprint);self.assertFalse(s.accepted)
 def test_schema_version_agreement(self):
  self.assertTrue(validate_json_schema_shape(SCENE_IR_JSON_SCHEMA));self.assertEqual(compatibility("1.0.0","1.0.0"),"COMPATIBLE")
 def test_forward_migration(self):
  d,r=migrate_scene_ir({"schema_version":"1.0.0"},"1.1.0");self.assertEqual(d["schema_version"],"1.1.0");self.assertFalse(r.lossy)
