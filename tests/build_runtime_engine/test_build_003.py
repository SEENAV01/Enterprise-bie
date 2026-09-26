import unittest
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.compiler_engine.pipeline import compile_game
from bie.game_engine.build_runtime_engine.interaction_simulation import simulate
class Build003(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ctx,_=build_inputs();cls.bundle=compile_game(cls.ctx);cls.r=simulate(cls.ctx,cls.bundle)
 def test_compiled_semantic_event_present(self):self.assertTrue(self.r.compiled_event_present)
 def test_mechanic_receipt_bound(self):self.assertTrue(self.r.mechanic_receipt_id);self.assertNotEqual(self.r.mechanic_receipt_id,'receipt:reset')
 def test_state_patch_bound(self):self.assertTrue(self.r.state_patch_fingerprint.startswith('sha256:'))
 def test_motion_is_causal(self):self.assertTrue(self.r.causal);self.assertTrue(self.r.motion_ids)
 def test_deterministic_simulation(self):self.assertEqual(self.r,simulate(self.ctx,self.bundle))
 def test_no_product_acceptance(self):self.assertFalse(self.r.product_accepted)
