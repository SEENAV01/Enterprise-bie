import unittest
from bie.game_engine.state_engine.conditions import *
from bie.game_engine.state_engine.fixtures import sample_level
from tests.state_engine.support import snapshot_values

class FailureConditionTests(unittest.TestCase):
 def setUp(self):self.level=sample_level();self.c=self.level.challenges[0]
 def test_initial_not_failed(self):self.assertFalse(evaluate_failure(self.level,self.c,snapshot_values(x=1.0,attempts=0)))
 def test_attempt_limit_fails(self):self.assertTrue(evaluate_failure(self.level,self.c,snapshot_values(x=1.0,attempts=4)))
 def test_failure_index_recorded(self):self.assertEqual(evaluate_conditions(self.level,self.c,snapshot_values(x=1.0,attempts=4)).matched_failure_indexes,(0,))
 def test_failure_without_success(self):
  r=evaluate_conditions(self.level,self.c,snapshot_values(x=1.0,attempts=4));self.assertFalse(r.success);self.assertTrue(r.failed)
 def test_deterministic(self):self.assertEqual(evaluate_failure(self.level,self.c,snapshot_values(x=1.0,attempts=4)),evaluate_failure(self.level,self.c,snapshot_values(x=1.0,attempts=4)))
 def test_success_state_not_failed(self):self.assertFalse(evaluate_failure(self.level,self.c,snapshot_values(x=2.0,attempts=0)))
