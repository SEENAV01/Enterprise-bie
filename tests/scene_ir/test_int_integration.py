import unittest
from bie.scene_ir.interaction_bindings import *
from bie.scene_ir.state_bindings import *
from bie.scene_ir.simulation_controls import *

class T(unittest.TestCase):
 def test_interaction_state_simulation_chain(self):
  ib=InteractionBinding("bind","tap-speed","tap",("slider-ui",),"set_state","handler:set_speed")
  self.assertEqual(validate_interaction_bindings([ib],("slider-ui",),("handler:set_speed",)),())
  sb=StateBinding("state-bind","sim.speed","speed-label","text","format","Speed: {}")
  self.assertEqual(validate_state_bindings([sb],("sim.speed",),("speed-label",)),())
  self.assertEqual(apply_state_transform(sb,5),"Speed: 5")
  sc=SimulationControl("speed-control","sim1","slider","sim.speed",0,10,1)
  self.assertEqual(validate_simulation_controls([sc],("sim1",),("sim.speed",),{"sim1":"conceptual"}),())

 def test_verified_control_guard(self):
  sc=SimulationControl("run","sim1","button","sim.run",requires_verified_execution=True)
  self.assertIn("verified_execution_required:run",
      validate_simulation_controls([sc],("sim1",),("sim.run",),{"sim1":"declared_model_output"}))
