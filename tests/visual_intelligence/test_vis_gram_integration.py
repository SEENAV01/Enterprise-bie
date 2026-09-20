import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.grammar_registry import VisualGrammarRegistry
from bie.visual_intelligence.physics_vector_grammar import PHYSICS_VECTOR_GRAMMAR, plan_physics_vectors
from bie.visual_intelligence.field_grammar import FIELD_GRAMMAR
from bie.visual_intelligence.process_flow_grammar import PROCESS_FLOW_GRAMMAR
from bie.visual_intelligence.biology_cellular_grammar import BIOLOGY_CELLULAR_GRAMMAR
from bie.visual_intelligence.chemistry_molecular_grammar import CHEMISTRY_MOLECULAR_GRAMMAR
from bie.visual_intelligence.geography_map_grammar import GEOGRAPHY_MAP_GRAMMAR
from bie.visual_intelligence.history_timeline_grammar import HISTORY_TIMELINE_GRAMMAR
from bie.visual_intelligence.causal_network_grammar import CAUSAL_NETWORK_GRAMMAR
from bie.visual_intelligence.mathematics_graph_grammar import MATHEMATICS_GRAPH_GRAMMAR
from bie.visual_intelligence.geometry_grammar import GEOMETRY_GRAMMAR
from bie.visual_intelligence.data_chart_grammar import DATA_CHART_GRAMMAR

GRAMMARS=[PHYSICS_VECTOR_GRAMMAR,FIELD_GRAMMAR,PROCESS_FLOW_GRAMMAR,BIOLOGY_CELLULAR_GRAMMAR,CHEMISTRY_MOLECULAR_GRAMMAR,GEOGRAPHY_MAP_GRAMMAR,HISTORY_TIMELINE_GRAMMAR,CAUSAL_NETWORK_GRAMMAR,MATHEMATICS_GRAPH_GRAMMAR,GEOMETRY_GRAMMAR,DATA_CHART_GRAMMAR]
class T(unittest.TestCase):
    def registry(self): r=VisualGrammarRegistry(); r.register_many(GRAMMARS); return r
    def test_all_registered(self): self.assertEqual(len(self.registry().list()),11)
    def test_unique_ids(self): self.assertEqual(len({g.grammar_id for g in GRAMMARS}),11)
    def test_physics_vector_resolution(self): self.assertEqual(self.registry().resolve(domain='physics',representation='vector_diagram',tags=['vector']).grammar.grammar_id,PHYSICS_VECTOR_GRAMMAR.grammar_id)
    def test_map_resolution(self): self.assertEqual(self.registry().resolve(domain='geography',representation='map').grammar.grammar_id,GEOGRAPHY_MAP_GRAMMAR.grammar_id)
    def test_timeline_resolution(self): self.assertEqual(self.registry().resolve(domain='history',representation='timeline').grammar.grammar_id,HISTORY_TIMELINE_GRAMMAR.grammar_id)
    def test_molecule_resolution(self): self.assertEqual(self.registry().resolve(domain='chemistry',representation='molecule').grammar.grammar_id,CHEMISTRY_MOLECULAR_GRAMMAR.grammar_id)
    def test_geometry_resolution(self): self.assertEqual(self.registry().resolve(domain='mathematics',representation='geometry_diagram').grammar.grammar_id,GEOMETRY_GRAMMAR.grammar_id)
    def test_chart_wildcard_resolution(self): self.assertEqual(self.registry().resolve(domain='sociology',representation='chart').grammar.grammar_id,DATA_CHART_GRAMMAR.grammar_id)
    def test_process_wildcard_resolution(self): self.assertEqual(self.registry().resolve(domain='biology',representation='workflow').grammar.grammar_id,PROCESS_FLOW_GRAMMAR.grammar_id)
    def test_snapshot_stable(self): self.assertEqual(self.registry().snapshot(),self.registry().snapshot())
    def test_all_semantic_constraints_present(self): self.assertTrue(all(g.semantic_constraints for g in GRAMMARS))
    def test_all_versioned(self): self.assertTrue(all(g.version=='1.0.0' for g in GRAMMARS))
    def test_plan_remains_review_required(self):
        p=plan_physics_vectors([{'id':'F','direction':[1,0],'source_ids':['s']}],frame_id='xy',evidence_refs=['s'],reasoning_refs=['r']); self.assertTrue(p.review_required); self.assertFalse(p.accepted)
if __name__=='__main__': unittest.main()
