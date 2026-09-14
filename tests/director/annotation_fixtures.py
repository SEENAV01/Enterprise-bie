"""Explicit protocol fixtures for annotations and review; no live quality claim."""
from dataclasses import replace
import copy,json
from bie.model_gateway.model_interface import ModelResponse
from bie.director.semantic_execution import EvaluatorIdentity
from bie.director.grounded_directing import execute_grounded_director
from bie.director.narration_annotations import AnnotationPolicy
from directing_fixtures import DirectorProtocolFixture,GENERATOR
from semantic_fixtures import ProtocolFixtureProvider,IDENTITY

ANNOTATOR=EvaluatorIdentity('protocol-fixture','annotator','adapter/1')
TERMS={'science':'electrons','economics':'double coincidence of wants','history':'temporal order'}


def span(row,start=0,end=None):
    if end is None:end=len(row['text'])
    return {'utterance_id':row['utterance_id'],'start_char':start,'end_char':end,'quote':row['text'][start:end]}


def annotation_record(payload):
    rows=payload['utterances'];index={r['utterance_id']:r for r in rows};by_scene={}
    for row in rows:by_scene.setdefault(row['scene_id'],[]).append(row)
    sentences=payload['complete_sentence_spans'];cid=payload['inputs']['objectives'][0]['concept_id']
    common={'confidence':.95,'rationale':'Controlled protocol annotation, not independently established semantic quality.'}
    claims=[]
    for i,s in enumerate(sentences):
        selected=span(index[s['utterance_id']],s['start_char'],s['end_char'])
        claims.append({'claim_id':'atomic:'+str(i+1),'span':selected,'kind':'QUESTION' if selected['quote'].endswith('?') else 'FACT',
                       'evidence_ids':index[s['utterance_id']]['evidence_ids'],**common})
    questions={q:item for item,q,a in payload['assessment_bindings']};answers={a:item for item,q,a in payload['assessment_bindings']}
    disc=[];pending=[]
    for i,row in enumerate(rows):
        uid=row['utterance_id'];opening=[questions[uid]] if uid in questions else []
        if not opening and any(c['span']['utterance_id']==uid and c['kind']=='QUESTION' for c in claims):opening=[uid+':prompt']
        answer=[answers[uid]] if uid in answers else list(pending)
        disc.append({'utterance_id':uid,'introduced_concepts':[cid] if i==0 else [],'required_concepts':[] if i==0 else [cid],
            'references':[] if i==0 else [rows[i-1]['utterance_id']], 'opens_questions':opening,'answers_questions':answer,**common})
        pending=opening if uid not in questions else []
    transitions=[];order=list(by_scene)
    for i,(left,right) in enumerate(zip(order,order[1:])):
        row=by_scene[right][0];s=next(s for s in sentences if s['utterance_id']==row['utterance_id'])
        transitions.append({'from_scene':left,'to_scene':right,'relation':'EVIDENCE' if 'history' in right and i==0 else 'CONTRAST',
            'cue_span':span(row,s['start_char'],s['end_char']),**common})
    case=payload['inputs']['lesson_id'].split(':')[-1];term=TERMS[case]
    first=next(row for row in rows if term.casefold() in row['text'].casefold());start=first['text'].casefold().index(term.casefold())
    terms=[{'term':term,'evidence_ids':first['evidence_ids'],'definition':span(first),**common}]
    emphasis=[{'anchor_id':'anchor:core-term','span':span(first,start,start+len(term)),'concept_id':cid,
               'strength':.7,'evidence_ids':first['evidence_ids'],**common}]
    pacing=[]
    for i,row in enumerate(rows):
        obligation=payload['pacing_obligations'][row['utterance_id']]
        pacing.append({'beat_id':'pace:'+str(i+1),'span':span(row),'mode':obligation['required_mode'] or ('INTRODUCE' if i==0 else 'EXPLAIN'),
            'concept_ids':[cid],'evidence_ids':row['evidence_ids'],'objective_ids':row['objective_ids'],
            'minimum_reflection_ms':obligation['minimum_reflection_ms'],**common})
    return {k:payload[k] for k in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint')}|{
        'claims':claims,'discourse':disc,'transitions':transitions,'terms':terms,'advisories':[],
        'repetitions':[],'emphasis':emphasis,'pacing':pacing,'review_reasons':[]}


class AnnotationProtocolFixture:
    identity=ANNOTATOR
    def __init__(self,transform=None):self.requests=[];self.transform=transform
    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content']);value=annotation_record(payload)
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(self.identity.provider,self.identity.model,value,{},'completed',{'test_fixture':True})


def base_result(f,generator=None,critic=None):
    return execute_grounded_director(f.io,f.inputs,generator or DirectorProtocolFixture(),GENERATOR,
                                     critic or ProtocolFixtureProvider(),IDENTITY)

