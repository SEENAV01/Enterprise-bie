import unittest
from enterprise.run_state import *

def machine():
    return build_run_state("run-1",{"SOURCE":[],"REASONING":["SOURCE"],"SCENE_IR":["REASONING"]})

class RunStateTests(unittest.TestCase):
    def test_cannot_ready_before_predecessor(self):
        m=machine()
        with self.assertRaises(RunStateError):m.mark_ready("REASONING")

    def test_success_requires_output_and_evidence(self):
        m=machine();m.mark_ready("SOURCE");m.start("SOURCE",[])
        with self.assertRaises(RunStateError):m.succeed("SOURCE",[],["ev"])
        with self.assertRaises(RunStateError):m.succeed("SOURCE",["out"],[])

    def test_happy_path(self):
        m=machine()
        m.mark_ready("SOURCE");m.start("SOURCE",[]);m.succeed("SOURCE",["src"],["ev1"])
        m.mark_ready("REASONING");m.start("REASONING",["src"]);m.succeed("REASONING",["reason"],["ev2"])
        m.mark_ready("SCENE_IR");m.start("SCENE_IR",["reason"]);m.succeed("SCENE_IR",["scene"],["ev3"])
        self.assertEqual(m.run_state,"EXECUTION_COMPLETE")

    def test_failure_requires_diagnostics_evidence_owner(self):
        m=machine();m.mark_ready("SOURCE");m.start("SOURCE",[])
        with self.assertRaises(RunStateError):m.fail("SOURCE",[],["e"],"BI")

    def test_retry_preserves_failed_attempt(self):
        m=machine();m.mark_ready("SOURCE");m.start("SOURCE",[])
        m.fail("SOURCE",["bad"],["ev-fail"],"BI")
        m.retry("SOURCE")
        self.assertEqual(len(m.stages["SOURCE"].attempts),2)
        self.assertEqual(m.stages["SOURCE"].attempts[0].state,"READY")
        self.assertEqual(m.stages["SOURCE"].attempts[0].evidence_refs,["ev-fail"])
        self.assertEqual(m.stages["SOURCE"].attempts[1].attempt,2)

    def test_illegal_transition_fails(self):
        m=machine()
        with self.assertRaises(RunStateError):m.start("SOURCE",[])

    def test_interrupted_running_not_success(self):
        m=machine();m.mark_ready("SOURCE");m.start("SOURCE",[])
        m.recover_interrupted("SOURCE","crash-evidence")
        self.assertEqual(m.stages["SOURCE"].current.state,"FAILED")
        self.assertEqual(m.run_state,"BLOCKED")

    def test_invalidation_requires_success(self):
        m=machine()
        with self.assertRaises(RunStateError):m.invalidate("SOURCE","changed",["ev"])

    def test_succeeded_stage_can_be_invalidated(self):
        m=machine();m.mark_ready("SOURCE");m.start("SOURCE",[]);m.succeed("SOURCE",["src"],["ev"])
        m.invalidate("SOURCE","source changed",["change-ev"])
        self.assertEqual(m.stages["SOURCE"].current.state,"INVALIDATED")

    def test_validation(self):
        m=machine();m.validate()

if __name__=="__main__":unittest.main()
