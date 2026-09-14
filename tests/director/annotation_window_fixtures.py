"""Authored protocol responses; no live-model teaching or review claim."""
import copy,json
from dataclasses import asdict
from bie.model_gateway.model_interface import ModelResponse
from bie.director.annotation_window_context import WindowedAnnotationPolicy,WindowedAnnotationReviewPolicy
from bie.director.narration_annotations import produce_annotations
from annotation_fixtures import ANNOTATOR
from annotation_review_fixtures import REVIEWER,review_record,runtime
from teaching_fixtures import context_annotation_record


def window_annotation_record(payload):
    data=copy.deepcopy(payload)
    # The old fixture declares a term only where its label is actually spoken.
    graph=data['inputs'].get('teaching_context',{}).get('knowledge_graph',{}).get('nodes',{})
    if graph:
        data['inputs']['teaching_context']['knowledge_graph']['nodes']={k:v for k,v in graph.items()
            if any(v['label'].casefold() in u['text'].casefold() for u in data['utterances'])}
    value=context_annotation_record(data)
    if payload['operation']=='ANNOTATE_SCENE':
        for key,id_key in (('claims','claim_id'),('advisories','advisory_id'),('emphasis','anchor_id'),('pacing','beat_id')):
            for row in value[key]:row[id_key]=payload['annotation_id_prefix']+row[id_key]
        value['scope_fingerprint']=payload['scope_fingerprint']
        return value
    return {k:value[k] for k in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint','discourse','transitions','terms','repetitions','review_reasons')}|{
        'local_production_fingerprint':payload['local_production_fingerprint']}


class WindowAnnotationFixture:
    def __init__(self,transform=None):self.requests=[];self.transform=transform
    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content']);value=window_annotation_record(payload)
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(ANNOTATOR.provider,ANNOTATOR.model,value,{},'completed',{'test_fixture':True})


class WindowReviewFixture:
    def __init__(self,transform=None):self.requests=[];self.transform=transform
    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content']);value=review_record(payload)
        value['review_scope_fingerprint']=payload['review_scope_fingerprint']
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(REVIEWER.provider,REVIEWER.model,value,{},'completed',{'test_fixture':True})


def production(f,base,provider=None,policy=WindowedAnnotationPolicy()):
    return produce_annotations(f.io,f.inputs,base,provider or WindowAnnotationFixture(),ANNOTATOR,policy)


def window_runtime(annotator=None,reviewer=None,policy=WindowedAnnotationPolicy(),review_policy=WindowedAnnotationReviewPolicy()):
    return runtime(annotator=annotator or WindowAnnotationFixture(),reviewer=reviewer or WindowReviewFixture(),policy=policy,review_policy=review_policy)
