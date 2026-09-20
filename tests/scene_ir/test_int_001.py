import unittest
from bie.scene_ir.interaction_bindings import *
class T(unittest.TestCase):
 def test_pass(self):
  b=InteractionBinding("b","i","tap",("e",),"show","handler:1")
  self.assertEqual(validate_interaction_bindings([b],("e",),("handler:1",)),())
 def test_target(self):
  b=InteractionBinding("b","i","tap",("x",),"show","handler:1")
  self.assertIn("unknown_target:b:x",validate_interaction_bindings([b],("e",),("handler:1",)))
 def test_handler(self):
  b=InteractionBinding("b","i","tap",("e",),"show","handler:x")
  self.assertIn("unknown_handler:b",validate_interaction_bindings([b],("e",),("handler:1",)))
 def test_event(self):
  with self.assertRaises(InteractionIRError):InteractionBinding("b","i","swipe",("e",),"x","h")
 def test_dup_target(self):
  with self.assertRaises(InteractionIRError):InteractionBinding("b","i","tap",("e","e"),"x","h")
 def test_dup_binding(self):
  b=InteractionBinding("b","i","tap",("e",),"x","h")
  with self.assertRaises(InteractionIRError):validate_interaction_bindings([b,b],("e",),("h",))
