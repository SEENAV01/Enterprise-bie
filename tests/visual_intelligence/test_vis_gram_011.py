import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.geometry_grammar import plan_geometry, GEOMETRY_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def points(self): return [{'id':'A','kind':'point','coordinates':[0,0],'source_ids':['s']},{'id':'B','kind':'point','coordinates':[1,0],'source_ids':['s']}]
    def test_identity(self): self.assertEqual(GEOMETRY_GRAMMAR.grammar_id,'bie.vis.grammar.geometry')
    def test_points(self): self.assertEqual(len(plan_geometry(self.points(),evidence_refs=['s'],reasoning_refs=['r']).elements),2)
    def test_segment_refs(self):
        p=plan_geometry(self.points()+[{'id':'AB','kind':'segment','refs':['A','B'],'source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[2]['payload']['refs'],['A','B'])
    def test_dimension(self):
        p=plan_geometry([{'id':'d','kind':'dimension','value':5,'unit':'cm','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[0]['payload']['unit'],'cm')
    def test_dimension_unit_required(self):
        with self.assertRaises(GrammarValidationError): plan_geometry([{'id':'d','kind':'dimension','value':5}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_unknown_ref(self):
        with self.assertRaises(GrammarValidationError): plan_geometry([{'id':'AB','kind':'segment','refs':['A','B'],'source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_kind(self):
        with self.assertRaises(GrammarValidationError): plan_geometry([{'id':'x','kind':'sphere'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_duplicate(self):
        with self.assertRaises(GrammarValidationError): plan_geometry(self.points()+[self.points()[0]],evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_geometry([],evidence_refs=['s'],reasoning_refs=['r'])
    def test_warning(self): self.assertTrue(plan_geometry(self.points(),evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_deterministic(self): self.assertEqual(plan_geometry(self.points(),evidence_refs=['s'],reasoning_refs=['r']).fingerprint,plan_geometry(self.points(),evidence_refs=['s'],reasoning_refs=['r']).fingerprint)
if __name__=='__main__': unittest.main()
