import unittest
from bie.pedagogy.pedagogy_section_readiness import pedagogy_readiness_gate

class TestPedagogySectionReadiness(unittest.TestCase):
    def checks(self):
        return {
          "objective_coverage":True,"prerequisite_coverage":True,"assessment_alignment":True,
          "cognitive_load_safe":True,"realbook_fixture":True,"integration_contract":True
        }

    def test_all_green_passes(self):
        self.assertTrue(pedagogy_readiness_gate(self.checks(),provenance_complete=True,reproducible=True).passed)

    def test_review_blocks(self):
        self.assertFalse(pedagogy_readiness_gate(self.checks(),review_items=["d1"],provenance_complete=True,reproducible=True).passed)

    def test_missing_required_check_rejected(self):
        c=self.checks(); del c["assessment_alignment"]
        with self.assertRaises(ValueError):
            pedagogy_readiness_gate(c,provenance_complete=True,reproducible=True)
