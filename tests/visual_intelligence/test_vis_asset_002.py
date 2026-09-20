import unittest
from bie.visual_intelligence.asset_contracts import *
from bie.visual_intelligence.source_asset_reuse import *
def n():return AssetNeed("n","map",("map","image"),("e",),("r",))
def c(i,source="source",kind="map",tags=("map",),prov=("e",),q=.8):return AssetCandidate(i,source,kind,tags,prov,quality_score=q)
class T(unittest.TestCase):
 def test_score(self):self.assertGreater(score_source_asset(n(),c("a")).score,.7)
 def test_choose(self):self.assertEqual(choose_source_reuse(n(),[c("a")]).selected_asset_id,"a")
 def test_non_source(self):self.assertEqual(score_source_asset(n(),c("a","external")).score,0)
 def test_empty(self):self.assertEqual(choose_source_reuse(n(),[]).action,"reuse_unavailable")
 def test_low(self):self.assertEqual(choose_source_reuse(n(),[c("a",kind="image",tags=(),prov=("x",),q=0)]).action,"reuse_unavailable")
 def test_tie(self):self.assertEqual(choose_source_reuse(n(),[c("b"),c("a")]).selected_asset_id,"a")
 def test_not_accepted(self):self.assertFalse(choose_source_reuse(n(),[c("a")]).accepted)
