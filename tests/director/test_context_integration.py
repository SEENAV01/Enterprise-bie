import json, tempfile, unittest
from context_fixtures import context_upstream, scored_event, publish_context, rebind
from teaching_fixtures import TeachingProtocolFixture, ContextAnnotationFixture
from directing_fixtures import executor, context, orchestrator
from annotation_review_fixtures import runtime
from repair_fixtures import retry_context, intents
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError
from bie.infrastructure.orchestrator import StageExecutionFailure


class ContextIntegrationTests(unittest.TestCase):
    def fixture(self,case='science',**kwargs):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); return context_upstream(tmp.name,case,**kwargs)

    def stage(self,f,**kwargs):
        annotation=kwargs.pop('annotations',runtime(annotator=ContextAnnotationFixture()))
        e,g,c,s=executor(f,generator=TeachingProtocolFixture(),annotations=annotation,**kwargs); self.addCleanup(s.close)
        return e,g,c,s

    def test_three_cases_use_registered_stage_and_review_only_consumers(self):
        for case in ('science','economics','math'):
            with self.subTest(case=case):
                f=self.fixture(case); e,g,c,s=self.stage(f); o=orchestrator(f,e)
                self.assertEqual(o.run_until_blocked_or_complete(),['DIRECTOR'])
                ref=o.state.stages['DIRECTOR'].current.output_artifact_refs[0]
                consumers=DirectorConsumers(f.io,e.revisions); _,execution=consumers._director(ref); v,a=intents(execution)
                visual=consumers.visual(ref,v)
                for candidate in (consumers.timing(ref),visual,consumers.animation(ref,visual,a),consumers.game_handoff(ref)):
                    artifact=consumers.read_current(candidate)
                    self.assertFalse(artifact.metadata['accepted']); self.assertFalse(artifact.metadata['release_ready'])
                    self.assertTrue(artifact.metadata['requires_review'])
                self.assertEqual(len(g.requests),3)

    def test_rich_success_replay_performs_no_generation_or_review_again(self):
        f=self.fixture('math'); e,g,c,s=self.stage(f); ctx=context(f); result=e(ctx)
        before=(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests))
        self.assertEqual(e(ctx),result)
        self.assertEqual(before,(len(g.requests),len(c.requests),len(e.annotations.annotator.requests),len(e.annotations.reviewer.requests)))

    def test_failed_annotation_repair_reuses_rich_narration_but_reexecutes_qa(self):
        f=self.fixture('math'); bad=ContextAnnotationFixture(lambda p,v,n:{})
        e,g,c,s=self.stage(f,annotations=runtime(annotator=bad)); first=context(f)
        with self.assertRaises(StageExecutionFailure): e(first)
        calls=len(g.requests),len(c.requests); e.annotations=runtime(annotator=ContextAnnotationFixture())
        result=e(retry_context(f,first)); self.assertEqual(len(g.requests),calls[0]); self.assertGreater(len(c.requests),calls[1])
        receipts=[f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair']
        self.assertEqual(receipts[-1].payload['action'],'REUSE_PLAN_NARRATION_RECHECK_QA')
        self.assertTrue(DirectorConsumers(f.io,e.revisions).read_current(DirectorConsumers(f.io,e.revisions).timing(result.output_artifact_refs[0])))

    def test_new_context_forces_generation_and_invalidates_prior_consumers(self):
        f=self.fixture(); e,g,c,s=self.stage(f); first=context(f); old=e(first)
        consumers=DirectorConsumers(f.io,e.revisions); old_timing=consumers.timing(old.output_artifact_refs[0])
        event=scored_event(f,score=1.); fresh=publish_context(f,observation_refs=(event,))
        f.pedagogy_ref,f.inputs=rebind(f,fresh); before=len(g.requests)
        result=e(retry_context(f,first)); self.assertEqual(len(g.requests)-before,3)
        receipt=next(f.io.load(r.artifact_id) for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_repair')
        self.assertEqual(receipt.payload['action'],'REGENERATE'); self.assertIn('INPUTS',receipt.payload['reason'])
        with self.assertRaises(RevisionError): consumers.read_current(old_timing)
        self.assertTrue(consumers.read_current(consumers.game_handoff(result.output_artifact_refs[0])))
        last=json.loads(g.requests[-1].messages[1]['content'])
        self.assertEqual(last['inputs']['teaching_context']['bridge_decision_ids'],['pedagogy:charge'])

    def test_context_ancestor_invalidation_prevents_old_output_replay(self):
        f=self.fixture(); e,g,c,s=self.stage(f); ctx=context(f); result=e(ctx)
        consumers=DirectorConsumers(f.io,e.revisions); timing=consumers.timing(result.output_artifact_refs[0])
        self.assertEqual(len(e.revisions.invalidate_inputs(f.io,f.run_id,(f.context_ref,),'source context superseded')),1)
        with self.assertRaises(RevisionError): consumers.read_current(timing)
        with self.assertRaises(StageExecutionFailure): e(ctx)

    def test_assessment_event_ancestor_invalidation_reaches_game_candidate(self):
        f=self.fixture('economics',scores=(.9,)); e,g,c,s=self.stage(f); result=e(context(f))
        consumers=DirectorConsumers(f.io,e.revisions); game=consumers.game_handoff(result.output_artifact_refs[0])
        self.assertEqual(len(e.revisions.invalidate_inputs(f.io,f.run_id,(f.observation_refs[0],),'reported score corrected')),1)
        with self.assertRaises(RevisionError): consumers.read_current(game)

    def test_corrupted_context_envelope_is_detected_before_consumer_use(self):
        f=self.fixture('math'); e,g,c,s=self.stage(f); result=e(context(f)); consumers=DirectorConsumers(f.io,e.revisions)
        candidate=consumers.timing(result.output_artifact_refs[0]); record=f.io.catalog.records[f.context_ref.artifact_id]
        f.io.catalog.cas._path(record.blob.digest).write_bytes(b'edited context envelope')
        with self.assertRaises(ValueError): consumers.read_current(candidate)


if __name__=='__main__': unittest.main()
