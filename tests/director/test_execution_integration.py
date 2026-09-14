from dataclasses import asdict, replace
import tempfile, unittest
from input_fixtures import upstream
from directing_fixtures import executor, context, DirectorProtocolFixture
from semantic_fixtures import ProtocolFixtureProvider, response_record
from bie.director.director_model import DirectingPolicy
from bie.director.director_executor import register_director_stage
from bie.infrastructure.orchestrator import EnterpriseOrchestrator, InMemoryArtifactResolver, StageDefinition, StageExecutionFailure
from bie.infrastructure.run_state import build_run_state


from directing_fixtures import orchestrator


class StageExecutionTests(unittest.TestCase):
    def fixture(self, **kwargs):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return upstream(temp.name, **kwargs)

    def stage(self, f, **kwargs):
        e,g,c,s = executor(f, **kwargs); self.addCleanup(s.close); return e,g,c,s

    def test_registered_canonical_orchestrator_runs_three_different_teaching_shapes(self):
        for case, scenes, calls in (("science", 2, 3), ("economics", 1, 2), ("history", 3, 4)):
            with self.subTest(case=case):
                f = self.fixture(case_id=case); e,g,c,s = self.stage(f); o = orchestrator(f,e)
                self.assertEqual(o.run_until_blocked_or_complete(), ["DIRECTOR"])
                self.assertEqual(o.state.stages["DIRECTOR"].current.state, "SUCCEEDED")
                output = f.io.load(o.artifacts.outputs_for_stage(f.run_id,"DIRECTOR")[0])
                self.assertEqual(len(output.payload["plan"]["scenes"]), scenes)
                self.assertEqual(len(g.requests), calls); self.assertEqual(len(c.requests), 5)
                self.assertFalse(output.metadata["accepted"]); self.assertFalse(output.metadata["release_ready"])
                self.assertTrue(output.metadata["requires_review"])
                graph = f.io.load_graph((output.to_ref(),))
                self.assertTrue(all(r.artifact_id in graph for r in f.inputs.parent_refs))

    def test_idempotent_success_replays_persisted_artifacts_without_provider_calls(self):
        f = self.fixture(); e,g,c,s = self.stage(f); ctx = context(f); first = e(ctx)
        before = len(g.requests),len(c.requests)
        self.assertEqual(e(ctx), first); self.assertEqual((len(g.requests),len(c.requests)), before)
        # Independent executor instance with the same durable claim store also replays.
        e2,g2,c2,s2 = executor(f); self.addCleanup(s2.close)
        self.assertEqual(e2(ctx), first); self.assertEqual(g2.requests, []); self.assertEqual(c2.requests, [])

    def test_success_replay_detects_corrupt_output_bytes(self):
        f = self.fixture(); e,g,c,s = self.stage(f); ctx = context(f); result = e(ctx)
        record = f.io.catalog.get_record(result.output_artifact_refs[0]); f.io.catalog.cas._path(record.blob.digest).write_bytes(b"damaged")
        before = len(g.requests)
        with self.assertRaises(StageExecutionFailure) as raised: e(ctx)
        self.assertEqual(raised.exception.diagnostics, ["DIRECTOR_IDEMPOTENCY_INVALID"])
        self.assertEqual(len(g.requests), before)

    def test_same_key_different_configuration_fails_without_duplicate_generation(self):
        f = self.fixture(); e,g,c,s = self.stage(f); ctx = context(f); e(ctx); calls = len(g.requests)
        changed = replace(ctx, configuration={"director": {**f.config,"title":"Changed title"}})
        with self.assertRaises(StageExecutionFailure) as raised: e(changed)
        self.assertEqual(raised.exception.diagnostics, ["DIRECTOR_IDEMPOTENCY_CONFLICT"])
        self.assertEqual(len(g.requests), calls)

    def test_existing_inflight_claim_requires_recovery(self):
        f = self.fixture(); e,g,c,s = self.stage(f); original = s.claim
        def claim(key,fp,owner): original(key,fp,"previous-worker"); return original(key,fp,owner)
        s.claim = claim
        with self.assertRaises(StageExecutionFailure) as raised: e(context(f))
        self.assertEqual(raised.exception.diagnostics, ["DIRECTOR_IN_FLIGHT_REQUIRES_RECOVERY"])
        self.assertEqual(g.requests, []); self.assertEqual(raised.exception.remediation_owner,"INFRA")

    def test_model_failure_has_real_cas_receipt_and_failed_replay_does_not_repeat_calls(self):
        f = self.fixture(); g = DirectorProtocolFixture(lambda p,v,n: {})
        e,g,c,s = self.stage(f,generator=g); ctx = context(f)
        with self.assertRaises(StageExecutionFailure) as first: e(ctx)
        evidence = e._read_blob(first.exception.evidence_refs[0])
        self.assertEqual(len(evidence["generation_attempts"]), 2); self.assertFalse(evidence["accepted"])
        with self.assertRaises(StageExecutionFailure) as replay: e(ctx)
        self.assertEqual(first.exception.evidence_refs,replay.exception.evidence_refs)
        self.assertEqual(len(g.requests),2); self.assertEqual(c.requests,[])

    def test_invalid_upstream_input_has_operational_evidence_before_any_model_call(self):
        f = self.fixture(); e,g,c,s = self.stage(f)
        with self.assertRaises(StageExecutionFailure) as raised: e(context(f,input_artifact_refs=["missing",f.reasoning_ref.artifact_id]))
        receipt = e._read_blob(raised.exception.evidence_refs[0])
        self.assertEqual(receipt["code"], "DIRECTOR_INPUT_INVALID"); self.assertEqual(receipt["generation_attempts"], [])
        self.assertEqual(g.requests, []); self.assertEqual(c.requests, [])

    def test_qa_blocker_persists_candidate_evidence_but_publishes_no_director_plan(self):
        f = self.fixture(); critic = ProtocolFixtureProvider(lambda p,n: response_record(p,verdict="CONTRADICTED"))
        e,g,c,s = self.stage(f,critic=critic); o = orchestrator(f,e)
        self.assertEqual(o.run_until_blocked_or_complete(), [])
        self.assertEqual(o.state.stages["DIRECTOR"].current.state, "FAILED")
        self.assertEqual(o.artifacts.outputs_for_stage(f.run_id,"DIRECTOR"), [])
        self.assertFalse(any(r.artifact_type == "director.plan" for r in f.io.catalog.records.values()))
        refs = o.state.stages["DIRECTOR"].current.evidence_refs
        evidence = f.io.load(refs[0]); self.assertEqual(evidence.artifact_type,"evidence.director_execution")
        self.assertEqual(evidence.metadata["status"],"BLOCKED")

    def test_stage_retry_budget_prevents_unbounded_model_execution(self):
        f = self.fixture(); e,g,c,s = self.stage(f,generator=DirectorProtocolFixture(lambda p,v,n:{}),policy=DirectingPolicy(maximum_stage_attempts=1))
        o = orchestrator(f,e); o.run_until_blocked_or_complete(); before = len(g.requests)
        o.retry_failed("DIRECTOR"); o.run_until_blocked_or_complete()
        self.assertEqual(len(g.requests),before)
        self.assertEqual(o.state.stages["DIRECTOR"].current.diagnostics,["DIRECTOR_STAGE_ATTEMPT_BUDGET_EXCEEDED"])

    def test_registration_preserves_existing_registry_and_rejects_conflicts(self):
        definitions, executors = {}, {}; d,e = register_director_stage(definitions,executors,lambda c:None)
        self.assertEqual(definitions,{}); self.assertEqual(executors,{})
        self.assertEqual(d["DIRECTOR"].output_type,"director.plan")
        with self.assertRaises(ValueError): register_director_stage(d,e,lambda c:None)
        with self.assertRaises(ValueError): register_director_stage({"DIRECTOR":replace(d["DIRECTOR"],predecessors=[])},{},lambda c:None)


if __name__ == "__main__": unittest.main()
