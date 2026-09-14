from dataclasses import replace
import tempfile
import unittest
from pathlib import Path

from bie.director.annotated_directing import AnnotationRuntime
from bie.director.director_artifacts import DirectorArtifactIO
from bie.director.director_durable_recovery import (
    DirectorLeaseStore, DirectorRecoveryCoordinator, SQLiteArtifactCatalog)
from bie.director.hierarchical_annotation_review import HierarchicalAnnotationReviewPolicy
from bie.director.hierarchical_annotations import HierarchicalAnnotationPolicy
from bie.director.production_adoption import (DirectorProductionAssembly,
    DirectorProductionRequest, ProductionSceneCorrection)
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore
from bie.infrastructure.orchestrator import StageExecutionFailure
from annotation_fixtures import ANNOTATOR
from annotation_review_fixtures import REVIEWER
from completion_fixtures import (HierarchicalAnnotationFixture, HierarchicalReviewFixture,
    RichTeachingProvider, SceneCorrectionFixture, rich_context)
from context_fixtures import context_upstream
from directing_fixtures import GENERATOR
from semantic_fixtures import IDENTITY, ProtocolFixtureProvider


class ProductionAdoptionTests(unittest.TestCase):
    def durable_fixture(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); root = Path(temp.name)
        f = context_upstream(root, 'science'); _,pedagogy,inputs = rich_context(f)
        f.pedagogy_ref=pedagogy;f.inputs=inputs
        durable = SQLiteArtifactCatalog(f.io.catalog.cas, root/'catalog.sqlite')
        for record in f.io.catalog.records.values(): durable.register(record)
        f.io=DirectorArtifactIO(durable)
        claims=SQLiteIdempotencyStore(root/'idempotency.sqlite')
        leases=DirectorLeaseStore(root/'leases.sqlite')
        self.addCleanup(durable.close);self.addCleanup(claims.close);self.addCleanup(leases.close)
        annotator=HierarchicalAnnotationFixture();reviewer=HierarchicalReviewFixture()
        runtime=AnnotationRuntime(annotator,ANNOTATOR,reviewer,REVIEWER,
            HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1),HierarchicalAnnotationReviewPolicy())
        generator=RichTeachingProvider();critic=ProtocolFixtureProvider()
        assembly=DirectorProductionAssembly(f.io,claims,DirectorRecoveryCoordinator(leases),
            generator,GENERATOR,critic,IDENTITY,runtime)
        request=DirectorProductionRequest(f.run_id,'production:science:1',1,f.config['lesson_id'],
            f.config['title'],f.config['language'],f.reasoning_ref,f.pedagogy_ref)
        return root,f,assembly,request,generator,critic,annotator,reviewer

    def test_request_contains_only_upstream_identity_not_hand_authored_directing(self):
        _,_,assembly,request,*_=self.durable_fixture();context=assembly.context(request)
        self.assertEqual(set(context.configuration),{'director'})
        self.assertNotIn('scenes',repr(context.configuration));self.assertNotIn('claims',repr(context.configuration))
        self.assertEqual(context.input_artifact_refs,[request.pedagogy_ref.artifact_id,request.reasoning_ref.artifact_id])

    def test_composition_root_requires_durable_hierarchical_runtime(self):
        root,f,assembly,request,*_=self.durable_fixture()
        weak=replace(assembly.executor.annotations,policy=replace(assembly.executor.annotations.policy,
            window_version='bie-dir-annotation-windows/1.0.0'))
        with self.assertRaises(ValueError):DirectorProductionAssembly(f.io,assembly.idempotency,assembly.recovery,
            assembly.executor.generator,GENERATOR,assembly.executor.critic,IDENTITY,weak)

    def test_registered_execution_persists_hierarchical_review_only_output_and_consumes_it(self):
        _,f,assembly,request,generator,critic,annotator,reviewer=self.durable_fixture()
        definitions,executors=assembly.register({},{});self.assertIn('DIRECTOR',definitions);self.assertIs(executors['DIRECTOR'],assembly.executor)
        result=assembly.execute(request);output=f.io.load(result.output_artifact_refs[0]);evidence=f.io.load(result.evidence_refs[0])
        self.assertEqual(output.metadata['accepted'],False);self.assertEqual(output.metadata['release_ready'],False)
        self.assertIn('discourse_scopes',evidence.payload['result']['annotation_production'])
        self.assertIn('discourse_schedule_fingerprint',evidence.payload['result']['annotation_review'])
        self.assertTrue(generator.requests and critic.requests and annotator.requests and reviewer.requests)
        handoff=assembly.consumers().game_handoff(output.to_ref())
        self.assertEqual(assembly.consumers().read_current(handoff).metadata['accepted'],False)

    def test_durable_restart_replays_without_any_provider_call(self):
        root,f,assembly,request,*_=self.durable_fixture();expected=assembly.execute(request)
        assembly.io.catalog.close();assembly.idempotency.close();assembly.recovery.leases.close()
        catalog=SQLiteArtifactCatalog(f.io.catalog.cas,root/'catalog.sqlite');claims=SQLiteIdempotencyStore(root/'idempotency.sqlite')
        leases=DirectorLeaseStore(root/'leases.sqlite')
        self.addCleanup(catalog.close);self.addCleanup(claims.close);self.addCleanup(leases.close)
        g=RichTeachingProvider();c=ProtocolFixtureProvider();a=HierarchicalAnnotationFixture();r=HierarchicalReviewFixture()
        runtime=AnnotationRuntime(a,ANNOTATOR,r,REVIEWER,HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1),HierarchicalAnnotationReviewPolicy())
        restarted=DirectorProductionAssembly(DirectorArtifactIO(catalog),claims,DirectorRecoveryCoordinator(leases),g,GENERATOR,c,IDENTITY,runtime)
        self.assertEqual(restarted.execute(request),expected)
        self.assertEqual((g.requests,c.requests,a.requests,r.requests),([],[],[],[]))

    def test_expired_crashed_running_revision_is_fenced_reclaimed_and_completed(self):
        _,_,assembly,request,generator,*_=self.durable_fixture()
        class CrashedProvider:
            def __init__(self):self.requests=[]
            def invoke(self,model_request):self.requests.append(model_request);raise KeyboardInterrupt('controlled worker loss')
        crashed=CrashedProvider();assembly.executor.generator=crashed
        with self.assertRaises(KeyboardInterrupt):assembly.execute(request)
        claim=assembly.idempotency.get(request.idempotency_key);self.assertEqual(claim.state,'CLAIMED')
        revision=assembly.executor.revisions.get(request.run_id,request.lesson_id);self.assertEqual(revision.state,'RUNNING')
        assembly.recovery.leases.db.execute('UPDATE director_leases SET expires_at=0 WHERE key=?',(request.idempotency_key,))
        assembly.recovery.leases.db.commit();assembly.executor.generator=generator
        result=assembly.execute(request)
        self.assertTrue(result.output_artifact_refs);self.assertEqual(assembly.idempotency.get(request.idempotency_key).state,'COMPLETED')
        self.assertEqual(assembly.recovery.leases.get(request.idempotency_key).epoch,2)
        self.assertTrue(generator.requests)

    def test_scene_correction_runs_through_registered_executor_and_reuses_unchanged_local_annotation(self):
        _,f,assembly,request,_,_,annotator,_=self.durable_fixture();first=assembly.execute(request)
        scene_ids=[row['scene_id'] for row in f.io.load(first.output_artifact_refs[0]).payload['plan']['scenes']]
        corrector=SceneCorrectionFixture();assembly.executor.generator=corrector
        repair=replace(request,idempotency_key='production:science:2',attempt=2,
            previous_idempotency_key=request.idempotency_key,
            scene_corrections=(ProductionSceneCorrection(scene_ids[0],('REVIEWED_LOCAL_EXPLANATION_GAP',)),))
        second=assembly.execute(repair);raw=f.io.load(second.evidence_refs[0]).payload['result']
        self.assertEqual(len(corrector.requests),1)
        corrected=[call['scene_ids'][0] for call in raw['base_result']['correction_calls']]
        self.assertEqual(corrected,[scene_ids[0]])
        self.assertEqual(len(raw['annotation_production']['source_reuses']),len(scene_ids)-1)
        with self.assertRaises(Exception):assembly.consumers().game_handoff(first.output_artifact_refs[0])

    def test_upstream_invalidation_stales_current_output_and_all_descendants(self):
        _,f,assembly,request,*_=self.durable_fixture();result=assembly.execute(request)
        child=assembly.consumers().game_handoff(result.output_artifact_refs[0])
        receipts=assembly.invalidate_superseded(f.run_id,(f.source_ref,),'source revision published')
        self.assertEqual(len(receipts),1)
        with self.assertRaises(Exception):assembly.consumers().read_current(child)

    def test_mismatched_run_or_repair_shape_fails_before_provider_calls(self):
        _,_,assembly,request,generator,critic,annotator,reviewer=self.durable_fixture()
        for bad in (replace(request,run_id='other'),replace(request,attempt=2),
                    replace(request,scene_corrections=(ProductionSceneCorrection('scene:x',('reason',)),))):
            with self.subTest(bad=bad),self.assertRaises((ValueError,StageExecutionFailure)):assembly.execute(bad)
        self.assertEqual((generator.requests,critic.requests,annotator.requests,reviewer.requests),([],[],[],[]))


if __name__=='__main__':unittest.main()
