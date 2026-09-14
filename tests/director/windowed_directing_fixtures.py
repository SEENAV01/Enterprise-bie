"""Controlled responses for window protocol and execution tests, not a teacher model."""
from dataclasses import asdict
import copy, json
from bie.model_gateway.model_interface import ModelResponse
from bie.director.director_artifacts import canonical
from bie.director.grounded_directing import execute_grounded_director
from bie.director.context_windows import WindowedDirectingPolicy
from directing_fixtures import GENERATOR
from semantic_fixtures import ProtocolFixtureProvider, IDENTITY
from teaching_fixtures import ContextAnnotationFixture


def response_record(payload, extra_scene=False):
    inputs=payload['inputs']; bindings={b['decision_id']:b for b in inputs['teaching_bindings']}
    context=inputs.get('teaching_context',{}); nodes=context.get('knowledge_graph',{}).get('nodes',{})
    objectives={o['objective_id']:o for o in inputs['objectives']}
    obligations=context.get('teaching_obligations',[])
    if payload['operation']=='PLAN_WINDOW':
        scenes=[]
        for did in payload['window']['decision_ids']:
            b=bindings[did]; related=[o for o in obligations if o['decision_id']==did]
            partitions=[[o] for o in related] if b['mode']['mode']=='DERIVATION' else [related]
            if extra_scene and b['mode']['mode']!='DERIVATION': partitions.append([])
            for i,part in enumerate(partitions):
                evidence={e for cell in b['assessments'] for e in cell['evidence_ids']}
                evidence.update(e for o in part for e in o['evidence_ids'])
                sid=payload['scene_id_prefix']+did+':'+str(i+1)
                scenes.append({'scene_id':sid,'title':'Explain '+did+' part '+str(i+1),'purpose':'Grounded teaching',
                    'teaching_mode':b['mode']['mode'],'pedagogy_decision_ids':[did],
                    'reasoning_decision_ids':b['reasoning_decision_ids'],'objective_ids':b['objective_ids'],
                    'evidence_ids':sorted(evidence),'parent_scene_ids':[scenes[-1]['scene_id']] if scenes else [],
                    'teaching_goal':'Explain the source statement and preserve its condition',
                    'teaching_moves':['DERIVE' if b['mode']['mode']=='DERIVATION' else 'EXPLAIN'],
                    'assessment_item_ids':[item for cell in b['assessments'] for item in cell['item_ids']] if i==len(partitions)-1 else [],
                    **({'teaching_obligation_ids':[o['obligation_id'] for o in part]} if context else {})})
        return {'input_fingerprint':inputs['input_fingerprint'],'lesson_id':inputs['lesson_id'],'scenes':scenes,
            'review_reasons':[],'global_input_fingerprint':payload['global_input_fingerprint'],'window_fingerprint':payload['window_fingerprint']}
    scene=payload['scene']; b=bindings[scene['pedagogy_decision_ids'][0]]
    cid=objectives[b['objective_ids'][0]]['concept_id']; node=nodes.get(cid)
    if node:
        definition=node['definitions'][0]['text']
        conditions=' '.join(c['condition'] for c in node['conditions'])
        label=node['label']
    else:
        label=objectives[b['objective_ids'][0]]['statement']; definition=inputs['source_passages'][0]['quote']; conditions=''
    if scene['teaching_moves']==['DERIVE']:
        oid=scene['teaching_obligation_ids'][0]; obligation=next(o for o in obligations if o['obligation_id']==oid)
        before,after=obligation['required_texts']
        text=label+': transform '+before+' to '+after+'. '+obligation['source_reason']+'. '+conditions
    else:
        text=label+': '+definition+' '+conditions
    assessment=[{'item_id':item,'question':'What does '+label+' establish, and what limit remains?',
        'expected_answer':definition+' '+conditions,'success_criteria':['Preserve the source statement and its explicit condition.'],
        'evidence_ids':scene['evidence_ids'],'response_time_ms':8000} for item in scene['assessment_item_ids']]
    return {'input_fingerprint':inputs['input_fingerprint'],'plan_fingerprint':payload['plan_fingerprint'],
        'scene_id':scene['scene_id'],'beats':[{'move':scene['teaching_moves'][0],'text':text,
            'evidence_ids':scene['evidence_ids'],'objective_ids':scene['objective_ids'],'pause_after_ms':500}],
        'assessments':assessment,'review_reasons':[],
        **({'teaching_realizations':[{'obligation_id':oid,'beat_index':0,'start_char':0,'end_char':len(text),'quote':text}
            for oid in scene['teaching_obligation_ids']]} if context else {}),
        'global_input_fingerprint':payload['global_input_fingerprint'],'window_fingerprint':payload['window_fingerprint']}


class WindowProtocolFixture:
    def __init__(self,transform=None,extra_scene=False): self.requests=[]; self.transform=transform; self.extra_scene=extra_scene
    def invoke(self,request):
        self.requests.append(request); payload=json.loads(request.messages[1]['content']); value=response_record(payload,self.extra_scene)
        if self.transform: value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(GENERATOR.provider,GENERATOR.model,value,{},'completed',{'test_fixture':True})


def windowed_base(f,provider=None,policy=WindowedDirectingPolicy()):
    return execute_grounded_director(f.io,f.inputs,provider or WindowProtocolFixture(),GENERATOR,
        ProtocolFixtureProvider(),IDENTITY,policy)
