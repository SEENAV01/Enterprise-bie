import unittest
from dataclasses import replace
from bie.game_engine.fixtures import sample_document
from bie.game_engine.interaction import RuleSpec,EffectSpec,EffectKind,InteractionContract,ActionKind
from bie.game_engine.expressions import Compare,CompareOp,Variable,Literal
from bie.game_engine.state_engine.action_router import compile_action_routes,dispatch_action
from bie.game_engine.state_engine.snapshots import initial_snapshot
from bie.game_engine.state_engine.contracts import ActionCommand
from bie.game_engine.errors import GameContractError

class ActionRouterTests(unittest.TestCase):
 def level(self):return sample_document().experiences[0].levels[0]
 def test_all_action_kinds_have_mechanic_mapping(self):
  import bie.game_engine.state_engine.action_router as r
  self.assertEqual(set(r._ACTION_MECHANIC),set(ActionKind))
 def test_drag_routes_to_bound_rule_and_mechanic(self):
  routes={r.action_id:r for r in compile_action_routes(self.level())};r=routes['drag:mover'];self.assertEqual(r.rule_id,'rule:move');self.assertEqual(r.mechanic_id,'drag_and_drop');self.assertEqual(r.state_bindings,('x',))
 def test_route_deterministic(self):self.assertEqual(compile_action_routes(self.level()),compile_action_routes(self.level()))
 def test_dispatch_updates_authoritative_snapshot(self):
  l=self.level();s=initial_snapshot(l.state);cmd=ActionCommand('cmd:h1',1,'drag:mover','actor:test',( ('x',2.0),('y',0.0) ),s.snapshot_id);after,e=dispatch_action(l,s,cmd);self.assertEqual(after.as_dict()['x'],2);self.assertNotEqual(after.snapshot_id,s.snapshot_id);self.assertEqual(e.transition_receipt.after_snapshot_id,after.snapshot_id);self.assertTrue(e.mechanic_patch_fingerprint.startswith('sha256:'))
 def test_stale_snapshot_fails_closed(self):
  l=self.level();s=initial_snapshot(l.state);cmd=ActionCommand('cmd:h1',1,'drag:mover','actor:test',( ('x',2.0),('y',0.0) ),'snapshot:wrong')
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_STALE_COMMAND'):dispatch_action(l,s,cmd)
 def test_ambiguous_top_rule_fails_closed(self):
  l=self.level();r=l.interaction.rules[0];r2=replace(r,rule_id='rule:move:2')
  bad=replace(l,interaction=InteractionContract(l.interaction.actions,(r,r2)))
  with self.assertRaisesRegex(GameContractError,'GAME_ROUTE_AMBIGUOUS_RULE'):compile_action_routes(bad)
