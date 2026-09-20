import unittest
from bie.visual_intelligence.asset_contracts import *
from bie.visual_intelligence.generated_asset_request import *
def n():return AssetNeed("n","diagram",("diagram","vector"),("e",),("r",))
class T(unittest.TestCase):
 def test_req(self):self.assertEqual(request_generated_asset(n(),media_kind="diagram",prompt_spec={"goal":"x"}).action,"request_generated_asset")
 def test_evidence(self):self.assertEqual(request_generated_asset(n(),media_kind="diagram",prompt_spec={"goal":"x"}).request["evidence_refs"],["e"])
 def test_seed(self):self.assertEqual(request_generated_asset(n(),media_kind="diagram",prompt_spec={"goal":"x"},deterministic_seed=7).request["deterministic_seed"],7)
 def test_bad_kind(self):
  with self.assertRaises(AssetValidationError):request_generated_asset(n(),media_kind="image",prompt_spec={"goal":"x"})
 def test_empty(self):
  with self.assertRaises(AssetValidationError):request_generated_asset(n(),media_kind="diagram",prompt_spec={})
 def test_forbidden(self):
  with self.assertRaises(AssetValidationError):request_generated_asset(n(),media_kind="diagram",prompt_spec={"invent_data":True})
 def test_not_accepted(self):self.assertFalse(request_generated_asset(n(),media_kind="diagram",prompt_spec={"goal":"x"}).accepted)
