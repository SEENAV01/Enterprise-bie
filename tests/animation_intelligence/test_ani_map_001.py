from hashlib import sha256
from bie.animation_intelligence.map_contracts import *
def ctx(**kw):
 d=dict(intent_id="map",evidence_refs=("src","src2"),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),crs="EPSG:4326",source_revision=1)
 d.update(kw);return MapContext(**d)
def view(i,center=(0,0),scale=1000,crs="EPSG:4326",src="src"):
 return MapView(i,crs,center,scale,0,0,src)

import unittest
from bie.animation_intelligence.map_transition import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate_map_transition(ctx(),source_view=view("a"),target_view=view("b",(1,1),500)).status,"REVIEW")
 def test_explicit_anchor_pass(self):self.assertEqual(animate_map_transition(ctx(),source_view=view("a"),target_view=view("b",(1,1),500),anchor=(0,0)).status,"PASS")
 def test_crs_block(self):self.assertEqual(animate_map_transition(ctx(),source_view=view("a"),target_view=view("b",crs="EPSG:3857")).status,"BLOCKED")
 def test_projection_review(self):self.assertEqual(animate_map_transition(ctx(),source_view=view("a"),target_view=view("b",crs="EPSG:3857"),allow_projection_change=True).status,"REVIEW")
 def test_large_scale_review(self):self.assertEqual(animate_map_transition(ctx(),source_view=view("a",scale=1),target_view=view("b",scale=1000),anchor=(0,0)).status,"REVIEW")
 def test_bad_kind(self):
  with self.assertRaises(MapAnimationError):animate_map_transition(ctx(),source_view=view("a"),target_view=view("b"),transition_kind="teleport")
 def test_grounding(self):
  with self.assertRaises(MapGroundingError):animate_map_transition(ctx(),source_view=view("a",src="x"),target_view=view("b"))
 def test_not_accepted(self):self.assertFalse(animate_map_transition(ctx(),source_view=view("a"),target_view=view("b"),anchor=(0,0)).accepted)
