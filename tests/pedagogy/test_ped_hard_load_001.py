import unittest
from bie.pedagogy.pedagogy_load_budget import LoadFactors,evaluate_load_budget

class TestPedagogyLoadBudget(unittest.TestCase):
    def test_overload_produces_actions(self):
        r=evaluate_load_budget(LoadFactors(1,1,1,1,1,0))
        self.assertTrue(r.overload)
        self.assertIn("split lesson or scene",r.recommendations)

    def test_segmentation_reduces_score(self):
        a=evaluate_load_budget(LoadFactors(.8,.5,.5,.5,.5,0))
        b=evaluate_load_budget(LoadFactors(.8,.5,.5,.5,.5,1))
        self.assertLess(b.score,a.score)
