import unittest
from bie.game_engine.state import StateVariableSpec,StateModel
from bie.game_engine.expressions import ValueType
from bie.game_engine.interaction import EffectSpec,EffectKind
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.effects import *
from bie.game_engine.state_engine.fixtures import sample_level

class EffectTests(unittest.TestCase):
 def setUp(self):self.model=sample_level().state;self.state={'x':1.0,'attempts':0}
 def apply(self,k,v,target='x'):return apply_effect(self.model,self.state,EffectSpec(target,k,v))
 def test_set(self):self.assertEqual(self.apply(EffectKind.SET,2.0)[0]['x'],2.0)
 def test_add(self):self.assertEqual(self.apply(EffectKind.ADD,2.0)[0]['x'],3.0)
 def test_sub(self):self.assertEqual(self.apply(EffectKind.SUB,0.5)[0]['x'],0.5)
 def test_mul(self):self.assertEqual(self.apply(EffectKind.MUL,2)[0]['x'],2.0)
 def test_div(self):self.assertEqual(self.apply(EffectKind.DIV,2)[0]['x'],0.5)
 def test_div_zero(self):
  with self.assertRaises(GameContractError):self.apply(EffectKind.DIV,0)
 def test_integer_preservation(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_EFFECT_INTEGER_PRESERVATION'):apply_effect(self.model,self.state,EffectSpec('attempts',EffectKind.DIV,2))
 def test_bounds_enforced(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_RANGE'):self.apply(EffectKind.ADD,99)
 def test_toggle_requires_bool(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_EFFECT_TOGGLE_BOOL'):self.apply(EffectKind.TOGGLE,None)
 def test_toggle_bool(self):
  m=StateModel((StateVariableSpec('flag',ValueType.BOOLEAN,False),));s={'flag':False};self.assertTrue(apply_effect(m,s,EffectSpec('flag',EffectKind.TOGGLE,None))[0]['flag'])
 def test_input_not_mutated(self):self.apply(EffectKind.ADD,1);self.assertEqual(self.state,{'x':1.0,'attempts':0})
 def test_delta_records_before_after(self):
  _,d=self.apply(EffectKind.ADD,1);self.assertEqual((d.before,d.after,d.operation),(1.0,2.0,'add'))
 def test_noop_delta_rejected(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_NOOP_DELTA'):self.apply(EffectKind.SET,1.0)
 def test_multiple_effects_ordered(self):
  out,ds=apply_effects(self.model,self.state,(EffectSpec('x',EffectKind.ADD,1),EffectSpec('x',EffectKind.MUL,2)));self.assertEqual(out['x'],4.0);self.assertEqual(len(ds),2)
