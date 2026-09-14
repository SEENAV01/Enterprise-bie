from dataclasses import replace
import tempfile,unittest
from input_fixtures import upstream
from directing_fixtures import executor,context,orchestrator,DirectorProtocolFixture
from annotation_review_fixtures import runtime
from annotation_fixtures import AnnotationProtocolFixture
from repair_fixtures import retry_context
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError
from bie.infrastructure.orchestrator import StageExecutionFailure


class RevisionIntegrationTests(unittest.TestCase):
    def fixture(self,case='science'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);return upstream(tmp.name,case)
    def stage(self,f,**kwargs):
        e,g,c,s=executor(f,annotations=kwargs.pop('annotations',runtime()),**kwargs);self.addCleanup(s.close);return e,g,c,s

    def test_original_registered_orchestrator_retry_resumes_persisted_base(self):
        f=self.fixture();e,g,c,s=self.stage(f,annotations=runtime(annotator=AnnotationProtocolFixture(lambda p,v,n:{})))
        o=orchestrator(f,e);self.assertEqual(o.run_until_blocked_or_complete(),[])
        key=s.db.execute('SELECT key FROM claims').fetchone()[0]
        o.configuration['director_repair']={'previous_idempotency_key':key};e.annotations=runtime()
        o.retry_failed('DIRECTOR');self.assertEqual(o.resume(),['DIRECTOR'])
        self.assertEqual(len(g.requests),3);self.assertEqual(o.state.stages['DIRECTOR'].current.attempt,2)
        refs=o.state.stages['DIRECTOR'].current.output_artifact_refs
        consumer=DirectorConsumers(f.io,e.revisions);self.assertTrue(consumer.read_current(consumer.timing(refs[0])))

    def test_running_revision_invalidated_by_source_change_cannot_publish_late(self):
        f=self.fixture();holder={};called=[]
        def invalidate(p,v,n):
            if n==1:
                called.extend(holder['e'].revisions.invalidate_inputs(f.io,f.run_id,(f.source_ref,),'source changed during generation'))
            return v
        e,g,c,s=self.stage(f,generator=DirectorProtocolFixture(invalidate));holder['e']=e
        with self.assertRaises(StageExecutionFailure) as err:e(context(f))
        self.assertEqual(len(called),1);self.assertEqual(err.exception.diagnostics,['DIRECTOR_REVISION_CONFLICT'])
        self.assertEqual(e.revisions.get(f.run_id,f.config['lesson_id']).state,'STALE')
        for record in f.io.catalog.records.values():
            if record.artifact_type=='director.plan':
                with self.assertRaises(RevisionError):DirectorConsumers(f.io,e.revisions).timing(record.artifact_id)

    def test_newer_revision_owner_prevents_old_worker_from_publishing_or_failing_it(self):
        f=self.fixture();e,g,c,s=self.stage(f)
        args=(f.run_id,f.config['lesson_id']);parents=[f.source_ref.artifact_id,f.reasoning_ref.artifact_id,f.pedagogy_ref.artifact_id]
        old,_=e.revisions.begin(*args,1,'sha256:'+'1'*64,'worker1',parents)
        new,_=e.revisions.begin(*args,2,'sha256:'+'2'*64,'worker2',parents)
        with self.assertRaises(RevisionError):e.revisions.publish(old,'old-output')
        e.revisions.fail(old);self.assertEqual(e.revisions.get(*args),new)

    def test_consumer_publication_rechecks_currentness_after_computation(self):
        f=self.fixture();e,g,c,s=self.stage(f);r=e(context(f));consumer=DirectorConsumers(f.io,e.revisions)
        original=consumer._persist
        def race(output,*args,**kwargs):
            e.revisions.invalidate_inputs(f.io,f.run_id,(f.pedagogy_ref,),'new PED revision before consumer publication')
            return original(output,*args,**kwargs)
        consumer._persist=race
        with self.assertRaises(RevisionError):consumer.timing(r.output_artifact_refs[0])
        self.assertFalse(any(r.artifact_type=='director.timing_candidate' for r in f.io.catalog.records.values()))

    def test_invalidation_of_unrelated_artifact_preserves_current_lesson(self):
        f=self.fixture();e,g,c,s=self.stage(f);r=e(context(f));consumer=DirectorConsumers(f.io,e.revisions)
        unrelated=f.io.derive('evidence.unrelated',f.run_id,(f.source_ref,),{'purpose':'unrelated QA'},stage_id='QA',metadata={'accepted':False})
        self.assertEqual(e.revisions.invalidate_inputs(f.io,f.run_id,(unrelated,),'unrelated result changed'),())
        self.assertTrue(consumer.read_current(consumer.game_handoff(r.output_artifact_refs[0])))

    def test_repeated_invalidation_keeps_original_evidence_without_new_mutation(self):
        f=self.fixture();e,g,c,s=self.stage(f);e(context(f))
        first=e.revisions.invalidate_inputs(f.io,f.run_id,(f.reasoning_ref,),'reasoning superseded')
        before=len(f.io.catalog.records)
        self.assertEqual(e.revisions.invalidate_inputs(f.io,f.run_id,(f.reasoning_ref,),'reasoning superseded'),())
        self.assertEqual(len(f.io.catalog.records),before);self.assertTrue(f.io.load(first[0]))

    def test_retry_cannot_make_the_same_invalidated_source_current_again(self):
        f=self.fixture();e,g,c,s=self.stage(f);first=context(f);e(first)
        actual_source=next(a.to_ref() for a in f.io.load_graph((f.source_ref,)).values() if a.artifact_type=='source.document')
        e.revisions.invalidate_inputs(f.io,f.run_id,(actual_source,),'source was superseded')
        before=len(g.requests),len(c.requests)
        with self.assertRaises(StageExecutionFailure) as err:e(retry_context(f,first))
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_REVISION_CONFLICT'])
        self.assertEqual(before,(len(g.requests),len(c.requests)))
        self.assertEqual(e.revisions.get(f.run_id,f.config['lesson_id']).state,'STALE')

    def test_third_repair_cannot_select_a_superseded_first_attempt(self):
        f=self.fixture();e,g,c,s=self.stage(f);first=context(f);e(first);e(retry_context(f,first))
        with self.assertRaises(StageExecutionFailure) as err:e(retry_context(f,first,attempt=3))
        self.assertEqual(err.exception.diagnostics,['DIRECTOR_REPAIR_REQUIRES_PREVIOUS_REVISION'])


if __name__=='__main__':unittest.main()
