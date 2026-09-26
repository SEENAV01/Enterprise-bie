import unittest
from bie.game_engine.mechanics_engine.reset import reset
class ResetTests(unittest.TestCase):
 def test_reset_is_deterministic_and_scoped(self):
  state,r=reset('mechanic:x',{'x':2},{'x':1});self.assertEqual(state,{'x':1});self.assertTrue(r.deterministic);self.assertFalse(r.product_accepted);self.assertEqual(r,reset('mechanic:x',{'x':2},{'x':1})[1])
 def test_reset_noop_rejected(self):
  with self.assertRaises(Exception):reset('mechanic:x',{'x':1},{'x':1})
