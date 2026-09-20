import unittest
from bie.scene_ir.ani_dsl_adopter import *
class T(unittest.TestCase):
 def handoff(self):
  return {"handoff_id":"ani:h","tracks":[{"track_id":"t","action":"reveal","target_ids":["e"],"start_ms":0,"end_ms":100,"source_refs":["src"],"reasoning_refs":["r"],"parameters":{}}]}
 def catalog(self):
  return [{"element_id":"e","element_type":"text","props":{"text":"Hello"},"source_refs":["src"],"reasoning_refs":["r"],"accessibility":{}}]
 def test_pass(self):
  d,r=adopt_ani_handoff(self.handoff(),scene_id="s",title="T",duration_ms=100,element_catalog=self.catalog(),ani_revision=3)
  self.assertEqual(d.upstream_revision,3);self.assertEqual(r.adopted_track_count,1)
 def test_unknown_target(self):
  h=self.handoff();h["tracks"][0]["target_ids"]=["x"]
  with self.assertRaises(AniAdoptionError):adopt_ani_handoff(h,scene_id="s",title="T",duration_ms=100,element_catalog=self.catalog())
 def test_no_tracks(self):
  with self.assertRaises(AniAdoptionError):adopt_ani_handoff({"handoff_id":"h","tracks":[]},scene_id="s",title="T",duration_ms=100,element_catalog=self.catalog())
 def test_lineage(self):
  c=self.catalog();c[0]["source_refs"]=[]
  with self.assertRaises(Exception):adopt_ani_handoff(self.handoff(),scene_id="s",title="T",duration_ms=100,element_catalog=c)
 def test_not_accepted(self):
  _,r=adopt_ani_handoff(self.handoff(),scene_id="s",title="T",duration_ms=100,element_catalog=self.catalog())
  self.assertFalse(r.accepted)
