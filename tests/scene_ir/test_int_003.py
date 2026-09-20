import unittest
from bie.scene_ir.simulation_controls import *
class T(unittest.TestCase):
 def test_slider(self):
  c=SimulationControl("c","sim","slider","sim.speed",0,10,1)
  self.assertEqual(validate_simulation_controls([c],("sim",),("sim.speed",),{"sim":"conceptual"}),())
 def test_slider_bounds(self):
  with self.assertRaises(InteractionIRError):SimulationControl("c","sim","slider","x",10,0,1)
 def test_step(self):
  with self.assertRaises(InteractionIRError):SimulationControl("c","sim","slider","x",0,10,0)
 def test_choice(self):
  c=SimulationControl("c","sim","choice","sim.mode",options=("a","b"))
  self.assertEqual(c.options,("a","b"))
 def test_unknown_sim(self):
  c=SimulationControl("c","sim","toggle","x")
  self.assertIn("unknown_simulation:c",validate_simulation_controls([c],(),("x",),{}))
 def test_verified_guard(self):
  c=SimulationControl("c","sim","button","x",requires_verified_execution=True)
  self.assertIn("verified_execution_required:c",validate_simulation_controls([c],("sim",),("x",),{"sim":"conceptual"}))
 def test_verified_pass(self):
  c=SimulationControl("c","sim","button","x",requires_verified_execution=True)
  self.assertEqual(validate_simulation_controls([c],("sim",),("x",),{"sim":"verified_observed_execution"}),())
