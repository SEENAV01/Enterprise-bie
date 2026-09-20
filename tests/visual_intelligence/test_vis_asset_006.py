import unittest
from bie.visual_intelligence.asset_contracts import *
from bie.visual_intelligence.asset_fallback import *
def n():return AssetNeed("n","graph",("graph","chart"),("e",),("r",))
class T(unittest.TestCase):
 def test_chart(self):self.assertEqual(choose_asset_fallback(n(),failed_kind="graph",reason="x").request["fallback_kind"],"chart")
 def test_filter(self):self.assertEqual(choose_asset_fallback(n(),failed_kind="graph",reason="x",available_kinds=["table"]).request["fallback_kind"],"table")
 def test_escalate(self):self.assertEqual(choose_asset_fallback(n(),failed_kind="graph",reason="x",available_kinds=["image"]).action,"escalate_asset_failure")
 def test_reason(self):
  with self.assertRaises(AssetValidationError):choose_asset_fallback(n(),failed_kind="graph",reason="")
 def test_preserve(self):self.assertTrue(choose_asset_fallback(n(),failed_kind="graph",reason="x").request["preserve_required_semantics"])
 def test_unknown(self):self.assertEqual(choose_asset_fallback(n(),failed_kind="unknown",reason="x").request["fallback_kind"],"textual_callout")
 def test_not_accepted(self):self.assertFalse(choose_asset_fallback(n(),failed_kind="graph",reason="x").accepted)
