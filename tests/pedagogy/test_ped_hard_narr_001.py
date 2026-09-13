import unittest
from bie.pedagogy.pedagogy_mode_arbitration import ModeCandidate,arbitrate_mode

class TestPedagogyModeArbitration(unittest.TestCase):
    def test_best_fit_selected(self):
        r=arbitrate_mode([
            ModeCandidate("EXPLANATION",.7,.7,.7,.5),
            ModeCandidate("SIMULATION",.9,.9,.9,.8)])
        self.assertEqual(r.selected_mode,"SIMULATION")

    def test_small_gain_does_not_churn_mode(self):
        r=arbitrate_mode([
            ModeCandidate("EXPLANATION",.8,.8,.8,.8),
            ModeCandidate("INQUIRY",.81,.81,.81,.81)],previous_mode="EXPLANATION",switch_margin=.08)
        self.assertEqual(r.selected_mode,"EXPLANATION")
