import unittest
from bie.scene_ir.state_bindings import *
class T(unittest.TestCase):
 def test_pass(self):
  b=StateBinding("b","sim.speed","e","opacity","clamp01")
  self.assertEqual(validate_state_bindings([b],("sim.speed",),("e",)),())
 def test_state(self):
  b=StateBinding("b","x","e","opacity")
  self.assertIn("unknown_state_path:b",validate_state_bindings([b],("y",),("e",)))
 def test_target(self):
  b=StateBinding("b","x","z","opacity")
  self.assertIn("unknown_target:b",validate_state_bindings([b],("x",),("e",)))
 def test_transform(self):
  with self.assertRaises(InteractionIRError):StateBinding("b","x","e","p","magic")
 def test_clamp(self):
  b=StateBinding("b","x","e","p","clamp01")
  self.assertEqual(apply_state_transform(b,2),1.0)
 def test_lookup(self):
  b=StateBinding("b","x","e","p","lookup")
  self.assertEqual(apply_state_transform(b,"a",{"a":"A"}),"A")
 def test_lookup_missing(self):
  b=StateBinding("b","x","e","p","lookup")
  with self.assertRaises(InteractionIRError):apply_state_transform(b,"a",{})
