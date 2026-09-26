import unittest
from dataclasses import replace
from bie.game_engine.state import StateVariableSpec,StateModel
from bie.game_engine.expressions import ValueType
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.state_variables import compile_state_model
from bie.game_engine.state_engine.snapshots import *
from bie.game_engine.state_engine.fixtures import sample_level

class StateVariableModelTests(unittest.TestCase):
 def setUp(self):self.model=sample_level().state
 def test_compile_schema(self):
  c=compile_state_model(self.model);self.assertEqual(c.variable_ids,('attempts','x'));self.assertFalse(c.product_accepted)
 def test_initial_snapshot_is_sorted_and_immutable(self):
  s=initial_snapshot(self.model);self.assertEqual([k for k,_ in s.values],['attempts','x']);self.assertEqual(s.tick,0)
 def test_snapshot_deterministic(self):self.assertEqual(initial_snapshot(self.model),initial_snapshot(self.model))
 def test_schema_fingerprint_changes_with_schema(self):
  other=StateModel(self.model.variables+(StateVariableSpec('flag',ValueType.BOOLEAN,False),));self.assertNotEqual(schema_fingerprint(self.model),schema_fingerprint(other))
 def test_missing_value_fails(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_COVERAGE'):validate_values(self.model,{'x':1})
 def test_extra_value_fails(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_COVERAGE'):validate_values(self.model,{'x':1,'attempts':0,'extra':1})
 def test_integer_type_preserved(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_TYPE'):make_snapshot(self.model,{'x':1,'attempts':1.5})
 def test_numeric_bounds_enforced(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_RANGE'):make_snapshot(self.model,{'x':99,'attempts':0})
 def test_boolean_not_accepted_as_number(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_TYPE'):make_snapshot(self.model,{'x':True,'attempts':0})
 def test_enum_membership(self):
  m=StateModel((StateVariableSpec('mode',ValueType.ENUM,'a',enum_values=('a','b')),));make_snapshot(m,{'mode':'b'})
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_VALUE_ENUM'):make_snapshot(m,{'mode':'c'})
 def test_parent_and_receipt_are_bound(self):
  a=initial_snapshot(self.model);b=make_snapshot(self.model,a.as_dict(),1,a.snapshot_id,'transition:x');self.assertEqual(b.parent_snapshot_id,a.snapshot_id)
 def test_product_acceptance_false(self):self.assertFalse(initial_snapshot(self.model).product_accepted)
