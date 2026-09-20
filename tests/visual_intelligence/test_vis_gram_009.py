import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.causal_network_grammar import plan_causal_network, CAUSAL_NETWORK_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def nodes(self): return [{'id':'a','role':'cause','source_ids':['s']},{'id':'b','role':'effect','source_ids':['s']}]
    def test_identity(self): self.assertEqual(CAUSAL_NETWORK_GRAMMAR.grammar_id,'bie.vis.grammar.causal_network')
    def test_causal_edge(self):
        p=plan_causal_network(self.nodes(),[{'source':'a','target':'b','kind':'causes','evidence_kind':'experimental','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.relations[0]['kind'],'causes')
    def test_association_warning(self):
        p=plan_causal_network(self.nodes(),[{'source':'a','target':'b','kind':'associated','evidence_kind':'observational','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r']); self.assertTrue(p.warnings)
    def test_bad_causal_evidence(self):
        with self.assertRaises(GrammarValidationError): plan_causal_network(self.nodes(),[{'source':'a','target':'b','kind':'causes','evidence_kind':'observational'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_cycle_rejected(self):
        e=[{'source':'a','target':'b','kind':'causes','evidence_kind':'causal','source_ids':['s']},{'source':'b','target':'a','kind':'causes','evidence_kind':'causal','source_ids':['s']}]
        with self.assertRaises(GrammarValidationError): plan_causal_network(self.nodes(),e,evidence_refs=['s'],reasoning_refs=['r'])
    def test_feedback_allowed(self):
        e=[{'source':'a','target':'b','kind':'causes','evidence_kind':'causal','source_ids':['s']},{'source':'b','target':'a','kind':'feedback','evidence_kind':'causal','source_ids':['s']}]; self.assertEqual(len(plan_causal_network(self.nodes(),e,evidence_refs=['s'],reasoning_refs=['r']).relations),2)
    def test_unknown_node(self):
        with self.assertRaises(GrammarValidationError): plan_causal_network(self.nodes(),[{'source':'a','target':'z','kind':'causes','evidence_kind':'causal'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_self_edge(self):
        with self.assertRaises(GrammarValidationError): plan_causal_network(self.nodes(),[{'source':'a','target':'a','kind':'causes','evidence_kind':'causal'}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_role(self):
        with self.assertRaises(GrammarValidationError): plan_causal_network([{'id':'x','role':'planet'}],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_causal_network([],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self):
        kw=dict(nodes=self.nodes(),edges=[],evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(plan_causal_network(**kw).fingerprint,plan_causal_network(**kw).fingerprint)
if __name__=='__main__': unittest.main()
