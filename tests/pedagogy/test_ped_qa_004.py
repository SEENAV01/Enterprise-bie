import unittest
from bie.pedagogy.assessment_alignment import assessment_alignment

class TestAssessmentAlignment(unittest.TestCase):
    def test_underassessment_blocks(self):
        r=assessment_alignment({"o":"APPLY"},[("q","o","REMEMBER")])
        self.assertFalse(r.passed)

    def test_matching_level_passes(self):
        self.assertTrue(assessment_alignment({"o":"APPLY"},[("q","o","APPLY")]).passed)
