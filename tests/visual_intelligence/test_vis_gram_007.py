import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.geography_map_grammar import plan_map, GEOGRAPHY_MAP_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def test_identity(self): self.assertEqual(GEOGRAPHY_MAP_GRAMMAR.grammar_id,'bie.vis.grammar.geography_map')
    def test_point(self):
        p=plan_map([{'id':'a','kind':'point','coordinates':[77,28],'source_ids':['s']}],crs='EPSG:4326',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'point_marker')
    def test_route(self):
        p=plan_map([{'id':'r','kind':'route','coordinates':[[77,28],[78,29]],'source_ids':['s']}],crs='EPSG:4326',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'route')
    def test_region(self):
        p=plan_map([{'id':'r','kind':'region','coordinates':[[0,0],[1,0],[1,1]],'source_ids':['s']}],crs='local',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'region')
    def test_incompatible_crs(self):
        with self.assertRaises(GrammarValidationError): plan_map([{'id':'a','kind':'point','coordinates':[1,2],'crs':'A'}],crs='B',evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_extent(self):
        with self.assertRaises(GrammarValidationError): plan_map([{'id':'a','kind':'point','coordinates':[1,2]}],crs='x',map_extent=[2,0,1,3],evidence_refs=['s'],reasoning_refs=['r'])
    def test_short_route(self):
        with self.assertRaises(GrammarValidationError): plan_map([{'id':'r','kind':'route','coordinates':[[1,2]]}],crs='x',evidence_refs=['s'],reasoning_refs=['r'])
    def test_short_region(self):
        with self.assertRaises(GrammarValidationError): plan_map([{'id':'r','kind':'region','coordinates':[[0,0],[1,0]]}],crs='x',evidence_refs=['s'],reasoning_refs=['r'])
    def test_duplicate(self):
        with self.assertRaises(GrammarValidationError): plan_map([{'id':'a','kind':'point','coordinates':[1,2]},{'id':'a','kind':'point','coordinates':[2,3]}],crs='x',evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_map([],crs='x',evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self):
        kw=dict(features=[{'id':'a','kind':'point','coordinates':[77,28],'source_ids':['s']}],crs='EPSG:4326',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_map(**kw).fingerprint,plan_map(**kw).fingerprint)
if __name__=='__main__': unittest.main()
