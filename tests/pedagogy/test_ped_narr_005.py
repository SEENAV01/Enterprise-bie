import unittest
from bie.pedagogy.simulation_mode import SimulationVariable,plan_simulation

class TestSimulationMode(unittest.TestCase):
    def test_valid_simulation(self):
        r=plan_simulation("force", [SimulationVariable("distance",1,10,5,"m")], "force", ["e1"])
        self.assertEqual(r.variables[0].name,"distance")

    def test_initial_outside_range_rejected(self):
        with self.assertRaises(ValueError):
            plan_simulation("x",[SimulationVariable("v",0,1,2,"m")],"y",["e"])
