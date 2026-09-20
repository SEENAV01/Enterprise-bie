from hashlib import sha256
from bie.animation_intelligence.map_contracts import *
def ctx(**kw):
 d=dict(intent_id="map",evidence_refs=("src","src2"),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),crs="EPSG:4326",source_revision=1)
 d.update(kw);return MapContext(**d)
def view(i,center=(0,0),scale=1000,crs="EPSG:4326",src="src"):
 return MapView(i,crs,center,scale,0,0,src)

import unittest
from bie.animation_intelligence.map_transition import animate_map_transition
from bie.animation_intelligence.route_region_animation import animate_route_region
class T(unittest.TestCase):
 def test_transition_then_route(self):
  tr=animate_map_transition(ctx(),source_view=view("overview",scale=10000),target_view=view("local",(1,1),1000),anchor=(1,1))
  rr=animate_route_region(ctx(),animation_id="route",route_points=((0,0),(1,1),(2,1)),route_source_ref="src")
  self.assertEqual((tr.status,rr.status),("PASS","PASS"))
 def test_shortest_path_guard(self):
  rr=animate_route_region(ctx(),animation_id="route",route_points=((0,0),(1,1)),route_source_ref="src",route_claim="shortest_path")
  self.assertEqual(rr.status,"BLOCKED")
 def test_projection_guard(self):
  tr=animate_map_transition(ctx(),source_view=view("a"),target_view=view("b",crs="EPSG:3857"))
  self.assertEqual(tr.status,"BLOCKED")
 def test_not_accepted(self):
  self.assertFalse(animate_route_region(ctx(),animation_id="route",route_points=((0,0),(1,1)),route_source_ref="src").accepted)
