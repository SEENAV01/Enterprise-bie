from hashlib import sha256
from bie.animation_intelligence.map_contracts import *
def ctx(**kw):
 d=dict(intent_id="map",evidence_refs=("src","src2"),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),crs="EPSG:4326",source_revision=1)
 d.update(kw);return MapContext(**d)
def view(i,center=(0,0),scale=1000,crs="EPSG:4326",src="src"):
 return MapView(i,crs,center,scale,0,0,src)

import unittest
from bie.animation_intelligence.route_region_animation import *
ROUTE=((0,0),(1,1),(2,1))
REG=({"region_id":"r1","boundary":[(0,0),(1,0),(1,1),(0,0)]},)
class T(unittest.TestCase):
 def test_route_pass(self):self.assertEqual(animate_route_region(ctx(),animation_id="x",route_points=ROUTE,route_source_ref="src").status,"PASS")
 def test_region_pass(self):self.assertEqual(animate_route_region(ctx(),animation_id="x",regions=REG,region_source_ref="src2").status,"PASS")
 def test_both(self):self.assertEqual(len(animate_route_region(ctx(),animation_id="x",route_points=ROUTE,route_source_ref="src",regions=REG,region_source_ref="src2").operations),2)
 def test_unordered_block(self):self.assertEqual(animate_route_region(ctx(),animation_id="x",route_points=ROUTE,route_source_ref="src",ordered=False).status,"BLOCKED")
 def test_claim_block(self):self.assertEqual(animate_route_region(ctx(),animation_id="x",route_points=ROUTE,route_source_ref="src",route_claim="shortest_path").status,"BLOCKED")
 def test_claim_pass(self):self.assertEqual(animate_route_region(ctx(payload={"route_evidence_level":"verified_network"}),animation_id="x",route_points=ROUTE,route_source_ref="src",route_claim="shortest_path").status,"PASS")
 def test_bad_region(self):
  with self.assertRaises(MapTopologyError):animate_route_region(ctx(),animation_id="x",regions=({"region_id":"r","boundary":[(0,0),(1,0)]},),region_source_ref="src2")
 def test_not_accepted(self):self.assertFalse(animate_route_region(ctx(),animation_id="x",route_points=ROUTE,route_source_ref="src").accepted)
