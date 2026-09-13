import unittest
from bie.pedagogy.teaching_mode_selection import select_teaching_mode

class TestTeachingModeSelection(unittest.TestCase):
    def test_low_readiness_prefers_explanation(self):
        self.assertEqual(select_teaching_mode(
            objective_level="ANALYZE", prerequisite_readiness=.3,
            mathematical_density=.8, dynamic_system=True,
            source_supports_derivation=True).mode, "EXPLANATION")

    def test_dynamic_apply_prefers_simulation(self):
        self.assertEqual(select_teaching_mode(
            objective_level="APPLY", prerequisite_readiness=.9,
            mathematical_density=.2, dynamic_system=True,
            source_supports_derivation=False).mode, "SIMULATION")
