import unittest
from bie.visual_intelligence.asset_contracts import *
from bie.visual_intelligence.asset_need_detection import *
class T(unittest.TestCase):
 def test_map(self): self.assertIn("map",detect_asset_need(need_id="n",semantic_role="map",evidence_refs=["e"],reasoning_refs=["r"]).media_kinds)
 def test_ground(self): self.assertEqual(detect_asset_need(need_id="n",semantic_role="diagram",evidence_refs=["e"],reasoning_refs=["r"]).evidence_refs,("e",))
 def test_bad_rep(self):
  with self.assertRaises(AssetValidationError): detect_asset_need(need_id="n",semantic_role="x",representation="bad",evidence_refs=["e"],reasoning_refs=["r"])
 def test_bad_conf(self):
  with self.assertRaises(AssetValidationError): detect_asset_need(need_id="n",semantic_role="map",evidence_refs=["e"],reasoning_refs=["r"],confidence_score=2)
 def test_priority(self):
  with self.assertRaises(AssetValidationError): detect_asset_need(need_id="n",semantic_role="map",evidence_refs=["e"],reasoning_refs=["r"],priority=101)
 def test_no_evidence(self):
  with self.assertRaises(AssetValidationError): detect_asset_need(need_id="n",semantic_role="map",evidence_refs=[],reasoning_refs=["r"])
 def test_deterministic(self):
  a=detect_asset_need(need_id="n",semantic_role="map",evidence_refs=["e"],reasoning_refs=["r"]); self.assertEqual(a,a)
