from dataclasses import replace
import tempfile,unittest
from input_fixtures import upstream
from directing_fixtures import executor,context,orchestrator
from annotation_fixtures import AnnotationProtocolFixture
from annotation_review_fixtures import ReviewProtocolFixture,runtime,trusted_review_policy
from bie.infrastructure.orchestrator import StageExecutionFailure
from semantic_fixtures import ProtocolFixtureProvider,response_record
from bie.director.narration_annotations import AnnotationPolicy


class AnnotatedStageTests(unittest.TestCase):
    def fixture(self,case='science'):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);return upstream(tmp.name,case)
    def stage(self,f,rt=None,**kwargs):
        rt=rt or runtime();e,g,c,s=executor(f,annotations=rt,**kwargs);self.addCleanup(s.close);return e,g,c,s,rt

    def test_registered_stage_consumes_annotations_and_emits_versioned_review_candidates(self):
        for case,claims in (('science',15),('economics',13),('history',14)):
            f=self.fixture(case);e,g,c,s,rt=self.stage(f);o=orchestrator(f,e)
            with self.subTest(case=case):
                self.assertEqual(o.run_until_blocked_or_complete(),['DIRECTOR'])
                output=f.io.load(o.state.stages['DIRECTOR'].current.output_artifact_refs[0])
                self.assertEqual(output.payload['schema_version'],'bie.dir.annotated_plan/1.0.0')
                self.assertEqual(len(output.payload['execution']['claims']),claims)
                graph=f.io.load_graph((output.to_ref(),))
                self.assertTrue(any(x.artifact_type=='evidence.director_base_execution' for x in graph.values()))
                evidence=f.io.load(output.payload['execution_evidence_ref']['artifact_id'])
                self.assertEqual(evidence.payload['schema_version'],'bie.dir.annotated_execution/1.0.0')
                result=evidence.payload['result']
                self.assertEqual(result['execution']['snapshot'],result['base_result']['execution']['snapshot'])
                self.assertTrue(result['execution']['emphasis']['anchors'])
                self.assertEqual(len(rt.annotator.requests),1);self.assertEqual(len(rt.reviewer.requests),1)
                self.assertTrue(output.metadata['requires_review']);self.assertFalse(output.metadata['accepted']);self.assertFalse(output.metadata['release_ready'])

    def test_success_replay_reuses_all_annotations_and_reviews_without_new_calls(self):
        f=self.fixture();e,g,c,s,rt=self.stage(f);ctx=context(f);first=e(ctx)
        before=(len(g.requests),len(c.requests),len(rt.annotator.requests),len(rt.reviewer.requests))
        self.assertEqual(e(ctx),first)
        self.assertEqual((len(g.requests),len(c.requests),len(rt.annotator.requests),len(rt.reviewer.requests)),before)
        e2,g2,c2,s2,rt2=self.stage(f)
        self.assertEqual(e2(ctx),first);self.assertEqual(rt2.annotator.requests,[]);self.assertEqual(rt2.reviewer.requests,[])

    def test_policy_change_cannot_replay_a_differently_reviewed_result_under_same_key(self):
        f=self.fixture();e,g,c,s,rt=self.stage(f);ctx=context(f);e(ctx)
        e2,g2,c2,s2,rt2=self.stage(f,runtime(review_policy=trusted_review_policy()))
        with self.assertRaises(StageExecutionFailure) as error:e2(ctx)
        self.assertEqual(error.exception.diagnostics,['DIRECTOR_IDEMPOTENCY_CONFLICT']);self.assertEqual(g2.requests,[])

    def test_annotation_failure_preserves_actual_base_candidate_and_failure_replays(self):
        f=self.fixture();rt=runtime(annotator=AnnotationProtocolFixture(lambda p,v,n:{}));e,g,c,s,rt=self.stage(f,rt);ctx=context(f)
        with self.assertRaises(StageExecutionFailure) as error:e(ctx)
        refs=error.exception.evidence_refs;base=f.io.load(refs[0]);receipt=e._read_blob(refs[1])
        self.assertEqual(base.artifact_type,'evidence.director_base_execution')
        self.assertTrue(base.payload['result']['execution']['snapshot']['utterances'])
        self.assertEqual([a['phase'] for a in receipt['generation_attempts']][-2:],['ANNOTATE','ANNOTATE'])
        before=(len(g.requests),len(rt.annotator.requests))
        with self.assertRaises(StageExecutionFailure) as replay:e(ctx)
        self.assertEqual(replay.exception.evidence_refs,refs);self.assertEqual((len(g.requests),len(rt.annotator.requests)),before)
        self.assertFalse(any(r.artifact_type=='director.plan' for r in f.io.catalog.records.values()))

    def test_review_issue_blocks_publication_while_retaining_complete_candidate_evidence(self):
        f=self.fixture()
        def mutate(p,v,n):v['judgments'][0].update(verdict='ISSUE',rationale='Incorrect annotation.');return v
        e,g,c,s,rt=self.stage(f,runtime(reviewer=ReviewProtocolFixture(mutate)));o=orchestrator(f,e)
        self.assertEqual(o.run_until_blocked_or_complete(),[])
        self.assertEqual(o.state.stages['DIRECTOR'].current.state,'FAILED')
        ref=o.state.stages['DIRECTOR'].current.evidence_refs[0];ev=f.io.load(ref)
        self.assertEqual(ev.metadata['status'],'BLOCKED');self.assertTrue(ev.payload['result']['annotation_review']['judgments'])
        self.assertFalse(any(r.artifact_type=='director.plan' for r in f.io.catalog.records.values()))

    def test_refused_review_is_recorded_and_never_marks_audience_review_complete(self):
        class Refusing(ReviewProtocolFixture):
            def invoke(self,request):return replace(super().invoke(request),finish_reason='refusal')
        f=self.fixture();e,g,c,s,rt=self.stage(f,runtime(reviewer=Refusing()));result=e(context(f))
        ev=f.io.load(result.evidence_refs[0]);r=ev.payload['result']
        self.assertEqual(r['annotation_review']['failures'],['INCOMPLETE_OR_REFUSED_RESPONSE'])
        findings=[f['code'] for q in r['qa_reports'] for f in q['findings']]
        self.assertIn('AUDIENCE_ANNOTATIONS_UNREVIEWED',findings);self.assertIn('ANNOTATION_COMPLETENESS_UNVERIFIED',findings)
        self.assertEqual(result.metadata['status'],'REVIEW_REQUIRED');self.assertFalse(result.metadata['release_ready'])

    def test_original_factual_contradiction_prevents_annotations_from_bypassing_guard(self):
        f=self.fixture();critic=ProtocolFixtureProvider(lambda p,n:response_record(p,verdict='CONTRADICTED'))
        e,g,c,s,rt=self.stage(f,critic=critic)
        with self.assertRaises(StageExecutionFailure) as error:e(context(f))
        self.assertEqual(error.exception.diagnostics,['DIRECTOR_QA_BLOCKED'])
        self.assertEqual(rt.annotator.requests,[]);self.assertEqual(rt.reviewer.requests,[])

    def test_corrupt_retained_base_evidence_invalidates_replay_without_regeneration(self):
        f=self.fixture();e,g,c,s,rt=self.stage(f);ctx=context(f);result=e(ctx)
        base=next(r for r in f.io.catalog.records.values() if r.artifact_type=='evidence.director_base_execution')
        f.io.catalog.cas._path(base.blob.digest).write_bytes(b'corrupt')
        before=len(g.requests),len(rt.annotator.requests)
        with self.assertRaises(StageExecutionFailure) as error:e(ctx)
        self.assertEqual(error.exception.diagnostics,['DIRECTOR_IDEMPOTENCY_INVALID'])
        self.assertEqual((len(g.requests),len(rt.annotator.requests)),before)

    def test_unresolved_transition_remains_explicit_review_in_persisted_output(self):
        f=self.fixture()
        def mutate(p,v,n):v['transitions'][0].update(relation='UNRESOLVED',cue_span=None,rationale='Speech does not establish this bridge.');return v
        e,g,c,s,rt=self.stage(f,runtime(annotator=AnnotationProtocolFixture(mutate)));result=e(context(f))
        ev=f.io.load(result.evidence_refs[0]);r=ev.payload['result']
        self.assertTrue(r['annotation_production']['annotations']['unresolved_transitions'])
        self.assertTrue(any(f['code']=='TRANSITION_UNRESOLVED' for q in r['qa_reports'] for f in q['findings']))
        self.assertEqual(result.metadata['status'],'REVIEW_REQUIRED')


if __name__=='__main__':unittest.main()
