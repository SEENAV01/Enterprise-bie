import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.history_timeline_grammar import plan_timeline, HISTORY_TIMELINE_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def event(self): return {'id':'e1','label':'Event','time_label':'1919','order_key':1919,'source_ids':['s']}
    def test_identity(self): self.assertEqual(HISTORY_TIMELINE_GRAMMAR.grammar_id,'bie.vis.grammar.history_timeline')
    def test_point_event(self): self.assertEqual(plan_timeline([self.event()],evidence_refs=['s'],reasoning_refs=['r']).elements[1]['primitive'],'event_marker')
    def test_uncertain_interval(self):
        e={'id':'e','time_label':'c. 1900','lower_bound':1895,'upper_bound':1905,'source_ids':['s']}; p=plan_timeline([e],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'uncertainty_band')
    def test_sorting(self):
        a=self.event(); b={'id':'e0','time_label':'1800','order_key':1800,'source_ids':['s']}; p=plan_timeline([a,b],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['id'],'event:e0')
    def test_missing_time_label(self):
        e=self.event(); e['time_label']=''
        with self.assertRaises(GrammarValidationError): plan_timeline([e],evidence_refs=['s'],reasoning_refs=['r'])
    def test_missing_order(self):
        e={'id':'e','time_label':'unknown','source_ids':['s']}
        with self.assertRaises(GrammarValidationError): plan_timeline([e],evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_bounds(self):
        e={'id':'e','time_label':'x','lower_bound':2,'upper_bound':1,'source_ids':['s']}
        with self.assertRaises(GrammarValidationError): plan_timeline([e],evidence_refs=['s'],reasoning_refs=['r'])
    def test_duplicate(self):
        with self.assertRaises(GrammarValidationError): plan_timeline([self.event(),self.event()],evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_timeline([],evidence_refs=['s'],reasoning_refs=['r'])
    def test_warning(self): self.assertTrue(plan_timeline([self.event()],evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_deterministic(self): self.assertEqual(plan_timeline([self.event()],evidence_refs=['s'],reasoning_refs=['r']).fingerprint,plan_timeline([self.event()],evidence_refs=['s'],reasoning_refs=['r']).fingerprint)
if __name__=='__main__': unittest.main()
