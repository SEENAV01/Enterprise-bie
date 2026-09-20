import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.biology_cellular_grammar import plan_cellular_diagram, BIOLOGY_CELLULAR_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def comps(self): return [{'id':'cell','kind':'cell','source_ids':['s']},{'id':'n','kind':'organelle','parent_id':'cell','source_ids':['s']}]
    def test_identity(self): self.assertEqual(BIOLOGY_CELLULAR_GRAMMAR.grammar_id,'bie.vis.grammar.biology_cellular')
    def test_plan(self): self.assertEqual(len(plan_cellular_diagram(self.comps(),[],evidence_refs=['s'],reasoning_refs=['r']).elements),2)
    def test_scale_warning(self): self.assertTrue(plan_cellular_diagram(self.comps(),[],evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_scale_bar(self): self.assertFalse(plan_cellular_diagram(self.comps(),[],evidence_refs=['s'],reasoning_refs=['r'],scale_bar='10 µm').warnings)
    def test_transport(self):
        p=plan_cellular_diagram(self.comps(),[{'source':'cell','target':'n','substance':'Ca2+','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.relations[0]['payload']['substance'],'Ca2+')
    def test_missing_substance(self):
        with self.assertRaises(GrammarValidationError): plan_cellular_diagram(self.comps(),[{'source':'cell','target':'n'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_unknown_target(self):
        with self.assertRaises(GrammarValidationError): plan_cellular_diagram(self.comps(),[{'source':'cell','target':'x','substance':'x'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_kind(self):
        with self.assertRaises(GrammarValidationError): plan_cellular_diagram([{'id':'x','kind':'planet'}],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_cellular_diagram([],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self):
        kw=dict(components=self.comps(),transports=[],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_cellular_diagram(**kw).fingerprint,plan_cellular_diagram(**kw).fingerprint)
if __name__=='__main__': unittest.main()
