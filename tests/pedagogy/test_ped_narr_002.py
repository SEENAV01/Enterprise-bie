import unittest
from bie.pedagogy.inquiry_mode import plan_inquiry

class TestInquiryMode(unittest.TestCase):
    def test_has_prediction_evidence_reflection(self):
        r=plan_inquiry("charged balloons","charge",["e1"])
        self.assertIn("Predict",r.prediction_prompt)
        self.assertIn("evidence",r.evidence_prompt.lower())
        self.assertIn("Revise",r.reflection_prompt)

    def test_grounding_required(self):
        with self.assertRaises(ValueError):
            plan_inquiry("x","c",[])
