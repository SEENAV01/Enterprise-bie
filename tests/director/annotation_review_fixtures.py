"""Separate reviewer fixtures; explicitly controlled, not empirical quality."""
from dataclasses import replace
import copy,json
from bie.model_gateway.model_interface import ModelResponse
from bie.director.semantic_execution import EvaluatorIdentity
from bie.director.narration_annotations import AnnotationPolicy
from bie.director.annotation_review import AnnotationReviewPolicy,reviewer_key
from bie.director.annotated_directing import AnnotationRuntime
from annotation_fixtures import ANNOTATOR,AnnotationProtocolFixture

REVIEWER=EvaluatorIdentity('protocol-fixture','annotation-reviewer','adapter/1')

def review_record(payload):
    return {k:payload[k] for k in ('input_fingerprint','snapshot_fingerprint','annotation_fingerprint')}|{
        'judgments':[{'subject_id':sid,'verdict':'SUPPORTED','confidence':.95,
          'rationale':'Controlled review verdict for protocol verification; not live model quality evidence.'} for sid in payload['required_subject_ids']]}


class ReviewProtocolFixture(AnnotationProtocolFixture):
    identity=REVIEWER
    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content']);value=review_record(payload)
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(self.identity.provider,self.identity.model,value,{},'completed',{'test_fixture':True})


def runtime(annotator=None,reviewer=None,policy=AnnotationPolicy(),review_policy=AnnotationReviewPolicy()):
    return AnnotationRuntime(annotator or AnnotationProtocolFixture(),ANNOTATOR,reviewer or ReviewProtocolFixture(),REVIEWER,policy,review_policy)


def trusted_review_policy(**changes):
    p=AnnotationReviewPolicy(**changes);return replace(p,trusted_reviewers=(reviewer_key(REVIEWER,p),))
