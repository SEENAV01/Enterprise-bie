import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.fixtures import *
from bie.game_engine.state_engine.manipulables import *
from bie.game_engine.state_engine.contracts import ActionCommand
from bie.game_engine.interaction import ActionSpec,ActionKind,InteractionContract

class ManipulableTests(unittest.TestCase):
 def setUp(self):self.level=sample_level()
 def test_compile_actions(self):self.assertEqual([x.action_id for x in compile_actions(self.level)],['drag:mover','submit'])
 def test_visual_target_must_exist(self):
  bad=replace(self.level.interaction,actions=(ActionSpec('drag:bad',ActionKind.DRAG,'missing','Move','Keys'),))
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_ACTION_VISUAL_TARGET_MISSING'):compile_actions(replace(self.level,interaction=bad))
 def test_drag_payload_normalized(self):
  r=normalize_command(self.level,drag_command());self.assertEqual(dict(r['payload']),{'x':2.0,'y':0.0})
 def test_drag_requires_xy(self):
  c=ActionCommand('cmd:x',1,'drag:mover','actor:learner',( ('x',2.0), ))
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_ACTION_PAYLOAD_REQUIRED'):normalize_command(self.level,c)
 def test_coordinate_type(self):
  c=ActionCommand('cmd:x',1,'drag:mover','actor:learner',tuple(sorted({'x':'bad','y':0}.items())))
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_ACTION_COORDINATE_TYPE'):normalize_command(self.level,c)
 def test_unknown_action_fails(self):
  c=ActionCommand('cmd:x',1,'nope','actor:learner')
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_UNKNOWN_ACTION'):normalize_command(self.level,c)
 def test_duplicate_payload_key_fails(self):
  c=ActionCommand('cmd:x',1,'drag:mover','actor:learner',( ('x',1),('x',2),('y',0) ))
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_COMMAND_PAYLOAD'):normalize_command(self.level,c)
 def test_negative_sequence_fails(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_COMMAND_SEQUENCE'):ActionCommand('cmd:x',-1,'submit','actor:learner').validate()
 def test_expected_snapshot_id_validated(self):drag_command(expected='snapshot:abc').validate()
 def test_accessibility_survives_compile(self):self.assertTrue(all(x.accessible_label for x in compile_actions(self.level)))
 def test_product_acceptance_false(self):self.assertFalse(normalize_command(self.level,drag_command())['product_accepted'])
