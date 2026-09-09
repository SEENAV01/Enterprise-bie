import unittest
from bie.infrastructure.run_state import build_run_state
from bie.infrastructure.orchestrator import *

def definitions():
    return {
      "SOURCE":StageDefinition("SOURCE",[],[],"source.document","BI"),
      "REASONING":StageDefinition("REASONING",["SOURCE"],["source.document"],"reasoning.decision_set","RE"),
      "SCENE_IR":StageDefinition("SCENE_IR",["REASONING"],["reasoning.decision_set"],"scene.ir","DSL")
    }

def state(): return build_run_state("run-1",{"SOURCE":[],"REASONING":["SOURCE"],"SCENE_IR":["REASONING"]})

def ok(ctx): return StageExecutionResult([f"out:{ctx.stage_id}"],[f"ev:{ctx.stage_id}"])

class Tests(unittest.TestCase):
    def test_full_order(self):
        m=state(); o=EnterpriseOrchestrator(m,definitions(),{k:ok for k in definitions()},InMemoryArtifactResolver())
        self.assertEqual(o.run_until_blocked_or_complete(),["SOURCE","REASONING","SCENE_IR"])
        self.assertEqual(m.run_state,"EXECUTION_COMPLETE")

    def test_artifact_handoff(self):
        m=state(); a=InMemoryArtifactResolver(); seen={}
        def source(ctx): return StageExecutionResult(["source:1"],["ev:s"])
        def reasoning(ctx): seen["x"]=ctx.input_artifact_refs; return StageExecutionResult(["reason:1"],["ev:r"])
        o=EnterpriseOrchestrator(m,definitions(),{"SOURCE":source,"REASONING":reasoning,"SCENE_IR":ok},a)
        o.run_until_blocked_or_complete(); self.assertEqual(seen["x"],["source:1"])

    def test_failure_blocks(self):
        m=state()
        def bad(ctx): raise StageExecutionFailure(["bad"],["ev:bad"],"RE")
        o=EnterpriseOrchestrator(m,definitions(),{"SOURCE":ok,"REASONING":bad,"SCENE_IR":ok},InMemoryArtifactResolver())
        self.assertEqual(o.run_until_blocked_or_complete(),["SOURCE"])
        self.assertEqual(m.run_state,"BLOCKED")

    def test_exception_fails_closed(self):
        m=state()
        def boom(ctx): raise RuntimeError("boom")
        o=EnterpriseOrchestrator(m,definitions(),{"SOURCE":boom,"REASONING":ok,"SCENE_IR":ok},InMemoryArtifactResolver())
        o.run_until_blocked_or_complete()
        self.assertEqual(m.stages["SOURCE"].current.state,"FAILED")
        self.assertEqual(m.stages["SOURCE"].current.remediation_owner,"BI")

    def test_retry_new_attempt(self):
        m=state(); calls=[]
        def flaky(ctx):
            calls.append(ctx.attempt)
            if len(calls)==1: raise StageExecutionFailure(["x"],["ev1"],"BI")
            return StageExecutionResult(["src"],["ev2"])
        o=EnterpriseOrchestrator(m,definitions(),{"SOURCE":flaky,"REASONING":ok,"SCENE_IR":ok},InMemoryArtifactResolver())
        o.run_until_blocked_or_complete(); o.retry_failed("SOURCE"); o.run_until_blocked_or_complete()
        self.assertEqual(calls,[1,2]); self.assertEqual(m.run_state,"EXECUTION_COMPLETE")

    def test_idempotency_stable(self):
        o=EnterpriseOrchestrator(state(),definitions(),{},InMemoryArtifactResolver(),{"mode":"x"})
        self.assertEqual(o._idempotency_key("SOURCE",1,[]),o._idempotency_key("SOURCE",1,[]))

    def test_idempotency_attempt_changes(self):
        o=EnterpriseOrchestrator(state(),definitions(),{},InMemoryArtifactResolver())
        self.assertNotEqual(o._idempotency_key("SOURCE",1,[]),o._idempotency_key("SOURCE",2,[]))

    def test_registry_mismatch_rejected(self):
        d=definitions(); d["REASONING"]=StageDefinition("REASONING",[],[],"x","RE")
        with self.assertRaises(OrchestratorError): EnterpriseOrchestrator(state(),d,{},InMemoryArtifactResolver())

    def test_missing_executor_stalls(self):
        o=EnterpriseOrchestrator(state(),definitions(),{"SOURCE":ok},InMemoryArtifactResolver())
        with self.assertRaises(OrchestratorError): o.run_until_blocked_or_complete()

    def test_success_contract(self):
        with self.assertRaises(OrchestratorError): StageExecutionResult([],["ev"]).validate()
        with self.assertRaises(OrchestratorError): StageExecutionResult(["out"],[]).validate()

    def test_resume_rejects_running(self):
        m=state(); o=EnterpriseOrchestrator(m,definitions(),{"SOURCE":ok},InMemoryArtifactResolver())
        m.mark_ready("SOURCE"); m.start("SOURCE",[])
        with self.assertRaises(OrchestratorError): o.resume()

if __name__=="__main__": unittest.main()
