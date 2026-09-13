import unittest
from bie.pedagogy.adaptive_policy_state_machine import AdaptiveState,next_state,state_fingerprint

class TestAdaptivePolicyStateMachine(unittest.TestCase):
    def base(self):
        return AdaptiveState("u","c","STANDARD",.5,1,("e0",))

    def test_prerequisite_gap_forces_bridge(self):
        n,t=next_state(self.base(),prerequisite_ready=False,misconception_detected=False,transfer_passed=False,new_mastery=.9,evidence_ids=["e1"])
        self.assertEqual(n.state,"BRIDGE")

    def test_misconception_precedes_acceleration(self):
        n,_=next_state(self.base(),prerequisite_ready=True,misconception_detected=True,transfer_passed=True,new_mastery=.95,evidence_ids=["e1"])
        self.assertEqual(n.state,"REMEDIATE")

    def test_deterministic_fingerprint(self):
        a,_=next_state(self.base(),prerequisite_ready=True,misconception_detected=False,transfer_passed=True,new_mastery=.95,evidence_ids=["e2","e1"])
        b,_=next_state(self.base(),prerequisite_ready=True,misconception_detected=False,transfer_passed=True,new_mastery=.95,evidence_ids=["e1","e2"])
        self.assertEqual(state_fingerprint(a),state_fingerprint(b))
