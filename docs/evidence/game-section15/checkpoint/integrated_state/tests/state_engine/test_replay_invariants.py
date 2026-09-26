import unittest
from bie.game_engine.errors import GameContractError
from bie.game_engine.expressions import *
from bie.game_engine.state_engine.fixtures import *
from bie.game_engine.state_engine.transition_engine import execute_rule
from bie.game_engine.state_engine.replay import verify_receipt_chain
from bie.game_engine.state_engine.invariants import *

class ReplayInvariantTests(unittest.TestCase):
 def test_replay_single_transition(self):
  b=sample_snapshot();a,r=execute_rule(sample_level(),b,drag_command(),'rule:move');self.assertEqual(verify_receipt_chain(b,(r,),a)['receipt_count'],1)
 def test_chain_break_rejected(self):
  b=sample_snapshot();a,r=execute_rule(sample_level(),b,drag_command(),'rule:move')
  from dataclasses import replace
  bad=replace(r,before_snapshot_id='snapshot:wrong')
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_REPLAY_CHAIN_BREAK'):verify_receipt_chain(b,(bad,),a)
 def test_duplicate_command_rejected(self):
  b=sample_snapshot();a,r=execute_rule(sample_level(),b,drag_command(),'rule:move')
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_REPLAY_DUPLICATE_COMMAND'):verify_receipt_chain(b,(r,r),a)
 def test_final_mismatch_rejected(self):
  b=sample_snapshot();a,r=execute_rule(sample_level(),b,drag_command(),'rule:move')
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_REPLAY_FINAL_MISMATCH'):verify_receipt_chain(b,(r,),b)
 def test_invariant_passes(self):self.assertEqual(verify_invariants(sample_level().state,sample_snapshot(),invariant_bounds())['verified'],1)
 def test_invariant_failure(self):
  inv=(StateInvariant('inv:x:too-high',Compare(CompareOp.GT,Variable('x'),Literal(5)),'x must be high'),)
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_INVARIANT_FAILED'):verify_invariants(sample_level().state,sample_snapshot(),inv)
 def test_replay_product_acceptance_false(self):
  b=sample_snapshot();a,r=execute_rule(sample_level(),b,drag_command(),'rule:move');self.assertFalse(verify_receipt_chain(b,(r,),a)['product_accepted'])
