import unittest
from bie.compiler.state_bindings_emitter import *
class T(unittest.TestCase):
 def binds(self):return ({"binding_id":"b","state_path":"sim.speed","target_id":"label","property_name":"text","transform":"percent"},)
 def test_emit(self):self.assertIn("stateBindings",emit_state_bindings(bindings=self.binds()).content)
 def test_percent(self):self.assertIn("Number(value) * 100",emit_state_bindings(bindings=self.binds()).content)
 def test_deterministic(self):self.assertEqual(emit_state_bindings(bindings=self.binds()).sha256,emit_state_bindings(bindings=self.binds()).sha256)
 def test_duplicate(self):
  b=self.binds()[0]
  with self.assertRaises(ReactEmitterError):emit_state_bindings(bindings=(b,b))
 def test_bad_transform(self):
  b=dict(self.binds()[0]);b["transform"]="eval"
  with self.assertRaises(ReactEmitterError):emit_state_bindings(bindings=(b,))
 def test_no_eval(self):self.assertNotIn("eval(",emit_state_bindings(bindings=self.binds()).content)
