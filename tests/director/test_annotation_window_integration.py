from dataclasses import replace
import tempfile,unittest
from window_fixtures import long_upstream
from windowed_directing_fixtures import WindowProtocolFixture
from annotation_window_fixtures import WindowAnnotationFixture,WindowReviewFixture,window_runtime
from annotation_review_fixtures import REVIEWER
from directing_fixtures import executor,context,orchestrator
from repair_fixtures import retry_context,intents
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.annotation_window_context import WindowedAnnotationPolicy
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError
from bie.infrastructure.orchestrator import StageExecutionFailure


class AnnotationWindowIntegrationTests(unittest.TestCase):
    def fixture(self,**kwargs):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        return long_upstream(tmp.name,**({'units':3,'page_characters':500}|kwargs))
    def stage(self,f,annotations=None):
        e,g,c,s=executor(f,generator=WindowProtocolFixture(),policy=WindowedDirectingPolicy(),
            annotations=annotations or window_runtime());self.addCleanup(s.close);return e,g,c,s

    def test_registered_large_lesson_runs_annotations_reviews_and_four_original_consumers(self):
        f=self.fixture(units=8,page_characters=7000);e,g,c,s=self.stage(f);o=orchestrator(f,e)
        self.assertEqual(o.run_until_blocked_or_complete(),['DIRECTOR']);ref=o.state.stages['DIRECTOR'].current.output_artifact_refs[0]
        consumers=DirectorConsumers(f.io,e.revisions);_,execution=consumers._director(ref);v,a=intents(execution);visual=consumers.visual(ref,v)
        candidates=(consumers.timing(ref),visual,consumers.animation(ref,visual,a),consumers.game_handoff(ref))
        for candidate in candidates:
            artifact=consumers.read_current(candidate);self.assertTrue(artifact.metadata['requires_review']);self.assertFalse(artifact.metadata['accepted'])
        self.assertEqual(len(e.annotations.annotator.requests),9);self.assertEqual(len(e.annotations.reviewer.requests),9)
        self.assertEqual(len({u.scene_id for u in execution.snapshot.utterances}),8)

    def test_persisted_idempotent_replay_adds_no_provider_calls(self):
        f=self.fixture();e,g,c,s=self.stage(f);ctx=context(f);result=e(ctx)
        before=(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests))
        self.assertEqual(e(ctx),result);self.assertEqual(before,(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests)))

    def test_failed_scene_annotation_repair_reuses_exact_narration_and_reruns_scoped_work(self):
        f=self.fixture();bad=window_runtime(annotator=WindowAnnotationFixture(lambda p,v,n:{}))
        e,g,c,s=self.stage(f,bad);first=context(f)
        with self.assertRaises(StageExecutionFailure):e(first)
        calls=len(g.requests),len(c.requests);key=s.db.execute('SELECT key FROM claims').fetchone()[0]
        e.annotations=window_runtime();result=e(retry_context(f,first))
        self.assertEqual(len(g.requests),calls[0]);self.assertGreater(len(c.requests),calls[1])
        self.assertEqual(len(e.annotations.annotator.requests),4);self.assertEqual(len(e.annotations.reviewer.requests),4)
        receipts=[f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair']
        self.assertEqual(receipts[-1].payload['action'],'REUSE_PLAN_NARRATION_RECHECK_QA')
        self.assertTrue(DirectorConsumers(f.io,e.revisions).read_current(DirectorConsumers(f.io,e.revisions).timing(result.output_artifact_refs[0])))

    def test_failed_review_scope_is_retained_as_review_evidence_and_consumer_revalidates_it(self):
        f=self.fixture();target='source:window:1:pedagogy:archive:1:1'
        review=WindowReviewFixture(lambda p,v,n:(_ for _ in ()).throw(RuntimeError('controlled')) if p['target_scope']==target else v)
        e,g,c,s=self.stage(f,window_runtime(reviewer=review));result=e(context(f))
        evidence=f.io.load(result.evidence_refs[0]);failures=evidence.payload['result']['annotation_review']['failures']
        self.assertTrue(any(x.startswith(target+':') for x in failures))
        consumers=DirectorConsumers(f.io,e.revisions);self.assertTrue(consumers.read_current(consumers.game_handoff(result.output_artifact_refs[0])))

    def test_observed_issue_blocks_publication_even_when_other_scopes_support_it(self):
        f=self.fixture()
        def issue(p,v,n):
            if p['target_scope'].startswith('source:'):
                v['judgments'][0]['verdict']='ISSUE';v['judgments'][0]['rationale']='Controlled issue.'
            return v
        e,g,c,s=self.stage(f,window_runtime(reviewer=WindowReviewFixture(issue)))
        with self.assertRaises(StageExecutionFailure) as err:e(context(f))
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_QA_BLOCKED'])
        self.assertFalse(any(r.artifact_type=='director.plan' for r in f.io.catalog.records.values()))

    def test_annotation_policy_change_reuses_generation_but_creates_new_revision_and_stales_consumers(self):
        f=self.fixture();e,g,c,s=self.stage(f);first=context(f);old=e(first);consumers=DirectorConsumers(f.io,e.revisions)
        timing=consumers.timing(old.output_artifact_refs[0]);before=len(g.requests);key=s.db.execute('SELECT key FROM claims').fetchone()[0]
        p=replace(e.annotations.policy,maximum_windows=64);e.annotations=window_runtime(policy=p)
        result=e(retry_context(f,first));self.assertEqual(len(g.requests),before)
        with self.assertRaises(RevisionError):consumers.read_current(timing)
        self.assertTrue(consumers.read_current(consumers.game_handoff(result.output_artifact_refs[0])))
        receipt=[f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair'][-1]
        self.assertEqual(receipt.payload['action'],'REUSE_PLAN_NARRATION_RECHECK_QA')

    def test_source_ancestor_invalidation_rejects_scoped_review_output_and_replay_without_calls(self):
        f=self.fixture();e,g,c,s=self.stage(f);ctx=context(f);result=e(ctx);consumers=DirectorConsumers(f.io,e.revisions)
        game=consumers.game_handoff(result.output_artifact_refs[0]);source=next(a.to_ref() for a in f.io.load_graph((f.source_ref,)).values() if a.artifact_type=='source.document')
        self.assertEqual(len(e.revisions.invalidate_inputs(f.io,f.run_id,(source,),'source superseded')),1)
        before=(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests))
        with self.assertRaises(RevisionError):consumers.read_current(game)
        with self.assertRaises(StageExecutionFailure):e(ctx)
        self.assertEqual(before,(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests)))


if __name__=='__main__':unittest.main()
