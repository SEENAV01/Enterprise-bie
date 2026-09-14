"""Preauthored teaching/annotation provider responses, not live-model evidence."""
import copy, json
from bie.model_gateway.model_interface import ModelResponse
from bie.director.grounded_directing import execute_grounded_director
from directing_fixtures import GENERATOR
from semantic_fixtures import ProtocolFixtureProvider, IDENTITY
from annotation_fixtures import ANNOTATOR, span


SCRIPTS = {
    'science': (
        ('pedagogy:charge', 'What electric current means', 'EXPLAIN',
         'Electric current is a flow of electric charge. Keep the distinction between charge and its carrier in view before we explain current in solid copper.'),
        ('pedagogy:copper', 'Identify the charge carriers in the solid metal', 'EXPLAIN',
         'In solid copper, mobile electrons carry electric current while the copper ions remain near their lattice positions. Conduction in solid copper is explained by the electrons that can move. This explanation applies to solid copper, not to every copper compound.')),
    'economics': (
        ('pedagogy:barter', 'Explain the matching requirement first', 'EXPLAIN',
         'The double coincidence of wants means that each trader must want what the other offers. Both wants must match for this direct barter; knowing only what one person wants does not establish that match.'),
        ('pedagogy:money', 'Explain separation and its condition', 'EXPLAIN',
         'An accepted medium of exchange lets a seller receive money and buy from a different person later. Selling and buying can therefore be separated. The medium must be accepted by the people involved; universal acceptance is not established.')),
    'math': (
        ('pedagogy:algebra', 'Apply the supplied first transformation', 'DERIVE',
         'For a real number x, combining like terms changes x + x to 2*x. The supplied rule is collecting like terms: two equal terms add to twice the term.'),
        ('pedagogy:algebra', 'Explain the next transformation and scope', 'DERIVE',
         'Next, change 2*x to x*2 by commutativity of multiplication: changing the factor order preserves the product. These transformations concern real numbers and do not establish a rule about arbitrary mathematical objects.')),
}
ASSESSMENTS = {
    'assessment:charge': ('What does electric current mean?', 'Electric current is a flow of electric charge.', ['Identify flow of electric charge.']),
    'assessment:copper': ('Which particles carry current in solid copper, and what do the ions do?',
        'Mobile electrons carry current; copper ions remain near their lattice positions.', ['Keep the explanation limited to solid copper.']),
    'assessment:barter': ('What must match in the double coincidence of wants?',
        'Each trader must want what the other offers.', ['Explain both wants, not only one.']),
    'assessment:money': ('How can money separate selling from buying, and what condition matters?',
        'An accepted medium of exchange lets a seller receive money and buy from another person later.', ['The people involved must accept the medium.']),
    'assessment:algebra': ('State both supplied transformations and their reasons for real x.',
        'x + x becomes 2*x by collecting like terms; 2*x becomes x*2 by commutativity of multiplication.',
        ['Two equal terms add to twice the term.', 'Changing the factor order preserves the product for real numbers.']),
}


def teaching_record(payload):
    inputs = payload['inputs']; case = inputs['lesson_id'].split(':')[-1]
    bindings = {b['decision_id']:b for b in inputs['teaching_bindings']}
    obligations = inputs['teaching_context']['teaching_obligations']; scripts = SCRIPTS[case]
    if payload['operation'] == 'PLAN':
        scenes = []
        for i, (did, title, move, text) in enumerate(scripts):
            b = bindings[did]; relevant = [o for o in obligations if o['decision_id'] == did]
            assigned = relevant[i:i+1] if case == 'math' else relevant
            last = not any(row[0] == did for row in scripts[i+1:])
            scenes.append({'scene_id': 'scene:' + case + ':' + str(i+1), 'title': title, 'purpose': 'Teach ' + title,
                'teaching_mode': b['mode']['mode'], 'pedagogy_decision_ids': [did],
                'reasoning_decision_ids': b['reasoning_decision_ids'], 'objective_ids': b['objective_ids'],
                'evidence_ids': sorted({e for c in b['assessments'] for e in c['evidence_ids']}),
                'parent_scene_ids': [scenes[-1]['scene_id']] if scenes else [], 'teaching_goal': title,
                'teaching_moves': [move], 'assessment_item_ids': [i for c in b['assessments'] for i in c['item_ids']] if last else [],
                'teaching_obligation_ids': [o['obligation_id'] for o in assigned]})
        return {'input_fingerprint': inputs['input_fingerprint'], 'lesson_id': inputs['lesson_id'], 'scenes': scenes, 'review_reasons': []}
    scene = payload['scene']; index = int(scene['scene_id'].split(':')[-1])-1
    did, title, move, text = scripts[index]; evidence = scene['evidence_ids']
    assessments = []
    for item in scene['assessment_item_ids']:
        question, answer, criteria = ASSESSMENTS[item]
        assessments.append({'item_id': item, 'question': question, 'expected_answer': answer,
            'success_criteria': criteria, 'evidence_ids': evidence, 'response_time_ms': 8000})
    return {'input_fingerprint': inputs['input_fingerprint'], 'plan_fingerprint': payload['plan_fingerprint'],
        'scene_id': scene['scene_id'], 'beats': [{'move': move, 'text': text, 'evidence_ids': evidence,
            'objective_ids': scene['objective_ids'], 'pause_after_ms': 700}], 'assessments': assessments, 'review_reasons': [],
        'teaching_realizations': [{'obligation_id': oid, 'beat_index': 0, 'start_char': 0, 'end_char': len(text), 'quote': text}
            for oid in scene['teaching_obligation_ids']]}


class TeachingProtocolFixture:
    def __init__(self, transform=None): self.requests=[]; self.transform=transform
    def invoke(self, request):
        self.requests.append(request); payload=json.loads(request.messages[1]['content']); value=teaching_record(payload)
        if self.transform: value=self.transform(payload, copy.deepcopy(value), len(self.requests))
        return ModelResponse(GENERATOR.provider, GENERATOR.model, value, {}, 'completed', {'test_fixture': True})


def context_annotation_record(payload):
    rows=payload['utterances']; index={r['utterance_id']:r for r in rows}; sentences=payload['complete_sentence_spans']
    common={'confidence': .95, 'rationale': 'Controlled context annotation fixture; semantic quality is unproven.'}
    claims=[{'claim_id':'context-claim:'+str(i), 'span':span(index[s['utterance_id']],s['start_char'],s['end_char']),
        'kind':'QUESTION' if index[s['utterance_id']]['text'][s['start_char']:s['end_char']].endswith('?') else 'FACT',
        'evidence_ids':index[s['utterance_id']]['evidence_ids'], **common}
        for i,s in enumerate(sentences)]
    by_objective={o['objective_id']:o['concept_id'] for o in payload['inputs']['objectives']}
    questions={q:item for item,q,a in payload['assessment_bindings']}; answers={a:item for item,q,a in payload['assessment_bindings']}
    disc=[]; seen=set(); pacing=[]; by_scene={}
    for i,row in enumerate(rows):
        uid=row['utterance_id']; by_scene.setdefault(row['scene_id'],[]).append(row)
        concepts={by_objective[o] for o in row['objective_ids']}
        disc.append({'utterance_id':uid,'introduced_concepts':sorted(concepts-seen),'required_concepts':sorted(concepts & seen),
            'references':[rows[i-1]['utterance_id']] if i else [], 'opens_questions':[questions[uid]] if uid in questions else [],
            'answers_questions':[answers[uid]] if uid in answers else [], **common}); seen.update(concepts)
        obligation=payload['pacing_obligations'][uid]
        pacing.append({'beat_id':'context-pace:'+str(i),'span':span(row),'mode':obligation['required_mode'] or 'EXPLAIN',
            'concept_ids':sorted(concepts),'evidence_ids':row['evidence_ids'],'objective_ids':row['objective_ids'],
            'minimum_reflection_ms':obligation['minimum_reflection_ms'], **common})
    transitions=[]; order=list(by_scene)
    for left,right in zip(order,order[1:]):
        row=by_scene[right][0]; s=next(s for s in sentences if s['utterance_id']==row['utterance_id'])
        transitions.append({'from_scene':left,'to_scene':right,'relation':'PREREQUISITE',
            'cue_span':span(row,s['start_char'],s['end_char']), **common})
    terms=[]; emphasis=[]
    for cid,concept in payload['inputs']['teaching_context']['knowledge_graph']['nodes'].items():
        label=concept['label']; row=next(r for r in rows if label.casefold() in r['text'].casefold())
        start=row['text'].casefold().index(label.casefold())
        terms.append({'term':label,'definition':span(row),'evidence_ids':row['evidence_ids'], **common})
        emphasis.append({'anchor_id':'emphasis:'+cid,'span':span(row,start,start+len(label)),'concept_id':cid,
            'strength':.7,'evidence_ids':row['evidence_ids'], **common})
    return {k:payload[k] for k in ('input_fingerprint','snapshot_fingerprint','plan_fingerprint')} | {
        'claims':claims,'discourse':disc,'transitions':transitions,'terms':terms,'advisories':[],
        'repetitions':[],'emphasis':emphasis,'pacing':pacing,'review_reasons':[]}


class ContextAnnotationFixture:
    def __init__(self, transform=None): self.requests=[]; self.transform=transform
    def invoke(self, request):
        self.requests.append(request); payload=json.loads(request.messages[1]['content']); value=context_annotation_record(payload)
        if self.transform: value=self.transform(payload, copy.deepcopy(value), len(self.requests))
        return ModelResponse(ANNOTATOR.provider, ANNOTATOR.model, value, {}, 'completed', {'test_fixture': True})


def context_base(f, generator=None, critic=None):
    return execute_grounded_director(f.io, f.inputs, generator or TeachingProtocolFixture(), GENERATOR,
        critic or ProtocolFixtureProvider(), IDENTITY)
