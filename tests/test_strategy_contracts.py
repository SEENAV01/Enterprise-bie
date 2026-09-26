import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import *
from bie.game_engine.strategy_engine.fixtures import rich_bundle, evidence, objective
from bie.game_engine.provenance import EvidenceRef, ProvenanceBundle

class StrategyContractTests(unittest.TestCase):
    def test_rich_bundle_valid(self):
        b=rich_bundle(); self.assertEqual(b.validate(), b)
    def test_objective_requires_ops(self):
        x=replace(rich_bundle().objectives[0],cognitive_operations=())
        with self.assertRaisesRegex(GameContractError,'COGNITIVE_OPERATION_REQUIRED'):x.validate()
    def test_objective_requires_forms(self):
        x=replace(rich_bundle().objectives[0],knowledge_forms=())
        with self.assertRaisesRegex(GameContractError,'KNOWLEDGE_FORM_REQUIRED'):x.validate()
    def test_objective_weight_bounded(self):
        with self.assertRaisesRegex(GameContractError,'OBJECTIVE_WEIGHT'):replace(rich_bundle().objectives[0],weight=0).validate()
    def test_runtime_capability_unknown_fails(self):
        with self.assertRaisesRegex(GameContractError,'UNKNOWN_RUNTIME_CAPABILITY'):rich_bundle().runtime.has('not_real')
    def test_retrieval_requires_unique_grounded_identity(self):
        x=rich_bundle().retrieval_items[0]; self.assertEqual(x.validate(),x)
    def test_manipulation_must_be_reversible(self):
        with self.assertRaisesRegex(GameContractError,'SAFETY_BOUNDARY'):replace(rich_bundle().manipulations[0],reversible=False).validate()
    def test_simulation_requires_io(self):
        with self.assertRaisesRegex(GameContractError,'SIMULATION_IO_REQUIRED'):replace(rich_bundle().simulations[0],parameter_ids=()).validate()
    def test_prediction_requires_precommit(self):
        with self.assertRaisesRegex(GameContractError,'PRECOMMIT_REQUIRED'):replace(rich_bundle().predictions[0],commitment_before_observation=False).validate()
    def test_diagnostic_requires_misconception_provenance(self):
        h='2'*64; p=ProvenanceBundle((EvidenceRef('s','p',h,'source'),EvidenceRef('r','d',h,'reasoning'),EvidenceRef('o','l',h,'objective')))
        with self.assertRaisesRegex(GameContractError,'PROVENANCE_ROLE_MISSING'):replace(rich_bundle().diagnostics[0],provenance=p).validate()
    def test_geo_bounds(self):
        with self.assertRaisesRegex(GameContractError,'MAP_LATITUDE'):replace(rich_bundle().geo_entities[0],latitude=91).validate()
    def test_equation_invariant_required(self):
        with self.assertRaisesRegex(GameContractError,'EQUATION_INVARIANT_REQUIRED'):replace(rich_bundle().equations[0],equivalence_invariant=False).validate()
    def test_causal_self_edge_forbidden(self):
        e=rich_bundle().causal_edges[0]
        with self.assertRaisesRegex(GameContractError,'CAUSAL_SELF_EDGE'):replace(e,effect_id=e.cause_id).validate()
    def test_bundle_unknown_objective_fails(self):
        sig=replace(rich_bundle().retrieval_items[0],objective_id='obj:missing'); b=replace(rich_bundle(),retrieval_items=(sig,))
        with self.assertRaisesRegex(GameContractError,'SIGNAL_UNKNOWN_OBJECTIVE'):b.validate()
    def test_assessment_forbids_eligible_with_blocker(self):
        a=StrategyAssessment(StrategyKind.RETRIEVAL,True,70,.8,('obj:1',),('blocked',),(),(),(),(),())
        with self.assertRaisesRegex(GameContractError,'ELIGIBLE_WITH_BLOCKERS'):a.validate()
    def test_decision_selected_requires_primary(self):
        d=StrategyDecision(DecisionStatus.SELECTED,None,None,(),(), 'sha256:'+'0'*64)
        with self.assertRaisesRegex(GameContractError,'PRIMARY_REQUIRED'):d.validate()
    def test_product_acceptance_forbidden(self):
        d=StrategyDecision(DecisionStatus.ABSTAIN_NO_ELIGIBLE,None,None,(),(), 'sha256:'+'0'*64,True)
        with self.assertRaisesRegex(GameContractError,'PRODUCT_ACCEPTANCE_FORBIDDEN'):d.validate()

if __name__=='__main__':unittest.main()
