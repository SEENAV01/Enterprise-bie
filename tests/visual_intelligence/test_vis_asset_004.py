import unittest
from bie.visual_intelligence.asset_contracts import *
from bie.visual_intelligence.external_asset_request import *
def n():return AssetNeed("n","image",("image",),("e",),("r",))
class T(unittest.TestCase):
 def test_req(self):self.assertEqual(request_external_asset(n(),media_kind="image",query_terms=["cell"]).action,"request_external_asset")
 def test_terms(self):self.assertEqual(request_external_asset(n(),media_kind="image",query_terms=["cell"]).request["query_terms"],["cell"])
 def test_domains(self):self.assertEqual(request_external_asset(n(),media_kind="image",query_terms=["x"],allowed_domains=["B.org","a.org"]).request["allowed_domains"],["a.org","b.org"])
 def test_rights(self):self.assertTrue(request_external_asset(n(),media_kind="image",query_terms=["x"]).request["require_rights_metadata"])
 def test_bad_kind(self):
  with self.assertRaises(AssetValidationError):request_external_asset(n(),media_kind="map",query_terms=["x"])
 def test_empty(self):
  with self.assertRaises(AssetValidationError):request_external_asset(n(),media_kind="image",query_terms=[])
 def test_review(self):self.assertTrue(request_external_asset(n(),media_kind="image",query_terms=["x"]).review_required)
