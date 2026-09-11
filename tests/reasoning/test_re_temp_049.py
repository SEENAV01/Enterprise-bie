import unittest
from bie.reasoning.temporal_integration_contract import *

class T(unittest.TestCase):
    def test_safe(self):
        self.assertTrue(downstream_safe(TemporalIntegrationPayload("r","RESOLVED","A before B",("e",),False,"year")))
    def test_missing_id(self):
        self.assertIn("missing_result_id",validate_integration_payload(TemporalIntegrationPayload("","RESOLVED","x",("e",),False)))
    def test_missing_evidence(self):
        self.assertIn("missing_evidence",validate_integration_payload(TemporalIntegrationPayload("r","RESOLVED","x",(),False)))
    def test_missing_conclusion(self):
        self.assertIn("missing_conclusion",validate_integration_payload(TemporalIntegrationPayload("r","RESOLVED",None,("e",),False)))
    def test_nonresolved_review(self):
        self.assertIn("review_required_for_nonresolved",validate_integration_payload(TemporalIntegrationPayload("r","AMBIGUOUS",None,("e",),False)))
