import unittest
from bie.visual_intelligence.asset_qa import *
def a(i="a",prov=("e",),s=.9,q=.9,rights=True,uri=False,gen=False,checked=False): return AssetItem(i,True,prov,s,q,rights,uri,gen,checked)
class T(unittest.TestCase):
 def test_pass(self): self.assertTrue(evaluate_asset_qa([a()],["e"],["r"]).passed)
 def test_rights(self): self.assertIn("asset_blocker:a",evaluate_asset_qa([a(rights=False)],["e"],["r"]).blockers)
 def test_uri(self): self.assertIn("unresolved_uri",evaluate_asset_qa([a(uri=True)],["e"],["r"]).metrics["issues"]["a"])
 def test_generated(self): self.assertIn("generated_not_grounding_checked",evaluate_asset_qa([a(gen=True)],["e"],["r"]).metrics["issues"]["a"])
 def test_prov(self): self.assertIn("missing_evidence_overlap",evaluate_asset_qa([a(prov=("x",))],["e"],["r"]).metrics["issues"]["a"])
 def test_quality(self): self.assertIn("asset_quality_warning:a",evaluate_asset_qa([a(q=.5)],["e"],["r"]).warnings)
 def test_dup(self):
  with self.assertRaises(AssetQAError): evaluate_asset_qa([a("a"),a("a")],["e"],["r"])
