import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.mathematics_graph_grammar import plan_math_graph, MATHEMATICS_GRAPH_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def samples(self): return [{'id':'s1','kind':'samples','points':[[1,2],[2,4]],'source_ids':['s']}]
    def test_identity(self): self.assertEqual(MATHEMATICS_GRAPH_GRAMMAR.grammar_id,'bie.vis.grammar.mathematics_graph')
    def test_samples(self): self.assertFalse(plan_math_graph(self.samples(),x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']).elements[1]['payload']['interpolation_claim'])
    def test_sample_warning(self): self.assertTrue(plan_math_graph(self.samples(),x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_analytic(self):
        p=plan_math_graph([{'id':'f','kind':'analytic','expression':'x**2','source_ids':['s']}],x_label='x',y_label='f(x)',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['payload']['expression'],'x**2')
    def test_bad_scale(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph(self.samples(),x_label='x',y_label='y',x_scale='symlog',evidence_refs=['s'],reasoning_refs=['r'])
    def test_log_nonpositive(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph([{'id':'s','kind':'samples','points':[[0,1],[1,2]]}],x_label='x',y_label='y',x_scale='log',evidence_refs=['s'],reasoning_refs=['r'])
    def test_missing_expression(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph([{'id':'f','kind':'analytic'}],x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_short_samples(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph([{'id':'s','kind':'samples','points':[[1,2]]}],x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_duplicate(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph(self.samples()+self.samples(),x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph([],x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_blank_axis(self):
        with self.assertRaises(GrammarValidationError): plan_math_graph(self.samples(),x_label='',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self):
        kw=dict(series=self.samples(),x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_math_graph(**kw).fingerprint,plan_math_graph(**kw).fingerprint)
if __name__=='__main__': unittest.main()
