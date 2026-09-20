import unittest
from bie.scene_ir.simulation_element import build
class T(unittest.TestCase):
    def test_valid(self): self.assertTrue(build('e','model:1',('s',),('r',),initial_state={}).element_type == 'simulation')
    def test_invalid(self):
        with self.assertRaises(Exception): build('e','m',('s',),('r',),initial_state={},execution_class='verified_observed_execution')
