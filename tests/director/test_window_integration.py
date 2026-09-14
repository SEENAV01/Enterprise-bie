from dataclasses import replace
import tempfile,unittest
from window_fixtures import long_upstream
from windowed_directing_fixtures import WindowProtocolFixture
from teaching_fixtures import ContextAnnotationFixture
from directing_fixtures import executor,context,orchestrator
from annotation_review_fixtures import runtime
from repair_fixtures import retry_context,intents
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError
from bie.director.recovery_codec import grounded_record
from bie.director.windowed_directing import WindowedDirectorResult
from bie.director.narration_annotations import verify_base
from bie.infrastructure.orchestrator import StageExecutionFailure


class WindowIntegrationTests(unittest.TestCase):
    def fixture(self,**kwargs):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);return long_upstream(tmp.name,**kwargs)

    def stage(self,f,**kwargs):
        e,g,c,s=executor(f,generator=WindowProtocolFixture(),policy=WindowedDirectingPolicy(),
            annotations=kwargs.pop('annotations',runtime(annotator=ContextAnnotationFixture())),**kwargs)
        self.addCleanup(s.close);return e,g,c,s

    def test_registered_orchestrator_publishes_all_four_review_only_consumer_candidates(self):
        f=self.fixture();e,g,c,s=self.stage(f);o=orchestrator(f,e)
        self.assertEqual(o.run_until_blocked_or_complete(),['DIRECTOR'])
        ref=o.state.stages['DIRECTOR'].current.output_artifact_refs[0]
        consumers=DirectorConsumers(f.io,e.revisions);_,execution=consumers._director(ref);v,a=intents(execution)
        visual=consumers.visual(ref,v)
        for candidate in (consumers.timing(ref),visual,consumers.animation(ref,visual,a),consumers.game_handoff(ref)):
            artifact=consumers.read_current(candidate)
            self.assertFalse(artifact.metadata['accepted']);self.assertFalse(artifact.metadata['release_ready'])
            self.assertTrue(artifact.metadata['requires_review'])
        self.assertEqual(len(g.requests),10);self.assertEqual(len(e.annotations.annotator.requests),1)
        self.assertEqual(len(e.annotations.reviewer.requests),1)
        self.assertEqual(len({u.scene_id for u in execution.snapshot.utterances}),8)

    def test_successful_persisted_replay_performs_no_provider_calls_again(self):
        f=self.fixture();e,g,c,s=self.stage(f);ctx=context(f);result=e(ctx)
        before=(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests))
        self.assertEqual(e(ctx),result)
        self.assertEqual(before,(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests)))

    def test_original_phase_repair_reuses_exact_windowed_base_and_reruns_factual_qa(self):
        f=self.fixture();bad=runtime(annotator=ContextAnnotationFixture(lambda p,v,n:{}))
        e,g,c,s=self.stage(f,annotations=bad);o=orchestrator(f,e)
        self.assertEqual(o.run_until_blocked_or_complete(),[])
        old=o.state.stages['DIRECTOR'].current
        saved=f.io.load(old.evidence_refs[0]).payload['result'];base=grounded_record(saved)
        self.assertIsInstance(base,WindowedDirectorResult);verify_base(f.io,f.inputs,base)
        before=len(g.requests),len(c.requests)
        key=s.db.execute('SELECT key FROM claims').fetchone()[0]
        e.annotations=runtime(annotator=ContextAnnotationFixture())
        o.configuration['director_repair']={'previous_idempotency_key':key}
        o.retry_failed('DIRECTOR');self.assertEqual(o.resume(),['DIRECTOR'])
        self.assertEqual(len(g.requests),before[0]);self.assertGreater(len(c.requests),before[1])
        retained=[f.io.load(r.artifact_id).payload['result'] for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_base_execution']
        self.assertEqual(retained[-1]['window_execution'],saved['window_execution'])
        self.assertEqual(retained[-1]['narrated_scenes'],saved['narrated_scenes'])
        receipts=[f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair']
        self.assertEqual(receipts[-1].payload['action'],'REUSE_PLAN_NARRATION_RECHECK_QA')

    def test_changed_window_policy_regenerates_and_invalidates_previous_consumers(self):
        f=self.fixture();e,g,c,s=self.stage(f);first=context(f);old=e(first)
        consumers=DirectorConsumers(f.io,e.revisions);timing=consumers.timing(old.output_artifact_refs[0]);before=len(g.requests)
        e.policy=replace(e.policy,prior_scene_count=2)
        result=e(retry_context(f,first));self.assertGreater(len(g.requests),before)
        receipts=[f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair']
        self.assertEqual(receipts[-1].payload['action'],'REGENERATE')
        with self.assertRaises(RevisionError):consumers.read_current(timing)
        self.assertTrue(consumers.read_current(consumers.game_handoff(result.output_artifact_refs[0])))

    def test_actual_source_ancestor_invalidation_reaches_windowed_consumers_and_replay(self):
        f=self.fixture();e,g,c,s=self.stage(f);ctx=context(f);result=e(ctx)
        consumers=DirectorConsumers(f.io,e.revisions);game=consumers.game_handoff(result.output_artifact_refs[0])
        source=next(a.to_ref() for a in f.io.load_graph((f.source_ref,)).values() if a.artifact_type=='source.document')
        self.assertEqual(len(e.revisions.invalidate_inputs(f.io,f.run_id,(source,),'original source superseded')),1)
        with self.assertRaises(RevisionError):consumers.read_current(game)
        before=len(g.requests),len(c.requests)
        with self.assertRaises(StageExecutionFailure):e(ctx)
        self.assertEqual(before,(len(g.requests),len(c.requests)))

    def test_unsegmented_annotation_budget_remains_explicit_and_retains_complete_window_base(self):
        f=self.fixture(page_characters=5600);e,g,c,s=self.stage(f)
        with self.assertRaises(StageExecutionFailure) as err:e(context(f))
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_CONTEXT_BUDGET_EXCEEDED'])
        self.assertEqual(len(e.annotations.annotator.requests),0)
        self.assertFalse(any(r.artifact_type=='director.plan' for r in f.io.catalog.records.values()))
        saved=f.io.load(err.exception.evidence_refs[0]).payload['result'];base=grounded_record(saved)
        self.assertEqual(len(base.narrated_scenes),8);verify_base(f.io,f.inputs,base)

    def test_indivisible_factual_page_budget_cannot_become_an_automatic_pass(self):
        f=self.fixture(units=1,page_characters=30000);e,g,c,s=self.stage(f,annotations=None)
        result=e(context(f));record=f.io.load(result.evidence_refs[0]).payload['result'];base=grounded_record(record)
        self.assertEqual(len(g.requests),2);self.assertEqual(len(c.requests),0)
        self.assertTrue(base.semantic_evaluation.failures)
        self.assertEqual({reason for _,reason in base.semantic_evaluation.failures},{'SOURCE_CONTEXT_BUDGET_EXCEEDED'})
        self.assertEqual(base.status,'REVIEW_REQUIRED');self.assertFalse(base.accepted)
        self.assertEqual(len(base.narrated_scenes),1);verify_base(f.io,f.inputs,base)


if __name__=='__main__':unittest.main()
