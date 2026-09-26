import unittest
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.deterministic_replay import verify_deterministic_replay
class Build004(unittest.TestCase):
 def test_replay_succeeds(self):self.assertTrue(verify_deterministic_replay(build_inputs()[0]).success)
 def test_second_run_identical(self):self.assertTrue(verify_deterministic_replay(build_inputs()[0]).identical_second_run)
 def test_replay_fingerprint_deterministic(self):self.assertEqual(verify_deterministic_replay(build_inputs()[0]).run_fingerprint,verify_deterministic_replay(build_inputs()[0]).run_fingerprint)
 def test_transition_receipt_present(self):self.assertTrue(verify_deterministic_replay(build_inputs()[0]).transition_receipt_ids[0].startswith('transition:'))
 def test_final_snapshot_differs(self):
  r=verify_deterministic_replay(build_inputs()[0]);self.assertNotEqual(r.initial_snapshot_id,r.final_snapshot_id)
 def test_no_product_acceptance(self):self.assertFalse(verify_deterministic_replay(build_inputs()[0]).product_accepted)
