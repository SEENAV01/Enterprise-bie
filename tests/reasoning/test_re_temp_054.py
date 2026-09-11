import unittest
from bie.reasoning.temporal_integration_exit_gate import *

class T(unittest.TestCase):
    def test_blocked(self):
        r=temporal_integration_exit_state(TemporalIntegrationEvidence(False,False,False,False,True))
        self.assertEqual(r["state"],"IMPLEMENTATION_SCOPE_BLOCKED")
        self.assertEqual(len(r["blockers"]),4)
    def test_complete_not_accepted(self):
        r=temporal_integration_exit_state(TemporalIntegrationEvidence(True,True,True,True,True))
        self.assertEqual(r["state"],"IMPLEMENTATION_SCOPE_COMPLETE_NOT_ACCEPTED")
    def test_realbook_harness_required(self):
        r=temporal_integration_exit_state(TemporalIntegrationEvidence(True,True,True,True,False))
        self.assertIn("realbook_harness_missing",r["blockers"])
