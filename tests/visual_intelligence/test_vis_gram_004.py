import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.process_flow_grammar import plan_process_flow, PROCESS_FLOW_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def nodes(self): return [{'id':'a','kind':'start','source_ids':['s']},{'id':'b','kind':'process','source_ids':['s']},{'id':'c','kind':'end','source_ids':['s']}]
    def test_identity(self): self.assertEqual(PROCESS_FLOW_GRAMMAR.grammar_id,'bie.vis.grammar.process_flow')
    def test_linear(self): self.assertEqual(len(plan_process_flow(self.nodes(),[{'source':'a','target':'b','source_ids':['s']},{'source':'b','target':'c','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']).relations),2)
    def test_decision(self):
        n=self.nodes(); n[1]['kind']='decision'; p=plan_process_flow(n,[],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[1]['primitive'],'decision_node')
    def test_unknown_kind(self):
        with self.assertRaises(GrammarValidationError): plan_process_flow([{'id':'x','kind':'bad','source_ids':['s']}],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_unknown_edge(self):
        with self.assertRaises(GrammarValidationError): plan_process_flow(self.nodes(),[{'source':'a','target':'z'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_implicit_cycle_rejected(self):
        with self.assertRaises(GrammarValidationError): plan_process_flow(self.nodes(),[{'source':'a','target':'b','source_ids':['s']},{'source':'b','target':'a','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_explicit_loop_allowed(self):
        p=plan_process_flow(self.nodes(),[{'source':'a','target':'b','source_ids':['s']},{'source':'b','target':'a','kind':'feedback','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.relations[1]['payload']['explicit_loop'],True)
    def test_duplicate_node(self):
        with self.assertRaises(GrammarValidationError): plan_process_flow([{'id':'a','source_ids':['s']},{'id':'a','source_ids':['s']}],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_process_flow([],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self):
        kw=dict(nodes=self.nodes(),edges=[],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_process_flow(**kw).fingerprint,plan_process_flow(**kw).fingerprint)
if __name__=='__main__': unittest.main()
