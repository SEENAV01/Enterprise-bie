import unittest
from dataclasses import replace
from bie.game_engine.canonical import fingerprint
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import StrategySignalBundle, StrategyDecision, DecisionStatus, StrategyKind
from bie.game_engine.strategy_engine.fixtures import single_strategy_bundle
from bie.game_engine.strategy_engine import manipulation,prediction
from bie.game_engine.director_engine.contracts import DirectorContext,DirectorConstraints,MasterySignal,MechanicKind
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.mechanic_selection import select_mechanics

def hybrid_context():
    a=single_strategy_bundle(StrategyKind.MANIPULATION);b=single_strategy_bundle(StrategyKind.PREDICTION)
    bundle=StrategySignalBundle(a.objectives+b.objectives,manipulations=a.manipulations,predictions=b.predictions,runtime=a.runtime,provenance=a.provenance).validate()
    ma=manipulation.assess(bundle);pa=prediction.assess(bundle)
    decision=StrategyDecision(DecisionStatus.SELECTED,StrategyKind.MANIPULATION,StrategyKind.PREDICTION,(ma,pa),('hybrid fixture',),fingerprint((ma,pa)),False).validate()
    mastery=tuple(MasterySignal(o.objective_id,.3,.9,2,o.provenance) for o in bundle.objectives)
    return DirectorContext(bundle,decision,mastery,DirectorConstraints(),bundle.provenance).validate()

class CrossStrategyTests(unittest.TestCase):
    def test_every_strategy_kind_produces_studio_plan(self):
        for kind in StrategyKind:
            p=plan_experience(director_context(kind));self.assertTrue(p.studio_grade_target);self.assertTrue(p.anti_slide_default);self.assertFalse(p.product_accepted)
    def test_strategy_to_mechanic_mapping_is_semantic(self):
        expected={StrategyKind.RETRIEVAL:MechanicKind.RETRIEVAL,StrategyKind.MANIPULATION:MechanicKind.MANIPULATE,StrategyKind.SIMULATION:MechanicKind.SIMULATION,StrategyKind.PREDICTION:MechanicKind.PREDICT,StrategyKind.DIAGNOSTIC:MechanicKind.DIAGNOSE,StrategyKind.TIMELINE:MechanicKind.TIMELINE,StrategyKind.MAP:MechanicKind.MAP,StrategyKind.EQUATION:MechanicKind.EQUATION,StrategyKind.CAUSAL_SYSTEM:MechanicKind.CAUSAL}
        for kind,mechanic in expected.items():self.assertEqual(select_mechanics(director_context(kind))[0].mechanic,mechanic)
    def test_dynamic_strategies_propagate_motion_requirements(self):
        for kind in StrategyKind:
            if kind is StrategyKind.RETRIEVAL:continue
            self.assertTrue(select_mechanics(director_context(kind))[0].motion_requirements)
    def test_hybrid_primary_secondary_covers_two_objectives(self):
        p=plan_experience(hybrid_context());self.assertEqual(len(p.objective_assignments),2);self.assertEqual(len(p.mechanic_assignments),2);self.assertEqual({x.mechanic for x in p.mechanic_assignments},{MechanicKind.MANIPULATE,MechanicKind.PREDICT})
    def test_hybrid_plan_has_secondary_strategy(self):self.assertEqual(plan_experience(hybrid_context()).secondary_strategy,StrategyKind.PREDICTION)
    def test_hybrid_levels_cover_all_objectives(self):
        p=plan_experience(hybrid_context());self.assertEqual({o for l in p.levels for o in l.objective_ids},{x.objective_id for x in p.objective_assignments})
    def test_partial_strategy_coverage_fails_closed(self):
        c=hybrid_context();bad=replace(c,decision=replace(c.decision,secondary=None,ranked=(c.decision.ranked[0],)))
        with self.assertRaisesRegex(GameContractError,'GAME_DIR_STRATEGY_OBJECTIVE_COVERAGE_INCOMPLETE'):bad.validate()
    def test_runtime_motion_loss_fails_for_dynamic(self):
        c=director_context(StrategyKind.SIMULATION);c=replace(c,signals=replace(c.signals,runtime=replace(c.signals.runtime,semantic_motion=False)))
        with self.assertRaises(GameContractError):select_mechanics(c)
