from dataclasses import asdict, replace
import tempfile, unittest
from unittest.mock import patch
from input_fixtures import upstream, CASES
from directing_fixtures import executor, context, DirectorProtocolFixture, GENERATOR
from annotation_review_fixtures import runtime
from annotation_fixtures import AnnotationProtocolFixture
from semantic_fixtures import ProtocolFixtureProvider, response_record
from repair_fixtures import retry_context
from bie.infrastructure.orchestrator import StageExecutionFailure
from bie.director.director_model import DirectingPolicy
from bie.director.recovery_codec import grounded_record
from bie.director.director_artifacts import fingerprint


class PhaseRepairTests(unittest.TestCase):
    def fixture(self, case='science'):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        f = upstream(tmp.name, case); return f

    def stage(self, f, **kwargs):
        e, g, c, s = executor(f, annotations=kwargs.pop('annotations', runtime()), **kwargs)
        self.addCleanup(s.close); return e, g, c, s

    def test_annotation_failure_resumes_exact_narration_with_real_factual_and_review_calls(self):
        f = self.fixture(); broken = runtime(annotator=AnnotationProtocolFixture(lambda p,v,n: {}))
        e,g,c,s = self.stage(f, annotations=broken); first = context(f)
        with self.assertRaises(StageExecutionFailure): e(first)
        generated, judged = len(g.requests), len(c.requests)
        e.annotations = runtime(); result = e(retry_context(f, first))
        self.assertEqual(len(g.requests), generated); self.assertGreater(len(c.requests), judged)
        self.assertEqual(len(e.annotations.annotator.requests), 1); self.assertEqual(len(e.annotations.reviewer.requests), 1)
        graph = f.io.load_graph((f.io.load(result.output_artifact_refs[0]).to_ref(),))
        receipts = [a for a in graph.values() if a.artifact_type == 'evidence.director_repair']
        self.assertEqual(receipts[0].payload['action'], 'REUSE_PLAN_NARRATION_RECHECK_QA')
        bases = [a.payload['result']['execution']['snapshot'] for a in graph.values() if a.artifact_type == 'evidence.director_base_execution']
        self.assertEqual(bases[0], bases[1])

    def test_recovery_after_executor_restart_uses_sqlite_and_cas_not_live_python_objects(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
        second,g2,c2,s2=self.stage(f); result=second(retry_context(f,first))
        self.assertEqual(g2.requests,[]); self.assertTrue(c2.requests)
        self.assertEqual(second.revisions.get(f.run_id,f.config['lesson_id']).artifact_id,result.output_artifact_refs[0])

    def test_repair_success_replay_makes_no_new_provider_calls(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first); repair=retry_context(f,first)
        expected=e(repair); before=len(g.requests),len(c.requests),len(e.annotations.annotator.requests)
        self.assertEqual(e(repair),expected)
        self.assertEqual((len(g.requests),len(c.requests),len(e.annotations.annotator.requests)),before)

    def test_changed_generation_policy_rebuilds_instead_of_reusing_narration(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
        e.policy=replace(e.policy,narration_prompt_version='revised-teaching-prompt/2')
        e(retry_context(f,first)); self.assertEqual(len(g.requests),6)
        receipt=next(f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair')
        self.assertEqual(receipt.payload['reason'],'CHANGED_GENERATION_POLICY')

    def test_changed_title_is_an_input_dependency_and_regenerates(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first); repair=retry_context(f,first)
        config={**repair.configuration,'director':{**f.config,'title':'Revised lesson framing'}}
        e(replace(repair,configuration=config)); self.assertEqual(len(g.requests),6)

    def test_real_source_revision_and_rebuilt_upstream_artifacts_force_regeneration(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
        original=CASES['science']
        with patch.dict(CASES,{'science':{**original,'text':original['text']+'\nThis source describes solid copper.'}}):
            revised=upstream(f.root,'science')
        f.io.catalog.records.update(revised.io.catalog.records)
        repair=replace(retry_context(f,first),input_artifact_refs=[revised.pedagogy_ref.artifact_id,revised.reasoning_ref.artifact_id])
        result=e(repair);self.assertEqual(len(g.requests),6)
        self.assertNotEqual(f.source_ref,revised.source_ref)
        self.assertIn(revised.pedagogy_ref,f.io.load(result.output_artifact_refs[0]).parent_refs)

    def test_changed_generator_identity_cannot_reuse_old_narration(self):
        f=self.fixture();e,g,c,s=self.stage(f);first=context(f);e(first)
        e.generator_identity=replace(GENERATOR,adapter_version='adapter/2')
        e(retry_context(f,first));self.assertEqual(len(g.requests),6)

    def test_in_flight_previous_claim_requires_infrastructure_recovery_without_provider_calls(self):
        f=self.fixture();e,g,c,s=self.stage(f);first=context(f)
        s.claim(first.idempotency_key,'in-flight-fingerprint','old-worker')
        with self.assertRaises(StageExecutionFailure) as err:e(retry_context(f,first))
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_REPAIR_REQUIRES_COMPLETED_ATTEMPT'])
        self.assertEqual(g.requests,[]);self.assertEqual(c.requests,[])

    def test_changed_critic_reruns_qa_and_cannot_bypass_a_new_contradiction(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
        e.critic=ProtocolFixtureProvider(lambda p,n:response_record(p,verdict='CONTRADICTED'))
        with self.assertRaises(StageExecutionFailure) as error:e(retry_context(f,first))
        self.assertEqual(error.exception.diagnostics,['DIRECTOR_QA_BLOCKED']); self.assertEqual(len(g.requests),3)
        self.assertEqual(e.revisions.get(f.run_id,f.config['lesson_id']).state,'FAILED')

    def test_failed_repair_receipt_replays_without_consuming_more_budget(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
        e.annotations=runtime(annotator=AnnotationProtocolFixture(lambda p,v,n:{})); repair=retry_context(f,first)
        with self.assertRaises(StageExecutionFailure) as initial:e(repair)
        before=len(g.requests),len(c.requests),len(e.annotations.annotator.requests)
        with self.assertRaises(StageExecutionFailure) as replay:e(repair)
        self.assertEqual(initial.exception.evidence_refs,replay.exception.evidence_refs)
        self.assertEqual(before,(len(g.requests),len(c.requests),len(e.annotations.annotator.requests)))

    def test_corrupt_saved_narration_fails_before_provider_recovery(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
        saved=next(r for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_base_execution')
        f.io.catalog.cas._path(saved.blob.digest).write_bytes(b'changed')
        before=len(g.requests),len(c.requests)
        with self.assertRaises(StageExecutionFailure):e(retry_context(f,first))
        self.assertEqual(before,(len(g.requests),len(c.requests)))

    def test_same_attempt_or_same_key_cannot_start_a_new_repair_revision(self):
        for same_key in (True,False):
            f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first)
            bad=replace(retry_context(f,first),idempotency_key=first.idempotency_key) if same_key else replace(retry_context(f,first),attempt=1)
            with self.assertRaises(StageExecutionFailure):e(bad)
            self.assertEqual(len(g.requests),3)

    def test_fourth_attempt_is_rejected_before_any_generation(self):
        f=self.fixture(); e,g,c,s=self.stage(f)
        with self.assertRaises(StageExecutionFailure) as err:e(replace(context(f),attempt=4))
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_STAGE_ATTEMPT_BUDGET_EXCEEDED']);self.assertEqual(g.requests,[])

    def test_old_success_replay_cannot_restore_superseded_director_output(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); e(first); e(retry_context(f,first))
        with self.assertRaises(StageExecutionFailure) as err:e(first)
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_REVISION_CONFLICT'])

    def test_decoder_rejects_unknown_fields_boolean_offsets_and_dynamic_class_names(self):
        f=self.fixture(); e,g,c,s=self.stage(f); r=e(context(f)); ev=f.io.load(r.evidence_refs[0])
        raw=ev.payload['result']['base_result']; self.assertEqual(fingerprint(asdict(grounded_record(raw))),fingerprint(raw))
        with self.assertRaises(ValueError):grounded_record({**raw,'__class__':'os.system'})
        raw['execution']['snapshot']['utterances'][0]['text']=False
        with self.assertRaises(ValueError):grounded_record(raw)


if __name__=='__main__':unittest.main()
