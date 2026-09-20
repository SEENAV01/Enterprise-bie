import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.data_chart_grammar import plan_chart, DATA_CHART_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def series(self): return [{'id':'a','values':[{'x':'A','y':1},{'x':'B','y':2}],'source_ids':['s']}]
    def test_identity(self): self.assertEqual(DATA_CHART_GRAMMAR.grammar_id,'bie.vis.grammar.data_chart')
    def test_bar(self): self.assertEqual(plan_chart(self.series(),chart_type='bar',x_label='cat',y_label='v',evidence_refs=['s'],reasoning_refs=['r']).elements[1]['primitive'],'bar')
    def test_line(self): self.assertEqual(plan_chart(self.series(),chart_type='line',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']).elements[1]['primitive'],'line_series')
    def test_scatter(self): self.assertEqual(plan_chart(self.series(),chart_type='scatter',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']).elements[1]['primitive'],'point_series')
    def test_error(self):
        s=[{'id':'a','values':[{'x':1,'y':2,'error':0.2}],'source_ids':['s']}]; p=plan_chart(s,chart_type='line',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['payload']['values'][0]['error'],0.2)
    def test_negative_error(self):
        s=[{'id':'a','values':[{'x':1,'y':2,'error':-1}]}]
        with self.assertRaises(GrammarValidationError): plan_chart(s,chart_type='line',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_negative_pie(self):
        s=[{'id':'a','values':[{'x':'A','y':-1}]}]
        with self.assertRaises(GrammarValidationError): plan_chart(s,chart_type='pie',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_nonzero_bar_baseline_warning(self): self.assertTrue(plan_chart(self.series(),chart_type='bar',x_label='x',y_label='y',y_baseline=10,evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_pie_warning(self): self.assertTrue(plan_chart(self.series(),chart_type='pie',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_bad_type(self):
        with self.assertRaises(GrammarValidationError): plan_chart(self.series(),chart_type='radar',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_chart([],chart_type='bar',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_duplicate(self):
        with self.assertRaises(GrammarValidationError): plan_chart(self.series()+self.series(),chart_type='bar',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self):
        kw=dict(series=self.series(),chart_type='bar',x_label='x',y_label='y',evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_chart(**kw).fingerprint,plan_chart(**kw).fingerprint)
if __name__=='__main__': unittest.main()
