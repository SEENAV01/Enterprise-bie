import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.fixtures import rich_bundle
from bie.game_engine.strategy_engine.selector import select_revision_strategy
from bie.game_engine.director_engine.contracts import DirectorContext,DirectorConstraints,MasterySignal,ScoringPolicy,HintStep,HintMode,AdaptationRule,AdaptAction
from bie.game_engine.director_engine.fixtures import director_context

class AdversarialTests(unittest.TestCase):
    def test_ambiguous_strategy_cannot_enter_director(self):
        b=rich_bundle();d=select_revision_strategy(b);m=tuple(MasterySignal(o.objective_id,.4,.8,1,o.provenance) for o in b.objectives)
        with self.assertRaisesRegex(GameContractError,'GAME_DIR_SELECTED_STRATEGY_REQUIRED'):DirectorContext(b,d,m,DirectorConstraints(),b.provenance).validate()
    def test_anti_slide_cannot_be_disabled(self):
        with self.assertRaises(GameContractError):replace(director_context().constraints,anti_slide_default=False).validate()
    def test_accessibility_flag_must_be_boolean(self):
        with self.assertRaises(GameContractError):replace(director_context().constraints,accessibility_required='yes').validate()
    def test_speed_bonus_is_forbidden(self):
        with self.assertRaises(GameContractError):ScoringPolicy(10,0,(),0,0,True,True).validate()
    def test_full_answer_hint_is_forbidden(self):
        with self.assertRaises(GameContractError):HintStep('h','obj:x',HintMode.CUE,1,0,1.0,'ref:h').validate()
    def test_hidden_targetless_remediation_is_forbidden(self):
        with self.assertRaises(GameContractError):AdaptationRule('a',1,'x',AdaptAction.REMEDIATE,'obj:x',None,'why').validate()
    def test_mastery_above_one_is_rejected(self):
        m=director_context().mastery[0]
        with self.assertRaises(GameContractError):replace(m,current_mastery=1.01).validate()
    def test_negative_attempt_count_is_rejected(self):
        m=director_context().mastery[0]
        with self.assertRaises(GameContractError):replace(m,attempts=-1).validate()
