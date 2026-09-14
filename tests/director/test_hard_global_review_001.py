from dataclasses import asdict,replace
import json,tempfile,unittest
from window_fixtures import long_upstream
from windowed_directing_fixtures import windowed_base
from annotation_window_fixtures import production,WindowReviewFixture
from annotation_review_fixtures import REVIEWER,ReviewProtocolFixture
from bie.director.annotation_review import (review_annotations,AnnotationReviewPolicy,
    annotation_review_qa,approved_subjects,reviewer_key,subjects)
from bie.director.annotation_window_context import WindowedAnnotationReviewPolicy
from bie.director.windowed_annotation_review import (WindowedAnnotationReview,verify_review_execution,
    verify_aggregate,review_contracts)
from bie.director.recovery_codec import annotation_production_record,annotation_review_record
from bie.director.director_artifacts import canonical,parse_json


class GlobalAnnotationReviewTests(unittest.TestCase):
    def fixture(self,**kwargs):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        return long_upstream(tmp.name,**({'units':3,'page_characters':500}|kwargs))
    def pair(self,f=None,provider=None,policy=None):
        f=f or self.fixture();b=windowed_base(f);p=production(f,b);r=provider or WindowReviewFixture();q=policy or WindowedAnnotationReviewPolicy()
        return f,b,p,r,review_annotations(f.inputs,b,p,r,REVIEWER,q)

    def test_large_annotation_gets_every_source_scene_and_one_global_review(self):
        f=self.fixture(units=8,page_characters=7000);b=windowed_base(f);p=production(f,b)
        old_provider=ReviewProtocolFixture();old=review_annotations(f.inputs,b,p,old_provider,REVIEWER,AnnotationReviewPolicy())
        self.assertEqual(old.failures,('DIRECTOR_CONTEXT_BUDGET_EXCEEDED',));self.assertFalse(old_provider.requests)
        r=WindowReviewFixture();review=review_annotations(f.inputs,b,p,r,REVIEWER,WindowedAnnotationReviewPolicy())
        self.assertEqual(len(r.requests),9);self.assertFalse(review.failures);verify_review_execution(f.inputs,b,p,review)

    def test_source_scopes_keep_complete_pages_and_global_scope_keeps_all_speech_without_pages(self):
        f,b,p,r,review=self.pair();payloads=[json.loads(x.messages[1]['content']) for x in r.requests]
        pages={x.page_id:x.text for x in f.inputs.catalog.pages};seen=set()
        for payload in payloads[:-1]:
            self.assertEqual(payload['review_kind'],'SOURCE_SCENES')
            for page in payload['grounded_narration']['inputs']['source_pages']:
                self.assertEqual(page['text'],pages[page['page_id']]);seen.add(page['page_id'])
        self.assertEqual(seen,set(pages));global_payload=payloads[-1]
        self.assertEqual(global_payload['review_kind'],'GLOBAL_DISCOURSE')
        self.assertFalse(global_payload['grounded_narration']['source_pages_in_this_request'])
        self.assertNotIn('source_pages',global_payload['grounded_narration']['inputs'])
        self.assertEqual([u['text'] for u in global_payload['grounded_narration']['utterances']],[u.text for u in b.execution.snapshot.utterances])

    def test_every_annotation_and_completeness_subject_has_scoped_observation(self):
        f,b,p,r,review=self.pair();observed={s for w in review.review_windows for s in w.required_subject_ids}
        self.assertEqual(observed,set(subjects(p.annotations)))
        self.assertEqual({j.subject_id for j in review.judgments},set(subjects(p.annotations)))
        self.assertEqual(len(review.judgments),len(subjects(p.annotations)))

    def test_global_interpretations_are_reviewed_in_global_and_relevant_source_scopes(self):
        f,b,p,r,review=self.pair();sid='discourse:'+p.annotations.discourse[-1].utterance_id
        scopes=[w.call.scope_id for w in review.review_windows if sid in w.required_subject_ids]
        self.assertIn('global:'+f.inputs.lesson_id,scopes);self.assertIn('source:'+b.plan.scenes[-1].scene_id,scopes)

    def test_distant_reference_retrieves_complete_antecedent_scene_for_source_review(self):
        f,b,p,_,_=self.pair()
        raw=parse_json(p.response_json);raw['discourse'][-1]['references']=[raw['discourse'][0]['utterance_id']]
        # Reconstruct a controlled, still structurally valid production so the
        # review scheduler must retrieve both exact scenes.
        from bie.director.narration_annotations import validate_annotations
        a=validate_annotations(raw,f.inputs,b,p.annotations.policy)
        p=replace(p,annotations=a,response_json=canonical(raw))
        contracts=tuple(review_contracts(f.inputs,b,p,WindowedAnnotationReviewPolicy()))
        target=next(c for c in contracts if c[0]=='source:'+b.plan.scenes[-1].scene_id)
        self.assertIn(b.plan.scenes[0].scene_id,target[1]);self.assertIn(b.plan.scenes[-1].scene_id,target[1])
        texts=[u['text'] for u in target[3]['grounded_narration']['utterances']]
        self.assertEqual(texts,[u.text for u in b.execution.snapshot.utterances if u.scene_id in target[1]])

    def test_one_scope_failure_is_retained_and_cannot_create_approval(self):
        f=self.fixture();b=windowed_base(f);p=production(f,b)
        first='source:'+b.plan.scenes[0].scene_id
        r=WindowReviewFixture(lambda payload,value,n:(_ for _ in ()).throw(RuntimeError('controlled')) if payload['target_scope']==first else value)
        policy=WindowedAnnotationReviewPolicy();policy=replace(policy,trusted_reviewers=(reviewer_key(REVIEWER,policy),))
        review=review_annotations(f.inputs,b,p,r,REVIEWER,policy)
        self.assertTrue(any(x.startswith(first+':') for x in review.failures));self.assertEqual(approved_subjects(p.annotations,review),frozenset())
        self.assertEqual(annotation_review_qa(b.execution.snapshot,p,review).status,'REVIEW_REQUIRED')

    def test_issue_dominates_supported_observations_from_other_scopes(self):
        f=self.fixture();b=windowed_base(f);p=production(f,b);target='discourse:'+p.annotations.discourse[0].utterance_id
        def issue(payload,value,n):
            if payload['target_scope'].startswith('source:'):
                for row in value['judgments']:
                    if row['subject_id']==target:row['verdict']='ISSUE';row['rationale']='Controlled observed omission.'
            return value
        review=review_annotations(f.inputs,b,p,WindowReviewFixture(issue),REVIEWER,WindowedAnnotationReviewPolicy())
        self.assertEqual(next(j.verdict for j in review.judgments if j.subject_id==target),'ISSUE')
        self.assertEqual(annotation_review_qa(b.execution.snapshot,p,review).status,'BLOCKED')

    def test_stale_scope_echo_and_missing_subject_become_explicit_failed_scope(self):
        for transform in (
            lambda p,v,n:{**v,'review_scope_fingerprint':'stale'},
            lambda p,v,n:{**v,'judgments':v['judgments'][:-1]}):
            f=self.fixture();b=windowed_base(f);p=production(f,b);r=WindowReviewFixture(transform)
            review=review_annotations(f.inputs,b,p,r,REVIEWER,WindowedAnnotationReviewPolicy())
            self.assertTrue(review.failures);self.assertTrue(any(j.verdict=='UNCERTAIN' for j in review.judgments))
            verify_review_execution(f.inputs,b,p,review)

    def test_unknown_or_duplicate_review_subject_is_rejected_by_bounded_retries(self):
        f=self.fixture();b=windowed_base(f);p=production(f,b)
        for transform in (
            lambda p,v,n:{**v,'judgments':v['judgments']+[dict(v['judgments'][0],subject_id='foreign')]},
            lambda p,v,n:{**v,'judgments':v['judgments']+[dict(v['judgments'][0])]}):
            r=WindowReviewFixture(transform);review=review_annotations(f.inputs,b,p,r,REVIEWER,WindowedAnnotationReviewPolicy())
            self.assertTrue(review.failures);verify_review_execution(f.inputs,b,p,review)

    def test_review_window_count_budget_fails_before_provider_calls(self):
        f=self.fixture();b=windowed_base(f);p=production(f,b);r=WindowReviewFixture()
        with self.assertRaises(Exception) as e:review_annotations(f.inputs,b,p,r,REVIEWER,WindowedAnnotationReviewPolicy(maximum_windows=3))
        self.assertIn('WINDOW_COUNT',str(e.exception));self.assertFalse(r.requests)

    def test_actual_requests_fit_unchanged_review_transport_budget(self):
        f,b,p,r,review=self.pair(self.fixture(units=8,page_characters=7000));policy=review.policy
        for request in r.requests:
            size=sum(len(m['content']) for m in request.messages)+len(canonical(request.response_schema))
            self.assertLessEqual(size,policy.execution.maximum_request_characters)

    def test_global_review_overflow_is_retained_after_all_source_scopes(self):
        f,b,p,r,review=self.pair(self.fixture(units=8));sizes=[sum(len(m['content']) for m in x.messages)+len(canonical(x.response_schema)) for x in r.requests]
        limit=sizes[-1]-512;self.assertGreater(limit,max(sizes[:-1]))
        policy=WindowedAnnotationReviewPolicy();policy=replace(policy,execution=replace(policy.execution,maximum_request_characters=limit))
        r=WindowReviewFixture();review=review_annotations(f.inputs,b,p,r,REVIEWER,policy)
        self.assertEqual(len(r.requests),len(b.plan.scenes));self.assertTrue(any(x.startswith('global:') for x in review.failures))
        self.assertEqual(approved_subjects(p.annotations,review),frozenset());verify_review_execution(f.inputs,b,p,review)

    def test_corrected_retry_fingerprints_reconstruct(self):
        f=self.fixture();b=windowed_base(f);p=production(f,b)
        r=WindowReviewFixture(lambda payload,value,n:{} if n==2 else value)
        review=review_annotations(f.inputs,b,p,r,REVIEWER,WindowedAnnotationReviewPolicy())
        self.assertEqual(len(review.attempts),len(review.review_windows)+1);verify_review_execution(f.inputs,b,p,review)

    def test_missing_extra_or_edited_request_evidence_fails_revalidation(self):
        f,b,p,r,review=self.pair();first=review.review_windows[0]
        bads=(replace(review,review_windows=review.review_windows[:-1]),replace(review,attempts=review.attempts[:-1]),
            replace(review,review_windows=(replace(first,call=replace(first.call,request_payload_fingerprint='edited')),)+review.review_windows[1:]),
            replace(review,review_windows=(first,first)+review.review_windows[1:]))
        for bad in bads:
            with self.subTest(),self.assertRaises(ValueError):verify_review_execution(f.inputs,b,p,bad)

    def test_changed_policy_or_input_revision_cannot_revalidate(self):
        f,b,p,r,review=self.pair()
        with self.assertRaises(ValueError):verify_review_execution(f.inputs,b,p,replace(review,policy=replace(review.policy,maximum_windows=9)))
        with self.assertRaises(ValueError):verify_review_execution(replace(f.inputs,title='changed'),b,p,review)

    def test_known_production_and_review_round_trip_without_class_selection_from_json(self):
        f,b,p,r,review=self.pair()
        decoded_p=annotation_production_record(parse_json(canonical(asdict(p))))
        decoded_r=annotation_review_record(parse_json(canonical(asdict(review))))
        self.assertEqual((decoded_p,decoded_r),(p,review));verify_review_execution(f.inputs,b,decoded_p,decoded_r)

    def test_stripped_window_metadata_cannot_fall_back_to_legacy_review(self):
        f,b,p,r,review=self.pair();raw=parse_json(canonical(asdict(review)));del raw['review_windows']
        with self.assertRaises(ValueError):annotation_review_record(raw)

    def test_separate_reviewer_identity_remains_required(self):
        f=self.fixture();b=windowed_base(f);p=production(f,b)
        with self.assertRaisesRegex(ValueError,'separate'):review_annotations(f.inputs,b,p,WindowReviewFixture(),p.identity,WindowedAnnotationReviewPolicy())

    def test_default_trust_boundary_stays_review_required(self):
        f,b,p,r,review=self.pair();self.assertEqual(approved_subjects(p.annotations,review),frozenset())
        report=annotation_review_qa(b.execution.snapshot,p,review)
        self.assertEqual(report.status,'REVIEW_REQUIRED');self.assertFalse(review.failures)


if __name__=='__main__':unittest.main()
