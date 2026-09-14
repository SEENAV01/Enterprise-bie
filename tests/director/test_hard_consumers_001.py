from dataclasses import asdict,replace
import tempfile,unittest
from input_fixtures import upstream
from directing_fixtures import executor,context
from annotation_review_fixtures import runtime
from annotation_fixtures import AnnotationProtocolFixture
from repair_fixtures import retry_context,intents
from bie.director.director_consumers import DirectorConsumers
from bie.director.director_revisions import RevisionError
from bie.infrastructure.orchestrator import StageExecutionFailure


class ConsumerGateTests(unittest.TestCase):
    def fixture(self,case='science'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);f=upstream(tmp.name,case)
        e,g,c,s=executor(f,annotations=runtime());self.addCleanup(s.close)
        result=e(context(f));return f,e,result,DirectorConsumers(f.io,e.revisions)

    def test_actual_time_visual_animation_and_game_handoff_consume_persisted_director(self):
        f,e,result,consumers=self.fixture();ref=result.output_artifact_refs[0]
        _,execution=consumers._director(ref);visuals,animations=intents(execution)
        timing=consumers.timing(ref);visual=consumers.visual(ref,visuals)
        animation=consumers.animation(ref,visual,animations);game=consumers.game_handoff(ref)
        for item,kind in ((timing,'director.timing_candidate'),(visual,'director.visual_sync_candidate'),
                          (animation,'director.animation_sync_candidate'),(game,'director.game_handoff_candidate')):
            artifact=consumers.read_current(item)
            self.assertEqual(artifact.artifact_type,kind);self.assertTrue(artifact.metadata['requires_review'])
            self.assertFalse(artifact.metadata['accepted']);self.assertFalse(artifact.metadata['release_ready'])
        self.assertTrue(f.io.load(visual).payload['result']['cues']);self.assertTrue(f.io.load(animation).payload['result']['cues'])
        self.assertEqual(f.io.load(game).payload['result']['mastery_checks'],list(execution.game_handoff.mastery_checks))

    def test_no_preview_can_be_used_as_release_render_or_acceptance_authority(self):
        f,e,result,consumers=self.fixture();ref=consumers.timing(result.output_artifact_refs[0])
        for purpose in ('RELEASE','RENDER','ACCEPT','PRODUCTION'):
            with self.subTest(purpose=purpose),self.assertRaises(ValueError):consumers.read_current(ref,purpose=purpose)

    def test_failed_annotation_repair_invalidates_all_old_consumer_kinds(self):
        f,e,result,consumers=self.fixture();ref=result.output_artifact_refs[0]
        _,execution=consumers._director(ref);v,a=intents(execution)
        visual=consumers.visual(ref,v)
        refs=(consumers.timing(ref),visual,consumers.animation(ref,visual,a),consumers.game_handoff(ref))
        e.annotations=runtime(annotator=AnnotationProtocolFixture(lambda p,v,n:{}))
        with self.assertRaises(StageExecutionFailure):e(retry_context(f,context(f)))
        for old in refs:
            with self.subTest(kind=old.artifact_type),self.assertRaises(RevisionError):consumers.read_current(old)
        self.assertTrue(all(f.io.load(old) for old in refs))  # Immutable audit evidence remains.

    def test_source_invalidation_blocks_transitive_animation_and_game_candidates(self):
        f,e,result,consumers=self.fixture();ref=result.output_artifact_refs[0]
        _,execution=consumers._director(ref);v,a=intents(execution);visual=consumers.visual(ref,v)
        animation=consumers.animation(ref,visual,a);game=consumers.game_handoff(ref)
        receipts=e.revisions.invalidate_inputs(f.io,f.run_id,(f.source_ref,),'BI source revision replaced')
        self.assertEqual(len(receipts),1);self.assertEqual(f.io.load(receipts[0]).payload['superseded_artifact_ids'],[f.source_ref.artifact_id])
        for old in (visual,animation,game):
            with self.assertRaises(RevisionError):consumers.read_current(old)

    def test_missing_revision_index_after_restart_fails_closed(self):
        f,e,result,consumers=self.fixture();ref=consumers.timing(result.output_artifact_refs[0])
        with e.revisions.db:e.revisions.db.execute('DELETE FROM director_revisions')
        with self.assertRaises(RevisionError):consumers.read_current(ref)

    def test_successful_repair_rejects_old_visual_for_new_animation(self):
        f,e,result,consumers=self.fixture();old=result.output_artifact_refs[0]
        _,execution=consumers._director(old);v,a=intents(execution);visual=consumers.visual(old,v)
        new=e(retry_context(f,context(f))).output_artifact_refs[0]
        with self.assertRaises(RevisionError):consumers.animation(new,visual,a)
        self.assertEqual(consumers.read_current(consumers.game_handoff(new)).metadata['status'],'REVIEW_REQUIRED')

    def test_stale_voice_or_narration_anchor_is_rejected_before_consumer_output(self):
        f,e,result,consumers=self.fixture();ref=result.output_artifact_refs[0]
        _,execution=consumers._director(ref);v,a=intents(execution)
        bad=replace(v[0],binding=replace(v[0].binding,anchor=replace(v[0].binding.anchor,utterance_fingerprint='sha256:'+'0'*64)))
        before=len(f.io.catalog.records)
        with self.assertRaises(ValueError):consumers.visual(ref,(bad,))
        self.assertEqual(len(f.io.catalog.records),before)

    def test_sync_conflicts_are_retained_but_cannot_feed_a_next_consumer(self):
        f,e,result,consumers=self.fixture();ref=result.output_artifact_refs[0]
        _,execution=consumers._director(ref);v,a=intents(execution)
        duplicate=replace(v[0],binding=replace(v[0].binding,intent_id='visual:2'))
        blocked=consumers.visual(ref,(v[0],duplicate))
        self.assertEqual(f.io.load(blocked).metadata['status'],'BLOCKED')
        with self.assertRaises(ValueError):consumers.animation(ref,blocked,a)

    def test_corrupt_source_bytes_block_consumer_even_when_envelopes_are_unchanged(self):
        f,e,result,consumers=self.fixture();ref=consumers.timing(result.output_artifact_refs[0])
        source=next(a for a in f.io.load_graph((f.source_ref,)).values() if a.artifact_type=='source.document');blob=source.payload['blob']
        f.io.catalog.cas._path(blob['digest']).write_bytes(b'source changed')
        with self.assertRaises(ValueError):consumers.read_current(ref)

    def test_edited_candidate_flags_or_type_cannot_remove_review(self):
        f,e,result,consumers=self.fixture();original=f.io.load(consumers.timing(result.output_artifact_refs[0]))
        fake=f.io.derive(original.artifact_type,f.run_id,original.parent_refs,original.payload,stage_id='DIRECTOR',
            metadata={'requires_review':False,'accepted':True,'release_ready':True,'status':'REVIEW_REQUIRED'})
        with self.assertRaises(ValueError):consumers.read_current(fake)


if __name__=='__main__':unittest.main()
