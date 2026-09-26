import unittest
from dataclasses import replace
from bie.game_engine.director_engine.contracts import *
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_context_valid(self):director_context().validate()
 def test_reject_abstain(self):
  c=director_context();bad=replace(c,decision=replace(c.decision,status=__import__('bie.game_engine.strategy_engine.contracts',fromlist=['DecisionStatus']).DecisionStatus.ABSTAIN_AMBIGUOUS,primary=None))
  with self.assertRaises(GameContractError):bad.validate()
 def test_constraints_anti_slide_locked(self):
  with self.assertRaises(GameContractError):replace(director_context().constraints,anti_slide_default=False).validate()
 def test_mastery_bounds(self):
  m=director_context().mastery[0]
  with self.assertRaises(GameContractError):replace(m,current_mastery=1.2).validate()
 def test_scoring_forbids_speed_pressure(self):
  with self.assertRaises(GameContractError):ScoringPolicy(10,0,(),0,0,True,True).validate()
 def test_hint_forbids_full_reveal(self):
  with self.assertRaises(GameContractError):HintStep('h','obj:x',HintMode.CUE,1,0,1.0,'ref:h').validate()
