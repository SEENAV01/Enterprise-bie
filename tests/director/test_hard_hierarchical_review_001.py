from dataclasses import asdict,replace
import tempfile
import unittest
from pathlib import Path

from bie.director.annotation_review import review_annotations,annotation_review_qa,approved_subjects,reviewer_key,COMPLETENESS
from bie.director.context_windows import WindowedDirectingPolicy
from bie.director.director_artifacts import canonical,parse_json
from bie.director.grounded_directing import execute_grounded_director
from bie.director.hierarchical_annotations import HierarchicalAnnotationPolicy
from bie.director.hierarchical_annotation_review import (HierarchicalAnnotationReviewPolicy,
    HierarchicalAnnotationReview,verify_hierarchical_review)
from bie.director.narration_annotations import produce_annotations
from bie.director.recovery_codec import annotation_review_record
from context_fixtures import context_upstream
from completion_fixtures import (rich_context,RichTeachingProvider,HierarchicalAnnotationFixture,HierarchicalReviewFixture)
from directing_fixtures import GENERATOR
from annotation_fixtures import ANNOTATOR
from annotation_review_fixtures import REVIEWER
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY


class HierarchicalReviewTests(unittest.TestCase):
    def fixture(self,transform=None,review_policy=None):
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        base=execute_grounded_director(f.io,inputs,RichTeachingProvider(),GENERATOR,ProtocolFixtureProvider(),IDENTITY,
            WindowedDirectingPolicy(continuity_reserve_characters=1000))
        ap=HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1);production=produce_annotations(
            f.io,inputs,base,HierarchicalAnnotationFixture(),ANNOTATOR,ap)
        policy=review_policy or HierarchicalAnnotationReviewPolicy()
        provider=HierarchicalReviewFixture(transform);review=review_annotations(inputs,base,production,provider,REVIEWER,policy)
        return f,inputs,base,production,provider,review

    def test_source_and_matching_hierarchical_scopes_all_execute(self):
        _,inputs,base,production,provider,review=self.fixture()
        self.assertIsInstance(review,HierarchicalAnnotationReview)
        self.assertEqual(len(base.plan.scenes)+len(production.discourse_scopes),len(review.review_windows))
        self.assertEqual(len(review.review_windows),len(provider.requests))
        self.assertEqual(review,verify_hierarchical_review(inputs,base,production,review))

    def test_no_review_request_contains_the_whole_spoken_lesson_marker(self):
        _,_,_,_,provider,_=self.fixture()
        self.assertFalse(any('COMPLETE_SPOKEN_LESSON_DISCOURSE' in request.messages[1]['content'] for request in provider.requests))

    def test_all_annotation_and_completeness_subjects_are_aggregated(self):
        _,_,base,production,_,review=self.fixture()
        report=annotation_review_qa(base.execution.snapshot,production,review)
        self.assertNotEqual('BLOCKED',report.status)
        self.assertEqual({j.subject_id for j in review.judgments},
            {r.subject_id for r in production.annotations.rationales}|{'completeness:'+x for x in COMPLETENESS})

    def test_issue_in_one_scope_dominates_supported_observations(self):
        target={'value':None}
        def change(payload,value,count):
            if count==1:
                target['value']=value['judgments'][0]['subject_id'];value['judgments'][0]['verdict']='ISSUE';value['judgments'][0]['confidence']=.99
            return value
        *_,review=self.fixture(change)
        self.assertEqual('ISSUE',next(j.verdict for j in review.judgments if j.subject_id==target['value']))

    def test_failed_scope_remains_evidence_and_prevents_trust(self):
        class Failing(HierarchicalReviewFixture):
            def invoke(self,request):
                if len(self.requests)<2:self.requests.append(request);raise RuntimeError('controlled failure')
                return super().invoke(request)
        f=context_upstream(Path(tempfile.mkdtemp()),'science');_,_,inputs=rich_context(f)
        base=execute_grounded_director(f.io,inputs,RichTeachingProvider(),GENERATOR,ProtocolFixtureProvider(),IDENTITY,
            WindowedDirectingPolicy(continuity_reserve_characters=1000))
        production=produce_annotations(f.io,inputs,base,HierarchicalAnnotationFixture(),ANNOTATOR,HierarchicalAnnotationPolicy(maximum_scenes_per_leaf=1))
        policy=HierarchicalAnnotationReviewPolicy();review=review_annotations(inputs,base,production,Failing(),REVIEWER,policy)
        self.assertTrue(review.failures);self.assertFalse(approved_subjects(production.annotations,review))

    def test_review_policy_can_trust_only_exact_configured_reviewer_key(self):
        base=HierarchicalAnnotationReviewPolicy();trusted=replace(base,trusted_reviewers=(reviewer_key(REVIEWER,base),))
        _,_,_,production,_,review=self.fixture(review_policy=trusted)
        self.assertTrue(approved_subjects(production.annotations,review))

    def test_persisted_review_roundtrips_and_revalidates_schedule(self):
        _,inputs,base,production,_,review=self.fixture();decoded=annotation_review_record(parse_json(canonical(asdict(review))))
        self.assertEqual(review,decoded);verify_hierarchical_review(inputs,base,production,decoded)

    def test_stripped_schedule_or_policy_metadata_is_rejected(self):
        _,_,_,_,_,review=self.fixture();raw=parse_json(canonical(asdict(review)))
        raw.pop('discourse_schedule_fingerprint')
        with self.assertRaises(ValueError):annotation_review_record(raw)


if __name__=='__main__':unittest.main()
