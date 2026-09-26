import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.fixtures import *
from bie.game_engine.state_engine.transition_engine import execute_rule
from bie.game_engine.state_engine.rules import eligible_rules
from bie.game_engine.state_engine.snapshots import make_snapshot

class TransitionEngineTests(unittest.TestCase):
 def test_real_transition(self):
  before=sample_snapshot();after,r=execute_rule(sample_level(),before,drag_command(expected=before.snapshot_id),'rule:move');self.assertEqual(after.as_dict()['x'],2.0);self.assertEqual(after.tick,1)
 def test_receipt_bound_to_after_snapshot(self):
  before=sample_snapshot();after,r=execute_rule(sample_level(),before,drag_command(expected=before.snapshot_id),'rule:move');self.assertEqual(after.transition_receipt_id,r.receipt_id)
 def test_receipt_before_after_ids(self):
  b=sample_snapshot();a,r=execute_rule(sample_level(),b,drag_command(expected=b.snapshot_id),'rule:move');self.assertEqual((r.before_snapshot_id,r.after_snapshot_id),(b.snapshot_id,a.snapshot_id))
 def test_stale_command_rejected(self):
  b=sample_snapshot()
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_STALE_COMMAND'):execute_rule(sample_level(),b,drag_command(expected='snapshot:stale'),'rule:move')
 def test_unknown_rule_rejected(self):
  b=sample_snapshot()
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_UNKNOWN_RULE'):execute_rule(sample_level(),b,drag_command(),'missing')
 def test_ineligible_rule_rejected(self):
  l=sample_level();b=make_snapshot(l.state,{'x':2.0,'attempts':0})
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_RULE_NOT_ELIGIBLE'):execute_rule(l,b,drag_command(),'rule:move')
 def test_deterministic_transition(self):
  b=sample_snapshot();x=execute_rule(sample_level(),b,drag_command(expected=b.snapshot_id),'rule:move');y=execute_rule(sample_level(),b,drag_command(expected=b.snapshot_id),'rule:move');self.assertEqual(x,y)
 def test_before_snapshot_not_mutated(self):
  b=sample_snapshot();vals=b.as_dict();execute_rule(sample_level(),b,drag_command(),'rule:move');self.assertEqual(b.as_dict(),vals)
 def test_eligible_rule_disappears_after_transition(self):
  b=sample_snapshot();a,_=execute_rule(sample_level(),b,drag_command(),'rule:move');self.assertEqual(eligible_rules(sample_level(),a),())
