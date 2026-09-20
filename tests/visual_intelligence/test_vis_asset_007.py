import unittest
from bie.visual_intelligence.asset_contracts import *
from bie.visual_intelligence.asset_quality import *
def a():return AssetCandidate("a","source","image",("context",),("e",),quality_score=.8)
def g():return {"semantic_alignment":.9,"legibility":.9,"resolution":.9,"provenance_quality":.9}
class T(unittest.TestCase):
 def test_score(self):self.assertGreater(evaluate_asset_quality(a(),metrics=g(),rights_ready=True).weighted_score,.8)
 def test_ready(self):self.assertTrue(production_ready(evaluate_asset_quality(a(),metrics=g(),rights_ready=True)))
 def test_rights(self):self.assertIn("rights_not_ready",evaluate_asset_quality(a(),metrics=g(),rights_ready=False).blockers)
 def test_floor(self):
  m=g();m["semantic_alignment"]=.5;self.assertIn("semantic_alignment_below_floor",evaluate_asset_quality(a(),metrics=m,rights_ready=True).blockers)
 def test_missing(self):
  with self.assertRaises(AssetValidationError):evaluate_asset_quality(a(),metrics={"semantic_alignment":.9},rights_ready=True)
 def test_bad(self):
  m=g();m["resolution"]=2
  with self.assertRaises(AssetValidationError):evaluate_asset_quality(a(),metrics=m,rights_ready=True)
 def test_threshold(self):
  with self.assertRaises(AssetValidationError):production_ready(evaluate_asset_quality(a(),metrics=g(),rights_ready=True),threshold=2)
