import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.interaction import *
from bie.game_engine.state import *
from bie.game_engine.expressions import *
class T(unittest.TestCase):
 def s(self):return StateModel((StateVariableSpec('x',ValueType.NUMBER,1),)).validate()
 def test_action_keyboard(self):ActionSpec('a',ActionKind.DRAG,'e','Drag','Arrow keys').validate()
 def test_drag_needs_keyboard(self):
  with self.assertRaises(GameContractError):ActionSpec('a',ActionKind.DRAG,'e','Drag').validate()
 def test_effect_target(self):
  with self.assertRaises(GameContractError):EffectSpec('y',EffectKind.SET,1).validate(self.s())
 def test_div_zero(self):
  with self.assertRaises(GameContractError):EffectSpec('x',EffectKind.DIV,0).validate(self.s())
 def test_rule(self):RuleSpec('r',Literal(True),(EffectSpec('x',EffectKind.SET,2),),'why',1,('src',)).validate(self.s())
 def test_rule_no_grounding(self):
  with self.assertRaises(GameContractError):RuleSpec('r',Literal(True),(EffectSpec('x',EffectKind.SET,2),),'why',1,()).validate(self.s())
 def test_contract_duplicate_action(self):
  a=ActionSpec('a',ActionKind.TAP,'e','tap')
  with self.assertRaises(GameContractError):InteractionContract((a,a),()).validate(self.s())
