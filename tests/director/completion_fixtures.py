"""Controlled completion fixtures; these do not claim live teaching quality."""
from dataclasses import asdict
import copy
import json

from bie.model_gateway.model_interface import ModelResponse
from bie.director.contextual_teaching import obligation_move
from bie.director.director_artifacts import canonical
from bie.director.rich_teaching import (GroundedWorkedExample, GroundedDemonstration,
    GroundedInquiry, GroundedMisconception, GroundedNotation)
from bie.director.teaching_context import SourceExcerpt, publish_teaching_context
from bie.director.director_inputs import publish_pedagogy, load_director_inputs
from directing_fixtures import GENERATOR
from annotation_fixtures import ANNOTATOR
from annotation_review_fixtures import REVIEWER,review_record
from annotation_window_fixtures import window_annotation_record
from teaching_fixtures import context_annotation_record


def excerpt(f, text, occurrence=0):
    start = -1
    for _ in range(occurrence + 1):
        start = f.text.index(text, start + 1)
    return SourceExcerpt('evidence:' + f.case_id, start, start + len(text), text)


def rich_specs(f):
    spec = __import__('context_fixtures').SPECS[f.case_id]
    first = spec['concepts'][0][2]
    target = spec['concepts'][-1][2]
    condition = spec['condition']
    link = spec['link']
    cid = f.concepts[-1].concept_id
    return (
        GroundedWorkedExample('worked-1', cid, excerpt(f, first), (excerpt(f, target),), excerpt(f, condition)),
        GroundedDemonstration('demo-1', cid, excerpt(f, first), excerpt(f, target), excerpt(f, condition), excerpt(f, link)),
        GroundedInquiry('inquiry-1', cid, excerpt(f, target), excerpt(f, link), excerpt(f, condition)),
        GroundedMisconception('mis-1', cid, excerpt(f, condition), excerpt(f, target), excerpt(f, link)),
        GroundedNotation('notation-1', cid, excerpt(f, spec['concepts'][-1][1]),
            'the named concept spoken aloud', excerpt(f, target)),
    )


def rich_context(f, specs=None, observation_refs=()):
    context_ref = publish_teaching_context(f.io, f.run_id, f.source_ref, f.concepts,
        f.prerequisites, f.derivations, observation_refs, rich_teaching=rich_specs(f) if specs is None else specs)
    ped_ref = publish_pedagogy(f.io, f.run_id, f.source_ref, f.reasoning_ref, f.plan,
        f.objectives, f.bindings, teaching_context_ref=context_ref)
    inputs = load_director_inputs(f.io, f.reasoning_ref, ped_ref, run_id=f.run_id, **f.config)
    return context_ref, ped_ref, inputs


def rich_response(payload):
    inputs = payload['inputs']; bindings = {row['decision_id']: row for row in inputs['teaching_bindings']}
    obligations = {row['obligation_id']: row for row in inputs['teaching_context']['teaching_obligations']}
    if payload['operation'] in ('PLAN', 'PLAN_WINDOW'):
        decision_ids = payload.get('window', {}).get('decision_ids', list(bindings))
        scenes = []
        for decision_id in decision_ids:
            binding = bindings[decision_id]
            assigned = [row for row in obligations.values() if row['decision_id'] == decision_id]
            scene_id = payload.get('scene_id_prefix', 'scene:rich:') + decision_id
            evidence = {eid for cell in binding['assessments'] for eid in cell['evidence_ids']}
            evidence.update(eid for row in assigned for eid in row['evidence_ids'])
            moves = list(dict.fromkeys([obligation_move(row['kind']) for row in assigned] or ['EXPLAIN']))
            scenes.append({'scene_id': scene_id, 'title': 'Grounded rich teaching '+decision_id,
                'purpose': 'Realize every source-bound teaching strategy', 'teaching_mode': binding['mode']['mode'],
                'pedagogy_decision_ids': [decision_id], 'reasoning_decision_ids': binding['reasoning_decision_ids'],
                'objective_ids': binding['objective_ids'], 'evidence_ids': sorted(evidence),
                'parent_scene_ids': [scenes[-1]['scene_id']] if scenes else [],
                'teaching_goal': 'Teach and independently check the grounded concept',
                'teaching_moves': moves, 'assessment_item_ids': [item for cell in binding['assessments'] for item in cell['item_ids']],
                'teaching_obligation_ids': [row['obligation_id'] for row in assigned]})
        result = {'input_fingerprint': inputs['input_fingerprint'], 'lesson_id': inputs['lesson_id'],
            'scenes': scenes, 'review_reasons': ['CONTROLLED_RICH_TEACHING_FIXTURE']}
        if payload['operation'] == 'PLAN_WINDOW':
            result.update(global_input_fingerprint=payload['global_input_fingerprint'],
                window_fingerprint=payload['window_fingerprint'])
        return result
    scene = payload['scene']; binding = bindings[scene['pedagogy_decision_ids'][0]]
    beats = []; realizations = []
    for oid in scene.get('teaching_obligation_ids', []):
        obligation = obligations[oid]
        text = ' — '.join(obligation['required_texts']) + '. ' + obligation['source_reason']
        index = len(beats)
        beats.append({'move': obligation_move(obligation['kind']), 'text': text,
            'evidence_ids': obligation['evidence_ids'], 'objective_ids': obligation['objective_ids'],
            'pause_after_ms': 500})
        realizations.append({'obligation_id': oid, 'beat_index': index, 'start_char': 0,
            'end_char': len(text), 'quote': text})
    if not beats:
        text = inputs['source_passages'][0]['quote']
        beats.append({'move': scene['teaching_moves'][0], 'text': text,
            'evidence_ids': scene['evidence_ids'], 'objective_ids': scene['objective_ids'], 'pause_after_ms': 500})
    assessments = []
    for item in scene['assessment_item_ids']:
        assessments.append({'item_id': item, 'question': 'Explain the grounded concept and its stated limit.',
            'expected_answer': inputs['source_passages'][0]['quote'],
            'success_criteria': ['Use the cited source and preserve its applicability condition.'],
            'evidence_ids': scene['evidence_ids'], 'response_time_ms': 8000})
    result = {'input_fingerprint': inputs['input_fingerprint'], 'plan_fingerprint': payload['plan_fingerprint'],
        'scene_id': scene['scene_id'], 'beats': beats, 'assessments': assessments,
        'review_reasons': ['CONTROLLED_RICH_TEACHING_FIXTURE'], 'teaching_realizations': realizations}
    if 'window_fingerprint' in payload:
        result.update(global_input_fingerprint=payload['global_input_fingerprint'],
            window_fingerprint=payload['window_fingerprint'])
    return result


class RichTeachingProvider:
    def __init__(self, transform=None):
        self.requests = []; self.transform = transform

    def invoke(self, request):
        self.requests.append(request)
        payload = json.loads(request.messages[1]['content'])
        value = rich_response(payload)
        if self.transform:
            value = self.transform(payload, copy.deepcopy(value), len(self.requests))
        return ModelResponse(GENERATOR.provider, GENERATOR.model, canonical(value), {}, 'completed', {'fixture': True})


class HierarchicalAnnotationFixture:
    def __init__(self, transform=None):
        self.requests=[];self.transform=transform;self.emitted_terms=set()

    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content']);operation=payload['operation']
        if operation=='ANNOTATE_SCENE':
            value=window_annotation_record(payload)
        elif operation=='ANNOTATE_DISCOURSE_LEAF':
            full=context_annotation_record(payload)
            terms=[]
            for row in full['terms']:
                key=row['term'].casefold()
                if key not in self.emitted_terms:terms.append(row);self.emitted_terms.add(key)
            value={k:full[k] for k in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint','discourse','transitions','repetitions','review_reasons')}
            value['terms']=terms;value['scope_fingerprint']=payload['scope_fingerprint']
        elif operation=='ANNOTATE_DISCOURSE_BOUNDARY':
            full=context_annotation_record(payload)
            value={k:full[k] for k in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint','transitions')}
            value.update(scope_fingerprint=payload['scope_fingerprint'],review_reasons=[])
        elif operation=='ANNOTATE_DISCOURSE_RETRIEVAL':
            value={k:payload[k] for k in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint','scope_fingerprint')}
            value.update(reference_links=[],repetitions=[],review_reasons=[])
        else:raise AssertionError(operation)
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(ANNOTATOR.provider,ANNOTATOR.model,value,{},'completed',{'fixture':True})


class HierarchicalReviewFixture:
    def __init__(self,transform=None):self.requests=[];self.transform=transform
    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content']);value=review_record(payload)
        value['review_scope_fingerprint']=payload['review_scope_fingerprint']
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(REVIEWER.provider,REVIEWER.model,value,{},'completed',{'fixture':True})


class SceneCorrectionFixture:
    def __init__(self,transform=None,no_change=False):self.requests=[];self.transform=transform;self.no_change=no_change
    def invoke(self,request):
        self.requests.append(request);payload=json.loads(request.messages[1]['content'])
        if self.no_change:
            value=copy.deepcopy(payload['prior_scene'])
            value.update(input_fingerprint=payload['global_input_fingerprint'],plan_fingerprint=payload['global_plan_fingerprint'])
        else:
            adapted={**payload,'plan_fingerprint':payload['global_plan_fingerprint']}
            value=rich_response(adapted);value['input_fingerprint']=payload['global_input_fingerprint']
            value['plan_fingerprint']=payload['global_plan_fingerprint']
            value['beats'][0]['text']+=' Corrected locally after explicit review.'
            if value.get('teaching_realizations'):
                value['teaching_realizations'][0]['quote']=value['beats'][0]['text']
                value['teaching_realizations'][0]['end_char']=len(value['beats'][0]['text'])
        if self.transform:value=self.transform(payload,copy.deepcopy(value),len(self.requests))
        return ModelResponse(GENERATOR.provider,GENERATOR.model,value,{},'completed',{'fixture':True})
