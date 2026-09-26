import unittest
from bie.game_engine.errors import GameContractError
from bie.game_engine.state_engine.conditions import *
from bie.game_engine.state_engine.fixtures import sample_level
from tests.state_engine.support import snapshot_values

class SuccessConditionTests(unittest.TestCase):
 def setUp(self):self.level=sample_level();self.c=self.level.challenges[0]
 def test_initial_not_success(self):self.assertFalse(evaluate_success(self.level,self.c,snapshot_values(x=1.0,attempts=0)))
 def test_target_success(self):self.assertTrue(evaluate_success(self.level,self.c,snapshot_values(x=2.0,attempts=0)))
 def test_success_evaluation_receipt(self):
  r=evaluate_conditions(self.level,self.c,snapshot_values(x=2.0,attempts=0));self.assertTrue(r.success);self.assertFalse(r.failed);self.assertTrue(r.state_fingerprint.startswith('sha256:'))
 def test_success_failure_conflict_fails(self):
  with self.assertRaisesRegex(GameContractError,'GAME_STATE_SUCCESS_FAILURE_CONFLICT'):evaluate_conditions(self.level,self.c,snapshot_values(x=2.0,attempts=4))
 def test_product_acceptance_false(self):self.assertFalse(evaluate_conditions(self.level,self.c,snapshot_values(x=2.0,attempts=0)).product_accepted)
 def test_deterministic(self):self.assertEqual(evaluate_conditions(self.level,self.c,snapshot_values(x=2.0,attempts=0)),evaluate_conditions(self.level,self.c,snapshot_values(x=2.0,attempts=0)))
