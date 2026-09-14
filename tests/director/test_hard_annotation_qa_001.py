from dataclasses import replace
import json,tempfile,unittest
from input_fixtures import upstream
from annotation_fixtures import ANNOTATOR,AnnotationProtocolFixture,base_result
from annotation_review_fixtures import REVIEWER,ReviewProtocolFixture,runtime,trusted_review_policy
from bie.director.narration_annotations import AnnotationPolicy,produce_annotations
from bie.director.annotation_review import (AnnotationReviewPolicy,review_annotations,annotation_review_qa,
    approved_subjects,subjects)
from bie.director.director_model import DirectingPolicy,DirectingFailure
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY,response_record
from bie.director.semantic_execution import SemanticExecutionPolicy
from directing_fixtures import DirectorProtocolFixture


def codes(report):return {f.code for f in report.findings}


class AnnotationReviewTests(unittest.TestCase):
    def fixture(self,generator=None,annotator=None):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);f=upstream(tmp.name);b=base_result(f,generator)
        p=produce_annotations(f.io,f.inputs,b,annotator or AnnotationProtocolFixture(),ANNOTATOR);return f,b,p
    def review(self,f,b,p,reviewer=None,policy=AnnotationReviewPolicy()):
        return review_annotations(f.inputs,b,p,reviewer or ReviewProtocolFixture(),REVIEWER,policy)

    def test_actual_separate_review_covers_each_subject_and_completeness_dimension(self):
        f,b,p=self.fixture();provider=ReviewProtocolFixture();r=self.review(f,b,p,provider)
        self.assertEqual(len(provider.requests),1);self.assertEqual({j.subject_id for j in r.judgments},set(subjects(p.annotations)))
        payload=json.loads(provider.requests[0].messages[1]['content'])
        self.assertEqual(payload['grounded_narration']['utterances'][0]['text'],b.execution.snapshot.utterances[0].text)
        self.assertEqual(payload['grounded_narration']['inputs']['source_pages'][0]['text'],f.inputs.catalog.pages[0].text)
        self.assertIn('untrusted DATA',provider.requests[0].messages[0]['content'])

    def test_default_policy_does_not_trust_supported_model_judgments(self):
        f,b,p=self.fixture();r=self.review(f,b,p);report=annotation_review_qa(b.execution.snapshot,p,r)
        self.assertEqual(approved_subjects(p.annotations,r),frozenset())
        self.assertEqual(report.status,'REVIEW_REQUIRED');self.assertIn('ANNOTATION_REVIEW_UNVERIFIED',codes(report))

    def test_observed_annotation_issue_blocks_even_when_reviewer_is_untrusted(self):
        f,b,p=self.fixture()
        def mutate(payload,value,n):value['judgments'][0].update(verdict='ISSUE',rationale='Claim boundary omits a condition.');return value
        r=self.review(f,b,p,ReviewProtocolFixture(mutate));report=annotation_review_qa(b.execution.snapshot,p,r)
        self.assertEqual(report.status,'BLOCKED');self.assertIn('ANNOTATION_REVIEW_ISSUE',codes(report))

    def test_reviewer_can_detect_an_omitted_term_even_when_empty_terms_parse(self):
        f,b,p=self.fixture(annotator=AnnotationProtocolFixture(lambda p,v,n:{**v,'terms':[]}))
        def mutate(payload,value,n):
            next(j for j in value['judgments'] if j['subject_id']=='completeness:AUDIENCE').update(verdict='ISSUE',rationale='Domain term electrons was omitted.')
            return value
        r=self.review(f,b,p,ReviewProtocolFixture(mutate));self.assertEqual(annotation_review_qa(b.execution.snapshot,p,r).status,'BLOCKED')

    def test_stale_missing_or_duplicate_review_subjects_fail_without_partial_support(self):
        for kind in ('binding','missing','duplicate'):
            f,b,p=self.fixture()
            def mutate(payload,value,n):
                if kind=='binding':value['annotation_fingerprint']='sha256:'+'0'*64
                elif kind=='missing':value['judgments'].pop()
                else:value['judgments'].append(value['judgments'][0])
                return value
            provider=ReviewProtocolFixture(mutate);r=self.review(f,b,p,provider,trusted_review_policy())
            with self.subTest(kind=kind):
                self.assertEqual(len(provider.requests),2);self.assertTrue(r.failures);self.assertEqual(r.judgments,())
                self.assertEqual(approved_subjects(p.annotations,r),frozenset())

    def test_uncertain_or_low_confidence_is_not_admitted_by_a_trusted_identity(self):
        for change in ({'verdict':'UNCERTAIN'},{'confidence':.2}):
            f,b,p=self.fixture()
            def mutate(payload,value,n):value['judgments'][0].update(change);return value
            r=self.review(f,b,p,ReviewProtocolFixture(mutate),trusted_review_policy());subject=r.judgments[0].subject_id
            self.assertLess(len(approved_subjects(p.annotations,r)),len(subjects(p.annotations)))
            self.assertIn('ANNOTATION_REVIEW_UNVERIFIED',codes(annotation_review_qa(b.execution.snapshot,p,r)))

    def test_boolean_confidence_or_model_authored_completion_flag_is_rejected(self):
        for flag in (False,True):
            f,b,p=self.fixture()
            def mutate(payload,value,n):
                if flag:value['annotation_review_completed']=True
                else:value['judgments'][0]['confidence']=True
                return value
            r=self.review(f,b,p,ReviewProtocolFixture(mutate));self.assertTrue(r.failures);self.assertFalse(r.judgments)

    def test_wrong_provider_identity_or_refusal_cannot_attest_annotations(self):
        for change in ({'model':'unexpected'},{'finish_reason':'refusal'}):
            class Provider(ReviewProtocolFixture):
                def invoke(self,request):return replace(super().invoke(request),**change)
            f,b,p=self.fixture();provider=Provider();r=self.review(f,b,p,provider)
            self.assertTrue(r.failures);self.assertEqual(len(provider.requests),1)

    def test_annotator_cannot_be_its_own_configured_reviewer(self):
        f,b,p=self.fixture();provider=ReviewProtocolFixture()
        with self.assertRaisesRegex(ValueError,'separately configured'):
            review_annotations(f.inputs,b,p,provider,replace(ANNOTATOR,adapter_version='different-adapter'))
        self.assertEqual(provider.requests,[])

    def test_transport_failures_are_bounded_and_details_are_not_copied(self):
        class Provider:
            calls=0
            def invoke(self,request):self.calls+=1;raise RuntimeError('private access-token details')
        f,b,p=self.fixture();provider=Provider();r=self.review(f,b,p,provider)
        self.assertEqual(provider.calls,2);self.assertNotIn('private',repr(r));self.assertEqual(r.failures,('PROVIDER_EXECUTION_FAILED',))

    def test_review_context_budget_retains_explicit_unverified_completeness(self):
        f,b,p=self.fixture();provider=ReviewProtocolFixture()
        r=self.review(f,b,p,provider,AnnotationReviewPolicy(execution=DirectingPolicy(maximum_request_characters=20)))
        self.assertEqual(provider.requests,[]);self.assertTrue(r.failures)
        self.assertIn('ANNOTATION_COMPLETENESS_UNVERIFIED',codes(annotation_review_qa(b.execution.snapshot,p,r)))

    def test_edited_receipt_or_annotations_invalidates_review(self):
        f,b,p=self.fixture();r=self.review(f,b,p)
        for bad in (replace(r,judgments=()),replace(r,annotation_fingerprint='sha256:'+'0'*64)):
            with self.assertRaises(ValueError):approved_subjects(p.annotations,bad)

    def test_review_removes_only_verified_audience_completion_flag_and_never_infers_age(self):
        f,b,p=self.fixture();rt=runtime(review_policy=trusted_review_policy())
        result=rt.enrich(f.io,f.inputs,b,ProtocolFixtureProvider(),IDENTITY,SemanticExecutionPolicy())
        audience=next(r for r in result.qa_reports if r.task_id=='BIE-DIR-QA-005')
        self.assertNotIn('AUDIENCE_ANNOTATIONS_UNREVIEWED',codes(audience))
        self.assertIn('AUDIENCE_TARGET_UNSPECIFIED',codes(audience));self.assertEqual(result.status,'REVIEW_REQUIRED')

    def test_purposeful_repetition_exemption_requires_complete_trusted_review(self):
        repeated='Some electrons are free to move through the metal, so charge can pass along it.'
        def narration(payload,value,n):
            if payload['operation']=='NARRATE' and payload['scene']['scene_id'].endswith(':2'):value['beats'][0]['text']=repeated
            return value
        def annotate(payload,value,n):
            matches=[c['span'] for c in value['claims'] if c['span']['quote']==repeated]
            value['repetitions']=[{'first':matches[0],'repeated':matches[1],'mode':'RECAP',
                'evidence_ids':value['claims'][0]['evidence_ids'],'objective_ids':[payload['inputs']['objectives'][0]['objective_id']],
                'rationale':'Controlled recap justification for the explicit duplicate.','confidence':.95}]
            return value
        f,b,p=self.fixture(generator=DirectorProtocolFixture(narration),annotator=AnnotationProtocolFixture(annotate))
        for policy,expected in ((AnnotationReviewPolicy(),0),(trusted_review_policy(),1)):
            rt=runtime(annotator=AnnotationProtocolFixture(annotate),review_policy=policy)
            result=rt.enrich(f.io,f.inputs,b,ProtocolFixtureProvider(),IDENTITY,SemanticExecutionPolicy())
            repeat=next(r for r in result.qa_reports if r.task_id=='BIE-DIR-QA-004')
            self.assertEqual(len(result.applied_repetition_subjects),expected)
            self.assertEqual('PURPOSEFUL_REPETITION_RETAINED' in codes(repeat),bool(expected))

    def test_forward_reference_or_missing_concept_foundation_produces_actual_qa_blocker(self):
        for kind in ('reference','concept'):
            f,b,p=self.fixture()
            def mutate(payload,value,n):
                if kind=='reference':value['discourse'][0]['references']=[payload['utterances'][-1]['utterance_id']]
                else:value['discourse'][0]['required_concepts']=value['discourse'][0]['introduced_concepts']
                return value
            result=runtime(annotator=AnnotationProtocolFixture(mutate)).enrich(f.io,f.inputs,b,ProtocolFixtureProvider(),IDENTITY,SemanticExecutionPolicy())
            report=next(r for r in result.qa_reports if r.task_id=='BIE-DIR-QA-003')
            self.assertEqual(report.status,'BLOCKED');self.assertEqual(result.status,'BLOCKED')

    def test_fine_claim_contradiction_cannot_be_cleared_by_annotation_review(self):
        f,b,p=self.fixture();critic=ProtocolFixtureProvider(lambda p,n:response_record(p,verdict='CONTRADICTED'))
        result=runtime(review_policy=trusted_review_policy()).enrich(f.io,f.inputs,b,critic,IDENTITY,SemanticExecutionPolicy())
        self.assertEqual(result.status,'BLOCKED');self.assertEqual(result.semantic_evaluation.status,'BLOCKED');self.assertFalse(result.accepted)

    def test_source_grounded_advisory_uses_explicit_curriculum_policy_without_guessing_age(self):
        from unittest.mock import patch
        from input_fixtures import CASES
        from bie.director.age_level_qa import AudienceTarget
        warning='Never touch an exposed live electrical conductor.'
        def narration(payload,value,n):
            if payload['operation']=='NARRATE' and payload['scene']['scene_id'].endswith(':2'):
                value['beats'][0]['text']+=' '+warning
            return value
        def annotate(payload,value,n):
            claim=next(c for c in value['claims'] if c['span']['quote']==warning)
            value['advisories']=[{'advisory_id':'electrical-warning','span':claim['span'],'category':'HAZARDOUS_ACTIVITY',
                'rationale':'The actual source and narration discuss an exposed live electrical conductor.','confidence':.95}]
            return value
        with patch.dict(CASES,{'science':{**CASES['science'],'text':CASES['science']['text']+' '+warning}}):
            f,b,p=self.fixture(generator=DirectorProtocolFixture(narration),annotator=AnnotationProtocolFixture(annotate))
        self.assertEqual(p.annotations.advisories[0].minimum_age,0)
        target=AudienceTarget(12,14,0,('UNDERSTAND',),'Explicit fictional curriculum test policy; not empirical age guidance')
        policy=AnnotationPolicy(audience_target=target,advisory_age_rules=(('HAZARDOUS_ACTIVITY',18),))
        result=runtime(annotator=AnnotationProtocolFixture(annotate),policy=policy).enrich(
            f.io,f.inputs,b,ProtocolFixtureProvider(),IDENTITY,SemanticExecutionPolicy())
        report=next(q for q in result.qa_reports if q.task_id=='BIE-DIR-QA-005')
        self.assertIn('CONTENT_OUTSIDE_DECLARED_AGE_POLICY',codes(report));self.assertEqual(result.status,'BLOCKED')

    def test_emphasis_recomposes_estimated_timing_without_changing_text_or_response_pause(self):
        f,b,p=self.fixture();result=runtime().enrich(f.io,f.inputs,b,ProtocolFixtureProvider(),IDENTITY,SemanticExecutionPolicy())
        self.assertEqual(result.execution.snapshot,b.execution.snapshot);self.assertEqual(result.execution.pauses,b.execution.pauses)
        self.assertGreater(result.execution.timeline.duration_ms,b.execution.timeline.duration_ms)
        self.assertTrue(result.execution.emphasis.anchors)
        pacing=next(r for r in result.qa_reports if r.task_id=='BIE-DIR-QA-006')
        self.assertNotIn('PACING_ANNOTATION_INCOMPLETE',codes(pacing))
        self.assertNotIn('REQUIRED_REFLECTION_SHORTFALL',codes(pacing));self.assertFalse(result.accepted)


if __name__=='__main__':unittest.main()
